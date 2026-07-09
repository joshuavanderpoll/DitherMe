import { invoke } from "@tauri-apps/api/core";

export interface Settings {
  scale: number;
  contrast: number;
  midtones: number;
  highlights: number;
  blur: number;
  pixelation: number;
  noise: number;
  threshold: number;
  algorithm: string;
  greyscale: boolean;
  foreground: string;
  background: string;
  foreground_opacity: number;
  background_opacity: number;
}

export interface ImageMeta {
  width: number;
  height: number;
  is_gif: boolean;
  frame_count: number;
  durations: number[];
}

export function defaultSettings(): Settings {
  return {
    scale: 100,
    contrast: 1,
    midtones: 1,
    highlights: 1,
    blur: 0,
    pixelation: 1,
    noise: 0,
    threshold: 128,
    algorithm: "Floyd-Steinberg",
    greyscale: true,
    foreground: "#FFFFFF",
    background: "#000000",
    foreground_opacity: 255,
    background_opacity: 255,
  };
}

export const openImage = (path: string) =>
  invoke<ImageMeta>("open_image", { path });

export const processFrame = (settings: Settings, frameIndex: number) =>
  invoke<ArrayBuffer>("process_frame", { settings, frameIndex });

export const exportStill = (
  path: string,
  settings: Settings,
  frameIndex: number,
) => invoke<null>("export_still", { path, settings, frameIndex });

export const exportGif = (path: string, settings: Settings) =>
  invoke<null>("export_gif", { path, settings });

export const saveTemplate = (path: string, settings: Settings) =>
  invoke<null>("save_template", { path, settings });

export const loadTemplate = (path: string) =>
  invoke<Settings>("load_template", { path });

export const algorithmList = () => invoke<string[]>("algorithm_list");
