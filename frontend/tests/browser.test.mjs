import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { after, test } from 'node:test'
import { startBrowserFixture } from './browser-engine.mjs'

const fixture = await startBrowserFixture()
const { browser, profile, session, address } = fixture
after(() => fixture.close())

async function screen(page, name) {
  if (process.env.JZS_SCREENSHOT_DIR)
    await page.screenshot({ path: join(process.env.JZS_SCREENSHOT_DIR, name + '.png'), fullPage: true })
}
async function checkScene(page, name, resource) {
  const scene = page.locator('figure.scene')
  await scene.locator('figcaption').getByText(name, { exact: true }).waitFor()
  const image = scene.locator('img')
  const source = await image.evaluate(async (el) => {
    await el.decode()
    return el.naturalWidth > 0 && el.naturalHeight > 0 ? el.currentSrc : ''
  })
  assert.equal(source, new URL('/scenes/' + resource, address).href)
}
async function navigate(page, label) {
  await page.getByRole('navigation').getByRole('button', { name: label, exact: true }).click()
}
async function current(page) {
  return page.evaluate(async () => {
    const headers = { Authorization: 'Bearer ' + sessionStorage.getItem('jzs-local-session') }
    const { worlds } = await (await fetch('/api/worlds', { headers })).json()
    return (await fetch('/api/worlds/' + worlds[0].id, { headers })).json()
  })
}
async function openCareer(page, wide = true) {
  // A second visit that only adds the session fragment does not remount the app.
  if (new URL(page.url()).origin === new URL(session).origin) await page.reload()
  else await page.goto(session)
  if (wide) await screen(page, 'cover')
  await enterCareerMenu(page)
  await page.getByRole('button', { name: '建立生涯' }).click()
  assert.equal(await page.getByRole('radio').count(), 8)
  await page.getByRole('radio', { name: /专业技术转任/ }).check()
  const name = page.getByLabel('角色称谓')
  assert.equal(await name.inputValue(), '新任联络员')
  assert.ok(await page.getByRole('button', { name: '进入办公室' }).isEnabled())
  await name.fill('')
  await name.focus()
  await page.keyboard.type('Lin')
  assert.equal(await name.inputValue(), 'Lin')
  await name.fill('')
  await page.keyboard.insertText('林岑')
  assert.equal(await name.inputValue(), '林岑')
  await page.getByLabel('真实性—可玩性平衡', { exact: true }).fill('0.371826')
  await page.getByText('世界种子（可选）').click()
  await page.getByRole('textbox', { name: '种子', exact: true }).fill('classic')
  if (wide) await screen(page, 'create')
  await page.getByRole('button', { name: '进入办公室' }).click()
  await page.getByRole('heading', { name: '我的办公桌' }).waitFor()
}
async function enterCareerMenu(page) {
  await page.getByRole('button', { name: '生涯模式', exact: true }).click()
}

test('desktop updates download in the background and keep both game modes available', async () => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } })
  try {
    const page = await context.newPage()
    const state = {
      current_version: '4.2.0', latest_version: null, phase: 'offline', supported: true,
      automatic: true, message: '无法连接发布服务。请稍后重试。',
    }
    let checks = 0
    const preferenceWrites = []
    await page.route(/\/api\/update(?:\/|$)/, async (route) => {
      const req = route.request()
      const path = new URL(req.url()).pathname
      if (path === '/api/update/preferences') {
        preferenceWrites.push(req.postDataJSON())
        state.automatic = req.postDataJSON().automatic
      } else if (path === '/api/update/check') {
        checks++
        Object.assign(state, { phase: 'downloading', latest_version: '4.3.0', downloaded_bytes: 16, total_bytes: 64 })
      } else if (state.phase === 'downloading') {
        state.phase = 'ready'
      }
      await route.fulfill({ json: state })
    })
    await page.goto(session)
    await page.getByText('暂时连不上更新服务').waitFor()
    await enterCareerMenu(page)
    await page.getByRole('button', { name: '模式选择', exact: true }).click()
    await page.getByText('更新设置').click()
    const automatic = page.getByRole('checkbox', { name: '自动检查并下载更新' })
    assert.ok(await automatic.isChecked())
    await automatic.uncheck()
    await page.getByRole('button', { name: '检查更新', exact: true }).click()
    const progress = page.getByRole('progressbar', { name: '下载进度' })
    await progress.waitFor()
    assert.equal(await progress.getAttribute('value'), '16')
    await page.getByText('新版 4.3.0 已就绪，下次打开自动更新').waitFor()
    assert.deepEqual(preferenceWrites, [{ automatic: false }])
    assert.equal(checks, 1)
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
    await page.getByRole('button', { name: '历史主角模式' }).click()
    await page.getByRole('button', { name: '开始长篇' }).waitFor()
    await page.getByRole('button', { name: '模式选择', exact: true }).click()
    await page.getByText('新版 4.3.0 已就绪，下次打开自动更新').waitFor()
    await page.getByText('更新设置').click()
    assert.equal(await automatic.isChecked(), false)
    assert.equal(checks, 1)
    state.supported = false
    await Promise.all([
      page.waitForResponse((r) => r.url().endsWith('/api/update')),
      page.reload(),
    ])
    assert.equal(await page.getByRole('contentinfo', { name: '游戏更新' }).count(), 0)
  } finally {
    await context.close()
  }
})

