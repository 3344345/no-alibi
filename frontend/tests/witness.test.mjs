import assert from 'node:assert/strict'
import { test } from 'node:test'
import { startBrowserFixture } from './browser-engine.mjs'

const api = '/api/chronicle'
const chapterId = 'witness_deng_xiaoping'
const button = (scope, name) => scope.getByRole('button', { name, exact: true })
const story = (page) => page.locator('article.story')
const handover = (page) => page.locator('section.handover')

async function interact(page, method, path, action) {
  const [response] = await Promise.all([
    page.waitForResponse((r) => r.request().method() === method && new URL(r.url()).pathname === path),
    action(),
  ])
  assert.ok(response.ok(), method + ' ' + path + ' returned ' + response.status())
  return response.json()
}

async function openLobby(page, fixture) {
  await page.goto(fixture.session)
  const catalog = await interact(page, 'GET', api, () => button(page, '历史主角模式').click())
  await page.getByRole('heading', { name: '亲历者', exact: true }).waitFor()
  assert.ok(catalog.chapters.some((c) => c.id === chapterId))
  return catalog
}

async function choose(page, before, id) {
  const offered = before.scene.choices.find((choice) => choice.id === id)
  assert.ok(offered, before.scene.id + ' should offer ' + id)
  await story(page).getByRole('heading', { name: before.scene.title, exact: true }).waitFor()
  const next = await interact(page, 'POST', api + '/' + before.id + '/choices', () =>
    button(story(page), offered.label).click(),
  )
  assert.equal(next.revision, before.revision + 1)
  const entry = next.journal.at(-1)
  assert.equal(entry.choice, id)
  if (next.finished || next.chapter.id !== before.chapter.id) {
    await handover(page).getByText(entry.result, { exact: true }).waitFor()
  } else {
    const receipt = story(page).locator('details.receipt')
    const summary = receipt.locator('summary')
    await summary.waitFor()
    assert.equal(await receipt.evaluate((el) => el.open), false)
    await summary.click()
    await receipt.getByText(entry.result, { exact: true }).waitFor()
    await summary.click()
  }
  return next
}

async function turnPage(page, view) {
  await handover(page).getByRole('button', { name: /^(翻至 |打开全卷行记)/ }).click()
  await page.getByRole('heading', { name: view.finished ? '全卷行记' : view.scene.title, exact: true }).waitFor()
}

async function compareOutcome(page, before, id, fates) {
  const next = await choose(page, before, id)
  assert.notEqual(next.chapter.id, before.chapter.id)
  const actual = handover(page)
  const result = next.journal.at(-1).result
  for (const fate of fates) assert.match(result, fate)
  await actual.getByRole('heading', { name: '史实对照', exact: true }).waitFor()
  await actual.getByText(before.chapter.history, { exact: true }).waitFor()
  await button(page, '年代与出处').click()
  const sources = page.getByRole('dialog', { name: '年代与出处' })
  assert.equal(await sources.getByLabel('查阅年代').inputValue(), before.chapter.id)
  await button(sources, '返回').click()
  assert.match(before.chapter.history, /蒋捷连.{0,15}遇难/)
  assert.match(before.chapter.history, /赵紫阳.{0,15}被撤职/)
  await turnPage(page, next)
  return next
}

async function resume(page, record) {
  const row = page.locator('.saves button').filter({ has: page.getByText(record.name, { exact: true }) })
  const saved = await interact(page, 'GET', api + '/' + record.id, () => row.click())
  assert.deepEqual(saved, record)
  await page.getByRole('heading', { name: record.finished ? '全卷行记' : record.scene.title, exact: true }).waitFor()
}

