import assert from 'node:assert/strict'
import { test } from 'node:test'
import { startBrowserFixture } from './browser-engine.mjs'

const button = (where, name) => where.getByRole('button', { name, exact: true })

test('the night switchboard changes a reservation before committing one audible or silent call sheet', { timeout: 90000 }, async () => {
  const fixture = await startBrowserFixture()
  try {
    const page = await fixture.browser.newPage({ viewport: { width: 390, height: 780 } })
    await page.goto(fixture.session)
    await button(page, '夜班来电').click()
    await button(page, '把话筒交给第一个来电的人').click()
    const desk = page.getByRole('region', { name: '夜班接线台' })
    await desk.waitFor()
    const submit = button(desk, '送出接线单')
    assert.equal(await submit.isEnabled(), false)
    const samples = []
    page.on('request', req => {
      if (req.url().includes('/chronicle/sound/line_')) samples.push(new URL(req.url()).pathname)
    })
    const guest = button(desk, '接听街口蛋糕房的罗师傅')
    await guest.focus()
    await page.keyboard.press('Enter')
    await desk.getByRole('button', { name: /为什么非得今晚/ }).click()
    await desk.getByText(/拿指头在我手心里头写/).waitFor()
    await button(desk, '把罗师傅的回拨条夹进值班簿').click()
    assert.deepEqual(samples, [])
    const audioButton = page.getByRole('switch', { name: '历史长篇音效' })
    await audioButton.click()
    const cable = button(desk, '接听车场值班房的冯巧')
    await cable.click()
    await button(desk, '把冯巧的回拨条夹进值班簿').click()
    assert.match(await desk.locator('.cost').innerText(), /罗师傅等炉火熄了就得打烊/)
    await button(desk, '接听公用电话的阿年').click()
    await button(desk, '留在唐棠耳机里').click()
    assert.equal(await submit.isEnabled(), true)
    assert.equal(await desk.evaluate(el => el.scrollWidth <= el.clientWidth + 1), true)
    assert.ok(samples.some(path => path.endsWith('line_conductor.mp3')))
    assert.ok(samples.some(path => path.endsWith('line_son.mp3')))
    const response = page.waitForResponse(r => r.request().method() === 'POST' &&
      new URL(r.url()).pathname.endsWith('/choices'))
    await submit.focus()
    await page.keyboard.press('Enter')
    const next = await (await response).json()
    assert.equal(next.scene.id, 'night_listen')
    assert.equal(next.journal.at(-1).choice, 'patch_private_conductor')
    assert.ok(next.marks.includes('约在首班车前给冯巧回电'))
    assert.ok(!next.marks.includes('约在炉火熄前给罗师傅回电'))
    await page.reload()
    await button(page, '夜班来电').click()
    await button(page, '把话筒交给第一个来电的人').click()
    await page.getByRole('heading', {name:next.scene.title,exact:true}).waitFor()
    assert.equal(await desk.count(), 0)
  } finally {
    await fixture.close()
  }
})