test('the first county desk decision sends the technician and shows her actual finding', async () => {
  const context = await browser.newContext()
  try {
    const page = await context.newPage()
    await openCareer(page, false)
    const desk = page.locator('.passage-request')
    await desk.getByRole('heading', { name: '今天还得绕南渠吗？' }).waitFor()
    const view = await current(page)
    assert.match(await desk.innerText(), /吴静禾/)
    assert.ok((await desk.innerText()).includes(view.documents.find((doc) => doc.id === 'D01-r1').body))
    const submit = async (action) => {
      const [response] = await Promise.all([
        page.waitForResponse((r) => r.url().endsWith('/commands') && r.request().method() === 'POST'),
        action.click(),
      ])
      assert.equal(response.status(), 200)
      return response.json()
    }
    await submit(desk.getByRole('button', { name: /申请检查临时便道/ }))
    await desk.getByText(/程向晚去验路了/).waitFor()
    const due = page.getByRole('button', { name: /前往下一事项/ })
    let after
    for (let i = 0; i < 6; i++) {
      after = await submit(due)
      if (after.documents.some((doc) => doc.kind === '检查记录' && doc.scope === '西段便道')) break
    }
    const finding = after.documents.find((doc) => doc.kind === '检查记录' && doc.scope === '西段便道')
    assert.ok(finding, 'technician delivered the inspection record')
    await desk.getByText(finding.body, { exact: false }).waitFor()
    assert.ok(await desk.getByRole('button', { name: /报请批准开放|安排便道整改/ }).isEnabled())
  } finally {
    await context.close()
  }
})
async function noOverflow(page) {
  assert.ok(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    'page exceeds viewport width',
  )
}

test('sound switch, archive paper and saved mute', { timeout: 30000 }, async () => {
  const ctx = await browser.newContext()
  const page = await ctx.newPage()
  await ctx.addInitScript(() => {
    window.testCues = []
    // The real nodes are wired only to an offline graph, never to a speaker.
    window.AudioContext = class extends OfflineAudioContext {
      constructor() { super(1, 24000, 24000) }
      get state() { return this.active ? 'running' : 'suspended' }
      async resume() { this.active = true }
      async suspend() { this.active = false }
      createBufferSource() {
        const voice = super.createBufferSource()
        const start = voice.start.bind(voice)
        voice.start = (...args) => {
          window.testCues.push({ ms: Math.round(voice.buffer.duration * 1000), at: performance.now() })
          start(...args)
        }
        return voice
      }
    }
  })
  const toggle = page.getByRole('switch', { name: '游戏音效' })
  const recorded = () => page.evaluate(() => window.testCues.map(cue => cue.ms))
  const cooldown = () => page.waitForFunction(() => performance.now() - window.testCues.at(-1).at > 450)
  async function clickSwitch() {
    const saved = page.waitForResponse(r => r.url().endsWith('/api/preferences') && r.request().method() === 'POST')
    await toggle.click()
    return (await (await saved).json()).sound_volume
  }
  try {
    await openCareer(page, false)
    assert.equal(await toggle.getAttribute('aria-checked'), 'false')
    assert.deepEqual(await recorded(), [])
    assert.ok((await clickSwitch()) > 0)
    assert.equal(await toggle.getAttribute('aria-checked'), 'true')
    assert.deepEqual(await recorded(), [220]) // Incoming-folder preview.
    await navigate(page, '档案')
    const sheet = page.locator('details.record').first().locator('summary')
    await cooldown()
    await sheet.click()
    assert.deepEqual(await recorded(), [220, 210]) // Opening an actual document.
    assert.equal(await clickSwitch(), 0)
    await cooldown()
    await sheet.click() // Close, then open the same document while muted.
    await sheet.click()
    assert.deepEqual(await recorded(), [220, 210])
    const restored = page.waitForResponse(r => r.url().endsWith('/api/preferences') && r.request().method() === 'GET')
    await page.reload()
    assert.equal((await (await restored).json()).sound_volume, 0)
    await enterCareerMenu(page)
    await page.getByRole('button', { name: '继续生涯' }).click()
    assert.equal(await toggle.getAttribute('aria-checked'), 'false')
    assert.deepEqual(await recorded(), [])
  } finally {
    // The browser suite shares one throwaway engine profile across contexts.
    const token = new URLSearchParams(new URL(session).hash.slice(1)).get('session')
    try {
      await ctx.request.post(address + '/api/preferences', {
        headers: { Authorization: 'Bearer ' + token }, data: { sound_volume: 0 },
      })
    } finally {
      await ctx.close()
    }
  }
})