async function sceneArt(page, person, prop) {
  const scene = page.locator('.scene-art .eyes').filter({has:page.getByRole('img',{name:person+'眼前的场景',exact:true})})
  await scene.waitFor()
  assert.equal(await scene.getAttribute('data-viewer'), person)
  if (prop) assert.equal(await scene.getAttribute('data-prop'), prop)
  const img = scene.locator('.reading-space')
  assert.match(await img.getAttribute('src'), /^\/(?:sets|reading)\/[^/]+\.webp$/)
  assert.equal(await scene.locator('.own').count(), 2)
  assert.ok(await img.evaluate(async (node) => {
    await node.decode()
    return node.naturalWidth >= 400 && node.naturalHeight >= 250
  }))
}

test('Shanghai tram passengers remember the chosen kitchen on reload and vote six months later', async () => {
  const fixture = await startBrowserFixture()
  try {
    const page = await fixture.browser.newPage()
    await openLobby(page, fixture)
    for (const [choice, other, ending] of [
      ['reserve_seat', '巷口传来滋啦一声', 'hospital'],
      ['invite_cooks', '老袁把饭盒送回来了', 'old_stop'],
    ]) {
      await page.getByLabel('选择亲历者与起始事件').selectOption('witness_shanghai_prices')
      await page.getByLabel('为这段长篇命名').fill(choice)
      let view = await interact(page, 'POST', api, () => button(page, '开始长篇').click())
      await sceneArt(page, '蒋经国')
      for (const id of ['tram_bowl', 'keep_twelve', choice]) view = await choose(page, view, id)
      assert.equal(view.scene.id, 'tram_run')
      const echo = choice === 'reserve_seat' ? '老袁把饭盒送回来了' : '巷口传来滋啦一声'
      await page.reload()
      await openLobby(page, fixture)
      await resume(page, view)
      const callbacks = story(page).locator('.story-echo > p')
      await callbacks.filter({hasText: echo}).waitFor({state: 'visible'})
      assert.equal(await callbacks.filter({hasText: other}).count(), 0)
      for (const id of ['meet_barge', 'turn_over']) view = await choose(page, view, id)
      assert.equal(view.scene.id, 'tram_map')
      await sceneArt(page, '蒋经国','ticket')
      await page.locator('.art-caption').getByText('半年后', {exact:true}).waitFor()
      view = await choose(page, view, ending)
      const result = view.journal.at(-1)
      assert.match(result.result, ending === 'hospital' ? /医院门前有了末班车/ : /保住一站的人/)
      await handover(page).getByText('史实对照', {exact:true}).waitFor()
      await interact(page, 'GET', api, () => button(page, '返回').click())
    }
  } finally {
    await fixture.close()
  }
})

test('Beijing leaves the office for a live studio and reaches the alternate 1992 broadcast', async () => {
  const fixture = await startBrowserFixture()
  try {
    const page = await fixture.browser.newPage()
    await openLobby(page, fixture)
    await page.getByLabel('选择亲历者与起始事件').selectOption(chapterId)
    let view = await interact(page, 'POST', api, () => button(page, '开始长篇').click())
    await sceneArt(page, '邓小平')
    for (const id of ['go_live', 'phones', 'second_night', 'local_air']) {
      view = await choose(page, view, id)
      // The save advances before the outgoing actor has finished responding.
      const sceneId=view.chapter.id+'/'+view.scene.id
      await page.locator('.perform[data-scene="'+sceneId+'"]').waitFor()
      const viewer={studio:'梁桂兰',switchboard:'梁桂兰',summer_broadcast:'邓小平',city_frequency:'外地女工'}[view.scene.id]
      await sceneArt(page,viewer,'radio')
      if (viewer!=='邓小平') {
        const storyArt=page.locator('.scene-art')
        assert.match(await storyArt.locator('.art-caption p').innerText(),/ · .+所见/)
        const stage=page.getByRole('region',{name:'人物现场'})
        const channel={studio:'电视台内线',switchboard:'直播电话',city_frequency:'地方台播出记录'}[view.scene.id]
        assert.match(await stage.locator('.own-name').innerText(),new RegExp('^你 · 邓小平.*'+channel+'$'))
        assert.equal(await stage.locator('.other-name').count(),0)
        assert.match(await stage.locator('.set').getAttribute('style'),/office\.webp/)
        const choices=page.getByRole('group',{name:'本幕行动'})
        assert.equal(await choices.getAttribute('data-decision-player'),'邓小平')
        await choices.locator('.decisions button').first().focus()
        await storyArt.locator('.eyes[data-viewer="邓小平"]').waitFor()
        await storyArt.getByRole('button',{name:/^回看/}).click()
        await storyArt.locator('.eyes[data-viewer="'+viewer+'"]').waitFor()
      }
    }
    await page.locator('.art-caption').getByText('架空的1992年', {exact:true}).waitFor()
    const next = await choose(page, view, 'listeners_veto')
    assert.ok(next.journal.at(-1).marks.includes('结局 · 不用等北京开门的星期三'))
  } finally {
    await fixture.close()
  }
})

