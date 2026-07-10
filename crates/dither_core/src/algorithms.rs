// All algorithms operate on a tightly-packed RGB buffer (3 bytes/pixel).
// The Python pipeline discards the dithered alpha in both output paths, so
// there is no need to touch a 4th channel here.

const CH: usize = 3;

// (dx, dy, weight). Atkinson pre-scales the error to an int before spreading,
// modelled by `prescale`.
struct ErrorDiffusion {
    offsets: &'static [(i32, i32, f32)],
    prescale: Option<f32>,
}

impl ErrorDiffusion {
    fn run(&self, buf: &mut [u8], w: u32, h: u32, threshold: u8) {
        let w = w as i32;
        let h = h as i32;
        for y in 0..h {
            for x in 0..w {
                for c in 0..CH {
                    let idx = ((y * w + x) as usize) * CH + c;
                    let old = buf[idx] as i32;
                    let new = if old < threshold as i32 { 0 } else { 255 };
                    buf[idx] = new as u8;
                    let diff = (old - new) as f32;
                    let err = match self.prescale {
                        Some(s) => (diff * s).trunc(),
                        None => diff,
                    };
                    for &(dx, dy, wt) in self.offsets {
                        let nx = x + dx;
                        let ny = y + dy;
                        if nx >= 0 && nx < w && ny >= 0 && ny < h {
                            let nidx = ((ny * w + nx) as usize) * CH + c;
                            let v = buf[nidx] as f32 + err * wt;
                            buf[nidx] = v.clamp(0.0, 255.0) as u8;
                        }
                    }
                }
            }
        }
    }
}

fn ordered(buf: &mut [u8], w: u32, h: u32, matrix: &[&[u8]], denom: u32, threshold_arg: i32) {
    let bias = threshold_arg - 128;
    let n = matrix.len() as u32;
    for y in 0..h {
        for x in 0..w {
            let mt = ((matrix[(y % n) as usize][(x % n) as usize] as u32) * 255 / denom) as u8;
            for c in 0..CH {
                let idx = ((y * w + x) as usize) * CH + c;
                let adjusted = (buf[idx] as i32 + bias).clamp(0, 255) as u8;
                buf[idx] = if adjusted > mt { 255 } else { 0 };
            }
        }
    }
}

fn checkered(buf: &mut [u8], w: u32, h: u32, block: u32, threshold_arg: i32) {
    let threshold = threshold_arg.clamp(0, 255) as u16;
    let low_t = (threshold * 2 / 3) as u8;
    let high_t = std::cmp::min(threshold * 4 / 3, 255) as u8;
    for y in 0..h {
        for x in 0..w {
            let base = ((y * w + x) as usize) * CH;
            let r = buf[base] as f32;
            let g = buf[base + 1] as f32;
            let b = buf[base + 2] as f32;
            let brightness = (0.299 * r + 0.587 * g + 0.114 * b) as u8;
            let same = (((x / block) + (y / block)) % 2) == 0;
            let pt = if same { low_t } else { high_t };
            let new = if brightness < pt { 0 } else { 255 };
            buf[base] = new;
            buf[base + 1] = new;
            buf[base + 2] = new;
        }
    }
}

const BAYER_2X2: [&[u8]; 2] = [&[0, 2], &[3, 1]];
const BAYER_4X4: [&[u8]; 4] = [
    &[0, 8, 2, 10],
    &[12, 4, 14, 6],
    &[3, 11, 1, 9],
    &[15, 7, 13, 5],
];
const BAYER_8X8: [&[u8]; 8] = [
    &[0, 32, 8, 40, 2, 34, 10, 42],
    &[48, 16, 56, 24, 50, 18, 58, 26],
    &[12, 44, 4, 36, 14, 46, 6, 38],
    &[60, 28, 52, 20, 62, 30, 54, 22],
    &[3, 35, 11, 43, 1, 33, 9, 41],
    &[51, 19, 59, 27, 49, 17, 57, 25],
    &[15, 47, 7, 39, 13, 45, 5, 37],
    &[63, 31, 55, 23, 61, 29, 53, 21],
];
const CLUSTERED_4X4: [&[u8]; 4] = [
    &[12, 5, 6, 13],
    &[4, 0, 1, 7],
    &[11, 3, 2, 8],
    &[15, 10, 9, 14],
];

