<script lang="ts">
  import GameUpdate from './GameUpdate.svelte'
  import ArchiveCinema from './ArchiveCinema.svelte'
  import Dialog from './Dialog.svelte'
  import StoryCinema from './StoryCinema.svelte'
  import CastGallery from './CastGallery.svelte'
  type Library = 'archive' | 'stories' | 'cast'
  let library: Library | null = null
  function openLibrary(next: Library, event: MouseEvent) {
    if (event.currentTarget instanceof HTMLButtonElement) event.currentTarget.focus()
    library = next
  }
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
      <nav class="libraries" aria-label="影像与人物">
        <button on:click={(event) => openLibrary('stories', event)}>剧情放映厅</button>
        <button on:click={(event) => openLibrary('archive', event)}>年代放映室</button>
        <button on:click={(event) => openLibrary('cast', event)}>人物与出处</button>
      </nav>
    </header>
    <h2 class="group-title">选择玩法</h2>
    <div class="modes" role="group" aria-label="模式选择">
      <button aria-label="生涯模式" on:click={county}>
        <img alt="" src="/county-office.jpg" />
        <span class="copy"
          ><small>澄川县</small><strong>生涯模式</strong>
          <span>在澄川县从一份工作起步，过自己的人生。也可以翻开《市井家书》，走进普通人的故事。</span>
        </span><b aria-hidden="true">→</b>
      </button>
      <button aria-label="历史主角模式" on:click={witness}>
        <img alt="" src="/chronicle/witness_chongqing_talks.webp" />
        <span class="copy"
          ><small>从戊戌变法到新世纪</small><strong>历史主角模式</strong>
          <span>选一桩真实的历史事件，以张学良、邓小平等亲历者的身份作决定。</span>
        </span><b aria-hidden="true">→</b>
      </button>
    </div>
    <h2 class="group-title features-title">精选故事</h2>
    <FeaturedStories {play} />
  </main>
  <GameUpdate />
</div>

{#if library === 'archive'}
  <Dialog title="年代放映室" onclose={() => (library = null)}><ArchiveCinema /></Dialog>
{:else if library === 'stories'}
  <Dialog title="剧情放映厅" onclose={() => (library = null)}><StoryCinema /></Dialog>
{:else if library === 'cast'}
  <Dialog title="人物与出处" onclose={() => (library = null)}><CastGallery /></Dialog>
{/if}

<style>
  .libraries {display:flex;justify-content:flex-end;gap:6px;margin-left:auto;}
  .libraries button {padding:.55rem .85rem;min-height:44px;color:#e5d9c1;background:transparent;border:1px solid #857a63;}
  .libraries button:hover,.libraries button:focus-visible {background:#353a32;border-color:#e0b573;}
  @media(max-width:600px){header{flex-wrap:wrap;row-gap:10px;}.libraries{width:100%;justify-content:flex-start;flex-wrap:wrap;}.libraries button{font-size:.86rem;padding:.36rem .65rem;min-height:38px;}}
  .mode-page {
    background: #1c201e;
    color: #f3e9d4;
    min-height: 100vh;
    padding: 0 clamp(16px, 5vw, 80px) clamp(24px, 5vw, 72px);
  }
  header,
  .group-title,
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
  .group-title {
    margin: 0 auto .65rem;
    font: 600 1.12rem/1.35 var(--serif);
    color: #efe3ce;
  }
  .features-title { margin-top: clamp(1.3rem, 3vh, 2.1rem); }
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
    min-height: clamp(160px, 21vh, 218px);
    padding: clamp(18px, 2.4vw, 34px);
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
      min-height: 112px;
      padding: 12px 16px;
    }
    .modes { gap: 8px; }
    .copy { gap: .16rem; }
    .copy strong { font-size: 1.55rem; }
    .copy small { font-size: .76rem; }
    .copy > span { font-size: .86rem; line-height: 1.4; }
    header {
      padding: 13px 0;
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
