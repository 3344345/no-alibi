<script lang="ts">
  import { onDestroy } from 'svelte'
  import waves from './reelWaves.json'

  export let choices: { id: string; label: string }[]
  export let disabled = false
  export let volume = 0
  export let onChoose: (id: string) => void

  const channels = [
    { id: 'sum', name: '两路合听', instructions: '唐棠当年用这个位置剪出了广告里的七秒。' },
    { id: 'stage', name: '台口话筒', instructions: '琴离话筒不到一臂，后排的动静要轻得多。' },
    { id: 'door', name: '后门话筒', instructions: '门边听得清每个人怎样起身。琴在礼堂的另一头。' },
  ] as const
  type Channel = typeof channels[number]['id']
  let channel: Channel = 'sum', duration = 7, cursor = 0, playing = false
  let audio: HTMLAudioElement | undefined, frame = 0, pending = false, silentClock = 0, audioFailed = false
  $: waveform = waves[channel]
  $: decision = choices.find(c => c.id === (duration === 12 ? 'cut_full' : 'cut_ad'))
  $: if (audio) audio.volume = Math.min(1, Math.max(0, volume / 100)) * .85
  $: if (playing && audio && !volume) stop()

  function stop() {
    cancelAnimationFrame(frame)
    pending = false
    playing = false
    if (audio) {
      audio.onended = null
      audio.onloadedmetadata = null
      audio.onerror = null
      audio.pause()
      audio = undefined
    }
  }
  function tick() {
    if (!playing) return
    cursor = Math.min(duration, audio ? audio.currentTime : (performance.now() - silentClock) / 1000)
    if (cursor >= duration - .015) { cursor = duration; stop(); return }
    frame = requestAnimationFrame(tick)
  }
  function readSilently(start: number) {
    silentClock = performance.now() - start * 1000
    playing = true
    tick()
  }
  function play() {
    if (disabled) return
    stop()
    audioFailed = false
    if (cursor >= duration - .03) cursor = 0
    const start = cursor
    if (!volume) { readSilently(start); return }
    const current = new Audio('/chronicle/sound/reel_' + channel + '.mp3')
    audio = current
    pending = true
    current.volume = Math.min(1, Math.max(0, volume / 100)) * .85
    current.onloadedmetadata = () => { if (audio === current) current.currentTime = start }
    current.onended = () => { if (audio === current) { cursor = duration; stop() } }
    function fallback() {
      if (audio !== current) return
      stop()
      audioFailed = true
      readSilently(start)
    }
    current.onerror = fallback
    void current.play().then(() => {
      if (audio !== current) return
      pending = false
      playing = true
      tick()
    }, fallback)
  }
  function route(key: Channel) {
    if (channel === key) return
    const resume = playing || pending
    stop()
    channel = key
    if (resume) play()
  }
  function length(value: number) {
    stop()
    duration = value
    cursor = Math.min(cursor, value)
  }
  function seek(value: number) {
    stop()
    cursor = Math.min(duration, Math.max(0, value))
  }
  function soundAt(time: number, source: Channel) {
    if (time < .6) return '引带转过去。磁带底噪很轻。'
    if (time < 2.75) return source === 'door' ? '远处两个琴音，第二个进得有点急。' : '两个琴键先后按下，第二个抢了半拍。'
    if (time < 4.45) return source === 'door' ? '远处又弹了一个低些的音。' : '琴键旁一声木头轻敲，第三个音才落下去。'
    if (time < 7) return source === 'sum' ? '琴音拖着尾巴，一片短促的响声从左往右散开。' :
      source === 'stage' ? '琴弦慢慢松下来，远处几下轻拍。' : '啪，咔哒。啪，咔哒。椅面打在靠背上，每把都要响两下。'
    if (time < 9.9) return source === 'stage' ? '琴已停下。门口有脚步回来。' : '鞋跟从后门绕回，几步越踩越近。'
    if (time < 11.4) return source === 'stage' ? '远处有人把门闩上了。' : '门闩刮过铁槽，落到底。'
    return '门关紧后，磁带还走了一小段。'
  }
  const timecode = (t: number) => '00:' + String(Math.floor(t)).padStart(2,'0') + '.' + Math.floor((t % 1) * 10)
  onDestroy(stop)
</script>

<svelte:window on:blur={stop}/>
<svelte:document on:visibilitychange={() => { if (document.hidden) stop() }}/>

