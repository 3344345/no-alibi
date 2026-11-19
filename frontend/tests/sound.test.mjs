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
