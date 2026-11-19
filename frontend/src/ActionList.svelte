<script lang="ts">
  import type { Action } from './types'
  export let actions: Action[] = []
  export let select: (a: Action) => void
  export let busy = false
  export let empty = '当前位置没有这类可办理的行动。'
</script>

{#if actions.length}<div class="action-list">
    {#each actions as act}
      <button
        type="button"
        class="action-row"
        disabled={busy || act.enabled === false}
        on:click={() => select(act)}
      >
        <span
          ><strong>{act.label}</strong>{#if act.description}<small>{act.description}</small>{/if}
          {#if act.enabled === false && act.reason}<small class="reason">暂不可办 · {act.reason}</small
            >{/if}
          {#if act.cost !== undefined && act.cost !== ''}<span class="action-cost"
              >{typeof act.cost === 'number' ? act.cost + ' 分钟' : act.cost}</span
            >{/if}
        </span><span class="row-arrow" aria-hidden="true">→</span>
      </button>
    {/each}
  </div>{:else}<p class="empty">{empty}</p>{/if}
