use dither_core::{algorithm_names, process, Settings};
use image::{AnimationDecoder, RgbaImage};
use serde::Serialize;
use std::io::BufReader;
use std::sync::Mutex;
use tauri::{AppHandle, Emitter, State};

pub struct Frame {
    pub rgba: Vec<u8>,
    pub w: u32,
    pub h: u32,
    pub duration_ms: u16,
}

#[derive(Default)]
pub struct Source {
    pub frames: Vec<Frame>,
    pub is_gif: bool,
}

#[derive(Default)]
pub struct AppState(pub Mutex<Source>);

#[derive(Serialize)]
pub struct ImageMeta {
    width: u32,
    height: u32,
    is_gif: bool,
    frame_count: usize,
    durations: Vec<u16>,
}

fn decode_gif(path: &str) -> Result<Vec<Frame>, String> {
    let file = std::fs::File::open(path).map_err(|e| e.to_string())?;
    let decoder =
        image::codecs::gif::GifDecoder::new(BufReader::new(file)).map_err(|e| e.to_string())?;
    let frames = decoder
        .into_frames()
        .collect_frames()
        .map_err(|e| e.to_string())?;
    let mut out = Vec::with_capacity(frames.len());
    for f in frames {
        let (numer, denom) = f.delay().numer_denom_ms();
        let dur = if denom == 0 { 100 } else { (numer / denom) as u16 };
        let buf = f.into_buffer();
        let (w, h) = buf.dimensions();
        out.push(Frame {
            rgba: buf.into_raw(),
            w,
            h,
            duration_ms: dur.max(1),
        });
    }
    Ok(out)
}

fn decode_still(path: &str) -> Result<Frame, String> {
    let img = image::ImageReader::open(path)
        .map_err(|e| e.to_string())?
        .with_guessed_format()
        .map_err(|e| e.to_string())?
        .decode()
        .map_err(|e| e.to_string())?
        .to_rgba8();
    let (w, h) = img.dimensions();
    Ok(Frame {
        rgba: img.into_raw(),
        w,
        h,
        duration_ms: 100,
    })
}

#[tauri::command]
pub fn open_image(state: State<AppState>, path: String) -> Result<ImageMeta, String> {
    let is_gif = path.to_lowercase().ends_with(".gif");
    let frames = if is_gif {
        decode_gif(&path)?
    } else {
        vec![decode_still(&path)?]
    };
    if frames.is_empty() {
        return Err("no frames decoded".into());
    }
    let (width, height) = (frames[0].w, frames[0].h);
    let durations = frames.iter().map(|f| f.duration_ms).collect();
    let meta = ImageMeta {
        width,
        height,
        is_gif,
        frame_count: frames.len(),
        durations,
    };
    let mut src = state.0.lock().unwrap();
    src.frames = frames;
    src.is_gif = is_gif;
    Ok(meta)
}

// Returns the processed frame as raw RGBA bytes (ArrayBuffer on the JS side).
// The frontend already knows width/height from open_image, and the pipeline
// always returns the original size, so no header is needed.
#[tauri::command]
pub fn process_frame(
    state: State<AppState>,
    settings: Settings,
    frame_index: usize,
) -> tauri::ipc::Response {
    let src = state.0.lock().unwrap();
    match src.frames.get(frame_index) {
        Some(frame) => {
            let (out, _, _) = process(&frame.rgba, frame.w, frame.h, &settings);
            tauri::ipc::Response::new(out)
        }
        None => tauri::ipc::Response::new(Vec::new()),
    }
}

fn processed_image(frame: &Frame, settings: &Settings) -> RgbaImage {
    let (out, w, h) = process(&frame.rgba, frame.w, frame.h, settings);
    RgbaImage::from_raw(w, h, out).expect("processed buffer size")
}

#[tauri::command]
pub fn export_still(
    state: State<AppState>,
    path: String,
    settings: Settings,
    frame_index: usize,
) -> Result<(), String> {
    let src = state.0.lock().unwrap();
    let frame = src
        .frames
        .get(frame_index)
        .ok_or_else(|| "frame out of range".to_string())?;
    let mut img = processed_image(frame, &settings);

    let lower = path.to_lowercase();
    if lower.ends_with(".ico") && (img.width() > 256 || img.height() > 256) {
        img = image::imageops::thumbnail(
            &img,
            img.width().min(256),
            img.height().min(256),
        );
    }
    img.save(&path).map_err(|e| e.to_string())
}

#[derive(Clone, Serialize)]
struct ExportProgress {
    done: usize,
    total: usize,
}

#[tauri::command]
pub fn export_gif(
    app: AppHandle,
    state: State<AppState>,
    path: String,
    settings: Settings,
) -> Result<(), String> {
    let src = state.0.lock().unwrap();
    if src.frames.is_empty() {
        return Err("no frames".into());
    }
    let total = src.frames.len();
    let file = std::fs::File::create(&path).map_err(|e| e.to_string())?;
    let mut encoder = image::codecs::gif::GifEncoder::new(file);
    encoder
        .set_repeat(image::codecs::gif::Repeat::Infinite)
        .map_err(|e| e.to_string())?;

    for (i, frame) in src.frames.iter().enumerate() {
        let img = processed_image(frame, &settings);
        let delay = image::Delay::from_numer_denom_ms(frame.duration_ms as u32, 1);
        let gif_frame = image::Frame::from_parts(img, 0, 0, delay);
        encoder.encode_frame(gif_frame).map_err(|e| e.to_string())?;
        let _ = app.emit(
            "export_progress",
            ExportProgress {
                done: i + 1,
                total,
            },
        );
    }
    Ok(())
}

#[tauri::command]
pub fn save_template(path: String, settings: Settings) -> Result<(), String> {
    let json = serde_json::to_string_pretty(&settings).map_err(|e| e.to_string())?;
    std::fs::write(&path, json).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn load_template(path: String) -> Result<Settings, String> {
    let data = std::fs::read_to_string(&path).map_err(|e| e.to_string())?;
    serde_json::from_str(&data).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn algorithm_list() -> Vec<String> {
    algorithm_names().into_iter().map(|s| s.to_string()).collect()
}
