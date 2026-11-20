import assert from 'node:assert/strict'
import { test } from 'node:test'
import { startBrowserFixture } from './browser-engine.mjs'

test('the pianist’s tape plays separate local microphones and a long cut changes the broadcast', { timeout: 90000 }, async () => {
  const f = await startBrowserFixture()
  try {
    const page = await f.browser.newPage({ viewport: {width: 390, height: 780} })
    const button = (scope, name) => scope.getByRole('button',{name, exact: true})
    const samples = []
    page.on('response', r => { if (r.ok() && /\/reel_(door|stage|sum)\.mp3$/.test(r.url())) samples.push(new URL(r.url()).pathname) })
    await page.addInitScript(() => {
      window.playedMicrophones = []
      const original = HTMLMediaElement.prototype.play
      HTMLMediaElement.prototype.play = function() {
        if (this.src.includes('/sound/reel_')) this.addEventListener('timeupdate', () => {
          if (!this.paused && this.currentTime > .12) window.playedMicrophones.push(this.src.split('/').at(-1))
        })
        return original.apply(this, arguments)
      }
    })
    await page.goto(f.session)
    await button(page,'倒带七秒').click()
    await button(page,'戴上耳机，听那七秒').click()
    const projection = button(page,'镜头阅读')
    await projection.waitFor()
    if (await projection.getAttribute('aria-pressed') === 'true') await projection.click()
    await button(page,'把自己的位子让给木椅，陪杏儿重新坐一遍').click()
    await button(page,'和她一头一边，把椅子抬到话筒旁边').click()
    const desk = page.getByRole('region',{name:'旧礼堂双路剪辑台'})
    await button(desk,'后门话筒').click()
    await button(desk,'走带').click()
    await page.waitForFunction(() => document.querySelector('.machine output')?.textContent !== '00:00.0')
    await button(desk,'停带').click()
    assert.deepEqual(samples, [])
    await page.getByRole('switch',{name:'历史长篇音效'}).click()
    await button(desk,'台口话筒').focus()
    await page.keyboard.press('Enter')
    await button(desk,'走带').click()
    await page.waitForFunction(() => window.playedMicrophones.includes('reel_stage.mp3'))
    await button(desk,'后门话筒').click()
    await page.waitForFunction(() => window.playedMicrophones.includes('reel_door.mp3'))
    await button(desk,'留到门关 · 12秒').click()
    await desk.getByRole('slider').focus()
    await page.keyboard.press('End')
    await desk.getByText('门关紧后，磁带还走了一小段。').waitFor()
    assert.ok(await desk.evaluate(e => e.scrollWidth <= e.clientWidth+1))
    assert.equal(await page.getByRole('button',{name:'播出七秒广告样带，把厂车的钱敲定'}).count(),0)
    const reply = page.waitForResponse(r=> r.request().method()==='POST' && new URL(r.url()).pathname.endsWith('/choices'))
    await button(desk,'从开头放到门闩落下，连空厅也播出去').press('Enter')
    const view = await (await reply).json()
    assert.equal(view.scene.id,'reel_open')
    assert.ok(view.marks.includes('散场 · 连空厅一起公播'))
    assert.equal(new Set(samples).size,2)
  } finally { await f.close() }
})
