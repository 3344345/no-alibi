import { strict as assert } from 'node:assert'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'
import { startBrowserFixture } from './browser-engine.mjs'

test('the story screening library and cast credits work offline at a narrow viewport', { timeout: 120000 }, async () => {
  const fixture = await startBrowserFixture()
  try {
    const page = await fixture.browser.newPage({ viewport: { width: 410, height: 805 } })
    const outside = []
    await page.route('**/*', route => {
      if (new URL(route.request().url()).hostname === '127.0.0.1') return route.continue()
      outside.push(route.request().url())
      return route.abort()
    })
    await page.goto(fixture.session)
    const open = page.getByRole('button', { name: '剧情放映厅', exact: true })
    await open.click()
    const theater = page.getByRole('dialog', { name: '剧情放映厅' })
    const catalog = JSON.parse(await readFile(new URL('../src/screenings.json', import.meta.url)))
    assert.equal(catalog.flatMap(shelf => shelf.films).length, 49)
    for (const shelf of catalog) {
      await theater.getByRole('button', { name: new RegExp('^' + shelf.name) }).click()
      const list = theater.getByRole('navigation', { name: shelf.name + '片单' })
      assert.equal(await list.getByRole('button').count(), shelf.films.length)
      for (const film of shelf.films) {
        await list.getByRole('button', { name: film.setting + ' ' + film.title, exact: true }).click()
        const video = theater.locator('video')
        await page.waitForFunction(id => {
          const v = document.querySelector('dialog video')
          return v?.src.endsWith('/' + id + '.mp4') && v.videoWidth > 0 && v.textTracks[0]?.cues?.length > 0
        }, film.id)
        assert.equal(await video.evaluate(v => v.paused), true)
      }
    }
    await theater.getByRole('button', { name:'声音关' }).click()
    await theater.getByRole('button', { name:'字幕开' }).click()
    const media = theater.locator('video')
    const state = await media.evaluate(v => [v.muted, v.textTracks[0].mode])
    assert.deepEqual(state, [false, 'disabled'])
    await media.evaluate(v => { v.muted = true; return v.play() })
    await page.waitForFunction(() => document.querySelector('dialog video')?.currentTime > .15)
    assert.equal(await theater.evaluate(d => d.scrollWidth <= d.clientWidth + 1), true)
    await page.keyboard.press('Escape')
    await theater.waitFor({ state: 'detached' })
    assert.equal(await open.evaluate(b => document.activeElement === b), true)

    const castButton = page.getByRole('button', { name:'人物与出处', exact:true })
    await castButton.click()
    const gallery = page.getByRole('dialog', { name:'人物与出处' })
    const names = gallery.getByRole('navigation', { name:'人物名单' })
    const data = async (name) => JSON.parse(await readFile(new URL('../src/' + name + 'Cast.json', import.meta.url)))
    const photos = await data('historical'), originals = await data('original')
    assert.equal(await names.getByRole('button').count(), Object.keys(photos).length + Object.keys(originals).length)
    const find = gallery.getByRole('searchbox', {name:'找人物'})
    await find.fill('李鹏')
    assert.equal(await gallery.getByRole('link', {name:/查看照片来源/}).getAttribute('href'), photos.李鹏.source)
    assert.equal(await gallery.getByRole('link', {name:/CC BY-SA/}).getAttribute('href'), photos.李鹏.licenseUrl)
    assert.match(await gallery.getByRole('article').innerText(), /沿用 CC BY-SA/)
    await find.fill('高勤荣')
    assert.equal(await gallery.getByRole('article').getByRole('img').getAttribute('src'), '/cast/' + originals.高勤荣.file + '.webp')
    assert.match(await gallery.getByRole('article').innerText(), /原创戏剧造型/)
    assert.equal(await gallery.getByRole('link').count(), 0)
    await find.fill('无此角色')
    await gallery.getByRole('button', {name:'查看全部人物'}).click()
    await gallery.getByRole('button', {name:'历史照片',exact:true}).click()
    assert.equal(await names.getByRole('button').count(), Object.keys(photos).length)
    assert.equal(await gallery.evaluate(d => d.scrollWidth <= d.clientWidth + 1), true)
    await page.keyboard.press('Escape')
    await page.getByRole('button', {name:'年代放映室',exact:true}).click()
    await page.getByRole('dialog', {name:'年代放映室'}).waitFor()
    assert.deepEqual(outside, [])
  } finally {
    await fixture.close()
  }
})
