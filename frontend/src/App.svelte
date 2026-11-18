<script lang="ts">
  import { onMount, tick } from 'svelte'
  import { api, ApiError, download, message, importSave } from './api'
  import { watchWorld } from './live'
  import { balanceString, dateAt, saveFile, stamp, starts, str, title } from './game'
  import type { Action, AttemptResult, Choice, Command, Page, Row, Value, View, World } from './types'
  import Menu from './Menu.svelte'
  import Dialog from './Dialog.svelte'
  import Balance from './Balance.svelte'
  import Recap from './Recap.svelte'
  import History from './History.svelte'
  import WorkingNote from './WorkingNote.svelte'
  import Sites from './Sites.svelte'
  import { cue } from './sound'
  import Records from './Records.svelte'
  import Timeline from './Timeline.svelte'
  import ActionList from './ActionList.svelte'

  let v: View | null = null,
    worlds: World[] = [],
    page: Page = '办公桌',
    loading = true,
    busy = false,
    offline = false
  let stopWatch: (() => void) | undefined,
    latestRevision = 0
  let profiles = starts
  let error = '',
    notice = '',
    receipt = '',
    category = '全部',
    archiveTab = '来文材料',
    peopleTab = '人物名录'
  let inputFile: HTMLInputElement,
    heading: HTMLElement,
    worldName = '',
    prompt = '',
    parseNote = ''
  let parsedStatus = '',
    lastAttempts: AttemptResult[] = []
  let options: Choice[] = [],
    picked: Action | null = null,
    formValues: Record<string, Value> = {}
  let draftBalance = '0.500000',
    font = 16,
    reduceMotion = false,
    volume = 0,
    detailed = true,
    hints = true,
    advanceMinutes = 60,
    forkRevision = 0
  let pending: Command | null = null,
    archiveSearch = '',
    compared: string[] = [],
    compareMode = false
  let reports: Row[] = [],
    archiveRows: Row[] = []
  const attemptLabels: Record<string, string> = {
    accepted: '已受理',
    unavailable: '未能办理',
    blocked: '前置未受理',
  }
  const separateKinds = [
    'advance',
    'set_balance',
    'batch',
    'destroy_note',
    'confirm_note',
    'career_exit',
    'hearing',
    'stage_end',
    'confirm_risk',
    'career_end',
    'finding',
  ]
  const pages: Page[] = ['办公桌', '行动', '日程', '档案', '人事与地点', '记事本', '设置']
  const navIcons = ['desk', 'action', 'calendar', 'archive', 'people', 'book', 'sliders']
  const paths: Record<string, string> = {
    desk: 'M3 5h18v12H3z M2 21h20 M8 17v4m8-4v4',
    action: 'M4 20l4-1 12-12-3-3L5 16z M13 8l3 3',
    calendar: 'M3 6h18v15H3z M7 3v6m10-6v6M3 11h18m-14 4h3m3 0h3',
    archive: 'M3 7h18v4H3z M5 12v9h14v-9 M9 15h6',
    people:
      'M3 20v-2c0-3 3-5 6-5s6 2 6 5v2m0-7c4 0 6 2 6 5v2 M12 7a3 3 0 1 1-6 0 3 3 0 0 1 6 0m4-3a3 3 0 1 1 0 6',
    book: 'M5 3h14v18H5z M8 3v18m3-13h5m-5 4h5',
    sliders: 'M3 6h6m4 0h8M3 12h12m4 0h2M3 18h2m4 0h12 M9 4v4m6 2v4M5 16v4',
  }
  const archiveTabs = ['来文材料', '项目台账', '案卷', '人物进展', '季度回顾', '经过']
  const tabHints: Record<string, string> = {
    办公桌: '已送达事项与当前安排',
    行动: '选择办理方式，或用自己的话说明意图',
    日程: '行程、承诺与时间推进',
    档案: '已取得的材料与已知经过',
    人事与地点: '已知的人物与场所',
    记事本: '随身物品与个人记录',
    设置: '模拟取向、阅读与生涯存档',
  }
  $: batchable =
    parsedStatus === 'parsed' &&
    options.length > 1 &&
    options.length <= 8 &&
    options.every((c) => {
      const a = matchAction(v, c)
      return !!a && a.enabled !== false && !c.confirm && !c.fields?.length && !separateConfirmation(a)
    })
  $: categories = ['全部', ...new Set((v?.actions ?? []).map((a) => a.category ?? '案头工作'))]
  $: visibleActions = (v?.actions ?? []).filter(
    (a) => category === '全部' || (a.category ?? '案头工作') === category,
  )
  $: selectedRecords = (v?.documents ?? []).filter((row) => row.id && compared.includes(row.id))
  $: archiveRows = !v
    ? []
    : archiveTab === '来文材料'
      ? v.documents
      : archiveTab === '项目台账'
        ? v.projects
        : archiveTab === '案卷'
          ? v.cases
          : archiveTab === '人物进展'
            ? (v.arcs ?? [])
            : reports
  $: filteredRows = (archiveRows ?? []).filter(
    (r) =>
      !archiveSearch.trim() ||
      [title(r), str(r, 'body'), str(r, 'source'), r.id, str(r, 'status')]
        .join(' ')
        .includes(archiveSearch.trim()),
  )
  $: if (v) reports = v.reports ?? v.quarter_reports ?? []
  $: date = dateAt(v?.minute ?? 0)
  const storageKey = (id: string) => 'jzs-pending-' + id
  onMount(() => {
    reduceMotion = window.matchMedia('(prefers-reduced-motion:reduce)').matches
    void api<{
      font_size: number
      sound_volume: number
      reduced_motion: boolean | null
      detailed_narration: boolean
      show_hints: boolean
    }>('/preferences')
      .then((pref) => {
        font = pref.font_size
        volume = pref.sound_volume
        reduceMotion = pref.reduced_motion ?? reduceMotion
        detailed = pref.detailed_narration
        hints = pref.show_hints
      })
      .catch((e) => (error = message(e)))
    void loadWorlds()
    return () => stopWatch?.()
  })
  $: if (typeof document !== 'undefined') {
    document.documentElement.style.fontSize = font + 'px'
    document.documentElement.classList.toggle('reduce-motion', reduceMotion)
  }
  let preferenceQueue = Promise.resolve()
  function preferences(update: Record<string, Value>) {
    preferenceQueue = preferenceQueue
      .then(() => api('/preferences', update))
      .then(() => {})
      .catch((e) => {
        error = message(e)
      })
  }
  function setFont(n: number) {
    font = n
    preferences({ font_size: n })
  }
  async function loadWorlds() {
    loading = true
    error = ''
    try {
      const [list, catalog] = await Promise.all([
        api<{ worlds: World[] }>('/worlds'),
        api<{
          starts: Array<{
            id: string
            name: string
            role: string
            age: number
            obligation: string
            days: number
          }>
        }>('/starts'),
      ])
      worlds = list.worlds
      profiles = catalog.starts.flatMap((row) => {
        const base = starts.find((s) => s.id === row.id)
        return base
          ? [
              {
                ...base,
                name: row.name,
                role: row.role,
                age: row.age,
                obligation: row.days + ' 日内' + row.obligation + '。',
              },
            ]
          : []
      })
      offline = false
    } catch (e) {
      error = message(e)
      offline = true
    } finally {
      loading = false
    }
  }
  function clearUI() {
    picked = null
    options = []
    parseNote = ''
    prompt = ''
    category = '全部'
    archiveSearch = ''
    compared = []
    compareMode = false
    lastAttempts = []
    error = ''
    notice = ''
    receipt = ''
    archiveTab = '来文材料'
    peopleTab = '人物名录'
  }
  async function goto(p: Page) {
    page = p
    lastAttempts = []
    picked = null
    notice = ''
    receipt = ''
    archiveSearch = ''
    if (p === '设置' && v) {
      draftBalance = v.policy.target
      forkRevision = v.revision
    }
    await tick()
    heading?.focus({ preventScroll: true })
    window.scrollTo(0, 0)
  }
  function enter(view: View) {
    clearUI()
    v = view
    worldName = view.world_id
    page = '办公桌'
    draftBalance = view.policy.target
    pending = null
    try {
      const raw = sessionStorage.getItem(storageKey(worldName))
      if (raw) pending = JSON.parse(raw)
    } catch {
      sessionStorage.removeItem(storageKey(worldName))
    }
    stopWatch?.()
    latestRevision = view.revision
    stopWatch = watchWorld(
      worldName,
      () => v?.revision ?? 0,
      async (revision) => {
        latestRevision = Math.max(latestRevision, revision)
        if (!busy && !pending) await synchronize(view.world_id)
      },
    )
    void tick().then(() => {
      heading?.focus({ preventScroll: true })
      window.scrollTo(0, 0)
    })
  }
  async function synchronize(id: string) {
    if (v?.world_id !== id || v.revision >= latestRevision) return
    const next = await api<View>('/worlds/' + encodeURIComponent(id))
    if (v?.world_id === id && !pending && next.revision > v.revision) {
      const policyChanged = next.policy.version !== v.policy.version
      v = next
      picked = null
      options = []
      parseNote = ''
      if (policyChanged) draftBalance = next.policy.target
      notice = '生涯档案已同步。'
      receipt = ''
    }
  }
  async function task(fn: () => Promise<void>) {
    if (busy) return
    busy = true
    error = ''
    try {
      await fn()
    } catch (e) {
      error = message(e)
    } finally {
      busy = false
    }
  }
  function create(data: { start: string; name: string; balance: string; seed?: string }) {
    void task(async () => enter(await api<View>('/worlds', data)))
  }
  function resume(id: string) {
    void task(async () => enter(await api<View>('/worlds/' + encodeURIComponent(id))))
  }
  function quit() {
    if (busy) return
    stopWatch?.()
    v = null
    clearUI()
    void loadWorlds()
  }
  function openImport() {
    inputFile.value = ''
    inputFile.click()
  }
  async function importGame(ev: Event) {
    const file = (ev.currentTarget as HTMLInputElement).files?.[0]
    if (!file) return
    await task(async () => {
      const raw = await file.text()
      try {
        JSON.parse(raw)
      } catch {
        throw new ApiError(400, '存档必须是可读取的 JSON 文件。')
      }
      enter(await importSave<View>(raw))
      notice = '存档已校验并载入。'
    })
  }
  function separateConfirmation(a: Action) {
    return (
      a.fields?.length ||
      a.confirmation_token ||
      a.confirm ||
      separateKinds.includes(a.kind) ||
      /销毁|焚烧|主动离开|确认退出|结束生涯|退休交接|死亡/.test(a.label)
    )
  }
  function matchAction(view: View | null, choice: Choice) {
    return view?.actions.find(
      (a) =>
        a.kind === choice.kind &&
        Object.keys(a.args ?? {}).every((k) => a.args?.[k] === choice.args[k]),
    )
  }
  function batch() {
    if (!batchable) return
    const attempts = options.map((choice, i) => ({
      id: 'a' + (i + 1),
      kind: choice.kind,
      args: choice.args,
      depends_on: [],
    }))
    void send('batch', { attempts })
  }
  function selectAction(a: Action, extra: Record<string, Value> = {}) {
    if (busy || pending || a.enabled === false || !v) return
    const values = {
      ...a.args,
      ...Object.fromEntries(
        (a.fields ?? []).map((f) => [f.name, f.default ?? (f.type === 'checkbox' ? false : '')]),
      ),
      ...extra,
    }
    if (separateConfirmation(a)) {
      picked = a
      formValues = values
    } else {
      void send(a.kind, values)
    }
  }
  async function send(kind: string, args: Command['args'], token: string | undefined = undefined) {
    if (!v || pending || busy) return
    const cmd: Command = {
      command_id: crypto.randomUUID(),
      expected_revision: v.revision,
      kind,
      args,
      ...(token ? { confirmation_token: token } : {}),
    }
    pending = cmd
    sessionStorage.setItem(storageKey(v.world_id), JSON.stringify(cmd))
    await deliver(cmd)
  }
  async function deliver(cmd: Command) {
    if (!v || busy) return
    const old = v,
      endpoint = '/worlds/' + encodeURIComponent(old.world_id)
    busy = true
    error = ''
    notice = ''
    receipt = ''
    picked = null
    options = []
    parseNote = ''
    try {
      const next = await api<View>(endpoint + '/commands', cmd)
      v = next
      cue(volume, next.location?.id)
      const previous = new Set(old.timeline.map((e) => e.id))
      const newEvents = (next.timeline ?? []).filter((e) => !previous.has(e.id))
      const last = newEvents.at(-1)
      lastAttempts = cmd.kind === 'batch' ? (next.last_action_results ?? []) : []
      notice =
        cmd.kind === 'batch'
          ? '已逐项核对办理结果。'
          : cmd.kind === 'set_balance'
            ? '目标取向已应用。'
            : last?.title || '操作已记录。'
      receipt = last?.text ?? ''
      draftBalance = next.policy.target
      pending = null
      sessionStorage.removeItem(storageKey(old.world_id))
      if (!categories.includes(category)) category = '全部'
    } catch (e) {
      error = message(e)
      if (
        e instanceof ApiError &&
        e.status >= 400 &&
        e.status < 500 &&
        ![408, 429].includes(e.status)
      ) {
        pending = null
        sessionStorage.removeItem(storageKey(old.world_id))
        if (e.status === 409 || cmd.confirmation_token) {
          try {
            v = await api<View>(endpoint)
            draftBalance = v.policy.target
          } catch {
            /* retain old projection with error */
          }
        }
      }
    } finally {
      busy = false
      if (v && !pending) void synchronize(v.world_id).catch(() => {})
    }
  }
  async function parseIntent() {
    if (!v || !prompt.trim() || busy) return
    await task(async () => {
      const result = await api<{ status: string; options: Choice[]; message: string }>(
        '/worlds/' + worldName + '/parse',
        { text: prompt.trim() },
      )
      parsedStatus = result.status
      options = result.options
      parseNote = result.message
      notice = ''
      receipt = ''
    })
  }
  function chooseOption(choice: Choice) {
    const found = matchAction(v, choice)
    if (found) selectAction(found, choice.args)
    else if (choice.kind === 'advance') void send(choice.kind, choice.args)
    else {
      parseNote = '当前可办理的事项已改变，请重新解析。'
      options = []
    }
  }
  function confirmPicked() {
    if (!picked) return
    const prepared = { ...formValues }
    for (const f of picked.fields ?? []) {
      if (f.type === 'number') prepared[f.name] = Number(prepared[f.name])
      if (typeof prepared[f.name] === 'string') prepared[f.name] = String(prepared[f.name]).trim()
    }
    void send(picked.kind, prepared, picked.confirmation_token)
  }
  function startForm() {
    picked = null
  }
  function diagnostic() {
    saveFile(
      new Blob(
        [
          JSON.stringify(
            {
              product: '局中事',
              page,
              world: v?.world_id ?? null,
              revision: v?.revision ?? null,
              minute: v?.minute ?? null,
              error,
            },
            null,
            2,
          ),
        ],
        { type: 'application/json' },
      ),
      '局中事-连接诊断.json',
    )
  }
  function nextStep() {
    void send('advance', {})
  }
  function exportSave() {
    if (v)
      void task(async () => {
        const blob = await download('/worlds/' + worldName + '/export')
        saveFile(blob, '局中事-' + (v?.name || '生涯') + '-r' + v?.revision + '.json')
        notice = '存档已导出。'
      })
  }
  function fork() {
    void task(async () => {
      enter(await api<View>('/worlds/' + worldName + '/fork', { revision: forkRevision }))
      notice = '已进入独立分支。'
    })
  }
  function toggleCompare(id: string) {
    compared = compared.includes(id) ? compared.filter((x) => x !== id) : [...compared.slice(-1), id]
  }