pub fn algorithm_names() -> Vec<&'static str> {
    vec![
        "Floyd-Steinberg",
        "False Floyd-Steinberg",
        "Sierra",
        "Sierra Lite",
        "Sierra Two-Row",
        "Atkinson",
        "Burkes",
        "Stucki",
        "Jarvis-Judice & Ninke",
        "Stevenson-Arce",
        "Knoll",
        "Bayer 2x2",
        "Bayer 4x4",
        "Bayer 8x8",
        "Clustered Dot 4x4",
        "Lattice-Boltzmann",
        "Checkered Small",
        "Checkered Medium",
        "Checkered Large",
    ]
}

// Dispatch by the display name used in the Python UI / template JSON.
// `buf` must be RGB (w*h*3). Unknown names fall back to Floyd-Steinberg.
pub fn dither(name: &str, buf: &mut [u8], w: u32, h: u32, threshold_arg: i32) {
    let t = threshold_arg.clamp(0, 255) as u8;
    match name {
        "Floyd-Steinberg" => ErrorDiffusion {
            offsets: &[
                (1, 0, 7.0 / 16.0),
                (-1, 1, 3.0 / 16.0),
                (0, 1, 5.0 / 16.0),
                (1, 1, 1.0 / 16.0),
            ],
            prescale: None,
        }
        .run(buf, w, h, t),
        "False Floyd-Steinberg" => ErrorDiffusion {
            offsets: &[(1, 0, 0.5), (0, 1, 0.5)],
            prescale: None,
        }
        .run(buf, w, h, t),
        "Sierra" => ErrorDiffusion {
            offsets: &[
                (1, 0, 5.0 / 32.0),
                (2, 0, 3.0 / 32.0),
                (-2, 1, 2.0 / 32.0),
                (-1, 1, 4.0 / 32.0),
                (0, 1, 5.0 / 32.0),
                (1, 1, 4.0 / 32.0),
            ],
            prescale: None,
        }
        .run(buf, w, h, t),
        "Sierra Lite" => ErrorDiffusion {
            offsets: &[(1, 0, 2.0 / 4.0), (-1, 1, 1.0 / 4.0)],
            prescale: None,
        }
        .run(buf, w, h, t),
        "Sierra Two-Row" => ErrorDiffusion {
            offsets: &[
                (1, 0, 4.0 / 16.0),
                (-1, 1, 3.0 / 16.0),
                (0, 1, 5.0 / 16.0),
                (1, 1, 4.0 / 16.0),
            ],
            prescale: None,
        }
        .run(buf, w, h, t),
        "Atkinson" => ErrorDiffusion {
            offsets: &[
                (1, 0, 1.0),
                (2, 0, 1.0),
                (-1, 1, 1.0),
                (0, 1, 1.0),
                (1, 1, 1.0),
                (0, 2, 1.0),
            ],
            prescale: Some(1.0 / 8.0),
        }
        .run(buf, w, h, t),
        "Burkes" => ErrorDiffusion {
            offsets: &[
                (1, 0, 8.0 / 32.0),
                (2, 0, 4.0 / 32.0),
                (-2, 1, 2.0 / 32.0),
                (-1, 1, 4.0 / 32.0),
                (0, 1, 8.0 / 32.0),
                (1, 1, 4.0 / 32.0),
                (2, 1, 2.0 / 32.0),
            ],
            prescale: None,
        }
        .run(buf, w, h, t),
        "Stucki" => ErrorDiffusion {
            offsets: &[
                (1, 0, 8.0 / 42.0),
                (2, 0, 4.0 / 42.0),
                (-2, 1, 2.0 / 42.0),
                (-1, 1, 4.0 / 42.0),
                (0, 1, 8.0 / 42.0),
                (1, 1, 4.0 / 42.0),
                (2, 1, 2.0 / 42.0),
                (-2, 2, 1.0 / 42.0),
                (-1, 2, 2.0 / 42.0),
                (0, 2, 4.0 / 42.0),
                (1, 2, 2.0 / 42.0),
                (2, 2, 1.0 / 42.0),
            ],
            prescale: None,
        }
        .run(buf, w, h, t),
        "Jarvis-Judice & Ninke" => ErrorDiffusion {
            offsets: &[
                (1, 0, 7.0 / 48.0),
                (2, 0, 5.0 / 48.0),
                (-2, 1, 3.0 / 48.0),
                (-1, 1, 5.0 / 48.0),
                (0, 1, 7.0 / 48.0),
                (1, 1, 5.0 / 48.0),
                (2, 1, 3.0 / 48.0),
                (-2, 2, 1.0 / 48.0),
                (-1, 2, 3.0 / 48.0),
                (0, 2, 5.0 / 48.0),
                (1, 2, 3.0 / 48.0),
                (2, 2, 1.0 / 48.0),
            ],
            prescale: None,
        }
        .run(buf, w, h, t),
        "Stevenson-Arce" => ErrorDiffusion {
            offsets: &[
                (2, 0, 32.0 / 200.0),
                (3, 0, 12.0 / 200.0),
                (-2, 1, 12.0 / 200.0),
                (1, 1, 26.0 / 200.0),
                (-3, 2, 12.0 / 200.0),
                (-1, 2, 26.0 / 200.0),
                (1, 2, 12.0 / 200.0),
                (3, 2, 12.0 / 200.0),
                (-2, 3, 12.0 / 200.0),
                (1, 3, 26.0 / 200.0),
                (0, 4, 12.0 / 200.0),
                (2, 4, 12.0 / 200.0),
            ],
            prescale: None,
        }
        .run(buf, w, h, t),
        "Knoll" => ErrorDiffusion {
            offsets: &[
                (1, 0, 12.0 / 136.0),
                (2, 0, 10.0 / 136.0),
                (3, 0, 7.0 / 136.0),
                (4, 0, 5.0 / 136.0),
                (-1, 1, 12.0 / 136.0),
                (0, 1, 12.0 / 136.0),
                (1, 1, 8.0 / 136.0),
                (2, 1, 5.0 / 136.0),
                (3, 1, 3.0 / 136.0),
                (-2, 2, 10.0 / 136.0),
                (-1, 2, 8.0 / 136.0),
                (0, 2, 5.0 / 136.0),
                (1, 2, 3.0 / 136.0),
                (2, 2, 2.0 / 136.0),
                (-3, 3, 7.0 / 136.0),
                (-2, 3, 5.0 / 136.0),
                (-1, 3, 3.0 / 136.0),
                (0, 3, 2.0 / 136.0),
                (1, 3, 1.0 / 136.0),
            ],
            prescale: None,
        }
        .run(buf, w, h, t),
        "Lattice-Boltzmann" => ErrorDiffusion {
            offsets: &[
                (1, 0, 1.0 / 6.0),
                (-1, 0, 1.0 / 6.0),
                (0, 1, 1.0 / 6.0),
                (0, -1, 1.0 / 6.0),
                (1, 1, 1.0 / 6.0),
                (-1, -1, 1.0 / 6.0),
            ],
            prescale: None,
        }
        .run(buf, w, h, t),
        "Bayer 2x2" => ordered(buf, w, h, &BAYER_2X2, 4, threshold_arg),
        "Bayer 4x4" => ordered(buf, w, h, &BAYER_4X4, 16, threshold_arg),
        "Bayer 8x8" => ordered(buf, w, h, &BAYER_8X8, 64, threshold_arg),
        "Clustered Dot 4x4" => ordered(buf, w, h, &CLUSTERED_4X4, 16, threshold_arg),
        "Checkered Small" => checkered(buf, w, h, 1, threshold_arg),
        "Checkered Medium" => checkered(buf, w, h, 2, threshold_arg),
        "Checkered Large" => checkered(buf, w, h, 4, threshold_arg),
        _ => ErrorDiffusion {
            offsets: &[
                (1, 0, 7.0 / 16.0),
                (-1, 1, 3.0 / 16.0),
                (0, 1, 5.0 / 16.0),
                (1, 1, 1.0 / 16.0),
            ],
            prescale: None,
        }
        .run(buf, w, h, t),
    }
}
