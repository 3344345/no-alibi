<script lang="ts">
  import { onDestroy } from 'svelte'
  import { setSoundscape } from './sound'
  import ReadingView from './ReadingView.svelte'
  import { countyCamera, type ReadingCamera } from './readingView'
  import NightBusDispatch from './NightBusDispatch.svelte'
  import { stamp } from './game'
  import type { Action, NightBusScene, View } from './types'

  export let scene: NightBusScene
  export let quiet = false
  export let visit:()=>void
  export let view: View
  export let busy: boolean
  export let choose: (action: Action) => void
  export let advance: (minutes: number) => void
  export let actionsPage: () => void

  $: choices = view.actions.filter(a => a.kind === 'night_bus')
  $: hearing = view.actions.some(a => a.kind === 'hearing')
  let camera: ReadingCamera
  $: camera = scene.art==='nightbus' ? countyCamera('bus',view.name || '你')
    : {room:'/sets/depot.webp',person:view.name || '你',prop:scene.dispatch?.length?'paper':'ticket'}
  $: setSoundscape(scene.stage === 'playing' && !view.ending && !quiet
    ? { room: scene.art === 'nightbus' ? 'platform' : 'room', music: scene.art === 'nightbus' ? 'vigil' : 'question' }
    : undefined)
  onDestroy(() => setSoundscape())
  $: waiting = scene.stage === 'waiting'
</script>

<section class="night-bus" aria-label="夜班车不进站">
  <header class:small={waiting || scene.stage === 'invitation'}>
    <div class="station-view"><ReadingView {camera}/></div>
    <div class="caption">
      <span>{scene.stage === 'invitation' ? '澄川县 · 七路夜班' : scene.act}</span>
      <h2>{scene.title}</h2>
      {#if scene.place && scene.stage !== 'invitation'}<span>{scene.place}</span>{/if}
    </div>
  </header>
  <div class="story">
    <button class="station-link" on:click={visit}>去七路站台看现场 ↗</button>
    {#if scene.reply}<p class="response">{scene.reply}</p>{/if}
    {#each scene.body.split('\n').filter(Boolean) as paragraph}<p>{paragraph}</p>{/each}
    {#if waiting && scene.due !== null}
      <p class="appointment">约在{stamp(scene.due)}。{!view.ending ? '赴约时，县里的其他日程也会往前走。' : ''}</p>
    {/if}
    {#if view.ending && scene.stage !== 'ending'}
      <p class="appointment">这份生涯已结档，七路行记留在这里。</p>
    {:else if hearing && scene.stage !== 'ending'}
      <button class="choice" disabled={busy} on:click={actionsPage}>先处理已经到场的听证</button>
    {:else if waiting && scene.due !== null}
      <button class="choice" disabled={busy} on:click={() => advance(Math.max(1, (scene.due ?? view.minute) - view.minute))}>赴约 · {stamp(scene.due)}</button>
    {:else if choices.length && scene.dispatch?.length}
      {#key scene.title}<NightBusDispatch plans={scene.dispatch} {choices} {busy} {choose} />{/key}
    {:else if choices.length}
      <div class="choices">{#each choices as choice}
        <button class="choice" disabled={busy} on:click={() => choose(choice)}>{choice.label}<span aria-hidden="true">→</span></button>
      {/each}</div>
    {:else if view.busy && scene.stage !== 'ending'}
      <p class="appointment">你手上的「{view.busy.title}」结束后，就可以接着办七路的事。</p>
    {:else if scene.stage === 'ending'}
      <small>本篇完 · 已收入生涯档案</small>
    {/if}
  </div>
</section>

<style>
  .station-link{background:transparent;border:0;border-bottom:1px solid;color:#715c34;padding:.3rem 0;cursor:pointer}
  .night-bus { background: var(--paper); border: 1px solid var(--line); border-radius: 4px; overflow: hidden; }
  header { position: relative; min-height: clamp(9rem, 15vw, 12rem); isolation: isolate; display: flex; align-items: flex-end; background: #26332f; }
  header.small { min-height: 7.8rem; }
  .station-view, header::after { position: absolute; inset: 0; width: 100%; height: 100%; }
  .station-view { z-index:-2; }
  header::after { content: ''; z-index: -1; background: linear-gradient(90deg, rgb(10 21 18 / 86%), rgb(10 21 18 / 8%)), linear-gradient(0deg, rgb(10 21 18 / 43%), transparent); }
  .caption { color: #fff7df; padding: 1.1rem 1.3rem; max-width: 90%; }
  .caption span, small, .appointment { font-size: .82rem; }
  h2 { font: 600 clamp(1.35rem, 2.6vw, 2rem)/1.3 var(--serif); color: inherit; margin: .28em 0 .13em; }
  .story { padding: .45rem clamp(.85rem, 2vw, 1.35rem) 1.1rem; }
  p { margin: .72em 0; font: 1.04rem/1.83 var(--serif); }
  .response { color: var(--muted); border-left: 2px solid #b18e56; padding-left: .8em; font-size: .93rem; }
  .appointment, small { font-family: inherit; color: var(--muted); }
  .choices { display: grid; gap: .4rem; }
  .choice { display: flex; gap: .6em; justify-content: space-between; align-items: center; width: 100%; min-height: 2.5rem; font-family: inherit; font-weight: 550; font-size: .94rem; line-height: 1.5; padding: .6em .8em; color: var(--ink); text-align: left; background: transparent; border: 1px solid #b4a78f; border-radius: 2px; cursor: pointer; }
  .choice:hover:not(:disabled), .choice:focus-visible { background: var(--soft); border-color: #806a46; }
  .choice:disabled { opacity: .55; }
</style>
