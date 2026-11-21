<script lang="ts">
  import { onMount, tick } from 'svelte'
  import { sceneBeats, type Shot } from './sceneReel'
  import { enableSound, playScore, stopScore } from './sound'
  import ReadingView from './ReadingView.svelte'
  import type { ReadingCamera } from './readingView'
  export let onRead: () => void
  export let camera: ReadingCamera
  export let shot: Shot | undefined
  export let date: string
  export let place: string
  export let role: string
  export let body: string
  export let previous: string
  export let revision: number
  export let gameId: string
  export let volume: number
  export let toggleAudio: () => void
  export let decide: () => void
  let index = 0, looking = false
  $: beats = sceneBeats(body,previous)
  $: beat = beats[index]
  const pageKey = 'jzs.reel.position.'
  onMount(() => {
    try {
      const saved = JSON.parse(sessionStorage.getItem(pageKey + gameId) ?? 'null')
      if (saved?.revision === revision && Number.isInteger(saved.index) && saved.index >= 0 && saved.index < beats.length) index = saved.index
    } catch { /* A private browser can play every scene without session storage. */ }
  })
  function seek(i: number) {
    if (i < 0 || i >= beats.length) return
    if (looking) stopScore()
    onRead()
    looking = false
    index = i
    try { sessionStorage.setItem(pageKey + gameId, JSON.stringify({revision,index})) } catch {}
  }
  function inspect() {
    looking = !looking
    if (looking && shot?.prop) { enableSound(); void playScore(shot.prop.cue) }
    else stopScore()
  }
  function replayProp() {
    if (!shot?.prop) return
    if (!volume) toggleAudio()
    enableSound()
    void playScore(shot.prop.cue)
  }
  function key(e: KeyboardEvent) {
    if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      e.preventDefault()
      seek(index + (e.key === 'ArrowRight' ? 1 : -1))
    }
  }
  async function finish() {
    if (looking) { stopScore(); looking = false }
    await tick()
    decide()
  }
</script>

<section class="reel" class:illustrated={camera.baked && shot?.firstPerson} aria-label="镜头阅读">
  <div class="image"><ReadingView {camera} close={looking}/></div>
  <div class="frame">
    <div class="slate"><span>{date}</span><i></i>{place}</div>
    {#if shot?.prop}<button on:keydown={key} class="listen" aria-pressed={looking} on:click={inspect}>
      <svg aria-hidden="true" viewBox="0 0 24 20"><path d="M2 8v4m4-7v10m4-13v16m4-12v8m4-11v14m4-10v6"/></svg>{shot.prop.name}
    </button>{/if}
    <div class="script">
      <div class="credit">{looking ? shot?.prop?.name : beat?.kind === 'consequence' ? '刚才的决定' : role}</div>
      <p aria-live="polite" aria-atomic="true">{looking ? shot?.prop?.detail : beat?.text}</p>
      {#if looking}<button class="replay" on:keydown={key} on:click={replayProp}>{volume ? '再听一次' : '开声重听'}</button>{/if}
      <nav aria-label="镜头控制">
        <button on:keydown={key} class="back" disabled={!index} on:click={() => seek(index-1)} aria-label="上一段">←</button>
        <span class="counter">{index+1} / {beats.length}</span>
        {#if index < beats.length-1}
          <button on:keydown={key} class="advance" on:click={() => seek(index+1)}>下一段 <b aria-hidden="true">→</b></button>
          <button on:keydown={key} class="skip" on:click={finish}>直接作决定</button>
        {:else}<button on:keydown={key} class="advance" on:click={finish}>轮到我了 <b aria-hidden="true">→</b></button>{/if}
      </nav>
    </div>
  </div>
</section>

<style>
  .reel{position:relative;isolation:isolate;color:#f5eee1;background:#141916;overflow:hidden;border:1px solid #514a3d}
  .image,.image:after{position:absolute;inset:0;z-index:-2}
  .image:after{content:'';z-index:0;background:linear-gradient(0deg,#0a0e0fed 0%,#0a0e10b5 19%,transparent 62%),linear-gradient(90deg,#10141286,transparent 62%)}
  .frame{min-height:clamp(350px,53vh,620px);padding:clamp(17px,3.1vw,48px);display:flex;flex-direction:column;position:relative}
  .slate{display:flex;align-items:center;gap:.65em;font:600 clamp(.9rem,1.3vw,1.2rem)/1.4 var(--sans);text-shadow:0 1px 6px #121713}.slate span{font-family:var(--serif);font-variant-numeric:tabular-nums}.slate i{display:block;height:1px;width:1.4em;background:#dfbf83}
  .listen{position:absolute;right:clamp(17px,3vw,48px);top:clamp(14px,2.6vw,40px);display:inline-flex;align-items:center;gap:.5em;background:#17201ce3;color:#f4e9d1;padding:.45rem .7rem;border:1px solid #b9a88a;border-radius:2px;font-size:.83rem}.listen[aria-pressed=true]{background:#494034}.listen svg{width:16px;height:14px;fill:none;stroke:#eac888;stroke-width:1.7}
  .script{margin-top:auto;padding-top:6.5rem;max-width:49em;text-shadow:0 1px 9px #101010}.credit{font-size:.83rem;color:#f3d59c;letter-spacing:.12em}.script p{margin:.4em 0 .8em;font:500 clamp(1.04rem,1.7vw,1.52rem)/1.65 var(--serif);color:#fff8ea}
  .replay{background:#171d19de;color:#f1dfbc;border:1px solid #b6a384;padding:.3rem .65rem;margin-bottom:.6rem;font-size:.85rem}
  nav{display:flex;align-items:center;flex-wrap:wrap;gap:.7rem}.counter{font: .82rem/1 var(--mono);color:#e7dece}.back,.advance,.skip{min-height:38px;text-shadow:none}.back,.skip{color:#f4e8d3;background:transparent;border:0}.back{border:1px solid #9a9484;width:38px}.advance{color:#2b2b23;background:#e9d4aa;border:1px solid #e9d4aa;padding:.38rem .85rem;font-weight:600}.advance b{margin-left:.6em}.skip{font-size:.84rem;text-decoration:underline;text-underline-offset:4px}.reel button:focus-visible{outline:2px solid #fff2d7;outline-offset:3px}
  @media(max-width:600px){.frame{min-height:360px}.slate{max-width:60%;flex-wrap:wrap}.script{padding-top:6.3rem}.image:after{background:linear-gradient(0deg,#101411fa 6%,#101411c7 38%,transparent 80%)}nav{gap:.45rem}}
  .illustrated .image{position:relative;inset:auto;z-index:0;aspect-ratio:16 / 9;}
  .illustrated .image::after{display:none;}
  .illustrated .frame{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:.75rem;min-height:0;padding:clamp(.9rem,1.8vw,1.5rem);}
  .illustrated .slate{align-self:center;flex-wrap:wrap;max-width:none;}
  .illustrated .listen{position:static;grid-column:2;justify-self:end;}
  .illustrated .script{grid-column:1 / -1;margin:0;padding:0;}
</style>
