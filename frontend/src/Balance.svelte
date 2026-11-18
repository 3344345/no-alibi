<script lang="ts">
  import { balanceString } from './game'
  export let value = '0.500000'
  export let prefix = 'balance'
  $: canonical = balanceString(value)
</script>

<div class="balance-control">
  <div class="form-line">
    <label for={prefix + '-number'}>真实性—可玩性平衡</label>
    <input
      class="digits numeric"
      id={prefix + '-number'}
      type="text"
      inputmode="decimal"
      maxlength="8"
      bind:value
      aria-invalid={!canonical}
    />
  </div>
  <input
    id={prefix + '-range'}
    aria-label="连续调整模拟取向"
    type="range"
    min="0"
    max="1"
    step="0.000001"
    value={canonical ?? 0.5}
    on:input={(event) => (value = Number(event.currentTarget.value).toFixed(6))}
  />
  <div class="range-labels"><span>0 严谨优先</span><span>0.5 兼顾</span><span>1 趣味优先</span></div>
  {#if !canonical}<p class="error">请输入 0 至 1 之间的数值，最多六位小数。</p>{/if}
</div>
