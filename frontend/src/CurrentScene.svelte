<script lang="ts">
  import type { Row } from './types'

  export let place: Row

  const panoramas: Record<string, string> = {
    L01: '/scenes/office.webp',
    L02: '/scenes/canal.webp',
    L07: '/scenes/home.webp',
  }
  let failedImage = ''
  $: id = place.id ?? ''
  $: photo = panoramas[id]
  $: cell = /^L0[1-9]$/.test(id) ? Number(id.slice(1)) - 1 : -1
  // The nine locations share a 1536 × 1024 sheet. Slice a single 3:2 tile
  // before fitting it to this strip so neighbouring locations never bleed in.
  $: crop = `${(cell % 3) * 512} ${(Math.floor(cell / 3) * 1024) / 3} 512 ${1024 / 3}`
</script>

{#if place.name}
  <figure class="scene">
    <figcaption aria-live="polite" aria-atomic="true">
      <strong>{place.name}</strong>
      {#if place.description}<p>{place.description}</p>{/if}
    </figcaption>
    {#if cell >= 0}
      <div class="image" aria-hidden="true">
        {#if photo && failedImage !== photo}
          {#key photo}
            <img src={photo} alt="" decoding="async" on:error={() => (failedImage = photo)} />
          {/key}
        {:else}
          <svg viewBox={crop} preserveAspectRatio="xMidYMid slice" focusable="false">
            <image href="/county-locations.jpg" width="1536" height="1024" />
          </svg>
        {/if}
      </div>
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

  img, svg {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  @media (max-width: 600px) {
    .scene {
      min-height: 4.75rem;
      margin-bottom: 0.75rem;
    }

    .image { flex-basis: 31%; }
  }
</style>