test('1989 witness, two named outcomes, their historical comparison, and both saves after restart', { timeout: 120000 }, async () => {
  const fixture = await startBrowserFixture()
  const errors = []
  let context
  async function freshPage() {
    context = await fixture.browser.newContext({ viewport: { width: 960, height: 820 } })
    const page = await context.newPage()
    page.setDefaultTimeout(8000)
    page.on('pageerror', (error) => errors.push(error.message))
    return page
  }
  try {
    let page = await freshPage()
    await openLobby(page, fixture)
    const picker = page.getByLabel('选择亲历者与起始事件')
    await picker.selectOption(chapterId)
    assert.match(await picker.locator('option:checked').innerText(), /1989/)
    await page.getByLabel('为这段长篇命名').fill('一九八九年的两种结局')
    let view = await interact(page, 'POST', api, () => button(page, '开始长篇').click())
    assert.equal(view.campaign, 'witness')
    assert.equal(view.start_chapter, chapterId)
    assert.equal(view.scene.id, 'april')
    assert.match(await story(page).locator('.date-line').innerText(), /邓小平/)
    await button(page, '本章史料').click()
    const sources = page.getByRole('dialog', { name: '年代与出处' })
    await sources.getByText(view.chapter.history, { exact: true }).waitFor()
    const testimony = view.chapter.sources.find((source) => source.name.includes('丁子霖'))
    assert.ok(testimony)
    await sources.locator('summary').getByText(testimony.name, { exact: true }).click()
    assert.equal(await sources.getByRole('link', { name: testimony.url, exact: true }).getAttribute('href'), testimony.url)
    await button(sources, '返回').click()
    for (const id of ['endorse', 'private', 'martial', 'stand']) view = await choose(page, view, id)
    assert.equal(view.scene.id, 'deadline')
    const junction = view
    const changed = await choose(page, junction, 'change')
    assert.equal(changed.scene.id, 'civil')
    await story(page).getByText(/蒋捷连在这个夜晚平安回家/).waitFor()
    const original = await compareOutcome(page, changed, 'retain', [/蒋捷连活了下来/, /赵紫阳.{0,15}留任/])

    await button(page, '行记与存档').click()
    const journal = page.getByRole('dialog', { name: '行记' })
    const forkPoint = journal.locator('details').filter({ has: page.locator('summary').filter({ hasText: junction.scene.title }) })
    await forkPoint.locator('summary').click()
    await forkPoint.getByText(changed.journal.at(-1).result, { exact: true }).waitFor()
    const forked = await interact(page, 'POST', api + '/' + original.id + '/fork', () =>
      button(forkPoint, '从此次选择前另开分线').click(),
    )
    assert.notEqual(forked.id, original.id)
    assert.equal(forked.start_chapter, chapterId)
    assert.equal(forked.scene.id, junction.scene.id)
    assert.deepEqual(forked.journal, junction.journal)
    const kept = await choose(page, forked, 'keep')
    assert.equal(kept.scene.id, 'loss')
    await story(page).getByText(/蒋捷连6月3日晚在北京遇难/).waitFor()
    let alternate = await compareOutcome(page, kept, 'official', [/蒋捷连遇难/, /赵紫阳随后被撤职/])
    assert.equal(alternate.chapter.id, original.chapter.id)
    assert.deepEqual(alternate.journal.slice(0, junction.revision), original.journal.slice(0, junction.revision))
    assert.notDeepEqual(alternate.marks, original.marks)

    for (let step = 0; !alternate.finished && step < 80; step++) {
      const previous = alternate
      const plain = previous.scene.choices.find((c) => !c.cites)
      assert.ok(plain, 'An ordinary decision is available from ' + previous.scene.id)
      alternate = await choose(page, previous, plain.id)
      if (alternate.finished || alternate.chapter.id !== previous.chapter.id) await turnPage(page, alternate)
    }
    assert.ok(alternate.finished)
    await context.close()
    context = null
    await fixture.restart()
    page = await freshPage()
    const restored = await openLobby(page, fixture)
    assert.deepEqual(new Set(restored.careers.map((s) => s.id)), new Set([original.id, alternate.id]))
    const comparison = page.locator('details.my-outcomes')
    await comparison.locator('summary').click()
    for (const record of [original, alternate]) {
      const ending = record.journal.findLast((e) => e.chapter_id === chapterId)
      await comparison.getByText(ending.result, { exact: true }).waitFor()
    }
    for (const record of [original, alternate]) {
      await resume(page, record)
      await button(page, '行记与存档').click()
      const log = page.getByRole('dialog', { name: '行记' })
      const end = record.journal.findLast((e) => e.chapter_id === chapterId)
      await log.locator('summary').filter({ hasText: end.title }).click()
      await log.getByText(end.result, { exact: true }).waitFor()
      await button(log, '返回').click()
      await interact(page, 'GET', api, () => button(page, '返回').click())
    }
    assert.deepEqual(errors, [])
  } finally {
    try {
      await context?.close()
    } finally {
      await fixture.close()
    }
  }
})

