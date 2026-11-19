<script lang="ts">
  import type { Action, Value } from './types'
  export let write: Action | undefined
  export let select: (action: Action, values: Record<string, Value>) => void
  let hypothesis = ''
</script>

<div class="working-note">
  <label class="field"
    >临时推测<textarea
      rows="3"
      maxlength="1000"
      bind:value={hypothesis}
      placeholder="你认为两份材料可能用了怎样的日期或范围？"
    ></textarea></label
  >
  <p class="helper">关闭对照后清空。需要留存时，可以写入当前可用的实体记事本。</p>
  {#if write}<button
      class="button compact"
      disabled={!hypothesis.trim()}
      on:click={() => write && select(write, { text: hypothesis.trim() })}>将推测记入本子</button
    >{/if}
</div>
