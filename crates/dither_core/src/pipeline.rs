use crate::algorithms;
use crate::settings::{parse_hex, Settings};
use image::{imageops, GrayImage, ImageBuffer, RgbImage, RgbaImage};
use rand::Rng;

// Pillow's exact RGB->L fixed-point transform (ITU-R 601-2), so ordered dithers
// see byte-identical input to the Python version.
fn luma(r: u8, g: u8, b: u8) -> u8 {
    ((r as u32 * 19595 + g as u32 * 38470 + b as u32 * 7471 + 0x8000) >> 16) as u8
}

fn contrast_mean(work: &[u8], channels: usize) -> f32 {
    let m = if channels == 1 {
        let sum: u64 = work.iter().map(|&v| v as u64).sum();
        sum as f64 / work.len().max(1) as f64
    } else {
        let n = (work.len() / 3).max(1);
        let mut sum = 0f64;
        for i in 0..n {
            sum += luma(work[i * 3], work[i * 3 + 1], work[i * 3 + 2]) as f64;
        }
        sum / n as f64
    };
    // Pillow: int(mean + 0.5)
    (m + 0.5) as i64 as f32
}

fn gaussian(work: Vec<u8>, w: u32, h: u32, channels: usize, sigma: f32) -> Vec<u8> {
    if channels == 1 {
        let img = GrayImage::from_raw(w, h, work).expect("grey buffer size");
        imageops::blur(&img, sigma).into_raw()
    } else {
        let img = RgbImage::from_raw(w, h, work).expect("rgb buffer size");
        imageops::blur(&img, sigma).into_raw()
    }
}

fn pixelate(work: Vec<u8>, w: u32, h: u32, channels: usize, sw: u32, sh: u32, pix: u32) -> Vec<u8> {
    let nn = imageops::FilterType::Nearest;
    if channels == 1 {
        let img = GrayImage::from_raw(w, h, work).expect("grey buffer size");
        let small = imageops::resize(&img, sw, sh, nn);
        imageops::resize(&small, sw * pix, sh * pix, nn).into_raw()
    } else {
        let img = RgbImage::from_raw(w, h, work).expect("rgb buffer size");
        let small = imageops::resize(&img, sw, sh, nn);
        imageops::resize(&small, sw * pix, sh * pix, nn).into_raw()
    }
}

