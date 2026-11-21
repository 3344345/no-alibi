<script lang="ts">
  import { onMount, onDestroy, tick } from 'svelte'
  import { api, download, message } from './api'
  import { saveFile } from './game'
  import { enableSound, playScore, stopScore, setSoundscape, type Score } from './sound'
  import { picture, pictureCaption } from './chronicleArt'
  import { sceneMix, linesOfSpeech, outcomeCue, sceneSetting } from './chronicleScene'
  import ChapterPath from './ChapterPath.svelte'
  import type { Feature } from './features'
  export let featured: Feature | null = null
  import ExamMixer from './ExamMixer.svelte'
  import CourtyardMoon from './CourtyardMoon.svelte'
  import NightSwitchboard from './NightSwitchboard.svelte'
  import XianTable from './XianTable.svelte'
  import FaceBooth from './FaceBooth.svelte'
  import TapeRoom from './TapeRoom.svelte'
  import ScenePlayback from './ScenePlayback.svelte'
  import ActingStage from './ActingStage.svelte'
  import {historyStage, startTurn, clearPerformance, filmOpen, inTheatre, presenting, playback} from './performance'
  export let reduced=false
  import { directedShot } from './sceneReel'
  import RidgeSurvey from './RidgeSurvey.svelte'
  import Dialog from './Dialog.svelte'
  export let initialCampaign: Campaign
  export let leave: (campaign: Campaign) => void
  export let volume: number
  export let toggleAudio: () => void
  type Chapter = {
    id: string
    year: string
    place: string
    title: string
    role: string
    intro: string
    history: string
    sources: { name: string; url: string }[]
  }
  type Campaign = 'witness' | 'family'
  type Exhibit = { id: string; title: string; detail: string }
  type Choice = { id: string; label: string; cites?: string[] }
  type Entry = {
    chapter_id: string
    scene: string
    choice?: string
    year: string
    place: string
    role: string
    title: string
    label: string
    result: string
    marks: string[]
    tone?: Score
    citations?: Exhibit[]
  }
  type Career = {
    start_chapter: string
    id: string
    name: string
    revision: number
    chapter_id: string
    finished: boolean
    edition?: 'serial_v1'
    opening_choice?: string
    standalone?: boolean
    outcomes?: Pick<Entry, 'chapter_id' | 'label' | 'result' | 'marks'>[]
  }
  type View = {
    campaign: Campaign
    start_chapter: string
    id: string
    name: string
    revision: number
    finished: boolean
    chapter: Chapter
    scene: {
      id: string
      title: string
      body: string
      base_body?: string
      callbacks?: { body: string; origin: number }[]
      choices: Choice[]
      exhibits?: Exhibit[]
    } | null
    journal: Entry[]
    marks: string[]
  }
  let catalogue: { chapters: Chapter[]; careers: Career[] } = { chapters: [], careers: [] }
  let game: View | null = null,
    busy = false,
    error = '',
    info = '',
    name = '',
    topic = ''
  let book: Chapter | null = null,
    handover: Entry | null = null
  $: setting = game?.scene ? sceneSetting(game.chapter.id, game.scene.id, game.scene.title, game.chapter) : null
  $: handoverSetting = handover ? sceneSetting(handover.chapter_id, handover.scene, handover.title, handover) : null
  $: stageScene = game?.scene ? historyStage(game.chapter,game.scene,setting?.place) : null
  $: displayedStage=stageScene ?? ($presenting?$playback.scene:undefined)
  let interactiveStage:ActingStage
  $: specialControls = !!game?.scene?.exhibits?.length || usingPuppets || usingTape || moonTable || switchboard || xianTable || usingExamMixer || surveyingRidge
  $: theatreChoices = specialControls ? [] : (game?.scene?.choices ?? []).filter(c=>!c.cites || (selected.length===2 && canCite(c)))
  let reelPreference: boolean | null = null
  let decisionArea: HTMLElement
  let reelTop: HTMLElement
  $: reels = reelPreference ?? !!game?.scene?.id.match(/^(face_|reel_)/u)
  async function switchReader() {
    reelPreference = !reels
    try { localStorage.setItem('jzs.reading', reelPreference ? 'reel' : 'page') } catch {}
    await tick()
    const target = reels ? reelTop : heading
    target?.focus({preventScroll:true})
    target?.scrollIntoView({block:'start'})
  }
  function reachDecision() {
    if (!decisionArea) return
    const control = decisionArea.querySelector<HTMLElement>('button:not(:disabled),input:not(:disabled),summary')
    decisionArea.scrollIntoView({block:'start'})
    const target = control ?? decisionArea
    target.focus({preventScroll:true})
  }
  $: currentWork = game?.scene?.id.startsWith('face_') ? '借我一张脸'
    : game?.scene?.id.startsWith('reel_') ? '倒带七秒'
    : game?.chapter.title
  $: usingPuppets = game?.chapter.id === 'may_fourth' && game?.scene?.id === 'face_screen'
  $: usingTape = game?.chapter.id === 'witness_deng_xiaoping' && game?.scene?.id === 'reel_mix'
  $: surveyingRidge = game?.chapter.id === 'witness_gao' && game?.scene?.id === 'bank_map'
  $: moonTable = game?.chapter.id === 'witness_bian' && game?.scene?.id === 'sky_half'
  $: switchboard = game?.chapter.id === 'witness_deng_xiaoping' && game?.scene?.id === 'night_switchboard'
  $: xianTable = game?.chapter.id === 'witness_zhang_xueliang' && /^(xian_wait|xian_second_[nxc]|xian_(nanking|xian|civil)_(first|second))$/.test(game?.scene?.id ?? '')
  $: usingExamMixer = game?.chapter.id === 'witness_entrance_exam' && game?.scene?.id === 'air_monitor'
  $: last = game?.journal.at(-1)
  $: chapterSteps = (game?.journal ?? []).map((entry, index) => ({ ...entry, index }))
    .filter((entry) => entry.chapter_id === (handover?.chapter_id ?? game?.chapter.id))
  $: setSoundscape(game?.scene && game.scene.id !== 'reel_mix' && !game.finished && !handover && !topic && !$filmOpen
    ? sceneMix(game.chapter.id, game.scene.id, last?.chapter_id === game.chapter.id ? last.tone : undefined)
    : undefined)
  let pending: { revision: number; choice: string; command_id: string } | null = null
  let input: HTMLInputElement,
    heading: HTMLElement,
    alive = true
  let selected: string[] = []
  let opened: string[] = []
  function toggleItem(id: string) {
    selected = selected.includes(id) ? selected.filter((s) => s !== id) : [...selected, id]
  }
  function revealItem(id: string, open: boolean) {
    if (open && !opened.includes(id)) opened = [...opened, id]
  }
  function canCite(choice: Choice) {
    return (
      !choice.cites || (selected.length === 2 && choice.cites.every((id) => selected.includes(id)))
    )
  }
  let mode: Campaign = initialCampaign
  let startChapter = ''
  let yearGroup = 0
  let search = ''
  let catalogueHeading: HTMLElement
  const periods = [
    { name: '全部', from: 0, through: 9999 },
    { name: '1949年前', from: 0, through: 1948 },
    { name: '1949–1976', from: 1949, through: 1976 },
    { name: '1977–1988', from: 1977, through: 1988 },
    { name: '1989年起', from: 1989, through: 9999 },
  ]
  const eventNames: Record<string, string> = {
    witness_tan_sitong: '戊戌变法',
    witness_zhan_tianyou: '京张铁路通车',
    witness_sun_yatsen: '辛亥革命与共和交接',
    witness_chen_duxiu: '五四之后陈独秀被捕',
    witness_gu_zhenghong: '五卅运动前夕的上海工潮',
    witness_shen_junru: '救国会七君子案',
    witness_zhang_xueliang: '西安事变',
    witness_minnie_vautrin: '南京安全区与金陵女子文理学院',
    witness_chongqing_talks: '重庆谈判',
    witness_shanghai_prices: '金圆券与上海经济管制',
    witness_liu_qingshan: '天津地委贪污案',
    witness_lushan_peng: '庐山会议',
    witness_lin_zhao: '林昭案',
    witness_bian: '文革中的卞仲耘',
    witness_entrance_exam: '恢复高考',
    witness_xiaogang: '小岗村大包干',
    witness_hu_fuming: '真理标准问题讨论',
    witness_yuan_geng: '蛇口工业区起步',
    witness_deng_xiaoping: '1989年北京抗议与戒严',
    witness_southern_tour: '南方谈话',
    witness_shang_aiyun: '呼格吉勒图案',
    witness_gao: '高勤荣调查渗灌工程',
    witness_xu_zhiyong: '孙志刚案与收容遣送制度',
    witness_deng: '新晃操场案',
    witness_jiang_yanyong: '北京非典疫情信息公开',
  }
  function eventName(ch: Chapter) {
    return eventNames[ch.id] ?? ch.title
  }
  function filterChapters(list: Chapter[], group: number, words: string) {
    const period = periods[group]
    const terms = words.trim().toLowerCase().split(/\s+/).filter(Boolean)
    return list.filter((ch) => {
      const y = Number.parseInt(ch.year, 10)
      const description = [ch.year, ch.place, ch.title, ch.role, eventName(ch), ch.history]
        .join(' ')
        .toLowerCase()
      return (
        y >= period.from && y <= period.through && terms.every((term) => description.includes(term))
      )
    })
  }
  $: visibleChapters = filterChapters(catalogue.chapters, yearGroup, search)
  function browse() {
    catalogueHeading?.focus()
    catalogueHeading?.scrollIntoView({ block: 'start' })
  }
  async function selectEvent(ch: Chapter) {
    startChapter = ch.id
    await focusScene()
  }
  $: starting = catalogue.chapters.find((ch) => ch.id === startChapter)
  $: myOutcomes = catalogue.careers.flatMap((c) =>
    (c.outcomes ?? [])
      .filter((e) => e.chapter_id === startChapter)
      .map((e) => ({ ...e, name: c.name })),
  )
  $: if (topic) stopScore()
  $: previousChapter = catalogue.chapters.find((ch) => ch.id === handover?.chapter_id)
  const prefix = '/chronicle'
  function endpoint(id: string) {
    return prefix + '/' + encodeURIComponent(id)
  }
  function showError(e: unknown) {
    return e instanceof SyntaxError ? '这个文件不是有效的 JSON 存档。' : message(e)
  }
  async function perform(work: () => Promise<void>) {
    if (busy) return
    busy = true
    error = ''
    info = ''
    try {
      await work()
    } catch (e) {
      if (alive) error = showError(e)
    } finally {
      if (alive) busy = false
    }
  }
  async function refresh(campaign: Campaign = mode) {
    const list = await api<typeof catalogue>(
      prefix + (campaign === 'witness' ? '?campaign=witness' : ''),
    )
    catalogue = list
    mode = campaign
    if (!list.chapters.some((ch) => ch.id === startChapter)) {
      startChapter =
        campaign === 'witness' && list.chapters.some((ch) => ch.id === 'witness_deng_xiaoping')
          ? 'witness_deng_xiaoping'
          : (list.chapters[0]?.id ?? '')
    }
  }
  async function enter(view: View) {
    stopScore()
    if (mode !== view.campaign) await refresh(view.campaign)
    clearPerformance()
    game = view
    book = null
    handover = null
    topic = ''
    pending = null
    error = ''
    await focusScene()
  }
  async function focusScene() {
    await tick()
    selected = []
    opened = []
    if (alive && !$inTheatre) {
      const focus = game?.scene && reels && !handover && !topic && reelTop ? reelTop : heading
      focus?.focus({ preventScroll: true })
      window.scrollTo(0, 0)
    }
  }
  function begin() {
    const title =
      name.trim() ||
      (mode === 'witness' && starting ? starting.year + ' · ' + eventName(starting) : '')
    if (title)
      void perform(async () => {
        await enter(
          await api<View>(
            prefix,
            mode === 'witness'
              ? { name: title, campaign: mode, start_chapter: startChapter }
              : { name: title, campaign: mode },
          ),
        )
        name = ''
      })
  }
  function resume(id: string) {
    void perform(async () => {
      await enter(await api<View>(endpoint(id)))
    })
  }
  function home() {
    void perform(async () => {
      await refresh()
      stopScore()
      clearPerformance()
      game = null
      handover = null
      pending = null
      topic = ''
      await focusScene()
    })
  }
  function choose(id: string) {
    if (!game || busy || (pending && pending.choice !== id)) return
    enableSound()
    const previous = game
    pending ??= { revision: previous.revision, choice: id, command_id: crypto.randomUUID() }
    const command = pending
    void perform(async () => {
      const action = previous.scene?.choices.find(c => c.id === id)
      const stageTurn = stageScene && action ? startTurn(stageScene, action.label) : null
      let next: View
      try {
        next = await api<View>(endpoint(previous.id) + '/choices', command)
        const outcome = next.journal[command.revision]
        const after=next.scene && next.chapter.id===previous.chapter.id ? historyStage(next.chapter,next.scene) : undefined
        const reaction=after?.other && action?.label.includes(after.other.name.replace(/^聂桂枝$/,'桂枝')) ? after : undefined
        void stageTurn?.resolve(outcome?.result ?? '',outcome?.tone,reaction)
      } catch (e) {stageTurn?.cancel(); throw e}
      if (!alive) return
      pending = null
      game = next
      const entry = next.journal[command.revision]
      if (next.chapter.id !== previous.chapter.id || next.finished) handover = entry
      if (previous.scene) void playScore(outcomeCue(previous.chapter.id, previous.scene.id, id, next.scene?.id ?? '', entry?.tone))
      await focusScene()
    })
  }
  function fork(at: number) {
    if (!game) return
    const id = game.id
    void perform(async () => {
      await enter(await api<View>(endpoint(id) + '/fork', { revision: at }))
      info = '已从这一步另建一份长篇。'
    })
  }
  async function readFile(event: Event) {
    const el = event.currentTarget as HTMLInputElement,
      file = el.files?.[0]
    el.value = ''
    if (!file) return
    if (file.size > 20 * 1024 * 1024) {
      error = '存档超过 20 MB。'
      return
    }
    await perform(async () => {
      await enter(await api<View>(prefix + '/import', JSON.parse(await file.text())))
      info = '长篇存档已导入。'
    })
  }
  function exportFile() {
    if (!game) return
    const current = game
    void perform(async () => {
      saveFile(
        await download(endpoint(current.id) + '/export'),
        '局中事-历史长篇-' + current.name + '.json',
      )
      info = '长篇存档已导出。'
    })
  }
  function turnPage() {
    handover = null
    void focusScene()
  }
  onMount(() => {
    try {
      const previous = localStorage.getItem('jzs.reading')
      if (previous === 'reel' || previous === 'page') reelPreference = previous === 'reel'
    } catch {}
    void perform(async () => {
      await refresh()
      if (!featured || !alive) return
      const opening = featured
      const saved = catalogue.careers.find((c) => !c.finished && (opening.edition
        ? c.edition === opening.edition
        : !c.edition && c.start_chapter === opening.chapter && c.opening_choice === opening.opening &&
          (opening.campaign === 'family' || c.standalone)))
      const view = saved ? await api<View>(endpoint(saved.id)) : await api<View>(prefix, {
        name: opening.title, campaign: opening.campaign, opening_choice: opening.opening,
        ...(opening.edition ? { edition: opening.edition } :
          opening.campaign === 'witness' ? { start_chapter: opening.chapter } : {}),
      })
      if (alive) await enter(view)
    })
  })
  onDestroy(() => {
    alive = false
    clearPerformance()
    setSoundscape(undefined)
    stopScore()
  })
