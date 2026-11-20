import { strict as assert } from 'node:assert'
import { test } from 'node:test'
import { startBrowserFixture } from './browser-engine.mjs'

test('all three local reels play, seek with the keyboard and show their Chinese notes offline', { timeout: 90000 }, async () => {
  const fixture = await startBrowserFixture()
  try {
    const page = await fixture.browser.newPage({viewport: {width: 930, height: 760}})
    const outside = []
    await page.route('**/*', async route => {
      const url = new URL(route.request().url())
      if (url.hostname !== '127.0.0.1') {
        outside.push(url.toString())
        return route.abort()
      }
      return route.continue()
    })
    await page.goto(fixture.session)
    const open = page.getByRole('button', {name: '年代放映室', exact: true})
    await open.focus()
    await page.keyboard.press('Enter')
    const dialog = page.getByRole('dialog', {name: '年代放映室'})
    for (const [movie, stop, start] of [
      ['从午门望进去', '门前的台阶', 21], ['汽车开进人群', '车顶周围', 22], ['合资厂的展示室', '转向展示区', 65],
    ]) {
      await dialog.getByRole('button', {name: new RegExp(movie)}).click()
      const video = dialog.locator('video')
      await page.waitForFunction(() => document.querySelector('video')?.readyState >= 1)
      assert.equal(await video.evaluate(v => v.paused && v.muted), true)
      assert.equal(await video.evaluate(v => v.videoWidth > 0), true)
      await dialog.getByRole('button', {name: new RegExp(stop)}).focus()
      await page.keyboard.press('Enter')
      await page.waitForFunction(s => {
        const v = document.querySelector('video')
        return v && !v.paused && v.currentTime > s + .15 && !!v.textTracks[0]?.activeCues?.length
      }, start)
      assert.equal(await video.evaluate(v => v.textTracks[0].language), 'zh')
    }
    await dialog.locator('summary').click()
    assert.match(await dialog.getByRole('link').getAttribute('href'), /reaganlibrary.gov/)
    await page.setViewportSize({width: 400, height: 640})
    assert.equal(await dialog.evaluate(d => d.scrollWidth <= d.clientWidth + 1), true)
    await page.keyboard.press('Escape')
    await dialog.waitFor({state: 'detached'})
    assert.equal(await open.evaluate(b => document.activeElement === b), true)
    assert.deepEqual(outside, [])
  } finally {
    await fixture.close()
  }
})