// Mirrors DitherMe/processor.py::process_frame. Input and output are packed RGBA
// at the original size.
pub fn process(src_rgba: &[u8], src_w: u32, src_h: u32, s: &Settings) -> (Vec<u8>, u32, u32) {
    let orig_w = src_w;
    let orig_h = src_h;

    // Guard against a malformed/short buffer so from_raw + indexing can't panic.
    let needed = (src_w as usize) * (src_h as usize) * 4;
    if src_w == 0 || src_h == 0 || src_rgba.len() < needed {
        return (src_rgba.to_vec(), src_w, src_h);
    }

    let mut alpha: GrayImage = ImageBuffer::new(src_w, src_h);
    for (i, px) in alpha.pixels_mut().enumerate() {
        px.0 = [src_rgba[i * 4 + 3]];
    }
    let mut rgb: RgbImage = ImageBuffer::new(src_w, src_h);
    for (i, px) in rgb.pixels_mut().enumerate() {
        px.0 = [src_rgba[i * 4], src_rgba[i * 4 + 1], src_rgba[i * 4 + 2]];
    }

    let scale = s.scale.clamp(1.0, 100.0) / 100.0;
    if (scale - 1.0).abs() > 1e-6 {
        let nw = ((orig_w as f32 * scale) as u32).max(1);
        let nh = ((orig_h as f32 * scale) as u32).max(1);
        rgb = imageops::resize(&rgb, nw, nh, imageops::FilterType::Lanczos3);
        alpha = imageops::resize(&alpha, nw, nh, imageops::FilterType::Lanczos3);
    }

    let mut w = rgb.width();
    let mut h = rgb.height();
    let channels: usize = if s.greyscale { 1 } else { 3 };

    let mut work: Vec<u8> = if s.greyscale {
        rgb.pixels().map(|p| luma(p.0[0], p.0[1], p.0[2])).collect()
    } else {
        rgb.into_raw()
    };

    // contrast (Pillow ImageEnhance.Contrast: blend toward a flat mean-gray)
    if (s.contrast - 1.0).abs() > 1e-6 {
        let mean = contrast_mean(&work, channels);
        let f = s.contrast;
        for v in work.iter_mut() {
            *v = (mean + f * (*v as f32 - mean)).round().clamp(0.0, 255.0) as u8;
        }
    }

    // midtones (gamma) + highlights, applied unconditionally like the Python code.
    // Guard the reciprocal so a 0 from an edited template can't produce inf/NaN.
    let inv = 1.0 / s.midtones.max(1e-4);
    for v in work.iter_mut() {
        let a = ((*v as f32 / 255.0).powf(inv) * s.highlights).clamp(0.0, 1.0);
        *v = (a * 255.0) as u8;
    }

    if s.blur > 0.0 {
        work = gaussian(work, w, h, channels, s.blur);
    }

    if s.pixelation > 1 {
        let pix = s.pixelation;
        let sw = (w / pix).max(1);
        let sh = (h / pix).max(1);
        work = pixelate(work, w, h, channels, sw, sh, pix);
        w = sw * pix;
        h = sh * pix;
    }

    if s.noise > 0 {
        let n = s.noise as i32;
        let mut rng = rand::thread_rng();
        for v in work.iter_mut() {
            let delta = rng.gen_range(-n..n);
            *v = (*v as i32 + delta).clamp(0, 255) as u8;
        }
    }

    // to RGB for the dither stage (replicate the single grey channel)
    let mut dith: Vec<u8> = if channels == 1 {
        let mut v = Vec::with_capacity((w * h * 3) as usize);
        for &g in work.iter() {
            v.push(g);
            v.push(g);
            v.push(g);
        }
        v
    } else {
        work
    };
    algorithms::dither(&s.algorithm, &mut dith, w, h, s.threshold);

    // pixelation/scale rounding can change dimensions, realign alpha (processor.py fix)
    if alpha.width() != w || alpha.height() != h {
        alpha = imageops::resize(&alpha, w, h, imageops::FilterType::Lanczos3);
    }
    let alpha_raw = alpha.into_raw();

    let count = (w * h) as usize;
    let mut out = vec![0u8; count * 4];
    if s.greyscale {
        let fg = parse_hex(&s.foreground);
        let bg = parse_hex(&s.background);
        let fg_op = s.foreground_opacity as f32 / 255.0;
        let bg_op = s.background_opacity as f32 / 255.0;
        for i in 0..count {
            let l = luma(dith[i * 3], dith[i * 3 + 1], dith[i * 3 + 2]);
            let a_norm = alpha_raw[i] as f32 / 255.0;
            let (col, op) = if l >= 128 { (fg, fg_op) } else { (bg, bg_op) };
            out[i * 4] = col[0];
            out[i * 4 + 1] = col[1];
            out[i * 4 + 2] = col[2];
            out[i * 4 + 3] = (a_norm * op * 255.0) as u8;
        }
    } else {
        for i in 0..count {
            out[i * 4] = dith[i * 3];
            out[i * 4 + 1] = dith[i * 3 + 1];
            out[i * 4 + 2] = dith[i * 3 + 2];
            out[i * 4 + 3] = alpha_raw[i];
        }
    }

    if w != orig_w || h != orig_h {
        let img = RgbaImage::from_raw(w, h, out).expect("rgba buffer size");
        let resized = imageops::resize(&img, orig_w, orig_h, imageops::FilterType::Nearest);
        (resized.into_raw(), orig_w, orig_h)
    } else {
        (out, orig_w, orig_h)
    }
}
