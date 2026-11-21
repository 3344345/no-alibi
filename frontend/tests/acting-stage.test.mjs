import assert from 'node:assert/strict'
import {test} from 'node:test'
import {startBrowserFixture} from './browser-engine.mjs'

test('a live exchange has two beats, commits once, preserves its receipt and hands the real tape desk back', {timeout:90000}, async()=>{
  const fixture=await startBrowserFixture()
  try {
    const page=await fixture.browser.newPage({viewport:{width:960,height:720}})
    const mistakes=[],commands=[]
    page.on('pageerror',e=>mistakes.push(e.message))
    page.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/choices'))commands.push(r.postDataJSON().choice)})
    await page.goto(fixture.session)
    await page.getByRole('button',{name:'倒带七秒',exact:true}).click()
    await page.getByRole('button',{name:'戴上耳机，听那七秒'}).click()
    await page.getByRole('button',{name:'进入现场'}).click()
    const stage=page.getByRole('dialog',{name:'人物现场'})
    assert.match(await stage.locator('.names').innerText(),/邓小平/)
    await stage.getByRole('button',{name:'听现场'}).click()
    await stage.locator('[data-speaker="player"]').waitFor()
    await stage.locator('[data-speaker="reply"],[data-speaker="narrator"]').waitFor()
    const count=commands.length
    await page.keyboard.press('2')
    await stage.locator('[data-speaker="player"]').waitFor()
    await page.keyboard.press('2')
    await stage.locator('[data-speaker="reply"]').waitFor()
    await stage.getByRole('complementary',{name:'刚才的决定与回应'}).waitFor()
    assert.deepEqual(commands.slice(count),['follow_chair'])
    await page.keyboard.press('1')
    const tools=stage.getByRole('region',{name:'现场操作台'})
    await tools.waitFor()
    assert.ok(await tools.locator('input,button').count()>2)
    await page.keyboard.press('Escape')
    const normal=page.getByRole('group',{name:'本幕行动'})
    assert.ok(await normal.locator('input,button').count()>2)
    assert.equal(await page.locator('.on-stage-controls').count(),0)
    assert.deepEqual(mistakes,[])
  } finally {await fixture.close()}
})

test('with reduced motion a county choice remains readable, normal actions and quiet films share the same stage', {timeout:65000},async()=>{
  const fixture=await startBrowserFixture()
  try {
    const page=await fixture.browser.newPage({viewport:{width:390,height:810},reducedMotion:'reduce'})
    await page.goto(fixture.session)
    await page.getByRole('button',{name:'生涯模式',exact:true}).click()
    await page.getByRole('button',{name:'建立生涯'}).click()
    await page.getByRole('button',{name:'进入办公室'}).click()
    await page.getByRole('button',{name:'进入现场'}).click()
    const stage=page.getByRole('dialog',{name:'人物现场'})
    assert.ok(await stage.locator('.decisions button').count()>1)
    await stage.getByRole('button',{name:'观看本场动画'}).click()
    await page.waitForFunction(()=>document.querySelector('.perform video')?.readyState>=2)
    assert.ok(await stage.locator('video').evaluate(v=>v.muted&&v.textTracks[0].mode==='showing'))
    await stage.getByRole('button',{name:'跳过短片'}).click()
    await stage.getByRole('button',{name:'退出现场'}).click()
    assert.ok(await page.getByRole('region',{name:'人物现场'}).isVisible())
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth))
  } finally {await fixture.close()}
})
