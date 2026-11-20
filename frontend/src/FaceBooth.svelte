<script lang="ts">
  import { onDestroy } from 'svelte'

  export let choices: {id: string; label: string}[]
  export let disabled = false
  export let volume = 0
  export let onChoose: (id: string) => void

  let rods = 24
  let bridalRod = 50
  let tried = ''
  let take = 0
  let sound: HTMLAudioElement | null = null
  const poses = [
    { id: 'double', title: '两背相靠', motion: '桂喜把两张脸送得更近，四只手一下长成怪鸟的翅膀。', beat: '一边发出很体面的雁叫，另一边却破了音。桂喜赶紧拿袖口堵住嘴，怕外头听见他在笑。' },
    { id: 'pull', title: '两头争轿', motion: '两只手一左一右够着轿杠，抬轿的人松开手就要往后倒。', beat: '桂喜替两个娘轮流讨一只鞋。席上传来瓷勺碰碗的脆响，门外有人跟着学了一声漏风的笑。' },
    { id: 'walk', title: '新娘退场', motion: '轿子还在原地，细下巴已经挪到窗框外面。', beat: '签子擦过木框，轿子空了。桂喜连打两下催人上场，外面一个孩子轻声问：“咦，人呢？”' },
  ]
  $: pose = bridalRod > 84 ? poses[2] : rods < 42 ? poses[0] : poses[1]
  $: option = choices.find(c => c.id === 'face_' + pose.id)
  $: spread = 4 + rods * .72
  $: revealed = tried === pose.id
  $: if (sound) {
    sound.volume = Math.min(1, Math.max(0, volume / 100)) * .77
    if (!volume) sound.pause()
  }

  function stop() {
    sound?.pause()
    sound = null
  }

  function rehearse(setup = pose.id) {
    if (disabled) return
    stop()
    tried = setup
    take += 1
    if (volume > 0) {
      sound = new Audio('/chronicle/sound/booth_' + setup + '.mp3')
      sound.volume = Math.min(1, volume / 100) * .77
      void sound.play().catch(() => {})
    }
  }

  function setPose(id: string) {
    rods = id === 'double' ? 22 : 74
    bridalRod = id === 'walk' ? 99 : 50
    rehearse(id)
  }
  function moveRod() {
    stop()
    tried = ''
  }
  onDestroy(stop)
</script>

