<script lang="ts">
  import { onMount } from "svelte";
  import { open, save } from "@tauri-apps/plugin-dialog";
  import { listen } from "@tauri-apps/api/event";
  import Slider from "./lib/Slider.svelte";
  import {
    algorithmList,
    defaultSettings,
    exportGif,
    exportStill,
    loadTemplate,
    openImage,
    processFrame,
    saveTemplate,
    type ImageMeta,
    type Settings,
  } from "./lib/api";

  let settings = $state<Settings>(defaultSettings());
  let meta = $state<ImageMeta | null>(null);
  let algorithms = $state<string[]>([]);
  let frameIndex = $state(0);
  let zoom = $state(1);
  let pan = $state({ x: 0, y: 0 });
  let playing = $state(false);
  let progress = $state(0);
  let status = $state("No image loaded");

  let canvasEl: HTMLCanvasElement | undefined;
  let dragging = false;
  let dragLast = { x: 0, y: 0 };
  let debounceTimer: ReturnType<typeof setTimeout> | undefined;
  let gifTimer: ReturnType<typeof setTimeout> | undefined;
  let gen = 0;

  const clamp = (v: number, lo: number, hi: number) =>
    Math.max(lo, Math.min(hi, v));

  onMount(() => {
    algorithmList().then((a) => (algorithms = a));
    const un = listen<{ done: number; total: number }>(
      "export_progress",
      (e) => {
        progress = e.payload.done / e.payload.total;
        if (e.payload.done >= e.payload.total) {
          status = "Export complete";
          setTimeout(() => (progress = 0), 600);
        }
      },
    );
    return () => {
      un.then((f) => f());
    };
  });

  // Reprocess whenever settings or the current frame change.
  $effect(() => {
    const snap = $state.snapshot(settings) as Settings;
    const idx = frameIndex;
    if (!meta) return;
    scheduleProcess(snap, idx);
  });

  function scheduleProcess(snap: Settings, idx: number) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => void doProcess(snap, idx), 80);
  }

  async function doProcess(snap: Settings, idx: number) {
    const myGen = ++gen;
    try {
      const buf = await processFrame(snap, idx);
      if (myGen === gen) draw(buf);
    } catch (e) {
      status = `Error: ${e}`;
    }
  }

  function draw(buf: ArrayBuffer) {
    if (!meta || !canvasEl) return;
    const { width, height } = meta;
    const need = width * height * 4;
    if (buf.byteLength < need) return;
    canvasEl.width = width;
    canvasEl.height = height;
    const ctx = canvasEl.getContext("2d");
    if (!ctx) return;
    const arr = new Uint8ClampedArray(buf.slice(0, need));
    ctx.putImageData(new ImageData(arr, width, height), 0, 0);
  }

  function resetView() {
    zoom = 1;
    pan = { x: 0, y: 0 };
  }

  async function load() {
    const path = await open({
      multiple: false,
      filters: [
        {
          name: "Image",
          extensions: ["png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff"],
        },
      ],
    });
    if (typeof path !== "string") return;
    try {
      meta = await openImage(path);
      frameIndex = 0;
      resetView();
      status = `${meta.width}x${meta.height}${meta.is_gif ? ` · ${meta.frame_count} frames` : ""}`;
    } catch (e) {
      status = `Error: ${e}`;
    }
  }

  async function doExport() {
    if (!meta) return;
    if (meta.is_gif) {
      const path = await save({ filters: [{ name: "GIF", extensions: ["gif"] }] });
      if (path) await exportGif(path, $state.snapshot(settings) as Settings);
    } else {
      const path = await save({
        filters: [
          { name: "PNG", extensions: ["png"] },
          { name: "JPEG", extensions: ["jpeg", "jpg"] },
          { name: "WebP", extensions: ["webp"] },
          { name: "TIFF", extensions: ["tiff"] },
          { name: "BMP", extensions: ["bmp"] },
          { name: "ICO", extensions: ["ico"] },
        ],
      });
      if (path) {
        await exportStill(path, $state.snapshot(settings) as Settings, frameIndex);
        status = "Export complete";
      }
    }
  }

  async function doSaveTemplate() {
    const path = await save({ filters: [{ name: "Template", extensions: ["json"] }] });
    if (path) await saveTemplate(path, $state.snapshot(settings) as Settings);
  }

  async function doLoadTemplate() {
    const path = await open({
      multiple: false,
      filters: [{ name: "Template", extensions: ["json"] }],
    });
    if (typeof path === "string") settings = await loadTemplate(path);
  }

  function reset() {
    settings = defaultSettings();
  }

  function playGif() {
    if (!meta?.is_gif) return;
    playing = true;
    tick();
  }
  function tick() {
    if (!playing || !meta) return;
    frameIndex = (frameIndex + 1) % meta.frame_count;
    gifTimer = setTimeout(tick, meta.durations[frameIndex] || 100);
  }
  function stopGif() {
    playing = false;
    clearTimeout(gifTimer);
  }

  function onWheel(e: WheelEvent) {
    e.preventDefault();
    // macOS trackpad pinch arrives as wheel + ctrlKey
    const factor = e.ctrlKey
      ? 1 - e.deltaY * 0.01
      : e.deltaY < 0
        ? 1.1
        : 1 / 1.1;
    zoom = clamp(zoom * factor, 0.1, 16);
  }
  function onPointerDown(e: PointerEvent) {
    dragging = true;
    dragLast = { x: e.clientX, y: e.clientY };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }
  function onPointerMove(e: PointerEvent) {
    if (!dragging) return;
    pan = {
      x: pan.x + (e.clientX - dragLast.x),
      y: pan.y + (e.clientY - dragLast.y),
    };
    dragLast = { x: e.clientX, y: e.clientY };
  }
  function onPointerUp() {
    dragging = false;
  }

  function onKey(e: KeyboardEvent) {
    if (!(e.metaKey || e.ctrlKey)) return;
    const k = e.key.toLowerCase();
    const map: Record<string, () => void> = {
      o: load,
      e: doExport,
      r: reset,
      s: doSaveTemplate,
      l: doLoadTemplate,
    };
    if (map[k]) {
      e.preventDefault();
      map[k]();
    }
  }