<section class="machine" aria-label="旧礼堂双路剪辑台">
  <header><div><small>旧礼堂现场录音</small><h2>把带子倒回来</h2></div><output>{timecode(cursor)}</output></header>
  <div class="glass">
    <div class="spools" aria-hidden="true">
      {#each [0,1] as num}
        <svg viewBox="0 0 100 100" class="spool" style={'transform:rotate(' + (cursor*(num ? 80 : 60)) + 'deg)'}>
          <circle cx="50" cy="50" r="46" fill="#313331" stroke="#b39f7b" stroke-width="2"/>
          <circle cx="50" cy="50" r={num ? 21+cursor*.7 : 32-cursor*.7} fill="#74503d" stroke="#282725" stroke-width="4"/>
          <g fill="#aaa38f" stroke="#dbcfb7" stroke-width=".6">{#each [0,120,240] as angle}<path transform={'rotate('+angle+' 50 50)'} d="M45 43 37 13Q50 6 62 13L54 43Z"/>{/each}</g>
          <circle cx="50" cy="50" r="8" fill="#d9ccb0"/><circle cx="50" cy="50" r="3" fill="#252a28"/>
        </svg>
      {/each}
    </div>
    <svg class="wave" viewBox="0 0 240 38" preserveAspectRatio="none" aria-hidden="true">
      {#each waveform as sample, i}<path d={'M'+(2*i+1)+' '+(19-sample*17)+'v'+(sample*34)} stroke={i*.1 >= duration ? '#526056' : '#dfbe82'} stroke-width="1.3"/>{/each}
      <path d={'M'+(cursor*20)+' 0v38'} stroke="#fff7dd" stroke-width="1.5"/>
    </svg>
  </div>
  <div class="channels" role="group" aria-label="选择监听话筒">{#each channels as item}<button type="button" {disabled} aria-pressed={channel === item.id} on:click={() => route(item.id)}>{item.name}</button>{/each}</div>
  <p class="instruction">{channels.find(c => c.id === channel)?.instructions}</p>
  <div class="transport">
    <button type="button" {disabled} on:click={() => playing || pending ? stop() : play()}>{playing || pending ? '停带' : '走带'}</button>
    <label>移磁头 <input type="range" min="0" max={duration} step=".1" value={cursor} aria-valuetext={timecode(cursor)} {disabled} on:input={e => seek(Number(e.currentTarget.value))}/></label>
  </div>
  <div class="captions" aria-live="polite" aria-atomic="true"><small>现场声字幕{audioFailed ? ' · 录音未能播放' : !volume ? ' · 静音' : ''}</small><p>{soundAt(cursor, channel)}</p></div>
  <fieldset disabled={disabled}><legend>送到播出间的带长</legend>
    <button type="button" aria-pressed={duration === 7} on:click={() => length(7)}>广告样带 · 7秒</button>
    <button type="button" aria-pressed={duration === 12} on:click={() => length(12)}>留到门关 · 12秒</button>
  </fieldset>
  <p class="price">{duration === 7 ? '七秒播完能兑现一趟厂车。唐棠剪掉的后半截，收音机前的人听不见。' : '多放这五秒，门口的声音会传遍全城，原先约好的掌声广告也就卖不成了。'}</p>
  {#if decision}<button class="send" type="button" {disabled} on:click={() => onChoose(decision!.id)}>{decision.label} <span aria-hidden="true">→</span></button>{/if}
</section>
<style>
  .machine{color:#ece0c5;background:#303937;border:1px solid #746d59;padding:clamp(.85rem,2vw,1.35rem);margin:1.1rem 0 1.4rem;border-radius:5px;box-shadow:inset 0 1px #708078}
  header{display:flex;align-items:center;justify-content:space-between;gap:.6rem}small{font:500 .76rem/1.4 var(--sans,sans-serif);color:#cebe9c}h2{margin:.15rem 0;font:600 1.38rem/1.22 var(--serif,serif);color:#f7edd4}
  output{background:#192420;color:#efd19b;padding:.35rem .55rem;border:1px solid #5e6457;font-family:monospace;font-size:1.05rem}
  .glass{display:grid;grid-template-columns:minmax(100px,32%) 1fr;gap:.7rem;align-items:center;background:#1b2421;padding:.5rem;border:1px solid #686d60;margin-top:.7rem}.spools{display:flex;gap:3%;min-width:0}.spool{width:48%}.wave{width:100%;height:44px}
  .channels{display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.7rem}.machine button{border:1px solid #988e76;background:#454d46;color:#f2e8d4;font:inherit;font-size:.9rem;padding:.48rem .65rem;min-height:36px;border-radius:2px;cursor:pointer}
  .machine button[aria-pressed=true]{background:#d5bd91;color:#2a312a;font-weight:650}.machine button:disabled{cursor:default;opacity:.55}.machine :focus-visible{outline:2px solid #f4dc9e;outline-offset:2px}
  .instruction,.price{font-size:.89rem;line-height:1.65;margin:.35rem 0 .65rem}.transport{display:flex;align-items:center;gap:.8rem}.transport label{font-size:.85rem;display:flex;align-items:center;gap:.45rem;flex:1}.transport input{width:45px;min-width:0;flex:1;accent-color:#d9bc83}
  .captions{margin:.65rem 0;background:#1d2724;border-left:2px solid #b4a179;padding:.4rem .65rem}.captions p{color:#ece6d9;font-size:.96rem;line-height:1.5;margin:.14rem 0}
  fieldset{border:0;padding:0;margin:.5rem 0}.machine legend{font-size:.83rem;color:#d6caae;margin-bottom:.25rem}fieldset button{margin-right:.3rem;margin-bottom:.25rem}.machine .send{width:100%;display:flex;justify-content:space-between;text-align:left;color:#26342e;background:#e9d4aa;border-color:#e5c992;padding:.65rem .8rem}
  @media(prefers-reduced-motion:reduce){.spool{transform:none!important}}
</style>
