<script lang="ts">
  import type { Row } from './types'

  export let place: Row

  import ReadingView from './ReadingView.svelte'
  import { countyCamera } from './readingView'

  $: id=place.id ?? ''
</script>

{#if place.name}
  <figure class="scene">
    <figcaption aria-live="polite" aria-atomic="true">
      <strong>{place.name}</strong>
      {#if place.description}<p>{place.description}</p>{/if}
    </figcaption>
    {#if /^L0[1-9]$/.test(id)}
      <div class="image"><ReadingView camera={countyCamera(id)}/></div>
    {/if}
  </figure>
{/if}

<style>
  .scene {
    display: flex;
    align-items: stretch;
    min-height: clamp(5.5rem, 9vw, 7.5rem);
    margin: 0 0 1rem;
    background: var(--paper);
    border: 1px solid var(--line);
    border-radius: 4px;
    overflow: hidden;
  }

  figcaption {
    align-self: center;
    flex: 1;
    min-width: 0;
    padding: 0.65rem clamp(0.8rem, 1.8vw, 1.4rem);
  }

  strong {
    font-family: var(--serif);
    font-size: clamp(1.05rem, 1.55vw, 1.3rem);
    line-height: 1.4;
  }

  p {
    margin: 0.2rem 0 0;
    font-size: 0.875rem;
    line-height: 1.55;
    color: var(--muted);
  }

  .image {
    flex: 0 0 44%;
    min-width: 0;
    position: relative;
    background: var(--soft);
  }

  @media (max-width: 600px) {
    .scene {
      min-height: 4.75rem;
      margin-bottom: 0.75rem;
    }

    .image { flex-basis: 31%; }
  }
</style>
