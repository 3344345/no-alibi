import { strict as assert } from 'node:assert'
import { test } from 'node:test'
import { startBrowserFixture } from './browser-engine.mjs'

const button = (scope, name) => scope.getByRole('button', { name, exact: true })

test('the Xi’an table lets a player try a bad question, reverse it, and bring a witness to court', { timeout: 90000 }, async () => {
  const fixture = await startBrowserFixture()
  try {
    const page = await fixture.browser.newPage({ viewport: { width: 390, height: 795 } })
    const errors = []
    page.on('pageerror', error => errors.push(error.message))
    await page.goto(fixture.session)
    await button(page, '历史主角模式').click()
    await page.getByLabel('选择亲历者与起始事件').selectOption('witness_zhang_xueliang')
    await page.getByLabel('为这段长篇命名').fill('椅脚杯底')
    async function submit(path, action) {
      const [response] = await Promise.all([
        page.waitForResponse(r => r.request().method() === 'POST' && new URL(r.url()).pathname === path),
        action(),
      ])
      assert.ok(response.ok(), response.status() + ' ' + path)
      return response.json()
    }
    let view = await submit('/api/chronicle', () => button(page, '开始长篇').click())
    async function commit(id) {
      const offered = view.scene.choices.find(c => c.id === id)
      assert.ok(offered, id)
      view = await submit('/api/chronicle/' + view.id + '/choices', () => button(page, offered.label).press('Enter'))
      await page.getByRole('heading', { name: view.scene.title, exact: true }).waitFor()
    }
    await commit('third_chair')
    const seats = page.getByRole('region', { name: '三把椅子' })
    assert.equal(await seats.getByRole('button').count(), 3)
    await commit('nanking')
    const talk = page.getByRole('region', { name: '和南京来客换座谈话' })
    await button(talk, '让他把话说完').press('Enter')
    await talk.getByText(/我隔着整条跑道呢/).waitFor()
    const first = button(talk, '你从跑道上看见了什么？')
    const last = button(talk, '哪一段是你没看见的？')
    await last.press('Enter')
    assert.equal(await button(talk, '照这个次序问').isDisabled(), true)
    await first.press('Enter')
    await button(talk, '照这个次序问').press('Enter')
    await talk.getByText(/像在审一个人/).waitFor()
    const offer = view.scene.choices.find(c => c.id === 'offer_word').label
    assert.equal(await button(talk, offer).count(), 0)
    await button(talk, '两句换个先后').press('Enter')
    await button(talk, '照这个次序问').press('Enter')
    await talk.getByText(/你肯给我一张纸吗/).waitFor()
    assert.equal(await talk.evaluate(el => el.scrollWidth <= el.clientWidth + 1), true)
    const before = view.revision
    await commit('offer_word')
    assert.equal(view.revision, before + 1)
    assert.equal(await seats.getByRole('button').count(), 2)
    await seats.getByText('带走了削好的笔', { exact: true }).waitFor()
    for (const id of ['chair_c', 'alone', 'say', 'pay', 'trial', 'call_runway', 'sleeves']) {
      await commit(id)
    }
    await page.locator('.story-echo').filter({ hasText: '来客的女儿捎来一支短铅笔' }).waitFor()
    assert.equal(view.scene.id, 'xian_future_trial')
    assert.deepEqual(errors, [])
  } finally {
    await fixture.close()
  }
})
