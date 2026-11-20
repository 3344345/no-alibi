<script lang="ts">
  import { onDestroy, tick } from 'svelte'

  const films = [
    {
      id: 'palace', year: '1901', place: '北京', title: '从午门望进去',
      format: '黑白默片 · 馆藏全片', runtime: '0:53',
      note: '摄影机架在高处，慢慢扫过宫墙。留意柱廊底下的小黑点，人一旦收进这幅全景，就只剩这么大。',
      source: '美国国会图书馆 · 影片目录', url: 'https://www.loc.gov/item/mp76000090/',
      credit: 'C. Fred Ackerman 于1901年1月31日拍摄。American Mutoscope & Biograph 1903年发行。The Forbidden City, Pekin，登记号 H34805。馆方推测机位在午门之上。',
      rights: '美国国会图书馆电影、广播和录音部藏。原片1903年已在美国发表，现属公版。保留馆藏片头、片尾和胶片痕迹。',
      stops: [[16, '宫墙入画'], [21, '门前的台阶'], [31, '屋脊与远处的树']] as const,
    },
    {
      id: 'arrival', year: '1946', place: '上海', title: '汽车开进人群',
      format: '黑白有声新闻片 · 上海段', runtime: '1:07',
      note: '先在地面看迎接的人，接着到高处俯看汽车。留意新闻摄影机站在哪里，以及镜头还能拍到哪些人的脸。',
      source: '美国国家档案馆 · 影片目录', url: 'https://catalog.archives.gov/id/39104',
      credit: 'United News 第197卷第一则，馆藏号 208-UN-197，NAID 39104。馆方编目年为1946。英文解说和配乐来自当时面向观众发行的新闻片。',
      rights: '美国国家档案馆列明本片使用无限制。采用 Federal Flix 保留的馆藏 DVD 转录，拷贝页面标明 CC0。保留上海报道的片题和原声。',
      stops: [[7, '舷梯前'], [22, '车顶周围'], [48, '主席台上与台下']] as const,
    },
    {
      id: 'factory', year: '1984', place: '上海', title: '合资厂的展示室',
      format: '彩色同期声 · 现场节选', runtime: '2:52',
      note: '1984年4月30日，里根访问上海福克斯波罗公司。仪表柜前的讲话告一段落，拍摄的人跟着大家走下讲台，来到展示区。',
      source: '里根总统图书馆 · 原始录像目录', url: 'https://www.reaganlibrary.gov/archives/video/trip-china-president-reagans-remarks-shanghai-foxboro-company',
      credit: '白宫电视办公室 WHTV 摄制，带号 F87，NAID 75502096。取馆藏 MP4 的 09:20 至 12:12，保留现场同期声。该公司由上海仪表方面与美国福克斯波罗公司合资开办。',
      rights: '里根总统图书馆将 WHTV 馆藏列为公版。本段取自美国国家档案馆的原始数字录像。',
      stops: [[0, '镜头从讲台拉远'], [14, '打开的红盒'], [65, '转向展示区'], [106, '人群让出的位置']] as const,
    },
  ]
  let current = films[0]
  let player: HTMLVideoElement
  let failure = ''
  let pendingJump: number | null = null
  let position = 0
  $: activeStop = current.stops.filter(([start]) => start <= position).at(-1)?.[0]

  function select(film: typeof current) {
    if (current.id === film.id) return
    player?.pause()
    pendingJump = null
    position = 0
    failure = ''
    current = film
  }
  function seek(time: number) {
    if (!player) return
    if (player.readyState === 0) {
      pendingJump = time
      player.load()
    } else {
      player.currentTime = time
      position = time
    }
  }
  async function playFrom(time: number) {
    seek(time)
    try {
      await player.play()
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      failure = '这段影像暂时无法播放，可以换一段再试。'
    }
  }
  function loaded() {
    // System WebKit can ignore the default attribute on a foreign-language caption track.
    const captions = player.textTracks[0]
    if (captions) captions.mode = 'showing'
    if (pendingJump !== null) {
      player.currentTime = pendingJump
      pendingJump = null
    }
  }
  function clock(seconds: number) {
    return Math.floor(seconds / 60) + ':' + String(seconds % 60).padStart(2, '0')
  }
  async function retry() {
    failure = ''
    await tick()
    player?.load()
  }
  onDestroy(() => player?.pause())
