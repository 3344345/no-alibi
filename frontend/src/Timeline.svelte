<script lang="ts">
  import { stamp } from './game'
  import type { Entry } from './types'
  export let entries: Entry[] = []
  export let detailed = true
</script>

{#if entries.length}
  <div class="timeline">
    {#each [...entries].reverse() as item}
      <article>
        <time>{stamp(item.minute)}</time>
        <h3>{item.title}</h3>
        {#if item.text && item.text !== item.title}{#if detailed}<p>{item.text}</p>{:else}<details>
              <summary>阅读经过</summary>
              <p>{item.text}</p>
            </details>{/if}{/if}
        {#if item.refs?.length}<small>关联记录 · {item.refs.join('、')}</small>{/if}
      </article>
    {/each}
  </div>
{:else}<p class="empty">目前没有已知经过。</p>{/if}
