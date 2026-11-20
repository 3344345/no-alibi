import assert from 'node:assert/strict'
import { test } from 'node:test'
import { startBrowserFixture } from './browser-engine.mjs'

test('the family shadow booth rehearses three poses and saves only the opening gong', {timeout:90000}, async () => {
  const fixture = await startBrowserFixture()
  const button = (scope, name) => scope.getByRole('button', {name, exact:true})
  try {
    const page = await fixture.browser.newPage({viewport:{width:390,height:790}})
    const clips = []
    page.on('request', req => { if (req.url().includes('/sound/booth_')) clips.push(req.url()) })
    await page.goto(fixture.session)
    await button(page, '借我一张脸').click()
    await button(page, '钻进喜棚后面的影箱').click()
    await page.getByRole('button', {name:/钻到席底下去/}).click()
    await page.getByRole('button', {name:/把靠出口的矮凳让她/}).click()
    const booth = page.getByRole('region', {name:'喜棚掌签台'})
    await booth.waitFor()
    const rows = page.locator('article.story footer > span')
    const before = await rows.innerText()
    await button(booth, '两头争轿').press('Enter')
    await booth.getByRole('img', {name:'戏窗上的姿势：两头争轿'}).waitFor()
    const motion = booth.getByLabel('两位娘的竹签', {exact:false})
    await motion.press('Home')
    await booth.getByRole('img', {name:'戏窗上的姿势：两背相靠'}).waitFor()
    await button(booth,'试走这段锣点').press('Enter')
    await booth.getByText(/另一边却破了音/).waitFor()
    assert.deepEqual(clips, [])
    await page.getByRole('switch', {name:'历史长篇音效'}).click()
    const response = page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/booth_walk.mp3'))
    await button(booth, '新娘退场').press('Enter')
    assert.ok((await response).ok())
    assert.equal(await rows.innerText(), before)
    assert.equal(await booth.evaluate(el => el.scrollWidth<=el.clientWidth+1),true)
    await booth.getByRole('button', {name:/让新娘出了影窗/}).press('Enter')
    await page.getByRole('heading', {name:'空轿倒有人要坐'}).waitFor()
    await page.reload()
    await button(page, '借我一张脸').click()
    await button(page, '钻进喜棚后面的影箱').click()
    await page.getByRole('button', {name:/让小圆自己试坐那顶空轿/}).click()
    await page.getByRole('heading', {name:'有一块肉专等迟到的人'}).waitFor()
  } finally { await fixture.close() }
})