test(
  'offline desktop journey, provenance, deterministic retry, real save and restoration',
  { timeout: 120000 },
  async () => {
    const context = await browser.newContext({
      viewport: { width: 1240, height: 820 },
      acceptDownloads: true,
    })
    const page = await context.newPage(),
      external = [],
      errors = []
    page.on('pageerror', (e) => errors.push(String(e)))
    await page.route('**/*', (r) => {
      const url = new URL(r.request().url())
      if (url.protocol.startsWith('http') && url.origin !== address) {
        external.push(url.origin)
        return r.abort()
      }
      return r.continue()
    })
    try {
      await openCareer(page)
      assert.equal(new URL(page.url()).hash, '')
      await screen(page, 'desk')
      const first = await current(page)
      assert.equal(first.policy.target, '0.371826')
      assert.equal(first.player.role, '县技术审查岗')
      await navigate(page, '档案')
      await page.getByRole('button', { name: '并排对照' }).click()
      const selections = page.locator('.compare-options input')
      await selections.nth(0).check()
      await selections.nth(1).check()
      assert.equal(await page.locator('.compare .letter').count(), 2)
      await navigate(page, '行动')
      await page.getByLabel('想怎么处理').fill('全听汇报然后暂缓答复')
      await page.getByRole('button', { name: '解析意图' }).click()
      await page.getByRole('button', { name: /选择「听完整项目汇报」/ }).waitFor()
      assert.equal((await current(page)).revision, first.revision)
      await page.getByRole('button', { name: /选择「暂缓答复」/ }).click()
      await page.getByRole('status').filter({ hasText: /答复/ }).waitFor()
      await navigate(page, '记事本')
      await page.getByRole('button', { name: /写入实体记事本/ }).click()
      await page.getByLabel('记录原文').fill('先查统计范围与日期。')
      await page.keyboard.press('Escape')
      assert.equal((await current(page)).notebook.entries.length, 0)
      await page.getByRole('button', { name: /写入实体记事本/ }).click()
      await page.getByLabel('记录原文').fill('先查统计范围与日期。')
      let attempted
      const failure = async (route) => {
        const req = route.request()
        if (!req.url().endsWith('/commands')) return route.fallback()
        attempted = req.postDataJSON()
        await route.fetch()
        await route.abort('connectionreset')
      }
      await page.route('**/commands', failure)
      await page.getByRole('button', { name: '确认办理' }).click()
      await page.getByRole('button', { name: '核对并重试' }).waitFor()
      await page.unroute('**/commands', failure)
      let retried
      page.once('request', (r) => {
        if (r.url().endsWith('/commands')) retried = r.postDataJSON()
      })
      await page.getByRole('button', { name: '核对并重试' }).click()
      await page.locator('.journal').getByText('先查统计范围与日期。').waitFor()
      assert.deepEqual(retried, attempted)
      assert.equal((await current(page)).notebook.entries.length, 1)
      await navigate(page, '设置')
      await page.getByLabel('真实性—可玩性平衡', { exact: true }).fill('0.863527')
      await page.getByRole('button', { name: '应用目标取向' }).click()
      await page.getByText('目标取向已应用。', { exact: true }).waitFor()
      let view = await current(page)
      assert.equal(view.policy.target, '0.863527')
      assert.equal(view.policy.effective, 0.371826)
      await navigate(page, '日程')
      await page.getByLabel('推进时长').selectOption({ label: '1 小时' })
      await page.getByRole('button', { name: '按时长推进' }).click()
      await page.waitForFunction(() => document.querySelector('.clock b')?.textContent === '10:00')
      view = await current(page)
      assert.ok(view.policy.effective > 0.371826 && view.policy.effective < 0.863527)
      await navigate(page, '设置')
      const dl = page.waitForEvent('download')
      await page.getByRole('button', { name: '导出当前存档' }).click()
      const file = await dl,
        saved = join(profile, 'export.json')
      await file.saveAs(saved)
      const data = JSON.parse(await readFile(saved, 'utf8'))
      assert.ok(Object.keys(data).length)
      await page.getByRole('button', { name: '返回主菜单' }).click()
      await page.getByRole('button', { name: '继续生涯' }).click()
      await page.getByRole('heading', { name: '我的办公桌' }).waitFor()
      assert.equal((await current(page)).minute, view.minute)
      await page.locator('input[type=file]').setInputFiles(saved)
      await page.getByText('存档已校验并载入。').waitFor()
      await navigate(page, '记事本')
      await page.locator('.journal').getByText('先查统计范围与日期。').waitFor()
      assert.deepEqual(errors, [])
      assert.deepEqual(external, [])
    } finally {
      await context.close()
    }
  },
)

