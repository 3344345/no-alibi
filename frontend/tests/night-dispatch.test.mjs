import assert from 'node:assert/strict'
import { test } from 'node:test'
import { startBrowserFixture } from './browser-engine.mjs'

test('the night dispatch works by keyboard on a narrow screen and returns to the county desk', async () => {
  const fixture = await startBrowserFixture()
  try {
    const ctx = await fixture.browser.newContext({ viewport: { width: 360, height: 740 } })
    const page = await ctx.newPage()
    // macOS WebKit defaults to Option-Tab for visiting all form controls.
    const nextControl = process.platform === 'darwin' && fixture.browser.browserType().name() === 'webkit'
      ? 'Alt+Tab' : 'Tab'
    await page.goto(fixture.session)
    await page.getByRole('button', { name: '生涯模式', exact: true }).click()
    await page.getByRole('button', { name: '建立生涯' }).click()
    await page.getByRole('button', { name: '进入办公室' }).click()
    const story = page.getByRole('region', { name: '夜班车不进站' })
    await story.getByRole('button', { name: /替伍琴排一趟/ }).click()
    const board = story.getByRole('region', { name: '七路调度台' })
    await board.getByRole('radio', { name: '22:40' }).focus()
    await page.keyboard.press('ArrowRight')
    assert.ok(await board.getByRole('radio', { name: '22:46' }).isChecked())
    await page.keyboard.press(nextControl)
    assert.ok(await board.getByRole('radio', { name: '沿河直行' }).evaluate(el => el === document.activeElement))
    await page.keyboard.press('ArrowRight')
    assert.ok(await board.getByRole('radio', { name: '绕澡堂' }).isChecked())
    await board.getByText('23:04', { exact: true }).waitFor()
    await board.getByText('三人都能搭上车').waitFor()
    await board.getByText('到桥时，接班车已经走了').waitFor()
    assert.ok(await board.evaluate(el => el.scrollWidth <= el.clientWidth + 1))
    await page.keyboard.press(nextControl)
    assert.ok(await board.getByRole('button', { name: /把这张表念给伍琴听/ }).evaluate(el => el === document.activeElement))
    await page.keyboard.press('Enter')
    await story.getByRole('heading', { name: '南门旧站牌碰面' }).waitFor()
    await story.getByRole('button', { name: /^赴约/ }).click()
    await story.getByText(/男孩认出了你的声音.*22:46/).waitFor()
    await ctx.close()
  } finally {
    await fixture.close()
  }
})
