use dither_core::{process, Settings};
use std::time::Instant;

fn main() {
    let (w, h) = (1200u32, 900u32);
    let mut src = vec![0u8; (w * h * 4) as usize];
    for (i, px) in src.chunks_mut(4).enumerate() {
        px[0] = (i % 255) as u8;
        px[1] = ((i / 7) % 255) as u8;
        px[2] = ((i / 13) % 255) as u8;
        px[3] = 255;
    }
    for algo in ["Floyd-Steinberg", "Bayer 4x4", "Atkinson"] {
        let mut s = Settings::default();
        s.algorithm = algo.to_string();
        // warm up
        let _ = process(&src, w, h, &s);
        let n = 20;
        let t = Instant::now();
        for _ in 0..n {
            let _ = process(&src, w, h, &s);
        }
        let ms = t.elapsed().as_secs_f64() * 1000.0 / n as f64;
        println!("{algo:<20} {w}x{h}: {ms:.1} ms/frame");
    }
}