test('two home modes keep same-named county, family and witness records independent after restart', { timeout: 60000 }, async () => {
  const fixture = await startBrowserFixture()
  let context
  const name = '同名存档'
  async function rootVisible(page) {
    for (const mode of ['生涯模式', '历史主角模式']) {
      const target = button(page, mode)
      await target.waitFor()
      assert.equal(await target.count(), 1)
    }
    assert.equal(await page.getByRole('group', { name: '模式选择' }).getByRole('button').count(), 2)
    for (const child of ['建立生涯', '继续生涯', '市井家书', '开始长篇']) {
      assert.equal(await button(page, child).count(), 0, child + ' is only available inside its mode')
    }
  }
  async function careerLobby(page) {
    await button(page, '生涯模式').click()
    await button(page, '建立生涯').waitFor()
    assert.equal(await button(page, '历史主角模式').count(), 0)
  }
  async function archiveLobby(page, campaign) {
    const label = campaign === 'family' ? '市井家书' : '历史主角模式'
    const result = await interact(page, 'GET', api, () => button(page, label).click())
    await page.getByLabel('为这段长篇命名').waitFor()
    assert.ok(result.chapters.length)
    assert.ok(result.chapters.every(c => c.id.startsWith('witness_') === (campaign === 'witness')))
    assert.equal(await page.getByLabel('选择亲历者与起始事件').count(), campaign === 'family' ? 0 : 1)
    assert.equal(await button(page, '市井家书').count(), 0)
    return result
  }
  async function toArchiveLobby(page) {
    await interact(page, 'GET', api, () => button(page, '返回').click())
  }
  async function createArchive(page, campaign) {
    if (campaign === 'witness') await page.getByLabel('选择亲历者与起始事件').selectOption(chapterId)
    await page.getByLabel('为这段长篇命名').fill(name)
    const created = await interact(page, 'POST', api, () => button(page, '开始长篇').click())
    assert.equal(created.name, name)
    assert.equal(created.campaign, campaign)
    return choose(page, created, created.scene.choices.find(c => !c.cites).id)
  }
  try {
    context = await fixture.browser.newContext()
    let page = await context.newPage()
    page.setDefaultTimeout(8000)
    await page.goto(fixture.session)
    await rootVisible(page)
    await careerLobby(page)
    await button(page, '建立生涯').click()
    await page.getByLabel('角色称谓').fill(name)
    const county = await interact(page, 'POST', '/api/worlds', () => button(page, '进入办公室').click())
    assert.equal(county.name, name)
    await button(page, '局中事 主菜单').click()
    await button(page, '继续生涯').waitFor()
    assert.deepEqual((await archiveLobby(page, 'family')).careers, [])
    const family = await createArchive(page, 'family')
    await toArchiveLobby(page)
    await button(page, '返回').click()
    await button(page, '继续生涯').waitFor()
    await button(page, '返回').click()
    await rootVisible(page)
    assert.deepEqual((await archiveLobby(page, 'witness')).careers, [])
    const witness = await createArchive(page, 'witness')
    assert.equal(new Set([witness.id, family.id, county.world_id]).size, 3)
    await toArchiveLobby(page)
    await button(page, '返回').click()
    await rootVisible(page)
    await context.close()
    context = null
    await fixture.restart()
    context = await fixture.browser.newContext()
    page = await context.newPage()
    page.setDefaultTimeout(8000)
    await page.goto(fixture.session)
    await rootVisible(page)
    const remembered = await archiveLobby(page, 'witness')
    assert.deepEqual(remembered.careers.map(c => c.id), [witness.id])
    await resume(page, witness)
    await toArchiveLobby(page)
    await button(page, '返回').click()
    await rootVisible(page)
    await careerLobby(page)
    const restoredCounty = await interact(page, 'GET', '/api/worlds/' + county.world_id, () => button(page, '继续生涯').click())
    assert.equal(restoredCounty.world_id, county.world_id)
    assert.equal(restoredCounty.name, name)
    assert.equal(restoredCounty.revision, county.revision)
    await button(page, '局中事 主菜单').click()
    const restoredFamily = await archiveLobby(page, 'family')
    assert.deepEqual(restoredFamily.careers.map(c => c.id), [family.id])
    await resume(page, family)
  } finally {
    try {
      await context?.close()
    } finally {
      await fixture.close()
    }
  }
})

