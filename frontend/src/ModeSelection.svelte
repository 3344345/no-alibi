<script lang="ts">
  import GameUpdate from './GameUpdate.svelte'
  import ArchiveCinema from './ArchiveCinema.svelte'
  import Dialog from './Dialog.svelte'
  let cinema = false
  import FeaturedStories from './FeaturedStories.svelte'
  import type { Feature } from './features'
  export let play: (story: Feature) => void
  export let county: () => void
  export let witness: () => void
</script>

<div class="mode-page">
  <main id="main">
    <header>
      <img src="/seal.svg" alt="" />
      <h1>局中事</h1>
      <button class="cinema-link" on:click={() => (cinema = true)}>年代放映室</button>
    </header>
    <FeaturedStories {play} />
    <div class="modes" role="group" aria-label="模式选择">
      <button aria-label="生涯模式" on:click={county}>
        <img alt="" src="/scenes/county-nightbus.webp" />
        <span class="copy"
          ><small>澄川县</small><strong>生涯模式</strong>
          <span>有人愿意付三千块，请你在县城旧影院的镜头里站一会儿。从办公桌进入《散场以后》，看看他们拿这段影像做了什么。</span>
        </span><b aria-hidden="true">→</b>
      </button>
      <button aria-label="历史主角模式" on:click={witness}>
        <img alt="" src="/chronicle/night_screen.webp" />
        <span class="copy"
          ><small>从戊戌变法到新世纪</small><strong>历史主角模式</strong>
          <span>选一件真实发生的事，成为亲历者。你作的决定，可以让人走向另一种命运。</span>
        </span><b aria-hidden="true">→</b>
      </button>
    </div>
  </main>
  <GameUpdate />
</div>

{#if cinema}
  <Dialog title="年代放映室" onclose={() => (cinema = false)}><ArchiveCinema /></Dialog>
{/if}

<style>
  .cinema-link {margin-left:auto; padding:.6rem .9rem; min-height:44px; background:transparent; color:#e5d9c1; border:1px solid #857a63;}
  .cinema-link:hover {background:#353a32;}
  .mode-page {
    background: #1c201e;
    color: #f3e9d4;
    min-height: 100vh;
    padding: 0 clamp(16px, 5vw, 80px) clamp(24px, 5vw, 72px);
  }
  header,
  .modes {
    max-width: 1400px;
    margin: auto;
  }
  header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: clamp(18px, 2.8vh, 38px) 0;
  }
  header img {
    width: 36px;
    height: 36px;
  }
  h1 {
    font: 600 clamp(1.8rem, 2.7vw, 3rem) / 1.2 var(--serif);
    letter-spacing: 0.12em;
  }
  .modes {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: clamp(12px, 2vw, 34px);
  }
  .modes button {
    position: relative;
    display: flex;
    align-items: flex-end;
    isolation: isolate;
    overflow: hidden;
    min-height: clamp(165px, 23vh, 280px);
    padding: clamp(20px, 3.5vw, 58px);
    gap: 14px;
    color: #fff3dc;
    border: 1px solid #635f52;
    background: #2a302c;
    text-align: left;
  }
  .modes button::after {
    position: absolute;
    inset: 0;
    content: '';
    z-index: -1;
    background: linear-gradient(
      0deg,
      rgba(18, 22, 19, 0.98),
      rgba(18, 22, 19, 0.8) 25%,
      rgba(18, 22, 19, 0.16) 68%
    );
  }
  .modes button:hover,
  .modes button:focus-visible {
    border-color: #f1c785;
  }
  .modes button > img {
    position: absolute;
    inset: 0;
    height: 100%;
    width: 100%;
    object-fit: cover;
    z-index: -2;
  }
  .copy {
    display: grid;
    gap: 0.5rem;
    max-width: 31em;
  }
  .copy small {
    color: #efd6a1;
    font-size: 0.88rem;
  }
  .copy strong {
    font-family: var(--serif);
    font-size: clamp(1.9rem, 3.5vw, 3.7rem);
    font-weight: 600;
  }
  .copy > span {
    font-size: clamp(0.9rem, 1.2vw, 1.16rem);
    line-height: 1.85;
    color: #eee5d4;
  }
  b {
    margin-left: auto;
    padding-bottom: 0.2em;
    font-size: 1.5rem;
    color: #e9c98e;
  }
  @media (max-width: 680px) {
    .modes {
      grid-template-columns: 1fr;
    }
    .modes button {
      min-height: 155px;
    }
    header {
      padding: 22px 0;
    }
    .modes button::after {
      background: linear-gradient(
        0deg,
        rgba(18, 22, 19, 0.97),
        rgba(18, 22, 19, 0.68) 48%,
        rgba(18, 22, 19, 0.18)
      );
    }
  }
</style>
