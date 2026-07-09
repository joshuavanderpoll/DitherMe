use serde::{Deserialize, Serialize};

// Field names match the Python `_get_settings()` dict so existing template JSON
// files load unchanged.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    pub scale: f32,
    pub contrast: f32,
    pub midtones: f32,
    pub highlights: f32,
    pub blur: f32,
    pub pixelation: u32,
    pub noise: u32,
    pub threshold: i32,
    pub algorithm: String,
    pub greyscale: bool,
    pub foreground: String,
    pub background: String,
    pub foreground_opacity: u8,
    pub background_opacity: u8,
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            scale: 100.0,
            contrast: 1.0,
            midtones: 1.0,
            highlights: 1.0,
            blur: 0.0,
            pixelation: 1,
            noise: 0,
            threshold: 128,
            algorithm: "Floyd-Steinberg".to_string(),
            greyscale: true,
            foreground: "#FFFFFF".to_string(),
            background: "#000000".to_string(),
            foreground_opacity: 255,
            background_opacity: 255,
        }
    }
}

pub fn parse_hex(hex: &str) -> [u8; 3] {
    let h = hex.trim().trim_start_matches('#');
    if h.len() >= 6 {
        let r = u8::from_str_radix(&h[0..2], 16).unwrap_or(0);
        let g = u8::from_str_radix(&h[2..4], 16).unwrap_or(0);
        let b = u8::from_str_radix(&h[4..6], 16).unwrap_or(0);
        [r, g, b]
    } else {
        [0, 0, 0]
    }
}