test('event directory covers the published catalogue, filters by era and launches the chosen witness',async()=>{
  const fixture=await startBrowserFixture()
  try {
    const page=await fixture.browser.newPage({viewport:{width:390,height:844}})
    const {chapters}=await openLobby(page,fixture)
    await page.setViewportSize({width:320,height:710})
    const events=page.getByLabel('选择亲历者与起始事件')
    const initial=await events.inputValue()
    const longest=await events.evaluate(select=>Array.from(select.options).sort((a,b)=>b.text.length-a.text.length)[0].value)
    await events.selectOption(longest)
    assert.ok(await events.evaluate(select=>select.getBoundingClientRect().right<=innerWidth && document.documentElement.scrollWidth===innerWidth))
    await events.selectOption(initial)
    await page.setViewportSize({width:390,height:844})
    await page.getByRole('button',{name:'浏览全部 '+chapters.length+' 个历史事件 ↓'}).click()
    const directory=page.getByRole('region',{name:'可选历史事件'})
    const cards=directory.locator('.event-grid>button')
    assert.equal(await cards.count(),chapters.length)
    const imageSizes=await cards.locator('img').evaluateAll(async imgs=>Promise.all(imgs.map(async img=>{
      img.loading='eager'
      await img.decode()
      return [img.naturalWidth,img.naturalHeight]
    })))
    assert.ok(imageSizes.every(([w,h])=>w>=400 && h>=250))
    await directory.getByRole('button',{name:'1949年前',exact:true}).click()
    assert.equal(await cards.count(),chapters.filter(ch=>Number.parseInt(ch.year,10)<1949).length)
    await directory.getByRole('button',{name:'全部',exact:true}).click()
    await directory.getByRole('searchbox').fill('卞仲耘')
    const selected=cards.filter({hasText:'文革中的卞仲耘'})
    await selected.click()
    assert.equal(await page.getByLabel('选择亲历者与起始事件').inputValue(),'witness_bian')
    await button(page, '年代与出处').click()
    const sources = page.getByRole('dialog', { name: '年代与出处' })
    assert.equal(await sources.getByLabel('查阅年代').inputValue(), 'witness_bian')
    await button(sources, '返回').click()
    assert.equal(await page.getByLabel('为这段长篇命名').inputValue(),'')
    const view=await interact(page,'POST',api,()=>button(page,'开始长篇').click())
    assert.equal(view.start_chapter,'witness_bian')
    assert.match(view.name,/1966/)
    assert.match(await story(page).locator('.date-line').innerText(),/王晶垚/)
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth))
  } finally { await fixture.close() }
})

