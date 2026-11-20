import assert from 'node:assert/strict'
import { test } from 'node:test'
import { startBrowserFixture } from './browser-engine.mjs'

test('the county screening pays once, changes reels, and brings the audience back one month later', { timeout: 90000 }, async () => {
  const fixture = await startBrowserFixture()
  try {
    const page = await fixture.browser.newPage({viewport:{width:390,height:780}})
    const tracks = new Set()
    page.on('response',r => {if (r.ok() && r.url().includes('/county_cinema_')) tracks.add(new URL(r.url()).pathname)})
    await page.goto(fixture.session)
    await page.getByRole('button',{name:'生涯模式',exact:true}).click()
    await page.getByRole('button',{name:'建立生涯'}).click()
    await page.getByRole('button',{name:'进入办公室'}).click()
    const open = page.getByRole('button',{name:/澄川 · 回声影院.*散场以后/})
    await open.click()
    const theatre = page.getByRole('dialog',{name:'散场以后'})
    async function play(name){ await theatre.getByRole('button',{name}).click() }
    await play(/带上这张票/)
    await play(/^赴约/)
    await play(/跟冉卉去放映间/)
    await play(/等冉卉把卖卡的钱/)
    await play(/收下三千元/)
    await play(/当着买卡人的面去找/)
    const slider = theatre.getByRole('slider')
    await slider.focus()
    await page.keyboard.press('End')
    await theatre.getByRole('img',{name:'六排四座的旧录像情境插画'}).waitFor()
    await page.waitForFunction(() => {
      const img = document.querySelector('dialog .screen > img')
      return img?.currentSrc.endsWith('county-film-chair.webp') && img.complete && img.naturalWidth === 1024
    })
    await theatre.getByRole('button',{name:'门廊下',exact:true}).press('Enter')
    await theatre.getByText(/短辫小姑娘握着半个馒头/).waitFor()
    assert.equal(tracks.size,0)
    await Promise.all([
      page.waitForResponse(r => r.ok() && r.url().includes('/county_cinema_booth.mp3')),
      play('场内声音关'),
    ])
    assert.ok(await theatre.evaluate(el => el.scrollWidth<=el.clientWidth+1))
    await play(/让全场听见年轻的冉卉/)
    await play(/把话筒递给没在片里/)
    await page.keyboard.press('Escape')
    await theatre.waitFor({state:'detached'})
    await open.click()
    await play(/^赴约/)
    await theatre.getByText(/她的名字如今排在售票员下面/).waitFor()
    await play(/把三千元出镜费全退回去/)
    await theatre.getByRole('heading',{name:'一张真正的退票'}).waitFor()
    await play(/收好这张票/)
    await theatre.waitFor({state:'detached'})
    await page.getByRole('region',{name:'夜班车不进站'}).getByRole('button',{name:/约伍琴在收车前见一面/}).waitFor()
  } finally {await fixture.close()}
})
