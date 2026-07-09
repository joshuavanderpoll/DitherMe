mod commands;

use commands::*;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .manage(AppState::default())
        .invoke_handler(tauri::generate_handler![
            open_image,
            process_frame,
            original_frame,
            export_still,
            export_gif,
            save_template,
            load_template,
            algorithm_list
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
