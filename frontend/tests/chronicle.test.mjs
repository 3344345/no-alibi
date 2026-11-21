import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { test } from 'node:test'
import { startBrowserFixture } from './browser-engine.mjs'

const endpoint = '/api/chronicle'
const name = '两代人的校样'
const story = (page) => page.locator('article.story')
const button = (page, text) => page.getByRole('button', { name: text, exact: true })
const responseFor = (page, path, method) =>
  page.waitForResponse((r) => new URL(r.url()).pathname === path && r.request().method() === method)
async function submit(page, path, method, click) {
  const [response] = await Promise.all([responseFor(page, path, method), click()])
  assert.ok(response.ok(), method + ' ' + path + ' returned ' + response.status())
  return response.json()
}
async function overflow(page) {
  const dimensions = await page.evaluate(() => [document.documentElement.scrollWidth, innerWidth])
  assert.ok(dimensions[0] <= dimensions[1], 'horizontal overflow at ' + dimensions.join('/'))
}
async function lobby(page, fixture) {
  await page.goto(fixture.session)
  await button(page, '生涯模式').click()
  const family = page.getByRole('button', { name: '市井家书', exact: true })
  const catalogue = await submit(page, endpoint, 'GET', () => family.click())
  assert.ok(catalogue.chapters.every((chapter) => !chapter.id.startsWith('witness_')))
  assert.ok(catalogue.chapters.some((c) => c.id === 'may_fourth'))
  return catalogue
}
async function startContext(fixture) {
  const ctx = await fixture.browser.newContext({ viewport: { width: 390, height: 844 }, acceptDownloads: true })
  const errors = [],
    outside = []
  await ctx.route('**/*', (route) => {
    const url = new URL(route.request().url())
    if (/^https?:$/.test(url.protocol) && url.origin !== fixture.address) {
      outside.push(url.origin)
      return route.abort()
    }
    return route.continue()
  })
  // Allow real decoding, gain, buffer wiring and start. Route playback into an
  // offline graph, so a release test never sends sound to the user's speakers.
  await ctx.addInitScript(() => {
    window.scoreStarts = []
    window.loopStarts = []
    window.loopStops = 0
    window.AudioContext = class extends OfflineAudioContext {
      constructor() {
        super(1, 24000, 24000)
      }
      get state() {
        return this.active ? 'running' : 'suspended'
      }
      async resume() {
        this.active = true
      }
      async suspend() {
        this.active = false
      }
      createBufferSource() {
        const voice = super.createBufferSource(),
          start = voice.start.bind(voice), stop = voice.stop.bind(voice)
        voice.stop = (...args) => {
          if (voice.loop) window.loopStops++
          stop(...args)
        }
        voice.start = (...args) => {
          if (voice.buffer.duration > 1) {
            const samples = voice.buffer.getChannelData(0)
            const log = voice.loop ? window.loopStarts : window.scoreStarts
            log.push({
              seconds: voice.buffer.duration,
              audible: samples.some((x) => Math.abs(x) > 0.01),
            })
          }
          start(...args)
        }
        return voice
      }
    }
  })
  const page = await ctx.newPage()
  page.setDefaultTimeout(7500)
  page.on('pageerror', (err) => errors.push(String(err)))
  return { ctx, page, errors, outside }
}
async function toggle(page, enabled) {
  const sw = page.getByRole('switch', { name: '历史长篇音效' })
  const pref = await submit(page, '/api/preferences', 'POST', () => sw.click())
  assert.equal(pref.sound_volume > 0, enabled)
  assert.equal(await sw.getAttribute('aria-checked'), String(enabled))
}
async function sceneVisible(page, view) {
  await story(page).getByRole('heading', { name: view.scene.title, exact: true }).waitFor()
  assert.deepEqual(
    await story(page).locator('.scene-body > p, .story-echo > p').allTextContents(),
    view.scene.body.split(/\n+/).filter((paragraph) => paragraph.trim()),
  )
  assert.deepEqual(
    await story(page).locator('.decisions button span').allTextContents(),
    view.scene.choices.filter((x) => !x.cites && !(view.scene.id === 'night_switchboard' && x.id.startsWith('patch_'))).map((x) => x.label),
  )
}
async function choose(page, old, id = old.scene.choices[0].id) {
  const visible = old.scene.choices.find((c) => c.id === id)
  assert.ok(visible, 'unavailable choice at ' + old.scene.id + ': ' + id)
  const view = await submit(page, endpoint + '/' + old.id + '/choices', 'POST', () =>
    button(story(page), visible.label).click(),
  )
  assert.equal(view.revision, old.revision + 1)
  const entry = view.journal.at(-1)
  assert.equal(entry.label, visible.label)
  if (old.chapter.id !== view.chapter.id || view.finished) {
    await page.locator('.handover blockquote').getByText(entry.result, { exact: true }).waitFor()
    await page
      .locator('.handover')
      .getByRole('button', { name: /^(翻至 |打开全卷行记)/ })
      .click()
    if (view.finished) await page.getByRole('heading', { name: '全卷行记', exact: true }).waitFor()
  }
  if (!view.finished) await sceneVisible(page, view)
  return view
}
async function investigate(page, current) {
  const desk = await choose(page, current, 'open_desk')
  assert.equal(desk.scene.id, 'desk_inspect')
  const region = page.getByRole('region', { name: '案头材料' })
  const items = desk.scene.exhibits
  assert.equal(items.length, 3)
  for (const item of items) {
    const select = button(region, '对照材料 · ' + item.title)
    assert.ok(await select.isDisabled())
    await region.locator('summary').getByText(item.title, { exact: true }).click()
    await region.getByText(item.detail, { exact: true }).waitFor()
    await page.waitForFunction((el) => !el.disabled, await select.elementHandle())
  }
  const pick = (idx) => button(region, '对照材料 · ' + items[idx].title).click()
  const applicable = (idx) =>
    desk.scene.choices.filter((c) => c.cites.includes(items[0].id) && c.cites.includes(items[idx].id))
  const displayed = () => story(page).locator('.decisions button span').allTextContents()
  await pick(0)
  assert.deepEqual(await displayed(), [])
  await pick(1)
  const pair = applicable(1)
  assert.deepEqual(
    await displayed(),
    pair.map((c) => c.label),
  )
  assert.ok(pair.length >= 2)
  assert.ok(await button(region, '对照材料 · ' + items[2].title).isDisabled())
  await pick(1)
  await pick(2)
  assert.deepEqual(
    await displayed(),
    applicable(2).map((c) => c.label),
  )
  assert.deepEqual(await story(page).getByRole('button', { name: pair[0].label, exact: true }).count(), 0)
  await overflow(page)
  const next = await choose(page, desk, applicable(2)[0].id)
  assert.equal(next.scene.id, 'desk_return')
  assert.ok(next.journal.at(-1).marks.length > 0)
  assert.deepEqual(next.journal.at(-1).citations, [items[0], items[2]])
  return next
}
async function readSource(page, chapter) {
  const dialog = page.getByRole('dialog', { name: '年代与出处' })
  await page.getByLabel('查阅年代').selectOption(chapter.id)
  await dialog.getByText(chapter.history, { exact: true }).waitFor()
  const source = chapter.sources[0]
  await dialog.locator('summary').getByText(source.name, { exact: true }).click()
  const anchor = dialog.getByRole('link', { name: source.url, exact: true })
  assert.equal(await anchor.getAttribute('href'), source.url)
  await overflow(page)
  await button(dialog, '返回').click()
}