test('compact layout, input and keyboard on every primary section', { timeout: 60000 }, async () => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } })
  const page = await context.newPage()
  try {
    await openCareer(page, false)
    await checkScene(page, '办公室', 'office.webp')
    await screen(page, 'mobile-desk')
    await noOverflow(page)
    for (const label of ['行动', '日程', '档案', '人事与地点', '记事本', '设置']) {
      await navigate(page, label)
      await noOverflow(page)
      assert.equal(await page.locator('h1').innerText(), label)
      if (label === '行动') {
        const action = page.locator('.action-list button:enabled').first()
        assert.ok(await action.evaluate((button) => {
          const rect = button.getBoundingClientRect()
          const target = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2)
          return button.contains(target)
        }), 'the first available action must be directly reachable in the mobile viewport')
      }
    }
    await page.getByLabel('正文字号').selectOption('20')
    assert.equal(await page.evaluate(() => getComputedStyle(document.documentElement).fontSize), '20px')
    await noOverflow(page)
    const menu = page.getByRole('button', { name: '返回主菜单' })
    await menu.focus()
    await page.keyboard.press('Enter')
    await page.getByRole('heading', { name: '生涯档案' }).waitFor()
  } finally {
    await context.close()
  }
})

test(
  'scene travel, quarter archive, terminal recap and continued play from a historical fork',
  { timeout: 90000 },
  async () => {
    const context = await browser.newContext({ viewport: { width: 1080, height: 740 } })
    const page = await context.newPage()
    async function doClick(button) {
      const committed = page.waitForResponse(
        (r) => r.url().endsWith('/commands') && r.request().method() === 'POST',
      )
      await button.click()
      const response = await committed
      assert.equal(response.status(), 200)
      return response.json()
    }
    try {
      await openCareer(page, false)
      await navigate(page, '人事与地点')
      await page.getByRole('button', { name: '场所', exact: true }).click()
      assert.equal(await page.locator('.site-card').count(), 9)
      const dest = page
        .locator('.site-card')
        .filter({ has: page.getByRole('heading', { name: /工地|现场/ }) })
        .first()
      await doClick(dest.getByRole('button', { name: /前往/ }))
      await navigate(page, '日程')
      const arrived = await doClick(page.getByRole('button', { name: '前往下一事项', exact: true }))
      assert.equal(arrived.location.id, 'L02')
      await navigate(page, '行动')
      await checkScene(page, arrived.location.name, 'canal.webp')
      await screen(page, 'canal-actions')
      await doClick(page.getByRole('button', { name: /沿西段核对现场/ }))
      await navigate(page, '日程')
      await doClick(page.getByRole('button', { name: '前往下一事项', exact: true }))
      await navigate(page, '档案')
      await page.getByRole('searchbox').fill('现场')
      assert.ok((await page.locator('.record summary').count()) > 0)
      await navigate(page, '人事与地点')
      await page.getByRole('button', { name: '场所', exact: true }).click()
      await doClick(
        page
          .locator('.site-card')
          .filter({ has: page.getByRole('heading', { name: '办公室', exact: true }) })
          .getByRole('button', { name: /前往/ }),
      )
      await navigate(page, '日程')
      const returned = await doClick(page.getByRole('button', { name: '前往下一事项', exact: true }))
      assert.equal(returned.location.id, 'L01')
      await navigate(page, '办公桌')
      await checkScene(page, returned.location.name, 'office.webp')
      await navigate(page, '日程')
      await page.getByLabel('推进时长').selectOption({ label: '90 天' })
      let advanced = await doClick(page.getByRole('button', { name: '按时长推进' }))
      assert.ok(advanced.quarter >= 2)
      await navigate(page, '档案')
      await page.getByRole('button', { name: '季度回顾', exact: true }).click()
      assert.ok((await page.locator('.record summary').count()) >= 1)
      const forkAt = advanced.revision
      await navigate(page, '行动')
      await page.getByRole('button', { name: /申请主动离任/ }).click()
      await doClick(page.getByRole('button', { name: '确认办理', exact: true }))
      await navigate(page, '日程')
      await page.getByLabel('推进时长').selectOption({ label: '7 天' })
      const ended = await doClick(page.getByRole('button', { name: '按时长推进' }))
      assert.equal(ended.ending.id, 'END02')
      await page.getByRole('button', { name: /回看已知经过/ }).click()
      await page.locator('.timeline article').first().waitFor()
      await navigate(page, '设置')
      await page.getByText('从历史修订分支').click()
      await page.getByLabel('分支起点').fill(String(forkAt))
      await page.getByRole('button', { name: '建立独立分支' }).click()
      await page.getByText('已进入独立分支。').waitFor()
      const branch = await current(page)
      assert.equal(branch.parent.revision, forkAt)
      assert.equal(branch.ending, null)
      await navigate(page, '行动')
      assert.ok((await page.locator('.action-row:not(:disabled)').count()) > 0)
    } finally {
      await context.close()
    }
  },
)

