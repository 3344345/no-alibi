<script lang="ts">
  import { onDestroy, tick } from 'svelte'
  import Dialog from './Dialog.svelte'
  import { stamp } from './game'
  import type { Action, Aftershow, View } from './types'

  export let scene: Aftershow
  export let view: View
  export let busy: boolean
  export let volume: number
  export let open = false
  export let error = ''
  export let choose: (action: Action) => void
  export let advance: (minutes: number) => void
  export let actionsPage: () => void
  export let toggleAudio: () => void
  const poster = '/scenes/county-aftershow.webp'
  const booth = '/scenes/county-reel.webp'
  const frames = [
    {at:0, name:'售票窗', id:'show_wages', img:'pay', line:'冯香朝排队的人偏过头。“他们愿意……愿意先开门。没说工资就这样算了。”'},
    {at:4, name:'门廊下', id:'show_girl', img:'girl', line:'镜头后面的男人问妈妈几点收工。短辫小姑娘握着半个馒头：“爸，咱能等她一块儿回去吃饭么？”'},
    {at:9, name:'六排四座', id:'show_empty', img:'chair', line:'画面里只剩一排翻椅。老柳蹲下身，用手绢擦了擦椅底，起身出了镜。再没有人说话。'},
  ]
  let second = 0, running = false, timer: ReturnType<typeof setInterval> | undefined
  let audio: HTMLAudioElement | undefined, soundKey = '', audioFailed = false
  let marker = '', heading: HTMLHeadingElement
  $: current = frames[second < 4 ? 0 : second < 9 ? 1 : 2]
  $: actions = view.actions.filter(a => a.kind === 'aftershow')
  $: selected = actions.find(a => a.args?.choice === current.id)
  $: isWaiting = scene.due !== null
  $: if ((open ? scene.node + '/' + scene.stage : '') !== marker) {
    marker = open ? scene.node + '/' + scene.stage : ''
    stopFilm()
    second = 0
    if (open) void tick().then(() => heading?.focus())
  }
  $: syncSound(open && volume > 0 && !isWaiting ? scene.sound : '', volume)
  function stopFilm() { clearInterval(timer); timer = undefined; running = false }
  function scrub(to: number) { stopFilm(); second = to }
  function playFilm() {
    if (running) { stopFilm(); return }
    if (second >= 40) second = 0
    running = true
    let start = performance.now() - second * 1000
    timer = setInterval(() => { second = Math.min(40, Math.floor((performance.now() - start)/1000)); if (second === 40) stopFilm() }, 180)
  }
  function stopAudio() { audio?.pause(); audio = undefined; soundKey = ''; audioFailed = false }
  function syncSound(key: string, level: number) {
    if (key === soundKey) { if (audio) audio.volume = level / 100 * .78; return }
    stopAudio()
    if (!key || document.hidden) return
    soundKey = key
    const track = new Audio('/chronicle/sound/county_cinema_' + key + '.mp3')
    audio = track
    track.volume = level / 100 * .78
    void track.play().catch(() => { if (audio === track) audioFailed = true })
  }
  function close() { stopFilm(); stopAudio(); open = false }
  function visibility() { if (document.hidden) {stopFilm(); stopAudio()} }
  onDestroy(() => {stopFilm(); stopAudio(); open = false})
</script>

<svelte:document on:visibilitychange={visibility}/>
<svelte:window on:blur={() => {stopFilm(); stopAudio()}}/>
<button class="playbill" on:click={() => open = true}>
  <img alt="" src={poster}/>
  <span><small>澄川 · 回声影院</small><strong>散场以后</strong><span>{scene.stage === 'invitation' ? '门缝里塞进来一张三十年前的电影票。' : scene.title}</span></span>
  <b aria-hidden="true">↗</b>
</button>

