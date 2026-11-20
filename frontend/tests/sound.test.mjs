import assert from 'node:assert/strict'
import test from 'node:test'
import { readFile } from 'node:fs/promises'
import ts from 'typescript'

// Node 22.0 does not load TypeScript directly. Use the project's pinned compiler.
const source = await readFile(new URL('../src/sound.ts', import.meta.url), 'utf8')
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
})
const { committedSound, soundSamples, cue, enableSound, setSoundVolume, silence } = await import(
  'data:text/javascript;base64,' + Buffer.from(outputText).toString('base64')
)

const base = { world_id: 'a', revision: 3, location: { id: 'L01' }, documents: [{ id: 'D01' }] }
const inbox = { id: 'new-letter', source_id: 'N14', kind: '文件声称' }

test('only a new visible incoming document or confirmed arrival cues a world change', () => {
  const next = { ...base, revision: 4 }
  assert.equal(committedSound(base, next), undefined)
  assert.equal(committedSound(base, { ...next, location: { id: 'L02' } }), 'arrival')
  assert.equal(committedSound(base, { ...next, documents: [...base.documents, inbox] }), 'delivery')
  assert.equal(
    committedSound(base, { ...next, documents: [inbox], location: { id: 'L02' } }),
    'arrival',
  )
  assert.equal(
    committedSound(base, { ...next, documents: [{ ...inbox, kind: '本人观察' }] }),
    undefined,
  )
  assert.equal(
    committedSound(base, { ...next, documents: [{ ...inbox, source_id: '本人' }] }),
    undefined,
  )
  assert.equal(committedSound(base, { ...base, documents: [inbox] }), undefined)
  assert.equal(committedSound(base, { ...next, world_id: 'b', documents: [inbox] }), undefined)
})

test('the three mono foley cues begin and finish quietly and retain headroom', () => {
  for (const kind of ['paper', 'delivery', 'arrival']) {
    const pcm = soundSamples(kind)
    assert.ok(pcm.length >= 2400 && pcm.length <= 7680)
    assert.equal(Math.abs(pcm[0]), 0)
    assert.equal(Math.abs(pcm.at(-1)), 0)
    assert.ok(pcm.every(Number.isFinite))
    const peak = pcm.reduce((v, x) => Math.max(v, Math.abs(x)), 0)
    assert.ok(peak > 0.08 && peak < 0.3)
  }
})

test('mute, hidden documents, keyboard unlocking and rapid repeated cues remain bounded', () => {
  let now = 1000,
    created = 0,
    started = 0,
    stopped = 0,
    lastGain
  const replacements = {
    document: { visibilityState: 'visible', hasFocus: () => true },
    performance: { now: () => now },
    AudioContext: class {
      state = 'running'
      currentTime = 0
      destination = {}
      constructor() {
        created++
      }
      createGain() {
        return {
          gain: {
            value: 0,
            setTargetAtTime(v) {
              lastGain = v
            },
          },
          connect() {},
        }
      }
      createBuffer() {
        return { copyToChannel() {} }
      }
      createBufferSource() {
        return {
          connect() {},
          disconnect() {},
          start() {
            started++
          },
          stop() {
            stopped++
          },
        }
      }
      resume() {
        this.state = 'running'
        return Promise.resolve()
      }
      suspend() {
        this.state = 'suspended'
        return Promise.resolve()
      }
    },
  }
  const originals = new Map(
    Object.keys(replacements).map((key) => [key, Object.getOwnPropertyDescriptor(globalThis, key)]),
  )
  try {
    for (const [key, value] of Object.entries(replacements))
      Object.defineProperty(globalThis, key, { configurable: true, value })
    setSoundVolume(0)
    enableSound()
    cue('arrival')
    assert.equal(created, 0)
    setSoundVolume(40)
    enableSound()
    cue('paper')
    cue('paper')
    assert.equal(created, 1)
    assert.equal(started, 1)
    now += 600
    cue('delivery')
    assert.equal(started, 2)
    setSoundVolume(0)
    assert.equal(lastGain, 0)
    assert.equal(stopped, 1)
    now += 1000
    cue('arrival')
    assert.equal(started, 2)
    globalThis.document.visibilityState = 'hidden'
    setSoundVolume(60)
    enableSound()
    cue('arrival')
    assert.equal(started, 2)
    silence()
  } finally {
    for (const [key, original] of originals) {
      if (original) Object.defineProperty(globalThis, key, original)
      else delete globalThis[key]
    }
  }
})