</script>

<svelte:head><title>{v ? page + ' · 局中事' : '局中事'}</title></svelte:head>
<a class="skip-link" href="#main">跳至主要内容</a>
<input
  class="visually-hidden"
  type="file"
  accept=".json,application/json"
  aria-label="导入生涯存档"
  bind:this={inputFile}
  on:change={importGame}
  tabindex="-1"
/>
{#if error}
  <aside class="error-banner" role="alert">
    <span>{error}</span><button class="link-button" on:click={diagnostic}>导出诊断</button><button
      class="plain"
      aria-label="关闭错误提示"
      on:click={() => (error = '')}>×</button
    >
  </aside>
{/if}
{#if !v}
  <Menu
    {profiles}
    {worlds}
    {busy}
    {loading}
    unavailable={offline}
    {create}
    {resume}
    importFile={openImport}
    reload={loadWorlds}
  />
{:else}
  <div class="game-shell">
    <aside class="rail">
      <button class="brand" disabled={busy} on:click={quit} aria-label="局中事 主菜单"
        ><img alt="" src="./seal.svg" />局中事</button
      >
      <div class="county-tag">江岚省 · 澄川县</div>
      <nav aria-label="生涯工作区">
        {#each pages as p, i}<button
            class:active={page === p}
            aria-current={page === p ? 'page' : undefined}
            on:click={() => goto(p)}
          >
            <svg
              viewBox="0 0 24 24"
              width="19"
              height="19"
              fill="none"
              stroke="currentColor"
              stroke-width="1.55"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"><path d={paths[navIcons[i]]} /></svg
            >
            <span>{p}</span>
          </button>{/each}
      </nav>
      <div class="rail-bottom">
        <div class="identity-mark">{v.name.slice(-1)}</div>
        <div>
          <b>{v.name}</b><small
            >{str(v.player, 'role') || starts.find((s) => s.id === v?.start)?.role}</small
          >
        </div>
      </div>
    </aside>
    <div class="workspace">
      <header class="desk-bar">
        <div class="crumb">生涯档案 <span>/</span> {page}</div>
        <div class="clock">
          <span class="clock-dot"></span> 第 {v.quarter} 季 <i>／</i> 第 {date.day} 天
          <b>{date.time}</b>
        </div>
      </header>
      <main class="workspace-main" id="main">
        <div class="page-heading">
          <div>
            <p class="kicker">{str(v.location, 'name') || '澄川县'} · {v.name}</p>
            <h1 tabindex="-1" bind:this={heading}>{page === '办公桌' ? '我的办公桌' : page}</h1>
          </div>
          {#if hints}<span class="page-hint">{tabHints[page]}</span>{/if}
        </div>
        {#if pending}<div class="feedback pending" role="status">
            <span
              ><strong>{busy ? '正在确认结果…' : '上次操作仍待确认'}</strong>
              {busy ? '' : '重试将沿用同一条命令。'}</span
            >{#if !busy}<button class="button compact" on:click={() => pending && deliver(pending)}
                >核对并重试</button
              >{/if}
          </div>{/if}
        {#if notice}<div class="feedback" role="status">
            <span
              ><strong>{notice}</strong>{#if receipt && receipt !== notice}<span>{receipt}</span
                >{/if}</span
            ><button class="plain close" aria-label="收起回执" on:click={() => (notice = '')}>×</button>
          </div>{/if}
        {#if notice && lastAttempts.length}<ol class="batch-results">
            {#each lastAttempts as r}<li>
                <strong>{attemptLabels[r.status] ?? r.status}</strong>
                · {r.text}
              </li>{/each}
          </ol>{/if}
        {#if v.ending}<section class="end-card">
            <p class="kicker">生涯终章</p>
            <h2>{title(v.ending)}</h2>
            <p>{str(v.ending, 'description', 'reason', 'text')}</p>
            <button
              class="link-button"
              on:click={() => {
                archiveTab = '经过'
                goto('档案')
              }}>回看已知经过 →</button
            >
          </section>{/if}
        {#if page === '办公桌'}
          <div class="desk-grid">
            <div class="column">
              <section class="paper lead-paper">
                <div class="section-title">
                  <div>
                    <p class="kicker">桌面来件</p>
                    <h2>当前事项</h2>
                  </div>
                  <button class="link-button" on:click={() => goto('档案')}>打开档案 →</button>
                </div>
                {#if v.timeline?.length && v.revision <= 1}{@const firstTask = v.timeline.find(
                    (e) => e.title === '今日待办',
                  )}
                  {#if firstTask}<p class="desk-brief">{firstTask.text}</p>{/if}{/if}
                {#if v.documents?.length}{@const doc =
                    v.revision <= 1
                      ? (v.documents.find((d) => d.id === 'D01-r1') ?? v.documents[0])
                      : v.documents[v.documents.length - 1]}
                  <article class="letter">
                    <div class="letter-meta">
                      <span>{str(doc, 'kind') || '来文材料'}</span><span>{doc.id}</span>
                    </div>
                    <h3>{title(doc)}</h3>
                    <div class="letter-source">
                      {str(doc, 'source')}
                      {str(doc, 'date') ? ' · ' + str(doc, 'date') : ''}
                    </div>
                    <p>{str(doc, 'body', 'description', 'summary')}</p>
                    {#if str(doc, 'scope')}<small>涉及范围　{str(doc, 'scope')}</small>{/if}
                  </article>
                {:else}<p class="empty">目前没有可查阅的来文。</p>{/if}
                {#if v.actions?.length}<div class="button-row">
                    <button class="button primary" on:click={() => goto('行动')}
                      >选择办理方式 <span aria-hidden="true">→</span></button
                    >
                  </div>{/if}
              </section>
              <section class="paper">
                <div class="section-title">
                  <h2>近期经过</h2>
                  <button
                    class="link-button"
                    on:click={() => {
                      archiveTab = '经过'
                      goto('档案')
                    }}>查看全部 →</button
                  >
                </div>
                <Timeline {detailed} entries={(v.timeline ?? []).slice(-3)} />
              </section>
            </div>
            <div class="column">
              <section class="paper calendar-card">
                <div class="section-title"><h2>下一项日程</h2></div>
                {#if v.appointments?.length}{@const a = v.appointments[0]}<span class="date-big"
                    >{dateAt(a.due).time}</span
                  ><small>第 {dateAt(a.due).quarter} 季 · 第 {dateAt(a.due).day} 天</small>
                  <h3>{a.title}</h3>{:else}<p class="empty">暂时没有已知的安排。</p>{/if}
                {#if !v.ending}<button
                    class="button compact full"
                    disabled={busy || !!pending}
                    on:click={nextStep}>前往下一事项 →</button
                  >{/if}
              </section>
              <section class="paper">
                <div class="section-title"><h2>在任职责</h2></div>
                <dl class="sheet">
                  <dt>当前岗位</dt>
                  <dd>{str(v.player, 'role', 'position')}</dd>
                  <dt>所在地点</dt>
                  <dd>{str(v.location, 'name')}</dd>
                  {#if v.commitments?.length}<dt>已有约定</dt>
                    <dd>{title(v.commitments[0])}</dd>{/if}
                </dl>
                <button class="link-button" on:click={() => goto('日程')}>查看履约记录 →</button>
              </section>
              <section class="paper">
                <div class="section-title"><h2>当前负担</h2></div>
                <dl class="sheet">
                  <dt>疲劳</dt>
                  <dd>{str(v.player, 'fatigue')}</dd>
                  <dt>压力</dt>
                  <dd>{str(v.player, 'pressure')}</dd>
                  <dt>韧性</dt>
                  <dd>{str(v.player, 'resilience')}</dd>
                  <dt>家庭安排</dt>
                  <dd>{str(v.family, 'care') || '暂无记录'}</dd>
                  <dt>培训计划</dt>
                  <dd>{str(v.family, 'training') || '暂无记录'}</dd>
                </dl>
              </section>
            </div>
          </div>
        {:else if page === '行动'}
          <div class="desk-grid">
            <section class="paper">
              <div class="section-title">
                <h2>可办理事项</h2>
                <small>{v.actions?.length ?? 0} 项</small>
              </div>
              <label class="filter"
                >办理类别<select bind:value={category}
                  >{#each categories as c}<option value={c}>{c}</option>{/each}</select
                ></label
              >
              {#if v.busy}<div class="feedback">
                  <span
                    ><strong>{str(v.busy, 'title')}</strong>{typeof v.busy.due === 'number'
                      ? stamp(v.busy.due) + ' 预计完成'
                      : ''}</span
                  ><button class="button compact" disabled={busy || !!pending} on:click={nextStep}
                    >前往下一事项</button
                  >
                </div>{/if}
              <ActionList actions={visibleActions} select={selectAction} busy={busy || !!pending} />
            </section>
            <section class="paper align-start">
              <div class="section-title"><h2>说明意图</h2></div>
              <form on:submit|preventDefault={parseIntent}>
                <label class="field"
                  >想怎么处理<textarea
                    rows="4"
                    maxlength="1000"
                    bind:value={prompt}
                    on:input={() => {
                      options = []
                      parseNote = ''
                      parsedStatus = ''
                    }}
                    placeholder="例如：我想比对两份报告。"
                  ></textarea></label
                ><button class="button compact" disabled={busy || !prompt.trim() || !!v.ending}
                  >解析意图</button
                >
              </form>
              {#if parseNote}<p class="helper" role="status">
                  {batchable ? '请核对每项行动的内容和代价。可以逐项办理，也可依次提交。' : parseNote}
                </p>{/if}
              {#each options as option, i}
                {@const visible = matchAction(v, option)}
                <button
                  class="choice"
                  disabled={busy || !!pending}
                  on:click={() => chooseOption(option)}
                >
                  <strong>{options.length > 1 ? i + 1 + ' · ' : ''}选择「{option.label}」 →</strong>
                  {#if visible?.description}<small>{visible.description}</small>{/if}
                  {#if option.cost || visible?.cost}<small
                      >办理代价 · {option.cost ?? visible?.cost}</small
                    >{/if}
                </button>
              {/each}
              {#if batchable}<button
                  class="button primary"
                  disabled={busy || !!pending}
                  on:click={batch}>按顺序提交</button
                >{/if}
            </section>
          </div>
        {:else if page === '日程'}
          <div class="desk-grid">
            <div class="column">
              <section class="paper">
                <div class="section-title">
                  <h2>已知行程</h2>
                  <Recap worldId={v.world_id} {detailed} />
                </div>
                {#if v.appointments?.length}<ol class="agenda">
                    {#each v.appointments as a}<li>
                        <time>{stamp(a.due)}</time><strong>{a.title}</strong>
                      </li>{/each}
                  </ol>{:else}<p class="empty">暂时没有已知的安排。</p>{/if}
              </section>
              <section class="paper">
                <div class="section-title"><h2>已有承诺</h2></div>
                <Records rows={v.commitments ?? []} empty="还没有需要履行的约定。" />
              </section>
            </div>
            <section class="paper align-start">
              <div class="section-title"><h2>推进时间</h2></div>
              <p class="helper">每个游戏日从 09:00 起算。阅读与整理档案时，时间暂停。</p>
              <label class="field"
                >推进时长<select bind:value={advanceMinutes}
                  ><option value={60}>1 小时</option><option value={480}>8 小时</option><option
                    value={1440}>1 天</option
                  ><option value={10080}>7 天</option><option value={129600}>90 天</option></select
                ></label
              >
              <div class="button-stack">
                <button
                  class="button primary"
                  disabled={busy || !!pending || !!v.ending}
                  on:click={() => send('advance', { minutes: advanceMinutes })}>按时长推进</button
                ><button class="button" disabled={busy || !!pending || !!v.ending} on:click={nextStep}
                  >前往下一事项</button
                >
              </div>
            </section>
          </div>
        {:else if page === '档案'}
          <section class="paper">
            <div class="tabs" aria-label="档案分类">
              {#each archiveTabs as tab}<button
                  class:active={archiveTab === tab}
                  aria-pressed={archiveTab === tab}
                  on:click={() => {
                    archiveTab = tab
                    archiveSearch = ''
                    compareMode = false
                  }}>{tab}</button
                >{/each}
            </div>
            {#if archiveTab === '经过'}<div class="section-title">
                <h2>已知经过</h2>
                <Recap worldId={v.world_id} {detailed} />
              </div>
              <History worldId={v.world_id} revision={v.revision} {detailed}/>
            {:else}
              {#if archiveTab === '项目台账' && v.finances}<div class="ledger">
                  {#each [['年度可用', 'annual_remaining'], ['季度可用', 'quarter_remaining'], ['已预留', 'reserved'], ['已支付', 'paid'], ['可用工作组', 'groups_available']] as [label, key]}
                    <div>
                      <small>{label}</small><strong
                        >{key === 'groups_available'
                          ? String(v.finances[key]) + ' 组'
                          : (Number(v.finances[key]) / 1000000).toLocaleString('zh-CN') +
                            ' 万元'}</strong
                      >
                    </div>
                  {/each}
                </div>{/if}
              {#if archiveTab === '项目台账' && v.offers?.length}<h3 class="subhead">已提出的方案</h3>
                <Records rows={v.offers} />{/if}
              <div class="search-row">
                <input
                  type="search"
                  aria-label="搜索档案"
                  placeholder="按名称、编号或内容查找"
                  bind:value={archiveSearch}
                />
                {#if archiveTab === '来文材料'}<button
                    class="button compact"
                    aria-pressed={compareMode}
                    on:click={() => {
                      compareMode = !compareMode
                      compared = []
                    }}>{compareMode ? '退出对照' : '并排对照'}</button
                  >{/if}
              </div>
              {#if archiveTab === '来文材料' && compareMode}
                <div class="compare-options">
                  {#each filteredRows as doc}<label
                      ><input
                        type="checkbox"
                        checked={!!doc.id && compared.includes(doc.id)}
                        on:change={() => doc.id && toggleCompare(doc.id)}
                      />{title(doc)}</label
                    >{/each}
                </div>
                <div class="compare">
                  {#each selectedRecords as r}<article class="letter">
                      <p class="kicker">{str(r, 'kind')} · {r.id}</p>
                      <h3>{title(r)}</h3>
                      <p>{str(r, 'body')}</p>
                      <small>{str(r, 'source')} · {str(r, 'date')} · {str(r, 'scope')}</small>
                    </article>{/each}
                </div>
                <WorkingNote
                  write={v.actions.find((a) => a.kind === 'write_note')}
                  select={selectAction}
                />
              {:else}<Records
                  rows={filteredRows}
                  empty={archiveSearch ? '没有匹配的记录。' : '目前没有已送达的记录。'}
                />{/if}
            {/if}
          </section>
        {:else if page === '人事与地点'}
          <section class="paper">
            <div class="tabs">
              {#each ['人物名录', '场所'] as t}<button
                  class:active={peopleTab === t}
                  aria-pressed={peopleTab === t}
                  on:click={() => (peopleTab = t)}>{t}</button
                >{/each}
            </div>
            {#if peopleTab === '人物名录'}<Records rows={v.people ?? []} />
            {:else}<p class="helper">
                当前位置 · {str(v.location, 'name')}
                {str(v.location, 'description')}
              </p>
              <Sites
                locations={v.locations ?? []}
                actions={v.actions ?? []}
                current={v.location?.id}
                select={selectAction}
                busy={busy || !!pending}
              />{/if}
          </section>
        {:else if page === '记事本'}
          <div class="desk-grid">
            <section class="paper">
              <div class="section-title">
                <h2>笔记正文</h2>
                <small>{v.notebook?.accessible ? '可翻阅' : '当前不可翻阅'}</small>
              </div>
              {#if v.notebook?.accessible}
                {#if v.notebook?.entries?.length}<div class="journal">
                    {#each v.notebook.entries as e}<article>
                        {#if typeof e.minute === 'number'}<time>{stamp(e.minute)}</time>{/if}
                        <p>{str(e, 'text', 'body')}</p>
                      </article>{/each}
                  </div>{:else}<p class="empty">记事本里还没有记录。</p>{/if}
              {:else}<p class="empty">需要取得实体记事本后才能阅读正文。</p>{/if}
            </section>
            <section class="paper align-start">
              <div class="section-title"><h2>管理记事本</h2></div>
              <p class="helper">
                所在位置 · {v.notebook?.location === 'player'
                  ? '随身携带'
                  : v.notebook?.location === 'destroyed'
                    ? '原件已销毁'
                    : (v.locations?.find((l) => l.id === v?.notebook?.location)?.name ??
                      v.notebook?.location ??
                      '未知')}
              </p>
              <ActionList
                actions={(v.actions ?? []).filter((a) =>
                  /笔记|记事本|本子|notebook|note_/.test(a.kind + a.label + a.category),
                )}
                select={selectAction}
                busy={busy || !!pending}
              />
            </section>
          </div>
        {:else if page === '设置'}
          <div class="desk-grid">
            <div class="column">
              <section class="paper">
                <div class="section-title"><h2>模拟取向</h2></div>
                <div class="stat-pair">
                  <div><small>当前有效取向</small><strong>{v.policy.effective.toFixed(6)}</strong></div>
                  <div><small>已确认的目标</small><strong>{v.policy.target}</strong></div>
                </div>
                <p class="helper">
                  {Math.abs(v.policy.effective - Number(v.policy.target)) > 1e-9
                    ? '过渡中，预计在' + stamp(v.policy.transition_end) + '达到目标。'
                    : '当前取向已生效。'} 新目标将在 240 游戏分钟内逐步生效。
                </p>
                <Balance bind:value={draftBalance} prefix="settings" />
                {#if v.policy.trajectory?.length}<details class="extra">
                    <summary>取向变更记录</summary>
                    <ol class="agenda">
                      {#each [...v.policy.trajectory].reverse() as entry}<li>
                          <time>{stamp(entry.minute)}</time><span
                            >{entry.start.toFixed(6)} → {entry.target}</span
                          >
                        </li>{/each}
                    </ol>
                  </details>{/if}
                <button
                  class="button primary"
                  disabled={busy ||
                    !!pending ||
                    !balanceString(draftBalance) ||
                    balanceString(draftBalance) === v.policy.target ||
                    !!v.ending}
                  on:click={() =>
                    send('set_balance', {
                      balance: balanceString(draftBalance)!,
                      expected_policy_version: v!.policy.version,
                      parameter_package_hash: v!.policy.parameter_package_hash,
                    })}>应用目标取向</button
                >
              </section>
              <section class="paper">
                <div class="section-title"><h2>阅读与声音</h2></div>
                <label class="field"
                  >正文字号<select
                    value={font}
                    on:change={(e) => setFont(Number(e.currentTarget.value))}
                    >{#each [14, 16, 18, 20, 22] as n}<option value={n}>{n} px</option>{/each}</select
                  ></label
                ><label class="check"
                  ><input
                    type="checkbox"
                    bind:checked={reduceMotion}
                    on:change={(e) => preferences({ reduced_motion: e.currentTarget.checked })}
                  />减少动效</label
                ><label class="check"
                  ><input
                    type="checkbox"
                    bind:checked={detailed}
                    on:change={(e) => preferences({ detailed_narration: e.currentTarget.checked })}
                  />展开经过正文</label
                ><label class="check"
                  ><input
                    type="checkbox"
                    bind:checked={hints}
                    on:change={(e) => preferences({ show_hints: e.currentTarget.checked })}
                  />显示页面操作提示</label
                ><label class="field"
                  >操作提示音 · {volume === 0 ? '静音' : volume + '%'}<input
                    aria-label="操作提示音音量"
                    type="range"
                    min="0"
                    max="100"
                    step="1"
                    bind:value={volume}
                    on:change={(e) => {
                      const value = Number(e.currentTarget.value)
                      preferences({ sound_volume: value })
                      cue(value, v?.location?.id)
                    }}
                  /></label
                >
              </section>
            </div>
            <section class="paper align-start">
              <div class="section-title"><h2>生涯存档</h2></div>
              <p class="helper">已保存至修订 {v.revision}。导出文件可用于备份或载入同一段生涯。</p>
              {#if v.parent}<p class="helper">当前生涯分支自原档案修订 {v.parent.revision}。</p>{/if}
              <div class="button-stack">
                <button class="button" on:click={exportSave} disabled={busy}>导出当前存档</button
                ><button class="button" on:click={openImport} disabled={busy}>导入存档</button>
              </div>
              <details class="extra">
                <summary>从历史修订分支</summary>
                <form on:submit|preventDefault={fork}>
                  <label class="field"
                    >分支起点<input
                      type="number"
                      min="0"
                      max={v.revision}
                      required
                      bind:value={forkRevision}
                    /></label
                  ><button class="button compact" disabled={busy}>建立独立分支</button>
                </form>
              </details>
              <button class="link-button" on:click={quit} disabled={busy}>返回主菜单 →</button>
            </section>
          </div>
        {/if}
      </main>
    </div>
  </div>
{/if}
{#if picked}
  <Dialog title={picked.label} onclose={startForm}
    ><form on:submit|preventDefault={confirmPicked}>
      <p>{picked.description}</p>
      {#if picked.cost}<p class="helper">办理代价 · {picked.cost}</p>{/if}
      {#each picked.fields ?? [] as f}<label class="field"
          >{f.label}
          {#if f.type === 'select'}<select bind:value={formValues[f.name]} required={f.required}
              >{#each f.options ?? [] as o}<option value={typeof o === 'string' ? o : o.value}
                  >{typeof o === 'string' ? o : o.label}</option
                >{/each}</select
            >
          {:else if f.type === 'number'}<input
              type="number"
              bind:value={formValues[f.name]}
              min={f.min}
              max={f.max}
              required={f.required}
            />
          {:else if f.type === 'checkbox'}<input
              type="checkbox"
              checked={!!formValues[f.name]}
              on:change={(e) => (formValues[f.name] = e.currentTarget.checked)}
            />
          {:else}<textarea
              rows="3"
              bind:value={formValues[f.name]}
              required={f.required}
              maxlength={f.maxLength ?? 1000}
            ></textarea>{/if}</label
        >{/each}
      {#if typeof picked.confirm === 'string'}<p class="helper">{picked.confirm}</p>{/if}
      <div class="dialog-foot">
        <button class="button" type="button" on:click={startForm}>取消</button><button
          class="button primary"
          disabled={busy}>确认办理</button
        >
      </div>
    </form></Dialog
  >
{/if}