test('a featured dressmaking story remembers the chosen pattern and resumes from the title screen', async () => {
  const f = await startBrowserFixture()
  try {
    const page = await f.browser.newPage({viewport: {width: 390, height: 844}})
    await page.goto(f.session)
    await button(page,'借一只袖子').click()
    const name = '拆开裁缝学徒的布信封'
    const view = await interact(page,'POST',api,() => page.getByRole('button',{name}).click())
    assert.equal(view.chapter_count,1)
    const path = api + '/' + view.id
    let game = view
    for (const id of ['ask_wearer','keep_playing','owner_cloth'])
      game = await choose(page,game,id)
    assert.equal(game.scene.id,'air_monitor')
    const bench = page.getByRole('region',{name:'裁缝试样台'})
    await button(bench,'腋下嵌三角').click()
    await bench.getByRole('slider').focus()
    await page.keyboard.press('End')
    await bench.getByText(/弓走到底/).waitFor()
    game = await interact(page,'POST',path+'/choices',() => bench.getByRole('button',{name:/剪开里襟/}).click())
    assert.equal(game.scene.id,'air_flash')
    await page.reload()
    await button(page,'借一只袖子').click()
    const resumed = await interact(page,'GET',path,() => page.getByRole('button',{name}).click())
    assert.equal(resumed.id,game.id)
    assert.equal(resumed.revision,game.revision)
    await page.getByRole('heading',{name:game.scene.title}).waitFor()
    assert.ok(await page.locator('.scene-art .reading-space').evaluate(i => i.complete && i.naturalWidth>100))
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth))
  } finally { await f.close() }
})

test('the cover can resume the same five-part serial while the two mode entrances remain available', async () => {
  const f = await startBrowserFixture()
  try {
    const p = await f.browser.newPage({viewport:{width:1024,height:768}})
    await p.goto(f.session)
    const open = () => p.getByRole('button',{name:/从西安的第三把椅子开始/}).click()
    const first = await interact(p,'POST',api,open)
    assert.equal(first.chapter_count,5)
    assert.equal(first.edition,'serial_v1')
    assert.equal(first.scene.id,'xian_wait')
    const next = await choose(p,first,first.scene.choices[0].id)
    await button(p,'返回').click()
    await p.getByRole('group',{name:'模式选择'}).waitFor()
    await p.reload()
    const resumed = await interact(p,'GET',api+'/'+first.id,open)
    assert.equal(resumed.id,first.id)
    assert.equal(resumed.scene.id,next.scene.id)
    assert.equal(resumed.revision,next.revision)
    await p.getByRole('heading',{name:next.scene.title,exact:true}).waitFor()
  } finally { await f.close() }
})