<section class="booth" aria-label="喜棚掌签台">
  <header><h2>把影人送到灯前</h2><span>桂喜掌锣，你掌签</span></header>
  <svg class="screen" viewBox="0 0 440 208" role="img" aria-label={'戏窗上的姿势：' + pose.title}>
    <defs>
      <radialGradient id="booth-silk" cx=".50" cy=".56" r=".72">
        <stop stop-color="#ffe9a3"/><stop offset=".47" stop-color="#eec578"/><stop offset=".91" stop-color="#ab7245"/><stop offset="1" stop-color="#70513e"/>
      </radialGradient>
      <pattern id="booth-weave" width="4" height="3" patternUnits="userSpaceOnUse"><path d="M0 0H4M0 0V3" stroke="#483117" stroke-width=".4" opacity=".35"/></pattern>
      <clipPath id="booth-bounds"><rect x="12" y="10" width="416" height="180" rx="2"/></clipPath>
      <g id="booth-woman">
        <path d="M-20 -49 Q-21 -61 -14 -68 Q-16 -77 -8 -77 Q-3 -76 -2 -71 Q6 -75 13 -67 L17 -60 L23 -57 L16 -54 L18 -51 L14 -48 L7 -47 L6 -38 L-6 -34Z" fill="currentColor"/>
        <path d="M-6 -66q8 -4 14 1M-2 -63l4 -2M6 -58l3 -1" fill="none" stroke="#e3b971" stroke-width="1.7"/>
        <path d="M-14 -46Q-27 -35 -22 -17L-29 14Q-13 24 14 17L11 -15Q16 -29 6 -40Z" fill="currentColor"/>
        <path d="M-16 -34l4 51M-8 -37l6 54M6 -30l-8 5" fill="none" stroke="#c98f52" stroke-width="1.3"/>
        <path d="M-11 16l-9 19 -10 2q0 4 15 3l16 -21M5 17l9 16 9 1 4 4 -19 1 -16 -19" fill="currentColor"/>
        <g transform={pose.id === 'double' ? 'rotate(-34 0 -30)' : undefined}><path d="M1 -31l16 13 18 -7 4 4 -22 13 -24 -12" fill="currentColor"/>
        <circle cx="15" cy="-12" r="1.6" fill="#e8bd73"/></g>
        <path d="M-5 12L-19 83 M34 -21L45 82" stroke="#69502e" stroke-width="1.8"/>
      </g>
    </defs>
    <rect width="440" height="208" fill="#483123"/><rect x="12" y="10" width="416" height="180" rx="2" fill="url(#booth-silk)"/>
    <g clip-path="url(#booth-bounds)">
      <path d="M8 8Q109 37 206 12Q299 32 433 8L433 1H8Z" fill="#502f28" opacity=".65"/>
      <g opacity=".7" stroke="#503421" fill="none"><path d="M137 133h163M161 163h110M169 132v28m94 -28v28" stroke-width="4"/><path d="M168 130l17 -21h61l18 21z" fill="#955539"/></g>
      {#key take}<g class:performing={take > 0 && revealed} class:empty={pose.id === 'walk'}>
      <g transform={'translate(' + (220-spread) + ' 124) scale(' + (pose.id==='double' ? '-1 1' : '1 1') + ')'} style="color:#382a23"><use class="performer first" href="#booth-woman"/></g>
      <g transform={'translate(' + (220+spread) + ' 126) scale(' + (pose.id==='double' ? '1 1' : '-1 1') + ')'} style="color:#743b2a"><use class="performer second" href="#booth-woman"/></g>
      <g transform={'translate(' + (220 + (bridalRod-50)*4.8) + ' 142)'}>
        <path d="M-10 -27q-3 -12 6 -16q10 -6 16 4l-3 7 5 3 -6 3 -3 5 8 21 -30 1z" fill="#884124"/>
        <path d="M-10 -39q0 -6 8 -8l8 4 -1 6z" fill="#a55132"/><path d="M-3 0l4 68" stroke="#997544" stroke-width="2"/>
      </g>
      </g>{/key}
      <rect width="440" height="190" fill="url(#booth-weave)"/>
    </g>
    <path d="M0 194h440" stroke="#ba8953" stroke-width="2"/>
  </svg>
  <div class="work">
    <label><span>两位娘的竹签</span><input type="range" min="0" max="100" bind:value={rods} on:input={moveRod} {disabled} aria-valuetext={rods < 42 ? '并拢，背靠背' : '拉开，一左一右'}/><small>并签　／　分开</small></label>
    <label><span>新娘的竹签</span><input type="range" min="50" max="100" bind:value={bridalRod} on:input={moveRod} {disabled} aria-valuetext={bridalRod > 84 ? '出了戏窗' : '在灯下'}/><small>台心　／　幕外</small></label>
    <p class="action" aria-live="polite">{pose.motion}</p>
    <div class="patterns" role="group" aria-label="照桂喜教的姿势试演">
      {#each poses as p}<button class:active={pose.id === p.id} aria-pressed={pose.id===p.id} {disabled} on:click={() => setPose(p.id)}>{p.title}</button>{/each}
    </div>
    <button class="try" {disabled} on:click={() => rehearse()}>试走这段锣点</button>
    <p class="aside" aria-live="polite">{revealed ? pose.beat : '桂喜把锣扣在袖口里。先试一遍给他看，席上的人还看不见。'}</p>
    {#if option}<button class="commit" {disabled} on:click={() => onChoose(option!.id)}>{option.label}<span aria-hidden="true"> →</span></button>{/if}
  </div>
</section>

<style>
  .booth{margin:1.45rem 0;background:#372c25;color:#f4e5ce;border:1px solid #6b523d;border-radius:4px;overflow:hidden}
  header,.work{padding:.85rem clamp(.75rem,2vw,1.35rem)}header{display:flex;align-items:center;justify-content:space-between;gap:.5rem;flex-wrap:wrap}
  h2{font:600 1.35rem var(--serif);color:#fff2d8;margin:0}header span,label small{font-size:.78rem;color:#e9caa4}.screen{width:100%;display:block}
  label{display:grid;grid-template-columns:minmax(6em,auto) minmax(36px,1fr) auto;align-items:center;gap:.6rem;margin:.25rem 0 .65rem;font-size:.92rem}
  input{width:100%;min-width:0;accent-color:#e4ba7c}
  .action,.aside{font-size:.96em;line-height:1.65;margin:.65rem 0}.aside{border-left:2px solid #af8760;padding-left:.7rem}
  .patterns{display:flex;gap:.35rem;flex-wrap:wrap}.booth button{font:inherit;font-size:.9rem;cursor:pointer;border:1px solid #a98b67;background:#493b30;color:#f7ead8;padding:.47rem .7rem;border-radius:3px}
  .booth .active{background:#67503c;border-color:#ecd19d}.booth .try{margin-top:.5rem}.booth .commit{width:100%;text-align:left;background:#ebce98;color:#32271f;font-weight:bold;line-height:1.6}
  button:disabled,input:disabled{opacity:.55;cursor:default}.booth :focus-visible{outline:2px solid #fff0b5;outline-offset:2px}
  @keyframes play-rod {0%,100%{transform:rotate(0)}18%{transform:rotate(5deg) translateY(-2px)}42%{transform:rotate(-4deg) translateY(-3px)}68%{transform:rotate(2deg)}}
  @media(prefers-reduced-motion:no-preference){
    .performing .performer{transform-box:fill-box;transform-origin:50% 100%;animation:play-rod 1.5s ease-in-out}
    .performing .second{animation-delay:.16s}.performing.empty .performer{animation-duration:2s}
  }
  @media(max-width:550px){label{grid-template-columns:6em 1fr}label small{display:none}}
</style>
