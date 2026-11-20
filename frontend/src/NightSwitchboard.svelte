<script lang="ts">
  import { onDestroy } from 'svelte'
  import { enableSound } from './sound'

  export let choices: { id: string; label: string }[]
  export let disabled = false
  export let volume = 0
  export let onChoose: (id: string) => void

  const lines = [
    { id: 'son', source: '公用电话', name: '阿年', bed: '硬币滚了一圈，落进铁盒。',
      voice: '我闺女说，奶奶要是来，就给她留那朵最大的奶油花。您说，我该答她来，还是不来？',
      ask: '“你想让谁听见？”', reply: '能让我妈听见最好。要是播，别念我闺女的学校啊。……您能不能别叫我“寻亲者”？张口就不像我了。' },
    { id: 'baker', source: '街口蛋糕房', name: '罗师傅', bed: '一把抹刀在铁烤盘上磕了两下。',
      voice: '蛋糕是我做的。孩子说要写俩字儿，爹只付了一个字的钱。你找个纸头，记我这儿。一会儿劳驾给我回一个。',
      ask: '“为什么非得今晚？”', reply: '明早六点人家就来拿。字我能白送，我不能替她想。她打进门就没说过那俩字，拿指头在我手心里头写。痒得我光顾着笑。' },
    { id: 'conductor', source: '车场值班房', name: '冯巧', bed: '一只铜车铃先闷后亮，隔了一拍又响一下。',
      voice: '上礼拜节目征报站声，还收吗？我练了一冬天，明儿头一回单独出车。我想给我爸留一句，他没坐过我的车。',
      ask: '“就在这儿试一句？”', reply: '“前方到站……” 等会儿啊，我一捏着电话就像在跟领导汇报。你们收工时给我摇回来，别的师傅都走了，我就敢拿我自己的腔调说。' },
  ] as const
  type Caller = typeof lines[number]['id']
  let connected: Caller | undefined
  let heard: Caller[] = []
  let replies: Caller[] = []
  let path: 'public' | 'private' | undefined
  let callback: Exclude<Caller, 'son'> | undefined
  let audio: HTMLAudioElement | undefined
  $: caller = lines.find(line => line.id === connected)
  $: chosenGuest = lines.find(line => line.id === callback)
  $: decision = choices.find(option => option.id === 'patch_' + path + '_' + callback)
  $: if (audio) {
    audio.volume = Math.max(0, Math.min(1, volume / 100)) * 0.72
    if (!volume) audio.pause()
  }

  function stopClip() {
    audio?.pause()
    audio = undefined
  }
  function pick(id: Caller) {
    if (disabled) return
    connected = id
    if (!heard.includes(id)) heard = [...heard, id]
    stopClip()
    if (!volume || document.hidden) return
    enableSound()
    audio = new Audio('/chronicle/sound/line_' + id + '.mp3')
    audio.volume = Math.max(0, Math.min(1, volume / 100)) * 0.72
    void audio.play().catch(() => {})
  }
  onDestroy(stopClip)
</script>

<svelte:window on:blur={stopClip}/>
<svelte:document on:visibilitychange={() => { if (document.hidden) stopClip() }}/>