test('walking around the half cistern changes its outline and reports a field comparison', async () => {
  const fixture = await startBrowserFixture()
  try {
    for (const [width, picked] of [[390, 'bank_one'], [1100, 'bank_two'], [800, 'bank_why']]) {
      const page = await fixture.browser.newPage({ viewport: { width, height: 850 } })
      await openLobby(page, fixture)
      await page.getByLabel('选择亲历者与起始事件').selectOption('witness_gao')
      await page.getByLabel('为这段长篇命名').fill('坡背' + width)
      let v = await interact(page, 'POST', api, () => button(page, '开始长篇').click())
      for (const id of ['bank_long', 'bank_up', 'bank_measure', 'bank_trace']) v = await choose(page,v,id)
      const survey = page.getByRole('region', { name: '绕池勘察' })
      await survey.waitFor()
      if (picked === 'bank_why') {
        await page.getByText('翻阅纸本走访记录', {exact:true}).click()
        await page.getByText('两个木牌',{ exact:true }).click()
        await survey.waitFor()
        v = await choose(page, v, picked)
      } else {
        const road = await survey.locator('svg').innerHTML()
        await button(survey, '侧坡').focus()
        await page.keyboard.press('Space')
        assert.equal(await button(survey, '侧坡').getAttribute('aria-pressed'), 'true')
        assert.notEqual(await survey.locator('svg').innerHTML(), road)
        const slider = survey.getByRole('slider', { name: '沿田埂移动' })
        await slider.focus()
        await page.keyboard.press('ArrowRight')
        assert.equal(await slider.inputValue(), '89')
        await button(survey,'背坡').click()
        await survey.getByRole('img', {name:/从背坡看，墙只砌了半弧/}).waitFor()
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
        await button(survey, '南路 · 三号牌').click()
        await button(survey, '东滩 · 饮水池').click()
        await button(survey,'核对这两处').click()
        await survey.getByText(/这两处对不上/).waitFor()
        if (picked === 'bank_one') {
          await button(survey, '东滩 · 饮水池').focus()
          await page.keyboard.press('Enter')
          await button(survey, '北路 · 四号牌').click()
          await button(survey,'核对这两处').click()
          await survey.getByText(/两条路指到同一道缺墙/).waitFor()
          if (process.env.JZS_RIDGE_PREVIEW) await survey.screenshot({path: process.env.JZS_RIDGE_PREVIEW})
        }
        const next = await interact(page,'POST',api+'/'+v.id+'/choices',() =>
          button(survey, picked === 'bank_one' ? '把这两条路记为一座池' : '先向木匠问清编号').click())
        assert.equal(next.revision, v.revision + 1)
        v = next
      }
      assert.equal(v.journal.at(-1).choice,picked)
      assert.equal(v.scene.id,picked === 'bank_two' ? 'bank_number' : 'bank_wages')
      if(picked === 'bank_one') assert.deepEqual(v.journal.at(-1).citations.map(c => c.id).sort(), ['north','south'])
      await page.close()
    }
  } finally {
    await fixture.close()
  }
})

