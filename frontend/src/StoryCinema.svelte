<script lang="ts">
  import AuditoriumView from './AuditoriumView.svelte'
  import { onDestroy } from 'svelte'
  import catalog from './screenings.json'

  type Film = (typeof catalog)[number]['films'][number]
  let group = catalog[0]
  let current = group.films[0]
  let player: HTMLVideoElement
  let muted = true
  let captions = true
  let failed = false
  function select(film: Film) {
    if (film.id === current.id) return
    player?.pause()
    failed = false
    current = film
  }
  function showGroup(index: number) {
    group = catalog[index]
    if (!group.films.some(f => f.id === current.id)) select(group.films[0])
  }
  function setCaptions() {
    const track = player?.textTracks[0]
    if (track) track.mode = captions ? 'showing' : 'disabled'
  }
  function muteChanged() {
    if (player) muted = player.muted
  }
  function retry() {
    failed = false
    player?.load()
  }
  onDestroy(() => player?.pause())
</script>

<section class="theater" aria-label="剧情短片">
  <nav class="shelves" aria-label="短片分类">
    {#each catalog as shelf, i}
      <button type="button" aria-pressed={group === shelf} on:click={() => showGroup(i)}>
        {shelf.name} <span>{shelf.films.length}</span>
      </button>
    {/each}
  </nav>
  <div class="layout">
    <div class="screen">
      <AuditoriumView>
{#key current.id}
        <video controls playsinline preload="metadata" bind:this={player} {muted}
          src={'/motion/' + current.id + '.mp4'} poster={current.poster || undefined} aria-label={current.title}
          on:volumechange={muteChanged} on:loadedmetadata={setCaptions} on:error={() => (failed = true)}>
          <track kind="captions" srclang="zh" label="中文声画字幕"
            src={'/motion/' + current.id + '.vtt'} default on:load={setCaptions} />
        </video>
      {/key}
      </AuditoriumView>
      {#if failed}
        <p role="status">这段本地影片暂时无法播放。<button type="button" on:click={retry}>重新载入</button></p>
      {/if}
      <div class="film-info">
        <div><small>{current.setting}</small><h3>{current.title}</h3></div>
        <span>{current.seconds} 秒</span>
      </div>
      <p class="cue">{current.cue}</p>
      <div class="toggles">
        <button type="button" aria-pressed={!muted} on:click={() => { muted = !muted; if (player) player.muted = muted }}>声音{muted ? '关' : '开'}</button>
        <button type="button" aria-pressed={captions} on:click={() => { captions = !captions; setCaptions() }}>字幕{captions ? '开' : '关'}</button>
      </div>
    </div>
    <nav class="list" aria-label={group.name + '片单'}>
      {#each group.films as film}
        <button type="button" aria-pressed={film.id === current.id} on:click={() => select(film)}>
          <span>{film.setting}</span><strong>{film.title}</strong>
        </button>
      {/each}
    </nav>
  </div>
</section>

<style>
  :global(dialog[aria-label='剧情放映厅']) {max-width:min(1160px,calc(100% - 24px));max-height:92dvh;padding:clamp(16px,2.5vw,32px);}
  .theater {color:#272d26;}
  button {cursor:pointer;}
  .shelves,.toggles {display:flex;flex-wrap:wrap;gap:6px;}
  .shelves {padding:0 0 15px;border-bottom:1px solid #bcb8a8;margin-bottom:16px;}
  .shelves button,.toggles button {min-height:38px;padding:5px 13px;background:transparent;color:#343d35;border:1px solid #a8aa99;border-radius:3px;}
  .shelves button[aria-pressed='true'] {background:#254137;border-color:#254137;color:#f6eedc;}
  .shelves span {font-size:.74em;margin-left:3px;font-variant-numeric:tabular-nums;}
  .layout {display:grid;grid-template-columns:minmax(0,2.3fr) minmax(178px,1fr);gap:clamp(12px,2vw,28px);align-items:start;}
  .screen {min-width:0;}
  video {display:block;width:100%;aspect-ratio:16/9;max-height:48dvh;background:#151a16;object-fit:contain;border-radius:2px;}
  video::cue {font-family:system-ui,sans-serif;color:white;background:rgba(18,23,19,.82);}
  .film-info {display:flex;align-items:flex-end;justify-content:space-between;gap:9px;margin-top:18px;}
  .film-info small,.film-info>span,.list span {font-size:.78rem;color:#605d50;}
  h3 {font:600 clamp(1.6rem,3vw,2.5rem)/1.23 var(--serif);margin:3px 0 0;}
  .cue {margin:7px 0 15px;line-height:1.55;}
  .list {display:grid;align-content:start;max-height:clamp(240px,54dvh,540px);overflow:auto;border-top:1px solid #b4b3a3;}
  .list button {background:transparent;display:grid;gap:2px;padding:11px 12px;text-align:left;border:0;color:#30352d;border-bottom:1px solid #c6c3b2;line-height:1.42;}
  .list button[aria-pressed='true'] {border-left:3px solid #81683f;background:#e5dfcc;padding-left:9px;}
  .list strong {font-family:var(--serif);font-size:1.08rem;}
  .toggles button {min-height:34px;font-size:.86rem;}
  button:focus-visible {outline:2px solid #976d32;outline-offset:-3px;}
  @media(max-width:700px){.layout{grid-template-columns:1fr;gap:14px}.list{max-height:190px;}.shelves{gap:4px;margin-bottom:11px;padding-bottom:11px}.shelves button{padding:3px 7px;font-size:.85rem;min-height:36px}.film-info{margin-top:9px}.cue{margin:3px 0 8px;}}
</style>