</script>

<main id="main" class="chronicle">
  <header class="mast">
    <button class="wordmark" disabled={busy} on:click={game ? home : () => leave(mode)}
      >局中事</button
    >
    <span class="mast-title">历史长篇</span>
    <div class="utilities">
      {#if game?.scene && !handover}<button aria-pressed={reels} on:click={switchReader}>镜头阅读</button>{/if}
      <button
        disabled={busy}
        on:click={() => {
          topic = '年代与出处'
          book = previousChapter ?? game?.chapter ?? starting ?? catalogue.chapters[0] ?? null
        }}>年代与出处</button
      >
      {#if game}<button disabled={busy} on:click={() => (topic = '行记')}>行记与存档</button>{/if}
      <button
        role="switch"
        aria-checked={volume > 0}
        aria-label="历史长篇音效"
        on:click={toggleAudio}>音效{volume ? '开' : '关'}</button
      >
      <button disabled={busy} on:click={game ? home : () => leave(mode)}
        >{game ? '长篇目录' : mode === 'family' ? '生涯模式' : '模式选择'}</button
      >
    </div>
  </header>
  {#if error}<div class="signal" role="alert">
      {error}
      {#if pending}<button disabled={busy} on:click={() => pending && choose(pending.choice)}
          >重试这次选择</button
        >{/if}
      <button disabled={busy} on:click={() => (game ? resume(game.id) : perform(refresh))}
        >重新读取</button
      >
    </div>{/if}
  {#if info}<p class="signal" role="status">{info}</p>{/if}
  {#if game && displayedStage && ((!handover && !game.finished) || $presenting)}
    <ActingStage bind:this={interactiveStage} embeddedControls={specialControls} controlsArea={decisionArea} scene={displayedStage} choices={theatreChoices} decide={choose} seeControls={reachDecision} {volume} {toggleAudio} {busy} {reduced}/>
  {/if}
  {#if !game}
    <div class="lobby">
      <div class="lobby-art">
        <img
          src={picture(
            mode === 'witness' ? (starting?.id ?? 'witness_deng_xiaoping') : 'chronicle_cover',
          )}
          alt=""
        />
        {#if mode === 'witness' && starting}<div class="art-caption">
            <span>{starting.year}</span><strong>{starting.place} · {starting.title}</strong>
            <p>年代情境插画</p>
          </div>{/if}
      </div>
      <section class="lobby-text">
        <p class="date-line">{mode === 'witness' ? '历史主角模式' : '生涯模式 · 市井家书'}</p>
        <h1 tabindex="-1" bind:this={heading}>{mode === 'witness' ? '亲历者' : '历史长篇'}</h1>
        {#if mode === 'witness'}
          <button class="browse" on:click={browse} disabled={busy}
            >浏览全部 {catalogue.chapters.length} 个历史事件 ↓</button
          >
          <label for="player-event">从哪件事开始</label>
          <select
            id="player-event"
            aria-label="选择亲历者与起始事件"
            bind:value={startChapter}
            disabled={busy}
          >
            {#each catalogue.chapters as ch}<option value={ch.id}
                >{ch.year} · {ch.role} ／ {eventName(ch)}</option
              >{/each}
          </select>
          {#if starting}<p class="lede">{starting.intro}</p>{/if}
          {#if myOutcomes.length}<details class="my-outcomes">
              <summary>对照我走过的结局</summary>
              {#each myOutcomes as e}<div>
                  <b>{e.name} · {e.label}</b>
                  <p>{e.result}</p>
                </div>{/each}
            </details>{/if}
        {:else}<p class="date-line">1919 — 2019</p>
          <p class="lede">从北京的一间印铺出发。把一件东西留给后来的人，也把它背后的承诺交给他。</p>
        {/if}
        <form on:submit|preventDefault={begin}>
          <label for="chron-name">为这段长篇命名</label>
          <div class="create-row">
            <input
              id="chron-name"
              maxlength="48"
              placeholder={mode === 'witness' ? '可选，留空使用事件名称' : '例如：家书'}
              bind:value={name}
            /><button
              class="gold"
              disabled={busy || (!name.trim() && mode === 'family') || !catalogue.chapters.length}
              >开始长篇</button
            >
          </div>
        </form>
        {#if catalogue.careers.length}<section class="saves">
            <h2>继续长篇</h2>
            {#each catalogue.careers as c}<button disabled={busy} on:click={() => resume(c.id)}
                ><b>{c.name}</b><span
                  >{c.finished
                    ? '已走完'
                    : catalogue.chapters.find((x) => x.id === c.chapter_id)?.title} · {c.revision} 次选择　→</span
                ></button
              >{/each}
          </section>{/if}
        <button class="text-link" disabled={busy} on:click={() => input.click()}
          >导入长篇存档</button
        >
      </section>
    </div>
    {#if mode === 'witness' && catalogue.chapters.length}
      <section class="event-index" aria-label="可选历史事件">
        <div class="index-head">
          <h2 bind:this={catalogueHeading} tabindex="-1">事件目录</h2>
          <input
            type="search"
            aria-label="搜索历史事件"
            placeholder="搜索人物、事件或地点"
            bind:value={search}
          />
        </div>
        <div class="periods" aria-label="按年代筛选">
          {#each periods as p, i}<button
              aria-pressed={yearGroup === i}
              on:click={() => (yearGroup = i)}>{p.name}</button
            >{/each}
        </div>
        <p class="matches" aria-live="polite">{visibleChapters.length} 个事件</p>
        <div class="event-grid">
          {#each visibleChapters as ch}<button
              disabled={busy}
              aria-pressed={ch.id === startChapter}
              on:click={() => selectEvent(ch)}
            >
              <img loading="lazy" src={picture(ch.id)} alt="" />
              <span class="card-text"
                ><small>{ch.year} {ch.place}</small><strong>{eventName(ch)}</strong><span
                  >{ch.role}</span
                ></span
              >
            </button>{:else}<p>
              没有找到相符的事件。<button
                class="text-link"
                on:click={() => {
                  yearGroup = 0
                  search = ''
                }}>显示全部</button
              >
            </p>{/each}
        </div>
      </section>
    {/if}
  {:else if handover}
    <section class="handover">
      <p class="date-line">{handoverSetting?.year} {handoverSetting?.place}</p>
      <h1 tabindex="-1" bind:this={heading}>{handover.title}</h1>
      <blockquote>{handover.result}</blockquote>
      {#if mode === 'witness' && previousChapter}<section class="comparison">
          <h2>史实对照</h2>
          <p>{previousChapter.history}</p>
          <button
            on:click={() => {
              book = previousChapter ?? null
              topic = '年代与出处'
            }}>查阅本章出处</button
          >
        </section>{/if}
      <p>{handover.marks.join(' · ')}</p>
      <button class="gold" on:click={turnPage}
        >{game.finished ? '打开全卷行记' : '翻至 ' + game.chapter.year + ' · ' + game.chapter.place}
        →</button
      >
    </section>
  {:else if game.finished}
    <section class="handover">
      <p class="date-line">{game.name}</p>
      <h1 tabindex="-1" bind:this={heading}>全卷行记</h1>
      <blockquote>{game.journal.at(-1)?.result}</blockquote>
      <p>
        {new Set(game.journal.map((e) => e.chapter_id)).size} 个历史章节，留下 {game.revision} 次选择和
        {game.marks.length} 项记录。
      </p>
      <button class="gold" on:click={() => (topic = '行记')}>回看沿途的选择</button>
    </section>
  {:else if game.scene}
    <div class="stage" class:reel-stage={reels}>
      {#if reels}
        <div tabindex="-1" class="reel-top" bind:this={reelTop}>
        {#key game.id + '/' + game.revision}
          <ScenePlayback portrait={picture(game.chapter.id, game.scene.id)} shot={directedShot(game.scene.id)}
            caption={pictureCaption(game.chapter.id, game.scene.id)} date={setting?.year ?? game.chapter.year}
            place={setting?.place ?? game.chapter.place} role={game.chapter.role} body={game.scene.base_body ?? game.scene.body}
            previous={last?.chapter_id === game.chapter.id && !['borrow_a_face','seven_seconds'].includes(last.choice ?? '') ? last.result : ''} revision={game.revision} gameId={game.id} decide={reachDecision} {volume} {toggleAudio}/>
        {/key}
        </div>
      {:else}<aside class="scene-art">
        <img src={picture(game.chapter.id, game.scene.id)} alt="" />
        <div class="art-caption">
          <span>{setting?.year}</span><strong>{setting?.place}</strong>
          <p>{pictureCaption(game.chapter.id, game.scene.id)}</p>
        </div>
      </aside>{/if}
      <article class="story">
        <p class="date-line">
          {mode === 'witness' ? '历史推演 · ' : ''}{currentWork}　／　{game.chapter.role}
        </p>
        <h1 tabindex="-1" bind:this={heading}>{game.scene.title}</h1>
        {#if !game.journal.length || game.journal.at(-1)?.chapter_id !== game.chapter.id}<p
            class="intro"
          >
            {game.chapter.intro}
          </p>{/if}
        {#key game.id + '/' + game.revision}<svelte:element this={reels ? 'details' : 'div'} class="scene-body" class:transcript={reels}>
          {#if reels}<summary>翻阅本幕全文</summary>{/if}
          {#each (game.scene.base_body ?? game.scene.body).split(/\n+/).filter((paragraph) => paragraph.trim()) as paragraph}
            <p>{#each linesOfSpeech(paragraph) as phrase}{#if phrase.startsWith('“')}<span class="speech">{phrase}</span>{:else}{phrase}{/if}{/each}</p>
          {/each}
        </svelte:element>{/key}
        {#key game.id + '/' + game.revision}
          {#each game.scene.callbacks ?? [] as callback}
            {@const source = game.journal[callback.origin]}
            <aside class="story-echo">
              <p>{callback.body}</p>
              {#if source}<details>
                <summary>回想当时的选择 · {source.title}</summary>
                <b>{source.label}</b><p>{source.result}</p>
              </details>{/if}
            </aside>
          {/each}
        {/key}
        <div class="play-area" aria-label="本幕行动" role="group" tabindex="-1" bind:this={decisionArea}>
        {#key game.id + '/' + game.revision}
          {#if usingPuppets}<FaceBooth choices={game.scene.choices} disabled={busy || !!pending} {volume} onChoose={choose}/>{/if}
          {#if usingTape}<TapeRoom choices={game.scene.choices} disabled={busy || !!pending} {volume} onChoose={choose}/>{/if}
          {#if moonTable}<CourtyardMoon disabled={busy || (!!pending && pending.choice !== 'sky_keep_sketch')} onChoose={choose}/>{/if}
          {#if switchboard}<NightSwitchboard choices={game.scene.choices} disabled={busy || !!pending} {volume} onChoose={choose}/>{/if}
          {#if xianTable}<XianTable sceneId={game.scene.id} choices={game.scene.choices} marks={game.marks} disabled={busy || !!pending} onChoose={choose}/>{/if}
        {/key}
        {#if usingExamMixer}<ExamMixer choices={game.scene.choices} disabled={busy || !!pending} onChoose={choose}/>{/if}
        {#if surveyingRidge}
          {#key game.id + '/' + game.revision}<RidgeSurvey {busy} pendingChoice={pending?.choice} onChoose={choose} />{/key}
        {/if}
        {#if game.scene.exhibits?.length}
          <svelte:element this={surveyingRidge ? 'details' : 'section'} class="exhibits" aria-label="案头材料">
            {#if surveyingRidge}<summary>翻阅纸本走访记录</summary>{:else}<h2>案头材料</h2>{/if}
            <p>翻看实物，选两份摆在一起，再作判断。</p>
            {#each game.scene.exhibits as e}
              <div class="object">
                <details on:toggle={(event) => revealItem(e.id, event.currentTarget.open)}>
                  <summary>{e.title}</summary>
                  <p>{e.detail}</p>
                </details>
                <button
                  aria-label={'对照材料 · ' + e.title}
                  aria-pressed={selected.includes(e.id)}
                  disabled={busy ||
                    !opened.includes(e.id) ||
                    (!selected.includes(e.id) && selected.length >= 2)}
                  on:click={() => toggleItem(e.id)}
                  >{selected.includes(e.id) ? '已对照' : '选入对照'}</button
                >
              </div>
            {/each}
            <small aria-live="polite">已选 {selected.length} / 2 件</small>
          </svelte:element>
        {/if}
        {#if !usingExamMixer && !xianTable && !usingPuppets}<div class="decisions" aria-label="你的选择">
          {#each game.scene.choices.filter((c) => !(usingTape && c.id.startsWith('cut_')) && !(moonTable && c.id === 'sky_keep_sketch') && !(switchboard && c.id.startsWith('patch_')) && (!c.cites || (selected.length === 2 && canCite(c)))) as c}<button
              disabled={busy || (!!pending && pending.choice !== c.id)}
              on:click={() => choose(c.id)}
              ><span>{c.label}</span><b aria-hidden="true">→</b></button
            >{/each}
        </div>{/if}
        </div>
        {#if last && last.chapter_id === game.chapter.id}
          {#key game.id + '/' + game.revision}
            <details class="receipt">
              <summary>回看上一幕 · {last.title}</summary>
              <b>{last.label}</b>
              <p>{last.result}</p>
              {#if last.marks.length}<small>留存 · {last.marks.join('、')}</small>{/if}
            </details>
          {/key}
        {/if}
        <footer>
          <span>{game.name} · 已保存 {game.revision} 次选择</span>
          <div>{#if chapterSteps.length}<button on:click={() => (topic = '本章足迹')}>本章足迹</button>{/if}
          <button
            on:click={() => {
              topic = '年代与出处'
              book = game?.chapter ?? null
            }}>本章史料</button
          ></div>
        </footer>
      </article>
    </div>
  {/if}
  <input
    hidden
    type="file"
    accept="application/json,.json"
    bind:this={input}
    aria-label="导入历史长篇文件"
    on:change={readFile}
  />
</main>

{#if topic}
  <Dialog title={topic} onclose={() => (topic = '')}>
    {#if topic === '年代与出处'}
      <div class="reader">
        <label for="era-select">查阅年代</label>
        <select
          id="era-select"
          value={book?.id}
          on:change={(e) =>
            (book = catalogue.chapters.find((c) => c.id === e.currentTarget.value) ?? null)}
          >{#each catalogue.chapters as c}<option value={c.id}>{c.year} · {c.title}</option
            >{/each}</select
        >
        {#if book}<h3>{book.title}</h3>
          <p class="meta">{book.year} · {book.place}</p>
          <p>{book.history}</p>
          <h4>资料出处</h4>
          {#each book.sources as s}<details>
              <summary>{s.name}</summary><a href={s.url} target="_blank" rel="noreferrer noopener"
                >{s.url}</a
              >
            </details>{/each}
          <p class="meta">
            {mode === 'witness'
              ? '人物和历史节点有出处。你在游戏里作的决定及其后果属于历史推演。'
              : '剧情中的对话、个人选择与年代插画为创作。所引史实见以上资料。'}
          </p>
        {/if}
      </div>
    {:else if topic === '本章足迹'}
      <ChapterPath entries={chapterSteps} {busy} {fork} {volume} {toggleAudio}/>
    {:else if game}
      <div class="reader">
        <div class="journal-tools">
          <p>{game.name} · 已保存 {game.revision} 次选择</p>
          <button disabled={busy} on:click={exportFile}>导出长篇存档</button>
        </div>
        {#if game.marks.length}<h3>{mode === 'witness' ? '人物命运与决定' : '代际留存'}</h3>
          <p>{game.marks.join('、')}</p>{/if}
        <h3>走过的路</h3>
        {#each game.journal.map((e, i) => ({ e, i })).reverse() as row}
          <details>
            <summary>{sceneSetting(row.e.chapter_id, row.e.scene, row.e.title, row.e).year} · {row.e.title}</summary>
            <p>{row.e.role} {row.e.label}</p>
            <p>{row.e.result}</p>
            {#if row.e.citations?.length}
              <section aria-label="已对照材料">
                <h4>已对照材料</h4>
                <dl>
                  {#each row.e.citations as item}
                    <dt>{item.title}</dt>
                    <dd>{item.detail}</dd>
                  {/each}
                </dl>
              </section>
            {/if}{#if row.e.marks.length}<p class="meta">留存 · {row.e.marks.join('、')}</p>{/if}
            <button disabled={busy} on:click={() => fork(row.i)}>从此次选择前另开分线</button>
          </details>
        {:else}<p>做出第一次选择后，会在这里留下记录。</p>{/each}
      </div>
    {/if}
  </Dialog>
{/if}

<style>
  .chronicle {
    min-height: 100vh;
    background: #191c1b;
    color: #f2e9d8;
    padding-bottom: clamp(1rem, 4vw, 4rem);
  }
  .mast {
    min-height: 74px;
    max-width: 1472px;
    margin: auto;
    display: flex;
    align-items: center;
    gap: 1.1rem;
    padding: 10px clamp(16px, 4vw, 64px);
    border-bottom: 1px solid #4d4c44;
  }
  .mast button,
  .text-link,
  .story footer button {
    border: 0;
    background: none;
    padding: 10px 0;
    min-height: 44px;
  }
  .wordmark {
    font-family: var(--serif);
    font-size: 1.55rem;
    font-weight: 700;
    letter-spacing: 0.1em;
  }
  .mast-title {
    border-left: 1px solid #777264;
    padding-left: 1rem;
    color: #debd83;
    font-size: 0.88rem;
    white-space: nowrap;
  }
  .utilities {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: clamp(0.7rem, 2.5vw, 2rem);
    font-size: 0.9rem;
  }
  .mast button:hover,
  .text-link:hover {
    color: #e3bd77;
  }
  .lobby,
  .stage {
    max-width: 1400px;
    margin: clamp(20px, 3.8vw, 60px) auto 0;
    width: calc(100% - clamp(32px, 8vw, 128px));
    display: grid;
    align-items: stretch;
  }
  .lobby {
    grid-template-columns: 1.04fr 1fr;
    background: #272b28;
    border: 1px solid #534e43;
  }
  .lobby-art,
  .scene-art {
    position: relative;
    min-width: 0;
    isolation: isolate;
  }
  .lobby-art img,
  .scene-art img {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  .lobby-art img {
    object-position: 42% 60%;
  }
  .lobby-text {
    padding: clamp(26px, 5vw, 78px);
    align-self: center;
  }
  .date-line {
    letter-spacing: 0.09em;
    color: #d4b482;
    font-weight: 600;
    font-size: 0.88rem;
  }
  .lobby h1,
  .handover h1 {
    margin: 0.35em 0;
    font-family: var(--serif);
    font-size: clamp(2.7rem, 5.5vw, 5.6rem);
    letter-spacing: 0.04em;
    font-weight: 500;
  }
  .lede {
    font-family: var(--serif);
    font-size: clamp(1.08rem, 1.7vw, 1.35rem);
    line-height: 1.9;
    color: #dfd7c8;
    max-width: 33em;
  }
  .lobby form {
    margin-top: 2rem;
  }
  .lobby label {
    display: block;
    font-size: 0.86rem;
    color: #dbd4c3;
    margin-bottom: 0.45rem;
  }
  .create-row {
    display: flex;
    gap: 0.65rem;
    flex-wrap: wrap;
  }
  .create-row input {
    min-width: 8rem;
    flex: 1;
    background: #1c201e;
    color: #fff4de;
    border: 1px solid #807763;
    padding: 0.55rem 0.8rem;
    border-radius: 2px;
  }
  .gold {
    border: 1px solid #e5c998;
    background: #e1be81;
    color: #22231c;
    font-weight: 700;
    min-height: 44px;
    padding: 0.55rem 1.2rem;
    border-radius: 2px;
  }
  .gold:hover:not(:disabled) {
    background: #f6d9a5;
  }
  .text-link {
    color: #dfcaa3;
    font-size: 0.88rem;
    text-decoration: underline;
    text-underline-offset: 0.3em;
  }
  .saves {
    margin: 1.55rem 0 0.5rem;
    padding: 0;
    background: none;
  }
  .saves h2 {
    font-size: 1.24rem;
    margin-bottom: 0.6rem;
  }
  .saves button,
  .decisions button {
    width: 100%;
    text-align: left;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    min-height: 48px;
  }
  .saves button {
    border: 0;
    border-top: 1px solid #545548;
    background: none;
    color: #f4ead6;
    padding: 0.5rem 0;
  }
  .saves button:hover {
    color: #efca80;
  }
  .saves button span {
    color: #d0c5af;
    text-align: right;
    font-size: 0.85rem;
  }
  .stage {
    grid-template-columns: minmax(0, 0.72fr) minmax(0, 1.35fr);
    background: #282a25;
    color: #2e2a23;
  }
  .scene-art {
    position: sticky;
    top: 0;
    max-height: 100vh;
    background: #282a25;
    min-height: 410px;
  }
  .scene-art img {
    object-position: 50% 45%;
  }
  .scene-art::after {
    content: '';
    position: absolute;
    inset: 38% 0 0;
    background: linear-gradient(transparent, rgba(15, 17, 15, 0.84));
    pointer-events: none;
  }
  .art-caption {
    position: absolute;
    bottom: clamp(20px, 3.7vw, 58px);
    left: clamp(20px, 3vw, 46px);
    right: 1rem;
    z-index: 1;
    color: #fff6e3;
    text-shadow: 0 1px 8px #302d25;
  }
  .art-caption span,
  .art-caption strong {
    display: block;
    font-family: var(--serif);
    font-weight: 500;
  }
  .art-caption span {
    font-size: clamp(2rem, 4.2vw, 4.5rem);
    line-height: 1.15;
  }
  .art-caption strong {
    font-size: clamp(1.12rem, 2vw, 1.7rem);
    margin: 0.25rem 0;
  }
  .art-caption p {
    font-size: 0.75rem;
    color: #ede2cc;
  }
  .story {
    background: #f3eee1;
    padding: clamp(24px, 3.5vw, 54px) clamp(24px, 5vw, 84px);
    min-width: 0;
  }
  .story .date-line,
  .reader .meta {
    color: #766246;
  }
  .story h1 {
    font-size: clamp(1.75rem, 3vw, 3.15rem);
    line-height: 1.35;
    font-weight: 600;
    margin: 0.6rem 0 1.2rem;
  }
  .story .intro {
    border-top: 1px solid #c7bca5;
    padding-top: 0.9rem;
    color: #605744;
    font-size: 0.91rem;
    margin: 1rem 0;
    white-space: pre-line;
  }
  .scene-body,
  .handover blockquote {
    font-size: clamp(1.08rem, 1.45vw, 1.3rem);
    font-family: var(--serif);
    line-height: 1.95;
    white-space: pre-line;
  }
  .scene-body { animation: page-in .26s ease-out both }
  .speech { color: #62462d; font-weight: 550 }
  .story footer div { display: flex; flex-wrap: wrap; gap: .85rem; }
  @keyframes page-in { from { opacity: .4 } to { opacity: 1 } }
  @media (prefers-reduced-motion: reduce) { .scene-body { animation: none } }
  :global(.reduce-motion) .scene-body { animation: none }
  .scene-body p {
    margin: 0;
    overflow-wrap: break-word;
  }
  .scene-body p + p {
    margin-top: 0.9em;
  }
  .story-echo { margin: .9rem 0 1.1rem; padding: .15rem .9rem .4rem; border-left: 2px solid #a17e51; }
  .story-echo p { margin: .25rem 0; line-height: 1.75; }
  .story-echo summary { color: #6c5231; font-size: .83rem; cursor: pointer; line-height: 1.55; }
  .story-echo details b, .story-echo details p { font-size: .91rem; }
  .stage.reel-stage{display:block;background:#19201c}
  .reel-stage .story{padding:clamp(20px,3vw,40px) clamp(22px,7vw,100px)}
  .reel-stage .story h1{font-size:clamp(1.55rem,2.6vw,2.4rem)}
  .reel-top:focus,.story:focus{outline:none}
  .transcript summary{font:500 .9rem/1.65 var(--sans);color:#685337;cursor:pointer}
  .transcript summary{margin-bottom:.45rem}
  .receipt {
    color: #5c4e3e;
    margin: 0.5rem 0;
  }
  .receipt summary {
    cursor: pointer;
    padding: 0.7rem 0;
    font-size: 0.9rem;
  }
  .receipt b,
  .receipt small {
    font-size: 0.8rem;
    color: #705739;
  }
  .receipt p {
    font-size: 0.94rem;
    line-height: 1.7;
    white-space: pre-line;
    margin: 0.3rem 0;
  }
  .decisions {
    display: grid;
    gap: 0.55rem;
    margin: 1.65rem 0 1.5rem;
  }
  .decisions button {
    padding: 0.76rem 1rem;
    background: #fcf8ee;
    border: 1px solid #b3a992;
    border-radius: 2px;
    color: #332f27;
    line-height: 1.5;
  }
  .decisions b {
    font-family: var(--serif);
    font-size: 1.1rem;
    color: #72552b;
  }
  .decisions button:hover:not(:disabled) {
    background: #eadfc9;
    border-color: #84653f;
  }
  .story footer,
  .journal-tools {
    display: flex;
    gap: 0.8rem;
    align-items: center;
    justify-content: space-between;
    border-top: 1px solid #c8bfae;
    font-size: 0.83rem;
    color: #645c4f;
  }
  .story footer button,
  .reader button {
    text-decoration: underline;
    text-underline-offset: 4px;
  }
  .handover {
    max-width: 750px;
    margin: clamp(3rem, 10vw, 9rem) auto;
    padding: 0 clamp(20px, 4vw, 46px);
  }
  .handover h1 {
    font-size: clamp(2rem, 4vw, 3.8rem);
  }
  .handover blockquote {
    margin: 1.5rem 0 1rem;
    border-left: 2px solid #a98d63;
    padding-left: 1rem;
    color: #ece0cc;
  }
  .handover .gold {
    margin-top: 1.5rem;
  }
  .signal {
    max-width: 1100px;
    margin: 1rem auto;
    padding: 0.5rem 1rem;
    background: #454339;
    color: #f6ecd8;
  }
  .signal button,
  .reader button {
    background: none;
    border: 0;
    color: inherit;
    min-height: 44px;
    padding: 0.4rem;
  }
  .reader {
    color: #363329;
  }
  .reader h3 {
    margin: 1rem 0 0.35rem;
  }
  .reader h4 {
    margin: 1.25rem 0 0.5rem;
  }
  .reader label {
    display: block;
    margin-bottom: 0.35rem;
    font-size: 0.87rem;
  }
  .reader select {
    width: 100%;
    padding: 0.6rem;
    border: 1px solid #9a927f;
    background: #fbfaf4;
    color: inherit;
  }
  .reader details {
    border-top: 1px solid #cbc7b9;
    padding: 0.45rem 0;
  }
  .reader summary {
    min-height: 36px;
    padding: 0.35rem 0;
  }
  .reader details p {
    margin: 0.35rem 0;
  }
  .reader a {
    display: inline-block;
    overflow-wrap: anywhere;
  }
  .reader .meta {
    font-size: 0.85rem;
    margin: 0.5rem 0;
  }
  @media (max-width: 760px) {
    .mast {
      flex-wrap: wrap;
      gap: 0.25rem 0.7rem;
      padding-top: 5px;
    }
    .mast-title {
      padding-left: 0.7rem;
    }
    .utilities {
      width: 100%;
      margin: 0;
      justify-content: space-between;
      gap: 0.4rem;
    }
    .utilities button {
      padding: 3px 0;
    }
    .lobby,
    .stage {
      width: calc(100% - 24px);
      margin: 14px auto 0;
      grid-template-columns: minmax(0, 1fr);
    }
    .lobby-art,
    .scene-art {
      height: clamp(145px, 43vw, 290px);
      min-height: 0;
    }
    .lobby-art img {
      object-position: 50% 66%;
    }
    .scene-art img {
      object-position: 50% 40%;
    }
    .scene-art {
      position: relative;
      height: clamp(100px, 28vw, 180px);
    }
    .art-caption {
      bottom: 12px;
      left: 18px;
    }
    .art-caption span {
      font-size: 1.82rem;
    }
    .art-caption strong,
    .art-caption p {
      display: inline;
      margin-right: 0.55rem;
    }
    .lobby-text,
    .story {
      padding: 22px 18px;
    }
    .story footer {
      flex-wrap: wrap;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    button {
      transition: none;
    }
  }

  .exhibits {
    margin: 1.2rem 0;
    background: #eae2d1;
    border-block: 1px solid #bbae93;
    padding: 0.9rem 1rem;
  }
  .exhibits h2 {
    font-size: 1.18rem;
  }
  .exhibits > p,
  .exhibits small {
    font-size: 0.84rem;
    color: #5f533f;
  }
  .object {
    border-top: 1px solid #c8bda5;
    margin-top: 0.55rem;
    padding: 0.25rem 0;
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: start;
    gap: 0.5rem;
  }
  .object details {
    padding: 0.2rem 0;
  }
  .object summary {
    font-family: var(--serif);
    font-weight: 700;
    padding: 0.3rem 0;
    min-height: 40px;
  }
  .object p {
    margin: 0.2rem 0 0.6rem;
    line-height: 1.7;
  }
  .object button {
    font-size: 0.8rem;
    border: 1px solid #ac9c7e;
    background: #faf5e8;
    padding: 0.45rem 0.6rem;
    min-height: 40px;
  }
  .object button[aria-pressed='true'] {
    background: #404c41;
    color: #fff8e5;
  }
  .lobby-text select {
    width: 100%;
    background: #1c201e;
    color: #f4e9d5;
    border: 1px solid #897d67;
    padding: 0.65rem 0.4rem;
    margin-bottom: 0.9rem;
  }
  .lobby-art:has(.art-caption)::after {
    content: '';
    position: absolute;
    inset: 30% 0 0;
    background: linear-gradient(transparent, rgba(12, 14, 13, 0.85));
  }
  .comparison {
    border-top: 1px solid #706756;
    margin: 1.3rem 0;
    padding-top: 1rem;
  }
  .comparison h2 {
    font-size: 1.2rem;
    color: #d8bb86;
  }
  .comparison p {
    font-size: 0.96rem;
    color: #e3dccf;
  }
  .comparison button {
    border: 0;
    background: none;
    color: #e3c997;
    text-decoration: underline;
    padding: 0.5rem 0;
  }
  .browse {
    border: 0;
    background: none;
    color: #eccb91;
    min-height: 40px;
    margin: 0 0 0.8rem;
    padding: 0;
    text-decoration: underline;
    text-underline-offset: 5px;
  }
  .event-index {
    max-width: 1400px;
    width: calc(100% - clamp(32px, 8vw, 128px));
    margin: clamp(25px, 4.5vw, 68px) auto 0;
  }
  .index-head,
  .periods {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    flex-wrap: wrap;
  }
  .index-head {
    justify-content: space-between;
    margin-bottom: 1.1rem;
  }
  .index-head h2 {
    font-size: clamp(1.6rem, 3vw, 2.5rem);
    font-weight: 550;
    scroll-margin-top: 1rem;
  }
  .index-head input {
    background: #262a26;
    color: #fff3db;
    border: 1px solid #827866;
    border-radius: 2px;
    padding: 0.5rem 0.8rem;
    max-width: 100%;
  }
  .periods button {
    border: 1px solid #716b5a;
    background: transparent;
    color: #ddd4bf;
    padding: 0.4rem 0.8rem;
    min-height: 40px;
  }
  .periods button[aria-pressed='true'] {
    background: #d8ba89;
    color: #23251f;
    border-color: #d8ba89;
  }
  .matches {
    margin: 0.6rem 0;
    font-size: 0.83rem;
    color: #c7bca7;
  }
  .event-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 275px), 1fr));
    gap: 12px;
  }
  .event-grid > button {
    background: #292d28;
    border: 1px solid #595a4e;
    padding: 0;
    text-align: left;
    display: flex;
    align-items: stretch;
    min-width: 0;
  }
  .event-grid > button:hover,
  .event-grid > button[aria-pressed='true'] {
    border-color: #dcbe89;
    background: #353a32;
  }
  .event-grid img {
    object-fit: cover;
    width: 28%;
    aspect-ratio: 0.88;
    max-height: 145px;
  }
  .card-text {
    display: grid;
    align-content: center;
    gap: 0.2rem;
    padding: 0.7rem 0.8rem;
  }
  .card-text small {
    color: #dbbc89;
  }
  .card-text strong {
    font-family: var(--serif);
    font-size: 1.05rem;
    color: #faf0db;
  }
  .card-text span {
    font-size: 0.8rem;
    color: #ddd5c4;
  }
  @media (max-width: 760px) {
    .event-index {
      width: calc(100% - 28px);
    }
    .index-head input {
      width: 100%;
    }
  }
  .my-outcomes {
    margin: 1rem 0;
    color: #eee3ca;
    border-block: 1px solid #645d4e;
    padding: 0.5rem 0;
  }
  .my-outcomes summary {
    padding: 0.4rem 0;
  }
  .my-outcomes div {
    margin: 0.5rem 0 1rem;
  }
  .my-outcomes b {
    color: #e3c797;
    font-size: 0.9rem;
  }
  .my-outcomes p {
    font-size: 0.91rem;
  }
</style>
