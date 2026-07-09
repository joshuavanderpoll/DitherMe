# DitherMe

Tauri + Rust + Svelte desktop app for dithering images and GIFs.

## Layout

- `crates/dither_core` — pure Rust image pipeline + all 19 dithering algorithms. No Tauri, no Python. Validated against the legacy Python output (`cargo run --example compare -- <golden_dir>`).
- `src-tauri` — Tauri shell. Commands: `open_image`, `process_frame` (returns raw RGBA), `export_still`, `export_gif`, `save_template`, `load_template`, `algorithm_list`.
- `src` — Svelte + TypeScript UI.

## Develop

```sh
pnpm install
pnpm tauri dev
```

## Build

```sh
pnpm tauri build
```

## Test the core

```sh
cargo test -p dither_core
```

## Notes

- Template JSON is field-compatible with the Python version.
- Pinch/zoom is native in the webview (`wheel` + `ctrlKey`), no platform hack.
- Bayer 4x4 / 8x8 / Clustered Dot use correct standard tiling; the legacy shipped `.so` had a drift bug (see project memory).