test(
  'historical chronicle from the cover to 2019, committed music, split records and fresh-profile restoration',
  { timeout: 180000 },
  async () => {
    let fixture = await startBrowserFixture(),
      context,
      second
    try {
      context = await startContext(fixture)
      let { page } = context
      const catalogue = await lobby(page, fixture)
      assert.ok(catalogue.chapters.length >= 11)
      assert.deepEqual(catalogue.careers, [])
      await overflow(page)
      await button(page, '年代与出处').click()
      await readSource(page, catalogue.chapters.at(-1))
      await page.getByLabel('为这段长篇命名').fill(name)
      let view = await submit(page, endpoint, 'POST', () => button(page, '开始长篇').click())
      const original = view.id
      const visited = new Set([view.chapter.id])
      await sceneVisible(page, view)
      assert.equal(view.chapter.year, '1919')
      assert.equal(
        await page.getByRole('switch', { name: '历史长篇音效' }).getAttribute('aria-checked'),
        'false',
      )
      await button(page, '本章史料').click()
      await readSource(page, view.chapter)
      await overflow(page)
      view = await choose(page, view, 'set_sheet')
      assert.deepEqual(await page.evaluate(() => window.loopStarts), [])
      await toggle(page, true)
      await page.waitForFunction(() => window.loopStarts.length === 2)
      const layers = await page.evaluate(() => window.loopStarts)
      assert.ok(layers.every((layer) => layer.seconds > 25 && layer.audible))
      assert.notEqual(layers[0].seconds, layers[1].seconds)
      assert.deepEqual(await page.evaluate(() => window.scoreStarts), [])
      const requests = []
      page.on('request', (r) => {
        if (new URL(r.url()).pathname.endsWith('.mp3')) requests.push(new URL(r.url()).pathname)
      })
      let beforeCommit
      await page.route(
        '**/choices',
        async (route) => {
          // Withhold the write before it reaches the engine. Nothing may score the
          // choice until the response contains its actual journal entry.
          await page.evaluate(
            () => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done))),
          )
          beforeCommit = { scores: await page.evaluate(() => window.scoreStarts), requests: [...requests] }
          await route.continue()
        },
        { times: 1 },
      )
      const music = page.waitForResponse((r) => new URL(r.url()).pathname === '/chronicle/evidence.mp3')
      view = await choose(page, view, 'ask_copyist')
      assert.deepEqual(beforeCommit, { scores: [], requests: [] })
      assert.equal(view.journal.at(-1).tone, 'evidence')
      assert.ok((await music).ok())
      await page.waitForFunction(() => window.scoreStarts.length === 1)
      const sounds = await page.evaluate(() => window.scoreStarts)
      assert.ok(sounds[0].seconds > 1 && sounds[0].audible)
      assert.ok(view.marks.includes('双行校样') && view.scene.choices.some((c) => c.id === 'compare_proof'))
      await toggle(page, false)
      assert.equal(await page.evaluate(() => window.loopStops), 2)
      assert.deepEqual(await page.evaluate(() => window.loopStarts), layers)
      await button(story(page), '本章足迹').click()
      const path = page.getByRole('dialog', { name: '本章足迹' })
      await path.getByText(view.journal[1].result, { exact: true }).waitFor()
      await button(path, '上一场').click()
      await path.getByText(view.journal[0].result, { exact: true }).waitFor()
      assert.equal(await path.locator('option').count(), 2)
      await button(path, '返回').click()
      const originalAfterTwo = view
      await button(page, '行记与存档').click()
      const journal = page.getByRole('dialog', { name: '行记' })
      await journal.locator('summary').first().click()
      await journal.getByText(view.journal[1].result, { exact: true }).waitFor()
      const split = await submit(page, endpoint + '/' + original + '/fork', 'POST', () =>
        button(journal, '从此次选择前另开分线').click(),
      )
      assert.notEqual(split.id, original)
      assert.equal(split.revision, 1)
      await sceneVisible(page, split)
      const changed = await choose(page, split, 'hold_line')
      assert.ok(!changed.marks.includes('双行校样'))
      assert.equal(
        await story(page)
          .getByRole('button', { name: /取出双行校样/ })
          .count(),
        0,
      )
      await button(page, '返回').click()
      const savedCareer = page.locator('.saves button').filter({ has: page.getByText(name, { exact: true }) })
      view = await submit(page, endpoint + '/' + original, 'GET', () => savedCareer.click())
      assert.deepEqual(view, originalAfterTwo)
      await sceneVisible(page, view)
      view = await choose(page, view, 'compare_proof')
      view = await choose(page, view)
      view = await choose(page, view, 'send_proof')
      assert.equal(view.chapter.year, '1927')
      assert.ok(view.marks.includes('北京印铺纸样'))
      assert.deepEqual(await page.evaluate(() => window.scoreStarts), sounds)
      assert.deepEqual(requests, ['/chronicle/evidence.mp3'])
      assert.deepEqual(context.errors, [])
      assert.deepEqual(context.outside, [])
      await context.ctx.close()
      context = null
      await fixture.restart() // New process and new loopback credentials, same SQLite database.
      context = await startContext(fixture)
      page = context.page
      const restarted = await lobby(page, fixture)
      assert.equal(restarted.careers.length, 2)
      assert.equal(
        await page.getByRole('switch', { name: '历史长篇音效' }).getAttribute('aria-checked'),
        'false',
      )
      const resumed = await submit(page, endpoint + '/' + original, 'GET', () =>
        page
          .locator('.saves button')
          .filter({ has: page.getByText(name, { exact: true }) })
          .click(),
      )
      assert.deepEqual(resumed, view)
      const mark = '双址家封'
      for (let i = 0; !view.finished && i < 130; i++) {
        if (!visited.has(view.chapter.id)) {
          visited.add(view.chapter.id)
          const image = page.locator('.scene-art .reading-space')
          const valid = await image.evaluate(async (el) => {
            await el.decode()
            return el.naturalWidth > 0 && el.naturalHeight > 0
          })
          assert.ok(valid, view.chapter.title)
          await overflow(page)
        }
        if (view.chapter.year === '1931' && view.scene.choices.some((c) => c.id === 'open_desk')) {
          view = await investigate(page, view)
          continue
        }
        const option = view.chapter.year === '1927' && view.scene.id === 'evening' ? 'send_old_type' : undefined
        view = await choose(page, view, option)
        if (option) assert.ok(view.journal.at(-1).marks.includes(mark))
      }
      assert.ok(view.finished && view.marks.includes(mark))
      assert.deepEqual(
        [...visited],
        catalogue.chapters.map((c) => c.id),
      )
      assert.deepEqual(await page.evaluate(() => window.scoreStarts), [])
      await button(page, '回看沿途的选择').click()
      const finalJournal = page.getByRole('dialog', { name: '行记' })
      assert.equal(await finalJournal.locator('details').count(), view.revision)
      await finalJournal.locator('summary').last().click()
      await finalJournal.getByText(view.journal[0].result, { exact: true }).waitFor()
      await overflow(page)
      const [file] = await Promise.all([
        page.waitForEvent('download'),
        button(finalJournal, '导出长篇存档').click(),
      ])
      assert.ok(file.suggestedFilename().includes(name))
      const filename = join(fixture.profile, 'chronicle-backup.json')
      await file.saveAs(filename)
      const archive = JSON.parse(await readFile(filename, 'utf8'))
      assert.equal(archive.id, original)
      assert.equal(archive.commands.length, view.revision)
      assert.deepEqual(context.errors, [])
      assert.deepEqual(context.outside, [])
      await context.ctx.close()
      context = null
      // Fresh data directory, empty browser storage and an upload through the normal file picker.
      second = await startBrowserFixture()
      context = await startContext(second)
      page = context.page
      assert.deepEqual((await lobby(page, second)).careers, [])
      const [picker] = await Promise.all([
        page.waitForEvent('filechooser'),
        button(page, '导入长篇存档').click(),
      ])
      const imported = await submit(page, endpoint + '/import', 'POST', () => picker.setFiles(filename))
      assert.deepEqual(imported, view)
      await page.getByRole('heading', { name: '全卷行记' }).waitFor()
      const paired = view.journal.find((e) => e.citations?.length === 2)
      assert.ok(paired)
      await button(page, '回看沿途的选择').click()
      const recoveredJournal = page.getByRole('dialog', { name: '行记' })
      const item = recoveredJournal
        .locator('details')
        .filter({ has: page.locator('summary').getByText(paired.year + ' · ' + paired.title, { exact: true }) })
      await item.locator('summary').click()
      await item.getByText(paired.result, { exact: true }).waitFor()
      const materials = item.getByRole('region', { name: '已对照材料' })
      for (const exhibit of paired.citations) {
        await materials.getByText(exhibit.title, { exact: true }).waitFor()
        await materials.getByText(exhibit.detail, { exact: true }).waitFor()
      }
      assert.equal(await materials.locator('dt').count(), 2)
      await button(recoveredJournal, '返回').click()
      await button(page, '返回').click()
      await button(page, '返回').click()
      await button(page, '建立生涯').click()
      await page.getByRole('radio', { name: /专业技术转任/ }).check()
      await page.getByLabel('角色称谓').fill('林舟')
      await button(page, '进入办公室').click()
      await page.getByRole('heading', { name: '我的办公桌' }).waitFor()
      await page.getByRole('navigation').getByRole('button', { name: '档案', exact: true }).click()
      assert.ok((await page.locator('details.record').count()) > 0)
      assert.deepEqual(context.errors, [])
      assert.deepEqual(context.outside, [])
    } finally {
      await context?.ctx.close()
      await second?.close()
      await fixture.close()
    }
  },
)