test('scene layers survive unchanged rooms, replace a single stem, and ignore late decodes after exit', async () => {
  // A fresh graph avoids coupling the test to the user's saved master volume.
  const api = await import('data:text/javascript;base64,' + Buffer.from(outputText).toString('base64') + '#layers')
  const requests = [], starts = [], stops = []
  let decode, late = false
  const replacements = {
    document: { visibilityState: 'visible', hasFocus: () => true },
    fetch: async (url) => {
      requests.push(url.split('/').at(-1))
      return { ok: true, arrayBuffer: async () => url }
    },
    AudioContext: class {
      state = 'running'
      currentTime = 1
      destination = {}
      createGain() {
        return { gain: { value: 0, setTargetAtTime() {}, cancelScheduledValues() {} },
          connect() {}, disconnect() {} }
      }
      createBufferSource() {
        return { connect() {}, disconnect() {}, start() { starts.push(this.buffer) },
          stop() { stops.push(this.buffer) } }
      }
      async decodeAudioData(url) {
        if (late) await new Promise((done) => { decode = done })
        return url.split('/').at(-1)
      }
      async suspend() { this.state = 'suspended' }
      async resume() { this.state = 'running' }
    },
  }
  const prior = new Map(Object.keys(replacements).map((key) =>
    [key, Object.getOwnPropertyDescriptor(globalThis, key)]))
  const settle = () => new Promise((done) => setImmediate(done))
  try {
    for (const [key, value] of Object.entries(replacements))
      Object.defineProperty(globalThis, key, { configurable: true, value })
    api.setSoundscape({room:'exchange', music:'question'})
    api.enableSound()
    assert.deepEqual(requests, [])
    api.setSoundVolume(40)
    api.enableSound()
    await settle()
    assert.deepEqual(starts.sort(), ['exchange.mp3','question.mp3'])
    api.setSoundscape({room:'exchange', music:'question'})
    api.enableSound()
    assert.equal(requests.length, 2)
    api.setSoundscape({room:'projector', music:'question'})
    await settle()
    assert.deepEqual(stops, ['exchange.mp3'])
    assert.equal(starts.at(-1), 'projector.mp3')
    late = true
    api.setSoundscape({room:'projector', music:'vigil'})
    await settle()
    api.setSoundscape(undefined)
    decode()
    await settle()
    assert.equal(starts.length, 3)
    assert.ok(stops.includes('question.mp3') && stops.includes('projector.mp3'))
    api.enableSound()
    assert.equal(requests.length, 4)
  } finally {
    api.setSoundVolume(0)
    for (const [key, original] of prior) {
      if (original) Object.defineProperty(globalThis, key, original)
      else delete globalThis[key]
    }
  }
})

test('alternate timelines keep their local year and location in scenes, handovers, and the journal', async () => {
  const source = await readFile(new URL('../src/chronicleScene.ts', import.meta.url), 'utf8')
  const result = ts.transpileModule(source, {compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}})
  const {sceneSetting} = await import('data:text/javascript;base64,' + Buffer.from(result.outputText).toString('base64'))
  const opening = {year:'1966',place:'北京·师大女附中'}
  for (const [scene, title, year] of [['sky_shift','二幕 · 1972年，凳子长高了','1972'],['sky_guest','三幕 · 来旁听的大人','1978'],['sky_last','四幕 · 那个不圆的地方','1986']]) {
    assert.deepEqual(sceneSetting('witness_bian',scene,title,opening),{year,place:'北京'})
  }
  assert.deepEqual(sceneSetting('witness_zhang_xueliang','xian_future_port','十场 · 到岸以后的船板',opening),{year:'架空的1945年',place:'海外港口'})
  assert.equal(sceneSetting('witness_zhang_xueliang','xian_future_trial','十场 · 准你出去一天',opening).year,'架空的1946年')
  assert.equal(sceneSetting('witness_zhang_xueliang','xian_bench','第八场 · 总有人在庭外站着',opening).place,'南京')
  assert.equal(sceneSetting('may_fourth','forme','',opening),opening)
})