test('the two courtyard drawings return years later and can be traced to the night they were made', async () => {
  const fixture = await startBrowserFixture()
  try {
    const page = await fixture.browser.newPage({ viewport: { width: 390, height: 795 } })
    await page.goto(fixture.session)
    await button(page, '粉笔画不圆的月亮').click()
    let game = await interact(page, 'POST', api, () => page.getByRole('button', { name: /走进王晶垚和孩子们的小院/ }).click())
    for (const id of ['sky_fact','sky_move','sky_swap']) game = await choose(page, game, id)
    const bench = page.getByRole('region', { name: '院里的月相桌' })
    const action = /把两张月样对折/
    assert.equal(await page.getByRole('button',{name: action}).count(), 0)
    const slider = bench.getByRole('slider')
    await slider.focus()
    await page.keyboard.press('End')
    await bench.getByRole('img', {name: '从这里看见一轮圆月'}).waitFor()
    for (const [who, phase] of [['蒋禾','一弯月牙'],['阿砚','鼓起来的月亮']]) {
      await button(bench, '站到' + who + '的脚印里').focus()
      await page.keyboard.press('Enter')
      await bench.getByRole('img', {name: '从这里看见' + phase}).waitFor()
      await button(bench, '把眼前的月样描在纸上').click()
    }
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
    game = await interact(page, 'POST', api + '/' + game.id + '/choices', () => bench.getByRole('button', { name: action }).click())
    for (const id of ['sky_work','sky_pay','sky_private','sky_guest_out']) game = await choose(page, game, id)
    const callback = page.locator('aside.story-echo').filter({hasText: '扁铁盒'})
    await callback.locator('summary').click()
    await callback.getByText('把两张月样对折，鞋尖朝向也画上去', {exact:true}).waitFor()
    game = await choose(page, game, 'sky_pass_sketch')
    assert.ok(game.marks.includes('院课 · 后排学生当了一堂老师'))
  } finally { await fixture.close() }
})

test('both mode entrances fit the opening screen and accept a click without scrolling', {timeout:30000}, async () => {
  const fixture = await startBrowserFixture()
  try {
    for (const [width,height] of [[1280,800],[1024,720],[390,844],[320,568]]) {
      const page = await fixture.browser.newPage({viewport:{width,height}})
      await page.goto(fixture.session)
      const modes = page.getByRole('group',{name:'模式选择'})
      await modes.waitFor()
      await page.evaluate(() => document.fonts.ready)
      assert.equal(await modes.getByRole('button').count(),2)
      for (const name of ['生涯模式','历史主角模式']) {
        const accessible = await button(modes,name).evaluate(node => {
          const r = node.getBoundingClientRect()
          const center = document.elementFromPoint(r.left + r.width / 2,r.top + r.height / 2)
          return scrollY === 0 && r.left >= 0 && r.right <= innerWidth
            && r.top >= 0 && r.bottom <= innerHeight && node.contains(center)
        })
        assert.ok(accessible,`${name} should be visible and uncovered on a fresh ${width}×${height} screen`)
      }
      await page.close()
    }
  } finally {await fixture.close()}
})

test('the chapter title and route to the decision stay in reach on desktop and phone', {timeout:30000}, async () => {
  const fixture = await startBrowserFixture()
  try {
    for (const viewport of [{width:1280,height:800},{width:390,height:844}]) {
      const page = await fixture.browser.newPage({viewport})
      await openLobby(page,fixture)
      await page.getByLabel('选择亲历者与起始事件').selectOption(chapterId)
      await page.getByLabel('为这段长篇命名').fill('开篇阅读 '+viewport.width)
      const opening = await interact(page,'POST',api,() => button(page,'开始长篇').click())
      const chapter = story(page)
      const title = chapter.getByRole('heading',{name:opening.scene.title,exact:true})
      const jump = chapter.getByRole('button',{name:/^本幕行动/})
      for (const el of [title,jump]) {
        await el.waitFor()
        assert.ok(await el.evaluate(node => {
          const r=node.getBoundingClientRect()
          return r.top >= 0 && r.bottom <= innerHeight
            && node.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))
        }), 'the scene title and first shortcut to choices should be in sight on entry')
      }
      await jump.click()
      const choices = page.getByRole('group',{name:'本幕行动'})
      assert.ok(await choices.evaluate(node => node.contains(document.activeElement)))
      await button(page,'镜头阅读').click()
      const reel = page.getByRole('region',{name:'镜头阅读'})
      await button(reel,'直接作决定').click()
      assert.ok(await choices.evaluate(node => node.contains(document.activeElement)))
      await button(page,'返回').click()
      await resume(page,opening)
      await page.close()
    }
  } finally {await fixture.close()}
})
