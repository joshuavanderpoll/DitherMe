<script lang="ts">
  interface Props {
    label: string;
    min: number;
    max: number;
    step?: number;
    value: number;
  }
  let { label, min, max, step = 1, value = $bindable() }: Props = $props();
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
      bind:value
    />
  </div>
  <input class="range" type="range" {min} {max} {step} bind:value />
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
</style>