test(
  'two live windows synchronize player projections and persist presentation settings',
  { timeout: 45000 },
  async () => {
    const ctx = await browser.newContext(),
      sender = await ctx.newPage(),
      receiver = await ctx.newPage()
    try {
      await openCareer(sender, false)
      await receiver.goto(session)
      await enterCareerMenu(receiver)
      await receiver.getByRole('button', { name: '继续生涯' }).click()
      await navigate(receiver, '记事本')
      await navigate(sender, '记事本')
      await sender.getByRole('button', { name: /写入实体记事本/ }).click()
      await sender.getByLabel('记录原文').fill('两处窗口共用此条记录。')
      await sender.getByRole('button', { name: '确认办理' }).click()
      await receiver.locator('.journal').getByText('两处窗口共用此条记录。').waitFor({ timeout: 10000 })
      await navigate(sender, '设置')
      await sender.getByLabel('正文字号').selectOption('22')
      const sent = sender.waitForResponse(
        (r) =>
          r.url().endsWith('/preferences') &&
          r.request().method() === 'POST' &&
          r.request().postDataJSON().show_hints === false,
      )
      await sender.getByLabel('显示页面操作提示').uncheck()
      assert.equal((await sent).status(), 200)
      await receiver.reload()
      await receiver.waitForFunction(
        () => getComputedStyle(document.documentElement).fontSize === '22px',
      )
      await enterCareerMenu(receiver)
      await receiver.getByRole('button', { name: '继续生涯' }).click()
      assert.equal(await receiver.locator('.page-hint').count(), 0)
      await noOverflow(receiver)
    } finally {
      await ctx.close()
    }
  },
)

test('enter with the default title and reload a saved career', { timeout: 30000 }, async () => {
  const ctx = await browser.newContext(),
    page = await ctx.newPage()
  try {
    await page.goto(session)
    await enterCareerMenu(page)
    await page.getByRole('button', { name: '建立生涯' }).click()
    await page.getByRole('button', { name: '进入办公室' }).click()
    await page.getByRole('heading', { name: '我的办公桌' }).waitFor()
    const original = await current(page)
    assert.equal(original.name, '新任联络员')
    await page.reload()
    await enterCareerMenu(page)
    await page.getByRole('button', { name: '刷新档案' }).click()
    await page.getByRole('button', { name: '继续生涯' }).click()
    await page.getByRole('heading', { name: '我的办公桌' }).waitFor()
    assert.equal((await current(page)).world_id, original.world_id)
  } finally {
    await ctx.close()
  }
})

