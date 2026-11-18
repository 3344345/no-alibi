<script lang="ts">
  import type { Row, Action } from './types'
  import { str, title } from './game'
  export let locations: Row[] = []
  export let actions: Action[] = []
  export let current: string | undefined
  export let busy = false
  export let select: (a: Action) => void
  function photo(id: string | undefined) {
    const n = Number(id?.slice(1) ?? 1) - 1
    return (n % 3) * 50 + '% ' + Math.floor(n / 3) * 50 + '%'
  }
</script>

<div class="location-grid">
  {#each locations as place}
    {@const go = actions.find((a) => a.kind === 'travel' && a.args?.location === place.id)}
    <article class="site-card">
      <div class="site-image" style:background-position={photo(place.id)} aria-hidden="true"></div>
      <div class="site-content">
        <div class="site-head">
          <h3>{title(place)}</h3>
          <small>{place.id === current ? '当前位置' : str(place, 'access')}</small>
        </div>
        <p>{str(place, 'description')}</p>
        {#if go}<button class="link-button" disabled={busy} on:click={() => select(go)}
            >前往 · {go.cost} →</button
          >
        {:else if current !== place.id}<small>当前没有可出发的行程。</small>{/if}
      </div>
    </article>
  {/each}
</div>
