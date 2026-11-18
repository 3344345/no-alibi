import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createInterface } from 'node:readline'
import { once } from 'node:events'
import { after, before, test } from 'node:test'
import { chromium, webkit } from 'playwright-core'

const root = fileURLToPath(new URL('../../', import.meta.url))
let server, browser, profile, session, address
before(async () => {
  profile = await mkdtemp(join(tmpdir(), 'jzs-browser-'))
  const bundle = process.env.JZS_TEST_APP
  const env={...process.env}
  if(bundle){delete env.PYTHONPATH;delete env.PYTHONHOME}
  server = spawn(
    bundle ? join(bundle,'Contents/MacOS/jzs-engine') : process.env.PYTHON || join(root, '.venv/bin/python'),
    [...(bundle?['--assets',join(bundle,'Contents/Resources/web')]:['main.py']), '--no-browser', '--data-dir', profile],
    { cwd: bundle ? profile : root, env, stdio: ['ignore', 'pipe', 'pipe'] },
  )
  const stdout = createInterface({ input: server.stdout })
  const [entry] = await Promise.race([
    once(stdout, 'line'),
    once(server, 'exit').then(() => {
      throw Error('Local test engine did not start')
    }),
  ])
  session = String(entry)
  address = new URL(session).origin
  browser =
    process.env.JZS_BROWSER === 'webkit'
      ? await webkit.launch()
      : await chromium.launch(
          process.env.CHROME_BIN ? { executablePath: process.env.CHROME_BIN } : { channel: 'chrome' },
        )
})
after(async () => {
  await browser?.close()
  if (server?.exitCode === null) {
    const ended = once(server, 'exit')
    server.kill()
    await ended
  }
  if (profile) await rm(profile, { recursive: true, force: true })
})
async function screen(page, name) {
  if (process.env.JZS_SCREENSHOT_DIR)
    await page.screenshot({ path: join(process.env.JZS_SCREENSHOT_DIR, name + '.png'), fullPage: true })
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
  await page.goto(session)
  if (wide) await screen(page, 'cover')
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
async function noOverflow(page) {
  assert.ok(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    'page exceeds viewport width',
  )
}

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
    await screen(page, 'mobile-desk')
    await noOverflow(page)
    for (const label of ['行动', '日程', '档案', '人事与地点', '记事本', '设置']) {
      await navigate(page, label)
      await noOverflow(page)
      assert.equal(await page.locator('h1').innerText(), label)
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
      await doClick(page.getByRole('button', { name: '前往下一事项', exact: true }))
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
    await page.getByRole('button', { name: '建立生涯' }).click()
    await page.getByRole('button', { name: '进入办公室' }).click()
    await page.getByRole('heading', { name: '我的办公桌' }).waitFor()
    const original = await current(page)
    assert.equal(original.name, '新任联络员')
    await page.reload()
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
      assert.equal(original.confirmation_token, exitAction.confirmation_token)
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