test(
  'temporary analysis and the event recap leave game time and source materials intact',
  { timeout: 45000 },
  async () => {
    const ctx = await browser.newContext(),
      page = await ctx.newPage()
    try {
      await openCareer(page, false)
      const start = await current(page)
      await navigate(page, '档案')
      await page.getByRole('button', { name: '并排对照' }).click()
      await page.getByLabel('临时推测').fill('这可能是不同区段。')
      await page.getByRole('button', { name: '将推测记入本子' }).click()
      assert.equal(await page.getByLabel('记录原文').inputValue(), '这可能是不同区段。')
      await page.keyboard.press('Escape')
      await page.getByRole('button', { name: '退出对照' }).click()
      await page.getByRole('button', { name: '并排对照' }).click()
      assert.equal(await page.getByLabel('临时推测').inputValue(), '')
      await page.getByRole('button', { name: '经过', exact: true }).click()
      await page.getByRole('button', { name: '回顾近期经过' }).click()
      const dialog = page.getByRole('dialog', { name: '近期经过' })
      await dialog.waitFor()
      assert.ok((await dialog.locator('.timeline article').count()) > 0)
      await dialog.getByRole('button', { name: '返回', exact: true }).click()
      await page.getByRole('heading', { name: '已知经过' }).waitFor()
      await navigate(page, '日程')
      await page.getByRole('button', { name: '回顾近期经过' }).click()
      await dialog.waitFor()
      await page.keyboard.press('Escape')
      const end = await current(page)
      assert.equal(end.revision, start.revision)
      assert.equal(end.minute, start.minute)
      assert.deepEqual(end.documents, start.documents)
      assert.deepEqual(end.notebook.entries, [])
    } finally {
      await ctx.close()
    }
  },
)

test('all eight careers can be entered from their published profiles', { timeout: 60000 }, async () => {
  const ctx = await browser.newContext(),
    page = await ctx.newPage()
  try {
    await page.goto(session)
    await enterCareerMenu(page)
    for (let i = 0; i < 8; i++) {
      await page.getByRole('button', { name: '建立生涯' }).click()
      const option = page.getByRole('radio').nth(i)
      await option.check()
      const expected = await option.getAttribute('value')
      await page.getByRole('button', { name: '进入办公室' }).click()
      await page.getByRole('heading', { name: '我的办公桌' }).waitFor()
      const state = await current(page)
      assert.equal(state.start, expected)
      assert.ok(state.documents.length > 0 && state.commitments.length > 0)
      const personalNote = state.documents.find((row) => ['START-field', 'START-tech'].includes(row.id))
      assert.ok((await page.locator('.passage-request').innerText()).includes(personalNote?.body ?? state.opening))
      await page.getByRole('button', { name: '局中事 主菜单' }).click()
    }
  } finally {
    await ctx.close()
  }
})

test(
  'a parsed sequence previews costs and displays each independent result',
  { timeout: 45000 },
  async () => {
    const ctx = await browser.newContext(),
      page = await ctx.newPage()
    try {
      await openCareer(page, false)
      await navigate(page, '行动')
      const field = page.getByLabel('想怎么处理'),
        parse = page.getByRole('button', { name: '解析意图' }),
        batch = page.getByRole('button', { name: '按顺序提交' })
      await field.fill('全听汇报然后暂缓答复')
      await parse.click()
      await batch.waitFor()
      assert.equal(
        await page
          .locator('.choice')
          .filter({ hasText: /办理代价/ })
          .count(),
        2,
      )
      const before = await current(page)
      await batch.click()
      await page.locator('.batch-results li').last().waitFor()
      const after = await current(page)
      assert.equal(after.revision, before.revision + 1)
      assert.deepEqual(
        after.last_action_results.map((r) => r.status),
        ['accepted', 'unavailable'],
      )
      assert.equal(await page.locator('.batch-results li').count(), 2)
      await navigate(page, '日程')
      const turn = page.waitForResponse((r) => r.url().endsWith('/commands'))
      await page.getByRole('button', { name: '前往下一事项' }).click()
      await turn
      await navigate(page, '行动')
      await field.fill('写入实体记事本然后暂缓答复')
      await parse.click()
      await page.getByRole('button', { name: /选择「写入实体记事本」/ }).waitFor()
      assert.equal(await batch.count(), 0)
      await field.fill('暂缓答复')
      assert.equal(await page.locator('.choice').count(), 0)
    } finally {
      await ctx.close()
    }
  },
)

