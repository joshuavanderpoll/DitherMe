<script lang="ts">
  import { onMount } from "svelte";
  import { open, save } from "@tauri-apps/plugin-dialog";
  import { listen } from "@tauri-apps/api/event";
  import { getCurrentWebview } from "@tauri-apps/api/webview";
  import Slider from "./lib/Slider.svelte";
  import {
    algorithmList,
    defaultSettings,
    exportGif,
    exportStill,
    loadTemplate,
    openImage,
    originalFrame,
    processFrame,
    saveTemplate,
    type ImageMeta,
    type Settings,
  } from "./lib/api";

  let settings = $state<Settings>(defaultSettings());
  let baseline = $state<Settings>(defaultSettings());
  let meta = $state<ImageMeta | null>(null);
  let algorithms = $state<string[]>([]);
  let frameIndex = $state(0);
  let zoom = $state(1);
  let pan = $state({ x: 0, y: 0 });
  let playing = $state(false);
  let progress = $state(0);
  let status = $state("No image loaded");
  let viewMode = $state<"After" | "Split">("After");
  let splitRatio = $state(0.5);
  let dragOver = $state(false);

  let canvasEl = $state<HTMLCanvasElement>();
  let origCanvasEl = $state<HTMLCanvasElement>();
  let stageEl = $state<HTMLDivElement>();
  let dragging = false;
  let draggingDivider = false;
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
    const unDrop = getCurrentWebview().onDragDropEvent((event) => {
      if (event.payload.type === "enter" || event.payload.type === "over") {
        dragOver = true;
      } else if (event.payload.type === "leave") {
        dragOver = false;
      } else if (event.payload.type === "drop") {
        dragOver = false;
        const p = event.payload.paths[0];
        if (p) void openPath(p);
      }
    });
    return () => {
      un.then((f) => f());
      unDrop.then((f) => f());
    };
  });

  // Reprocess whenever settings or the current frame change.
  $effect(() => {
    const snap = $state.snapshot(settings) as Settings;
    const idx = frameIndex;
    if (!meta) return;
    scheduleProcess(snap, idx);
  });

  // Keep the "before" canvas in sync with the current frame (split view).
  $effect(() => {
    const idx = frameIndex;
    if (!meta) return;
    void drawOriginal(idx);
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

  function drawTo(canvas: HTMLCanvasElement | undefined, buf: ArrayBuffer) {
    if (!meta || !canvas) return;
    const { width, height } = meta;
    const need = width * height * 4;
    if (buf.byteLength < need) return;
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const arr = new Uint8ClampedArray(buf.slice(0, need));
    ctx.putImageData(new ImageData(arr, width, height), 0, 0);
  }

  function draw(buf: ArrayBuffer) {
    drawTo(canvasEl, buf);
  }

  async function drawOriginal(idx: number) {
    try {
      drawTo(origCanvasEl, await originalFrame(idx));
    } catch (e) {
      status = `Error: ${e}`;
    }
  }

  function resetView() {
    zoom = 1;
    pan = { x: 0, y: 0 };
  }

  async function openPath(path: string) {
    try {
      meta = await openImage(path);
      frameIndex = 0;
      resetView();
      status = `${meta.width}x${meta.height}${meta.is_gif ? ` · ${meta.frame_count} frames` : ""}`;
    } catch (e) {
      status = `Error: ${e}`;
    }
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
    if (typeof path === "string") await openPath(path);
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
    if (typeof path === "string") {
      const loaded = await loadTemplate(path);
      settings = loaded;
      baseline = { ...loaded };
    }
  }

  function reset() {
    settings = defaultSettings();
    baseline = defaultSettings();
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
    // In split view, grabbing near the divider drags it instead of panning.
    if (viewMode === "Split" && stageEl) {
      const r = stageEl.getBoundingClientRect();
      const dividerX = r.left + splitRatio * r.width;
      if (Math.abs(e.clientX - dividerX) <= 14) {
        draggingDivider = true;
        (e.target as HTMLElement).setPointerCapture(e.pointerId);
        return;
      }
    }
    dragging = true;
    dragLast = { x: e.clientX, y: e.clientY };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }
  function onPointerMove(e: PointerEvent) {
    if (draggingDivider && stageEl) {
      const r = stageEl.getBoundingClientRect();
      splitRatio = clamp((e.clientX - r.left) / r.width, 0.05, 0.95);
      return;
    }
    if (!dragging) return;
    pan = {
      x: pan.x + (e.clientX - dragLast.x),
      y: pan.y + (e.clientY - dragLast.y),
    };
    dragLast = { x: e.clientX, y: e.clientY };
  }
  function onPointerUp() {
    dragging = false;
    draggingDivider = false;
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
  <header class="toolbar">
    <div class="group">
      <button class="tbtn strong" onclick={load}>Upload</button>
      <button class="tbtn" onclick={doExport} disabled={!meta}>Export</button>
      <button class="tbtn" onclick={reset}>Reset</button>
    </div>
    <div class="mid">
      {#if progress > 0}
        <div class="progress"><div class="bar" style="width:{progress * 100}%"></div></div>
      {/if}
      <span class="status">{status}</span>
    </div>
    <div class="group">
      <button class="tbtn" onclick={doSaveTemplate}>Save Template</button>
      <button class="tbtn" onclick={doLoadTemplate}>Load Template</button>
    </div>
  </header>

  <div class="body">
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="viewport"
      class:dragover={dragOver}
      onwheel={onWheel}
      onpointerdown={onPointerDown}
      onpointermove={onPointerMove}
      ondblclick={resetView}
    >
      {#if dragOver}
        <div class="drophint">Drop file here</div>
      {/if}
      <div
        class="stage"
        bind:this={stageEl}
        style="width:{meta ? meta.width + 'px' : 'auto'}; height:{meta
          ? meta.height + 'px'
          : 'auto'}; transform: translate({pan.x}px, {pan.y}px) scale({zoom});"
      >
        {#if meta}
          <canvas bind:this={origCanvasEl} class="layer"></canvas>
          <canvas
            bind:this={canvasEl}
            class="layer"
            style={viewMode === "Split"
              ? `clip-path: inset(0 0 0 ${splitRatio * 100}%);`
              : ""}
          ></canvas>
          {#if viewMode === "Split"}
            <div class="divider" style="left:{splitRatio * 100}%;"></div>
          {/if}
        {:else if !dragOver}
          <div class="empty">Upload an image or GIF</div>
        {/if}
      </div>

      {#if meta}
        <div class="viewtoggle">
          <button
            class:active={viewMode === "After"}
            onclick={() => (viewMode = "After")}>After</button
          >
          <button
            class:active={viewMode === "Split"}
            onclick={() => (viewMode = "Split")}>Split</button
          >
        </div>
      {/if}

      {#if meta?.is_gif}
        <div class="playbar">
          {#if playing}
            <button class="tbtn" onclick={stopGif}>Stop</button>
          {:else}
            <button class="tbtn" onclick={playGif}>Play</button>
          {/if}
          <span class="frames">{frameIndex + 1} / {meta.frame_count}</span>
        </div>
      {/if}
    </div>

    <aside class="panel" class:disabled={!meta}>
      <select bind:value={settings.algorithm} class="select" disabled={!meta}>
        {#each algorithms as a (a)}
          <option value={a}>{a}</option>
        {/each}
      </select>

      <label class="check">
        <input type="checkbox" bind:checked={settings.greyscale} disabled={!meta} /> Greyscale
      </label>

      <Slider label="Scale (%)" min={1} max={100} bind:value={settings.scale} default={baseline.scale} disabled={!meta} />
      <Slider label="Contrast" min={0.5} max={3} step={0.1} bind:value={settings.contrast} default={baseline.contrast} disabled={!meta} />
      <Slider label="Midtones" min={0.5} max={3} step={0.1} bind:value={settings.midtones} default={baseline.midtones} disabled={!meta} />
      <Slider label="Highlights" min={0.5} max={3} step={0.1} bind:value={settings.highlights} default={baseline.highlights} disabled={!meta} />
      <Slider label="Blur" min={0} max={10} step={0.1} bind:value={settings.blur} default={baseline.blur} disabled={!meta} />
      <Slider label="Pixelation" min={1} max={20} bind:value={settings.pixelation} default={baseline.pixelation} disabled={!meta} />
      <Slider label="Noise" min={0} max={100} bind:value={settings.noise} default={baseline.noise} disabled={!meta} />
      <Slider label="Threshold" min={0} max={255} bind:value={settings.threshold} default={baseline.threshold} disabled={!meta} />

      <label class="color">
        Foreground
        <input type="color" bind:value={settings.foreground} disabled={!meta} />
      </label>
      <Slider label="Foreground Opacity" min={0} max={255} bind:value={settings.foreground_opacity} default={baseline.foreground_opacity} disabled={!meta} />

      <label class="color">
        Background
        <input type="color" bind:value={settings.background} disabled={!meta} />
      </label>
      <Slider label="Background Opacity" min={0} max={255} bind:value={settings.background_opacity} default={baseline.background_opacity} disabled={!meta} />
    </aside>
  </div>
</div>

<style>
  .app {
    position: relative;
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  .toolbar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 10px;
    background: var(--container-bg);
    border-bottom: 1px solid #000;
  }
  .group {
    display: flex;
    gap: 6px;
  }
  .mid {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    min-width: 0;
  }
  .tbtn {
    background: var(--btn);
    color: var(--text);
    border: 1px solid #2f323a;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    cursor: pointer;
    white-space: nowrap;
  }
  .tbtn:hover:not(:disabled) {
    background: var(--btn-hover);
  }
  .tbtn:disabled {
    opacity: 0.4;
    cursor: default;
  }
  .tbtn.strong {
    font-weight: 600;
  }
  .body {
    flex: 1;
    display: flex;
    min-height: 0;
  }
  .viewport {
    position: relative;
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
    position: relative;
    flex: none;
    transform-origin: center center;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .layer {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    image-rendering: pixelated;
    display: block;
  }
  .divider {
    position: absolute;
    top: 0;
    height: 100%;
    width: 2px;
    margin-left: -1px;
    background: #ff2d2d;
    pointer-events: none;
  }
  .divider::before,
  .divider::after {
    content: "";
    position: absolute;
    left: 50%;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #ff2d2d;
    transform: translateX(-50%);
  }
  .divider::before {
    top: 0;
  }
  .divider::after {
    bottom: 0;
  }
  .viewtoggle {
    position: absolute;
    left: 14px;
    bottom: 14px;
    display: flex;
    background: rgba(0, 0, 0, 0.6);
    border-radius: 8px;
    overflow: hidden;
    backdrop-filter: blur(4px);
  }
  .viewtoggle button {
    background: transparent;
    color: #cfd2d6;
    border: none;
    padding: 6px 14px;
    font-size: 12px;
    cursor: pointer;
  }
  .viewtoggle button.active {
    background: var(--accent);
    color: #fff;
  }
  .empty {
    color: #e8e8e8;
    font-size: 14px;
    padding: 14px 22px;
    background: rgba(14, 15, 16, 0.72);
    border: 1px solid #2f323a;
    border-radius: 10px;
    backdrop-filter: blur(2px);
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
  .panel.disabled {
    opacity: 0.5;
  }
  .playbar {
    position: absolute;
    bottom: 16px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 10px;
    background: rgba(0, 0, 0, 0.6);
    border-radius: 20px;
    backdrop-filter: blur(4px);
  }
  .frames {
    font-size: 12px;
    color: #cfd2d6;
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
    width: 160px;
    flex: none;
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
    font-size: 12px;
    color: #8a8f96;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .viewport.dragover {
    outline: 2px dashed var(--accent);
    outline-offset: -6px;
  }
  .drophint {
    position: absolute;
    z-index: 5;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    padding: 10px 18px;
    border-radius: 8px;
    background: rgba(14, 15, 16, 0.82);
    color: #e8e8e8;
    font-size: 14px;
    pointer-events: none;
  }
</style>