</script>

<svelte:window on:keydown={onKey} on:pointerup={onPointerUp} />

<div class="app">
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="viewport"
    onwheel={onWheel}
    onpointerdown={onPointerDown}
    onpointermove={onPointerMove}
    ondblclick={resetView}
  >
    <div
      class="stage"
      style="transform: translate({pan.x}px, {pan.y}px) scale({zoom});"
    >
      <canvas bind:this={canvasEl} class:hidden={!meta}></canvas>
      {#if !meta}
        <div class="empty">Upload an image or GIF</div>
      {/if}
    </div>
  </div>

  <aside class="panel">
    <button class="btn upload" onclick={load}>Upload Image/GIF</button>

    <select bind:value={settings.algorithm} class="select">
      {#each algorithms as a (a)}
        <option value={a}>{a}</option>
      {/each}
    </select>

    <label class="check">
      <input type="checkbox" bind:checked={settings.greyscale} /> Greyscale
    </label>

    <Slider label="Scale (%)" min={1} max={100} bind:value={settings.scale} />
    <Slider label="Contrast" min={0.5} max={3} step={0.1} bind:value={settings.contrast} />
    <Slider label="Midtones" min={0.5} max={3} step={0.1} bind:value={settings.midtones} />
    <Slider label="Highlights" min={0.5} max={3} step={0.1} bind:value={settings.highlights} />
    <Slider label="Blur" min={0} max={10} step={0.1} bind:value={settings.blur} />
    <Slider label="Pixelation" min={1} max={20} bind:value={settings.pixelation} />
    <Slider label="Noise" min={0} max={100} bind:value={settings.noise} />
    <Slider label="Threshold" min={0} max={255} bind:value={settings.threshold} />

    <label class="color">
      Foreground
      <input type="color" bind:value={settings.foreground} />
    </label>
    <Slider label="Foreground Opacity" min={0} max={255} bind:value={settings.foreground_opacity} />

    <label class="color">
      Background
      <input type="color" bind:value={settings.background} />
    </label>
    <Slider label="Background Opacity" min={0} max={255} bind:value={settings.background_opacity} />

    <div class="btnrow">
      <button class="btn" onclick={doExport} disabled={!meta}>Export</button>
      <button class="btn" onclick={reset}>Reset</button>
    </div>
    <div class="btnrow">
      <button class="btn" onclick={doSaveTemplate}>Save Template</button>
      <button class="btn" onclick={doLoadTemplate}>Load Template</button>
    </div>

    {#if meta?.is_gif}
      <div class="btnrow">
        {#if playing}
          <button class="btn" onclick={stopGif}>Stop GIF</button>
        {:else}
          <button class="btn" onclick={playGif}>Play GIF</button>
        {/if}
      </div>
    {/if}

    {#if progress > 0}
      <div class="progress"><div class="bar" style="width:{progress * 100}%"></div></div>
    {/if}
    <div class="status">{status}</div>
  </aside>
</div>

<style>
  .app {
    display: flex;
    height: 100%;
  }
  .viewport {
    flex: 1;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    background:
      repeating-conic-gradient(#bfbfbf 0% 25%, #e0e0e0 0% 50%) 50% / 20px 20px;
    margin: 10px;
    border-radius: 4px;
    cursor: grab;
  }
  .viewport:active {
    cursor: grabbing;
  }
  .stage {
    transform-origin: center center;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  canvas {
    image-rendering: pixelated;
    display: block;
    max-width: none;
  }
  canvas.hidden {
    display: none;
  }
  .empty {
    color: #555;
    font-size: 14px;
    padding: 40px;
  }
  .panel {
    width: 300px;
    background: var(--panel-bg);
    padding: 12px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .btn {
    display: block;
    width: 100%;
    background: var(--btn);
    color: var(--text);
    border: 1px solid #2f323a;
    border-radius: 6px;
    padding: 9px 10px;
    cursor: pointer;
    font-size: 13px;
  }
  .btn:hover:not(:disabled) {
    background: var(--btn-hover);
  }
  .btn:disabled {
    opacity: 0.4;
    cursor: default;
  }
  .upload {
    font-weight: 600;
    margin-bottom: 2px;
  }
  .btnrow {
    display: flex;
    gap: 6px;
  }
  .btnrow .btn {
    width: auto;
    flex: 1;
  }
  .select {
    width: 100%;
    background: var(--container-bg);
    color: var(--text);
    border: 1px solid #2f323a;
    border-radius: 6px;
    padding: 9px 10px;
    font-size: 13px;
    cursor: pointer;
    appearance: none;
    background-image: linear-gradient(45deg, transparent 50%, #8a8f96 50%),
      linear-gradient(135deg, #8a8f96 50%, transparent 50%);
    background-position:
      calc(100% - 16px) 50%,
      calc(100% - 11px) 50%;
    background-size:
      5px 5px,
      5px 5px;
    background-repeat: no-repeat;
  }
  .select option {
    background: var(--container-bg);
    color: var(--text);
  }
  .check {
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .color {
    font-size: 12px;
    color: #cfd2d6;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 4px;
  }
  .color input {
    width: 48px;
    height: 26px;
    border: none;
    background: none;
  }
  .progress {
    height: 6px;
    background: var(--track);
    border-radius: 3px;
    overflow: hidden;
  }
  .bar {
    height: 100%;
    background: var(--accent);
  }
  .status {
    font-size: 11px;
    color: #8a8f96;
    margin-top: 2px;
  }
</style>