<section class="board" aria-label="夜班接线台">
  <header><h2>夜班接线台</h2><span>四月二十五日　23:53</span></header>
  <p class="brief">唐棠把耳机递过来。阿年等你定要不要进直播。另外两路都想收播后跟她说一句，今夜只约得上一位。</p>
  <div class="panel" role="group" aria-label="选择一部来电听筒">
    {#each lines as line, i}
      <button type="button" class:active={connected === line.id} aria-pressed={connected === line.id}
        aria-label={'接听' + line.source + '的' + line.name} {disabled} on:click={() => pick(line.id)}>
        <span class="channel"><i></i> 0{i + 1}</span><strong>{line.source}</strong>
        <small>{connected === line.id ? '听筒接通' : heard.includes(line.id) ? '再听一次' : '举起听筒'}</small>
      </button>
    {/each}
  </div>
  <div class="receiver" aria-live="polite">
    {#if caller}
      <p class="sound">{caller.bed}</p>
      <p><b>{caller.name}</b>　“{caller.voice}”</p>
      {#if replies.includes(caller.id)}
        <p class="reply"><b>唐棠</b>　{caller.ask}<br/><b>{caller.name}</b>　“{caller.reply}”</p>
      {:else}
        <button type="button" class="ask" {disabled} on:click={() => { if (caller) replies = [...replies, caller.id] }}>
          问一句　{caller.ask}
        </button>
      {/if}
      {#if caller.id === 'son'}
        <div class="jacks" role="group" aria-label="给阿年接哪一线">
          <button type="button" class:selected={path === 'public'} aria-pressed={path === 'public'} {disabled}
            on:click={() => path = 'public'}>接进直播间</button>
          <button type="button" class:selected={path === 'private'} aria-pressed={path === 'private'} {disabled}
            on:click={() => path = 'private'}>留在唐棠耳机里</button>
        </div>
      {:else}
        <button type="button" class="slip" aria-pressed={callback === caller.id} {disabled}
          on:click={() => { if (connected && connected !== 'son') callback = callback === connected ? undefined : connected }}>
          {callback === caller.id ? '取回' : '把'}{caller.name}的回拨条{callback === caller.id ? '' : '夹进值班簿'}
        </button>
      {/if}
    {:else}
      <p class="idle">三盏灯都亮着。拿起一部听筒，就能听到主动打进节目的人。</p>
    {/if}
  </div>
  <div class="ticket">
    <div><small>阿年的声音</small><b>{path === 'public' ? '直播间' : path === 'private' ? '只给唐棠听' : '等接线'}</b></div>
    <div><small>收播后回拨</small><b>{chosenGuest?.name ?? '留给谁？'}</b></div>
  </div>
  <p class="cost" aria-live="polite">{callback === 'baker' ? '给蛋糕房回话，冯巧得赶在首班车前出门。' : callback === 'conductor' ? '给车场回话，罗师傅等炉火熄了就得打烊。' : '听过来电再填回拨条。送出前都能改。'}</p>
  <button type="button" class="send" disabled={disabled || !decision} on:click={() => { if (decision) onChoose(decision.id) }}>
    送出接线单 <span aria-hidden="true">→</span>
  </button>
</section>

<style>
  .board{margin:1.6rem 0;padding:clamp(.85rem,3vw,1.45rem);border:1px solid #776b4f;background:#e5dac0;color:#302e27;box-shadow:inset 0 0 0 3px #eee5d2}
  .board header,.channel,.ticket,.send,.jacks{display:flex;align-items:center}
  .board header{justify-content:space-between;flex-wrap:wrap;gap:.4rem}
  .board h2{margin:0;font:650 1.25rem/1.3 Georgia,'Songti SC',serif}
  .board header span,.board small,.sound,.channel,.cost{font-family:system-ui,sans-serif}
  .board header span,.board small,.sound,.channel{font-size:.78rem}
  .board .brief,.board .cost{margin:.65rem 0;font-size:.87rem;line-height:1.65}
  .panel{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:5px;background:#313932;padding:7px;border:1px solid #42483c}
  .panel button{display:grid;justify-items:center;gap:.32rem;min-width:0;padding:.65rem .16rem;color:#f4ead3;background:#455044;border:1px solid #71715b;box-shadow:inset 0 -3px 0 #303a32;font:inherit;cursor:pointer}
  .panel button.active{background:#5a543e;border-color:#edce87}
  .channel{gap:.35rem;color:#ddccab;letter-spacing:.14em}
  .channel i{width:.65rem;height:.65rem;border-radius:50%;background:#ddb57d;box-shadow:0 0 0 2px #343b32}
  .active .channel i{background:#f9df96;box-shadow:0 0 0 2px #413a24,0 0 7px 2px #b79d4d}
  .panel strong{font-size:clamp(.75rem,2.8vw,.97rem);font-weight:600}
  .panel small{color:#e2d5b8;font-size:.7rem}
  .board .receiver{min-height:9rem;background:#f9f3df;padding:.8rem 1rem;border:1px solid #9b9071;border-top:0}
  .receiver p{margin:0 0 .5rem;font-size:.98rem;line-height:1.8}
  .receiver .idle,.receiver .sound{color:#645b49}
  .receiver .sound{font-size:.78rem}
  .ask,.slip,.jacks button{font:inherit;color:#3a4639;border:1px solid #8d876f;background:#f5eedb;padding:.4rem .65rem;cursor:pointer;text-align:left;min-height:2.3rem}
  .ask{display:block;border:0;border-bottom:1px dotted #726e57;background:transparent;padding:0;min-height:2rem}
  .slip,.jacks{margin:.65rem 0 0}.jacks{gap:.4rem;flex-wrap:wrap}
  .slip[aria-pressed=true],.jacks .selected{background:#39483d;color:#fff1ce}
  .reply{border-left:2px solid #b19c72;padding-left:.6rem}
  .ticket{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.8rem;border-bottom:1px dashed #82795f;padding:.65rem 0}
  .ticket div{display:grid;gap:2px}.ticket small{color:#5c5442}
  .board .send{justify-content:space-between;width:100%;min-height:2.65rem;background:#33483e;color:#fff7dd;border:1px solid #324638;padding:.45rem .8rem;font:inherit;cursor:pointer}
  .board button:disabled{opacity:.55;cursor:default}
  .board button:focus-visible{outline:3px solid #96712b;outline-offset:3px}
  @media(max-width:470px){.board{padding:.65rem}.board .receiver{padding:.6rem}.panel{padding:5px;gap:3px}.panel strong{font-size:.77rem}}
</style>