test('the night broadcast follows the location and plays the family waltz only after permission', async () => {
  const fixture = await startBrowserFixture()
  let context
  try {
    context = await startContext(fixture)
    const { page } = context
    const requests = []
    page.on('request', (r) => {
      const path = new URL(r.url()).pathname
      if (path.startsWith('/chronicle/sound/')) requests.push(path.split('/').at(-1))
    })
    await page.goto(fixture.session)
    await submit(page, endpoint, 'GET', () => button(page, '历史主角模式').click())
    await page.getByLabel('选择亲历者与起始事件').selectOption('witness_deng_xiaoping')
    let view = await submit(page, endpoint, 'POST', () => button(page, '开始长篇').click())
    await toggle(page, true)
    for (const id of ['night_line', 'private', 'laugh', 'sheet', 'date', 'whole', 'child',
                      'cut', 'correct', 'letters', 'together']) {
      view = await choose(page, view, id)
    }
    assert.equal(view.scene.id, 'night_supper')
    for (const track of ['exchange.mp3', 'projector.mp3', 'platform.mp3', 'afterlight.mp3'])
      assert.ok(requests.includes(track), track)
    assert.ok(!requests.includes('kitchen_waltz.mp3'))
    const dance = page.waitForResponse((r) => new URL(r.url()).pathname.endsWith('/kitchen_waltz.mp3'))
    view = await choose(page, view, 'music')
    assert.ok((await dance).ok())
    await page.waitForFunction(() => window.scoreStarts.some((s) => s.seconds >= 13.7 && s.seconds < 14 && s.audible))
    await button(story(page), '本章足迹').click()
    const path = page.getByRole('dialog', {name: '本章足迹'})
    assert.equal(await path.locator('option').count(), view.journal.length)
    await button(path, '重听那晚的手风琴').click()
    await page.waitForFunction(() => window.scoreStarts.filter((s) => s.seconds >= 13.7 && s.seconds < 14).length === 2)
    const fork = await submit(page, endpoint + '/' + view.id + '/fork', 'POST', () =>
      button(path, '从这场另走一条路').click())
    assert.equal(fork.scene.id, 'night_supper')
    const startCount = requests.filter((file) => file === 'kitchen_waltz.mp3').length
    const voices = await page.evaluate(() => window.scoreStarts.filter((s) => s.seconds >= 13.7 && s.seconds < 14).length)
    view = await choose(page, fork, 'closed')
    assert.equal(view.scene.id, 'night_clock')
    assert.equal(requests.filter((file) => file === 'kitchen_waltz.mp3').length, startCount)
    assert.equal(await page.evaluate(() => window.scoreStarts.filter((s) => s.seconds >= 13.7 && s.seconds < 14).length), voices)
    assert.deepEqual(context.errors, [])
    assert.deepEqual(context.outside, [])
  } finally {
    await context?.ctx.close()
    await fixture.close()
  }
})