{#if open}
  <Dialog title="散场以后" onclose={close}>
    <section class="cinema" aria-label="回声影院">
      <div class="screen" class:editing={scene.node === 'spool'}>
        {#if scene.node === 'spool'}
          <img src={'/scenes/county-film-' + current.img + '.webp'} alt={current.name + '的旧录像情境插画'}/>
        {:else}
          <img src={['booth','offer','paid','family','kept'].includes(scene.node) ? booth : poster} alt="回声影院情境插画"/>
        {/if}
        <div class="caption"><small>{scene.act}</small><h3 tabindex="-1" bind:this={heading}>{scene.title}</h3></div>
      </div>
      <div class="inset">
        <div class="transport"><button type="button" aria-pressed={volume > 0} on:click={toggleAudio}>{volume > 0 ? '场内声音开' : '场内声音关'}</button>
          {#if volume > 0 && !isWaiting}<button on:click={() => { stopAudio(); syncSound(scene.sound,volume) }}>{audioFailed ? '重新播放声音' : '重听场内声音'}</button>{/if}
        </div>
        {#if error}<p role="alert">{error} <button on:click={close}>返回办公桌处理</button></p>{/if}
        {#if scene.reply}<p class="reply">{scene.reply}</p>{/if}
        {#each scene.body.split('\n').filter(Boolean) as paragraph}<p>{paragraph}</p>{/each}
        {#if view.ending && scene.stage !== 'ending'}
          <p>这份生涯已经结档。</p>
        {:else if view.actions.some(a => a.kind === 'hearing') && scene.stage !== 'ending'}
          <button class="action" on:click={() => { close(); actionsPage() }}>先去处理已经到场的听证</button>
        {:else if isWaiting && scene.due !== null}
          <p>赴约时，县里的其他日程也会往前走。</p>
          <button class="action" disabled={busy} on:click={() => advance(Math.max(1, (scene.due ?? view.minute) - view.minute))}>赴约 · {stamp(scene.due)}</button>
        {:else if scene.node === 'spool' && actions.length}
          <div class="editbench" aria-label="原带放映台" role="group">
            <div class="deck"><span>现场原带</span><output>00:{String(second).padStart(2,'0')} / 00:40</output></div>
            <label>拖动磁带，选择公映片段<input type="range" min="0" max="40" step="1" value={second} on:input={e => scrub(+e.currentTarget.value)} aria-valuetext={second+'秒，'+current.name}/></label>
            <div class="stops">
              <button aria-pressed={running} on:click={playFilm}>{running ? '暂停回放' : '顺放原带'}</button>
              {#each frames as frame}<button aria-pressed={current.id === frame.id} on:click={() => scrub(frame.at)}>{frame.name}</button>{/each}
            </div>
            <p class="transcript" aria-live="polite">{current.line}</p>
            {#if selected}<button class="send" disabled={busy} on:click={() => {stopFilm(); if(selected) choose(selected)}}>{selected.label} →</button>{/if}
          </div>
        {:else if actions.length}
          <div class="actions">{#each actions as a}<button class="action" disabled={busy} on:click={() => choose(a)}>{a.label}<span aria-hidden="true">→</span></button>{/each}</div>
        {:else if scene.stage === 'ending'}
          <button class="action" on:click={close}>收好这张票，回办公桌</button>
        {:else if view.busy}<p>等「{view.busy.title}」办完，可以回影院接着看。</p>{/if}
      </div>
    </section>
  </Dialog>
{/if}

<style>
  .playbill{position:relative;isolation:isolate;overflow:hidden;color:#f9ebcf;background:#1a2420;text-align:left;min-height:8.4rem;width:100%;border:1px solid #615d4e;display:flex;align-items:flex-end;justify-content:space-between;padding:1rem 1.2rem;cursor:pointer}
  .playbill>img,.playbill::after,.screen>img,.screen::after{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:-2;object-position:50% 47%}.playbill::after,.screen::after{content:'';background:linear-gradient(90deg,#101810ee,#121c1961 70%,#18181525);z-index:-1}
  .playbill>span{display:grid;gap:.18rem}.playbill strong,.caption h3{font:600 1.8rem/1.24 var(--serif);color:#fff2d6}.playbill small,.caption small{color:#e2c59a;font-size:.8rem}.playbill b{font-size:1.4rem}.playbill:focus-visible,.cinema button:focus-visible,.cinema input:focus-visible{outline:3px solid #ba8644;outline-offset:2px}
  :global(dialog:has(.cinema)){width:57rem;max-width:calc(100% - 18px);max-height:92dvh;padding:0;background:#f4edde}
  :global(dialog:has(.cinema) .dialog-head){padding:.5rem 1rem;border-bottom:1px solid #514a3d;background:#202a24;color:#fcf5e2}
  :global(dialog:has(.cinema) .dialog-head h2){margin:0;color:inherit;font-size:1.05rem}:global(dialog:has(.cinema) .dialog-head button){color:inherit}
  .screen{isolation:isolate;position:relative;background:#262b24;height:clamp(9rem,32vh,21rem);display:flex;align-items:end;overflow:hidden}.screen::after{background:linear-gradient(0deg,#17211beb,transparent 64%)}.screen.editing img{object-position:50% 44%}
  .caption{padding:1rem clamp(1.1rem,4vw,2.7rem)}.caption h3{margin:.25em 0 0;font-size:clamp(1.4rem,3.7vw,2.3rem)}.inset{padding:.6rem clamp(.95rem,4vw,2.7rem) 1.6rem}.inset p{font:1.03rem/1.82 var(--serif);margin:.85em 0;white-space:normal}
  .inset p.reply{font-size:.9rem;color:#6b5d49;border-left:2px solid #a88d5e;padding-left:.8rem}.transport{display:flex;gap:.8rem}.transport button,.stops button{padding:.36rem .48rem;font:inherit;font-size:.82rem;border:1px solid #897d64;color:inherit;background:transparent;cursor:pointer}
  .actions{display:grid;gap:.45rem}.action,.send{width:100%;text-align:left;display:flex;justify-content:space-between;gap:.55rem;font:inherit;padding:.65rem .8rem;line-height:1.5;border:1px solid #aaa18b;background:#fffaf0;color:#342e24;cursor:pointer}.action:disabled,.send:disabled{opacity:.55}
  .editbench{background:#253029;border:1px solid #425245;color:#f1e4c7;padding:.95rem}.deck,.stops,.editbench label{display:flex;gap:.65rem;align-items:center;flex-wrap:wrap}.deck{justify-content:space-between;color:#e7c792}.deck output{font:14px monospace}.editbench label{font-size:.86rem;margin:.75rem 0}.editbench input{flex:1;min-width:6rem;accent-color:#ebcb91}.stops button{color:#f1e7ca}.stops button[aria-pressed=true]{background:#e4cf9f;color:#253029}.send{background:#e4cf9f}.inset .transcript{color:#f8ebd2}
</style>
