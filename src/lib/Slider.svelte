<script lang="ts">
  interface Props {
    label: string;
    min: number;
    max: number;
    step?: number;
    value: number;
    default: number;
    disabled?: boolean;
  }
  let {
    label,
    min,
    max,
    step = 1,
    value = $bindable(),
    default: defaultValue,
    disabled = false,
  }: Props = $props();

  function clampLive() {
    if (Number.isFinite(value)) {
      if (value > max) value = max;
      else if (value < min) value = min;
    }
  }
  function normalize() {
    value = Number.isFinite(value) ? Math.min(max, Math.max(min, value)) : defaultValue;
  }
</script>

<div class="slider">
  <div class="row">
    <span class="label">{label}</span>
    <input
      class="num"
      type="number"
      {min}
      {max}
      {step}
      {disabled}
      title="Double-click to reset"
      ondblclick={() => !disabled && (value = defaultValue)}
      oninput={clampLive}
      onchange={normalize}
      bind:value
    />
  </div>
  <input class="range" type="range" {min} {max} {step} {disabled} bind:value />
</div>

<style>
  .slider {
    padding: 4px 0;
  }
  .row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    margin-bottom: 2px;
  }
  .label {
    color: #cfd2d6;
  }
  .num {
    width: 56px;
    background: var(--container-bg);
    color: var(--text);
    border: 1px solid #2a2c33;
    border-radius: 4px;
    padding: 1px 4px;
    text-align: right;
  }
  .range {
    width: 100%;
    accent-color: var(--accent);
  }
  .num:disabled,
  .range:disabled {
    cursor: not-allowed;
  }
</style>
