# pylint: disable=no-member, missing-module-docstring, missing-function-docstring, unbalanced-tuple-unpacking
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageColor


def apply_noise(img, noise_level):
    if noise_level == 0:
        return img
    arr = np.array(img)
    noise = np.random.randint(-noise_level, noise_level, arr.shape, dtype=np.int16)
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))


def process_frame(img, algorithms, settings):
    orig_w, orig_h = img.width, img.height

    # preserve alpha before any conversion so transparent images stay correct
    alpha = img.convert("RGBA").split()[3]

    scale = settings["scale"] / 100.0
    if scale != 1.0:
        new_w = max(1, int(orig_w * scale))
        new_h = max(1, int(orig_h * scale))
        img_rgb = img.convert("RGB").resize((new_w, new_h), Image.LANCZOS)
        alpha = alpha.resize((new_w, new_h), Image.LANCZOS)
    else:
        img_rgb = img.convert("RGB")

    work = img_rgb.convert("L") if settings["greyscale"] else img_rgb
    work = ImageEnhance.Contrast(work).enhance(settings["contrast"])

    arr = np.array(work, dtype=np.float32) / 255.0
    arr = np.clip(arr ** (1.0 / settings["midtones"]) * settings["highlights"], 0, 1)
    work = Image.fromarray((arr * 255).astype(np.uint8))

    if settings["blur"] > 0:
        work = work.filter(ImageFilter.GaussianBlur(settings["blur"]))

    pix = int(settings["pixelation"])
    if pix > 1:
        small = work.resize((max(1, work.width // pix), max(1, work.height // pix)), Image.NEAREST)
        work = small.resize((small.width * pix, small.height * pix), Image.NEAREST)

    work = apply_noise(work, int(settings["noise"]))

    # pass RGBA with forced alpha=255 so the C code only dithers RGB channels
    r, g, b = work.convert("RGB").split()
    rgba_in = Image.merge("RGBA", (r, g, b, Image.new("L", r.size, 255)))
    raw = rgba_in.tobytes()
    w, h = rgba_in.size
    dithered_raw = algorithms[settings["algorithm"]].dither(raw, w, h, int(settings["threshold"]))
    dithered = Image.frombytes("RGBA", (w, h), dithered_raw)

    if settings["greyscale"]:
        gray = np.array(dithered.convert("L"))
        orig_alpha = np.array(alpha, dtype=np.float32) / 255.0
        fg = ImageColor.getrgb(settings["foreground"])
        bg = ImageColor.getrgb(settings["background"])
        fg_op = settings["foreground_opacity"] / 255.0
        bg_op = settings["background_opacity"] / 255.0

        out = np.zeros((*gray.shape, 4), dtype=np.uint8)
        mask = gray >= 128
        out[mask, :3] = fg
        out[~mask, :3] = bg
        out[mask, 3] = (orig_alpha[mask] * fg_op * 255).astype(np.uint8)
        out[~mask, 3] = (orig_alpha[~mask] * bg_op * 255).astype(np.uint8)
        final = Image.fromarray(out, "RGBA")
    else:
        # discard C's alpha channel, restore original
        r, g, b, _ = dithered.split()
        final = Image.merge("RGBA", (r, g, b, alpha))

    # only resize back if scale was applied — at scale=100 final is already original size
    if final.size != (orig_w, orig_h):
        return final.resize((orig_w, orig_h), Image.NEAREST)
    return final
