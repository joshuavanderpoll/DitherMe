pub mod algorithms;
pub mod pipeline;
pub mod settings;

pub use algorithms::algorithm_names;
pub use pipeline::process;
pub use settings::Settings;

#[cfg(test)]
mod tests {
    use super::*;

    fn checker(w: u32, h: u32) -> Vec<u8> {
        let mut v = vec![0u8; (w * h * 4) as usize];
        for y in 0..h {
            for x in 0..w {
                let i = ((y * w + x) * 4) as usize;
                let c = if (x + y) % 2 == 0 { 200 } else { 60 };
                v[i] = c;
                v[i + 1] = c / 2;
                v[i + 2] = c / 3;
                v[i + 3] = 255;
            }
        }
        v
    }

    #[test]
    fn output_is_original_size_for_all_algorithms() {
        let (w, h) = (37u32, 41u32);
        let src = checker(w, h);
        for name in algorithm_names() {
            let mut s = Settings::default();
            s.algorithm = name.to_string();
            let (out, ow, oh) = process(&src, w, h, &s);
            assert_eq!((ow, oh), (w, h), "{name}");
            assert_eq!(out.len(), (w * h * 4) as usize, "{name}");
        }
    }

    #[test]
    fn pixelation_and_scale_preserve_output_size() {
        // The size mismatch that crashed the Python version: odd dims + pixelation.
        let (w, h) = (99u32, 98u32);
        let src = checker(w, h);
        for &pix in &[1u32, 3, 7, 20] {
            for &scale in &[100.0f32, 50.0, 37.0, 500.0, 1000.0] {
                for &grey in &[true, false] {
                    let mut s = Settings::default();
                    s.pixelation = pix;
                    s.scale = scale;
                    s.greyscale = grey;
                    let (out, ow, oh) = process(&src, w, h, &s);
                    assert_eq!((ow, oh), (w, h));
                    assert_eq!(out.len(), (w * h * 4) as usize);
                }
            }
        }
    }

    fn flat(w: u32, h: u32, v: u8) -> Vec<u8> {
        let mut buf = vec![0u8; (w * h * 4) as usize];
        for p in buf.chunks_mut(4) {
            p[0] = v;
            p[1] = v;
            p[2] = v;
            p[3] = 255;
        }
        buf
    }

    #[test]
    fn flat_white_and_black_map_cleanly() {
        let (w, h) = (16u32, 16u32);
        for name in algorithm_names() {
            let mut s = Settings::default();
            s.algorithm = name.to_string();
            s.foreground = "#FFFFFF".to_string();
            s.background = "#000000".to_string();

            let (out, _, _) = process(&flat(w, h, 255), w, h, &s);
            assert!(
                out.chunks(4).all(|p| p[0] == 255),
                "{name}: flat white should be all foreground"
            );

            let (out, _, _) = process(&flat(w, h, 0), w, h, &s);
            assert!(
                out.chunks(4).all(|p| p[0] == 0),
                "{name}: flat black should be all background"
            );
        }
    }

    #[test]
    fn malformed_input_does_not_panic() {
        let s = Settings::default();
        // buffer too short for the claimed dimensions
        let (out, w, h) = process(&[0u8; 3], 10, 10, &s);
        assert_eq!((w, h), (10, 10));
        assert_eq!(out.len(), 3);
        // zero dimensions
        let (_out, w, h) = process(&[], 0, 0, &s);
        assert_eq!((w, h), (0, 0));
    }

    #[test]
    fn zero_midtones_stays_finite() {
        let (w, h) = (8u32, 8u32);
        let src = checker(w, h);
        let mut s = Settings::default();
        s.midtones = 0.0;
        // inv = 1/eps is huge: (v/255)^inv collapses to 0 except pure white, so
        // this mostly maps to background. The point is it stays finite and sized.
        let (out, _, _) = process(&src, w, h, &s);
        assert_eq!(out.len(), (w * h * 4) as usize);
        assert!(out.chunks(4).all(|p| p[3] == 255));
    }

    #[test]
    fn greyscale_maps_to_foreground_background_colors() {
        let (w, h) = (8u32, 8u32);
        let src = checker(w, h);
        let mut s = Settings::default();
        s.foreground = "#FF0000".to_string();
        s.background = "#00FF00".to_string();
        let (out, _, _) = process(&src, w, h, &s);
        for p in out.chunks(4) {
            let is_fg = p[0] == 255 && p[1] == 0 && p[2] == 0;
            let is_bg = p[0] == 0 && p[1] == 255 && p[2] == 0;
            assert!(is_fg || is_bg, "pixel {:?} not fg/bg", p);
        }
    }
}