</script>

<section class="cinema" aria-label="历史纪录影像">
  <nav aria-label="选择影片">
    {#each films as film}
      <button type="button" class:chosen={film.id === current.id} aria-pressed={film.id === current.id} on:click={() => select(film)}>
        <span>{film.year} · {film.place}</span><strong>{film.title}</strong>
      </button>
    {/each}
  </nav>
  <header>
    <div><small>{current.year} · {current.place}</small><h3>{current.title}</h3></div>
    <span>{current.format} · {current.runtime}</span>
  </header>
  {#key current.id}
    <video controls playsinline preload="metadata" muted bind:this={player}
      aria-label={current.title} poster={'/cinema/' + current.id + '.jpg'}
      src={'/cinema/' + current.id + '.mp4'}
      on:loadedmetadata={loaded} on:timeupdate={() => position = player?.currentTime ?? 0}
      on:error={() => failure = '未能读取这段本地影像，可以重试或切换影片。'}>
      <track kind="captions" srclang="zh" label="中文镜头注释" src={'/cinema/' + current.id + '.vtt'} default />
    </video>
  {/key}
  {#if failure}<p class="error" role="status">{failure} <button on:click={retry}>重新载入</button></p>{/if}
  <p class="note">{current.note}</p>
  <div class="stops" role="group" aria-label="跳到镜头并播放">
    {#each current.stops as [time, label]}
      <button type="button" class:here={activeStop === time} on:click={() => playFrom(time)}>
        <span>{clock(time)}</span> {label}
      </button>
    {/each}
  </div>
  <details><summary>原片与出处</summary>
    <p>{current.credit}</p><p>{current.rights}</p>
    <a href={current.url} target="_blank" rel="noopener noreferrer">{current.source}</a>
  </details>
</section>

<style>
  :global(dialog[aria-label="年代放映室"]) { max-width: min(920px, calc(100% - 24px)); padding: clamp(14px,2.5vw,26px); }
  .cinema { color:#2d302a; }
  nav { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:7px; margin-bottom:18px; }
  nav button { background:transparent; border:1px solid #bbb4a2; padding:9px 12px; text-align:left; border-radius:3px; }
  nav button.chosen { background:#27352f; border-color:#27352f; color:#faf5e9; }
  nav span, small { display:block; font-size:.78rem; letter-spacing:.06em; }
  nav strong { font-size:.98rem; font-weight:600; display:block; margin-top:2px; }
  header { display:flex; justify-content:space-between; align-items:flex-end; gap:14px; margin:0 0 9px; }
  header span { font-size:.78rem; color:#645f52; text-align:right; }
  header h3 { font-size:1.5rem; margin:1px 0 0; }
  video { display:block; width:100%; height:clamp(168px,43vh,440px); object-fit:contain; background:#101310; }
  video::cue { color:white; background:rgba(16,18,15,.82); font-size:18px; }
  .note { font-size:1rem; line-height:1.65; margin:10px 0; }
  .stops { display:flex; flex-wrap:wrap; gap:6px; }
  .stops button,.error button { padding:5px 9px; font-size:.86rem; color:#33382f; background:#f6f3e9; border:1px solid #c3beae; border-radius:3px; }
  .stops .here { border-color:#516955; background:#e2e7d9; }
  .stops span { font-variant-numeric:tabular-nums; color:#645c49; }
  details { margin-top:13px; font-size:.82rem; line-height:1.5; }
  summary { cursor:pointer; }
  details p { margin:5px 0; }
  a { color:#3a594b; }
  @media(max-width:520px) {
    nav { gap:3px; margin-bottom:10px; }
    nav button { padding:6px; }
    nav strong { font-size:.84rem; }
    header { align-items:center; }
    header h3 { font-size:1.2rem; }
    header span { max-width:9em; }
    video::cue { font-size:14px; }
    video { height:auto; max-height:40vh; aspect-ratio:4 / 3; }
  }
</style>