test(
  'major decisions retain the exact confirmation on a retried receipt',
  { timeout: 45000 },
  async () => {
    const ctx = await browser.newContext(),
      page = await ctx.newPage()
    try {
      await openCareer(page, false)
      const v = await current(page),
        exitAction =
          v.actions.find((a) => a.kind === 'career_exit' && a.args.reason === 'exit') ??
          v.actions.find((a) => a.label === '申请主动离任')
      assert.ok(exitAction.confirmation_token)
      await navigate(page, '行动')
      await page.getByRole('button', { name: /申请主动离任/ }).click()
      let modal = page.getByRole('dialog', { name: '申请主动离任' })
      await modal.getByText(exitAction.confirm, { exact: true }).waitFor()
      await modal.getByRole('button', { name: '取消' }).click()
      assert.equal((await current(page)).revision, v.revision)
      await page.getByRole('button', { name: /申请主动离任/ }).click()
      await modal.waitFor()
      const updatedAction = (await current(page)).actions.find((a) => a.kind === exitAction.kind && a.label === exitAction.label)
      assert.notEqual(updatedAction.confirmation_token, exitAction.confirmation_token)
      let original
      const interrupted = async (route) => {
        original = route.request().postDataJSON()
        const reply = await route.fetch()
        assert.equal(reply.status(), 200)
        await route.abort('connectionreset')
      }
      await page.route('**/commands', interrupted)
      await modal.getByRole('button', { name: '确认办理' }).click()
      await page.getByRole('button', { name: '核对并重试' }).waitFor()
      await page.unroute('**/commands', interrupted)
      assert.equal(original.confirmation_token, updatedAction.confirmation_token)
      const retry = page.waitForRequest((r) => r.url().endsWith('/commands'))
      await page.getByRole('button', { name: '核对并重试' }).click()
      assert.deepEqual((await retry).postDataJSON(), original)
      await page.getByRole('status').filter({ hasText: '申请已送达' }).waitFor()
      const updated = await current(page)
      assert.equal(updated.revision, v.revision + 1)
      assert.equal(updated.appointments.filter((t) => t.title === '岗位交接确认').length, 1)
    } finally {
      await ctx.close()
    }
  },
)

test('player package exposes no Inspector routes to an authenticated player', async () => {
  const token = new URLSearchParams(new URL(session).hash.slice(1)).get('session')
  const headers = { Authorization: 'Bearer ' + token }
  const catalog = await fetch(address + '/api/starts', { headers })
  assert.equal(catalog.status, 200)
  const career = await fetch(address + '/api/worlds', {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ start: 'S01', name: '边界复核', balance: '0.500000' }),
  })
  assert.equal(career.status, 201)
  const { id } = await career.json()
  for (const path of ['/inspector', '/api/inspector', '/api/worlds/' + id + '/inspector', '/openapi.json']) {
    const reply = await fetch(address + path, { headers })
    assert.equal(reply.status, 404, path)
    assert.deepEqual(await reply.json(), { detail: 'Not Found' })
  }
})

test('a delayed recap cannot reopen an old revision after the player moves on', {timeout: 45000}, async () => {
  const ctx = await browser.newContext(), page = await ctx.newPage()
  let release
  const delayed = new Promise((resolve) => { release = resolve })
  try {
    await openCareer(page, false)
    await navigate(page, '日程')
    let captured
    const ready = new Promise((resolve) => { captured = resolve })
    await page.route('**/recap', async (route) => {
      const response = await route.fetch()
      captured()
      await delayed
      await route.fulfill({response})
    })
    await page.getByRole('button', { name: '回顾近期经过' }).click()
    await ready
    const receipt = page.waitForResponse((r) => r.url().endsWith('/commands'))
    await page.getByRole('button', { name: '按时长推进' }).click()
    assert.equal((await receipt).status(), 200)
    await page.waitForFunction(() => document.querySelector('.clock b')?.textContent !== '09:00')
    release()
    await page.waitForFunction(() => [...document.querySelectorAll('button')].some((b) => b.textContent.trim() === '回顾近期经过' && !b.disabled))
    assert.equal(await page.getByRole('dialog', {name:'近期经过'}).count(), 0)
    await page.unroute('**/recap')
    await page.getByRole('button', { name: '回顾近期经过' }).click()
    await page.getByRole('dialog', {name:'近期经过'}).waitFor()
  } finally {
    release()
    await ctx.close()
  }
})

test('report choices, social and family visits, notebook custody and a twelve-quarter transfer', {timeout: 180000}, async () => {
  const ctx = await browser.newContext(), page = await ctx.newPage()
  async function commit(click) {
    const reply = page.waitForResponse((r) => r.url().endsWith('/commands') && r.request().method() === 'POST')
    await click()
    const response = await reply
    assert.equal(response.status(), 200)
    return response.json()
  }
  async function act(kind, args = {}, values = {}) {
    const state = await current(page)
    const action = state.actions.find((a) => a.kind === kind &&
      Object.entries(args).every(([key, value]) => a.args[key] === value))
    assert.ok(action, kind + ' at ' + state.location.name)
    await navigate(page, '行动')
    const button = page.locator('.action-row').filter({has: page.getByText(action.label, {exact: true})})
    if (action.fields.length || action.confirm || ['destroy_note', 'confirm_note', 'stage_end', 'career_exit'].includes(kind)) {
      await button.click()
      const dialog = page.getByRole('dialog', {name: action.label})
      for (const [field, value] of Object.entries(values)) await dialog.getByLabel(field).fill(value)
      return commit(() => dialog.getByRole('button', {name: '确认办理'}).click())
    }
    return commit(() => button.click())
  }
  async function wait(label = '1 小时') {
    await navigate(page, '日程')
    await page.getByLabel('推进时长').selectOption({label})
    return commit(() => page.getByRole('button', {name: '按时长推进'}).click())
  }
  async function travel(place) {
    await act('travel', {location: place})
    let view = await wait()
    if (view.location.id !== place) view = await wait()
    assert.equal(view.location.id, place)
  }
  try {
    const choices = [['no','full'],['later','skip'],['free','short'],['yes','full']]
    for (const [choice, mode] of choices) {
      await openCareer(page, false)
      let view = await act('invite', {choice}, choice === 'free' ? {'回复内容': '我愿意赴约。'} : {})
      assert.ok(view.documents.find((d) => d.id === 'INVITE-reply'))
      view = await act('report', {mode})
      if (view.busy) await wait('8 小时')
      if (choice !== 'yes') {
        await page.getByRole('button', {name:'局中事 主菜单'}).click()
        await page.getByRole('button', {name:'模式选择', exact: true}).click()
      }
    }
    await act('appointment', {place:'L05'})
    await act('write_note', {}, {'记录原文':'等收件人确认会面，原报告仍待核对。'})
    await act('leave_note')
    await travel('L04')
    const atDinner = await current(page)
    assert.equal(atDinner.notebook.accessible, false)
    const publicData = await page.evaluate(async ({world_id, revision}) => {
      const path = '/api/worlds/' + encodeURIComponent(world_id)
      const headers = {Authorization: 'Bearer ' + sessionStorage.getItem('jzs-local-session')}
      const surfaces = await Promise.all(['', '/history', '/recap'].map(async (suffix) => {
        const response = await fetch(path + suffix, {headers})
        if (!response.ok) throw Error('Cannot read ' + suffix)
        return response.text()
      }))
      const controller = new AbortController()
      const updates = await fetch(path + '/events?after=' + (revision - 1), {headers, signal:controller.signal})
      const reader = updates.body.getReader(), decoder = new TextDecoder()
      let wire = ''
      try {
        while (!wire.includes('data:') || !wire.endsWith('\n\n')) {
          const next = await reader.read()
          if (next.done) break
          wire += decoder.decode(next.value, {stream:true})
        }
      } finally {
        controller.abort()
      }
      return {surfaces, wire}
    }, {world_id:atDinner.world_id, revision:atDinner.revision})
    assert.match(publicData.wire, /event: update/)
    for (const response of [...publicData.surfaces, publicData.wire]) {
      for (const marker of ['等收件人确认会面，原报告仍待核对。','排期初始归档','"beliefs"','"health_window"','"rng_seed"','V4-TV01']) {
        assert.ok(!response.includes(marker), 'hidden information reached the player channel')
      }
    }
    await act('mentor', {who:'N12', mode:'ask'})
    await wait()
    await act('speak', {mode:'limited'})
    await wait()
    await act('speak', {mode:'decline'})
    await wait()
    await travel('L07')
    await act('family_plan', {mode:'share'})
    await wait()
    await travel('L01')
    await act('take_note')
    await act('copy_note')
    await wait()
    await act('destroy_note')
    let view = await act('confirm_note', {choice:'yes'})
    assert.equal(view.notebook.accessible, false)
    for (let i = 0; i < 12; i++) view = await wait('90 天')
    assert.ok(view.quarter >= 13)
    const id = view.world_id
    await page.reload()
    await enterCareerMenu(page)
    await page.getByRole('button', {name: '继续生涯'}).click()
    assert.equal((await current(page)).world_id, id)
    assert.equal((await current(page)).revision, view.revision)
    await act('career_exit', {reason:'transfer'})
    await wait('7 天')
    view = await act('stage_end', {id:'END04'})
    assert.equal(view.ending.id,'END04')
    await page.getByRole('button', {name:/回看已知经过/}).click()
    await page.locator('.timeline article').first().waitFor()
  } finally {
    await ctx.close()
  }
})
