import type { View } from './types'

export type Sound = 'paper' | 'delivery' | 'arrival'
const durations: Record<Sound, number> = { paper: 0.21, delivery: 0.22, arrival: 0.32 }

type AudibleView = Pick<View, 'world_id' | 'revision' | 'location' | 'documents'>

export function committedSound(before: AudibleView, after: AudibleView): Sound | undefined {
  if (after.world_id !== before.world_id || after.revision <= before.revision) return
  if (before.location.id && after.location.id && after.location.id !== before.location.id)
    return 'arrival'
  const prior = new Set(before.documents.map((item) => item.id))
  const received = after.documents.some(
    (item) =>
      item.id &&
      !prior.has(item.id) &&
      typeof item.source_id === 'string' &&
      /^N\d+$/.test(item.source_id) &&
      item.kind !== '本人观察',
  )
  if (received) return 'delivery'
}

const sampleRate = 24000
const tau = Math.PI * 2

function stroke(t: number, start: number, length: number) {
  const u = (t - start) / length
  return u > 0 && u < 1 ? Math.sin(Math.PI * u) ** 2 : 0
}

function knock(t: number, pitch: number, decay: number) {
  if (t < 0) return 0
  const ring = Math.sin(tau * pitch * t) + 0.35 * Math.sin(tau * 2.63 * pitch * t)
  return (1 - Math.exp(-t / 0.003)) * Math.exp(-t / decay) * ring
}

/** Three short mono foley samples. The fixed noise stream is independent of the game seed. */
export function soundSamples(kind: Sound): Float32Array<ArrayBuffer> {
  const samples = new Float32Array(Math.ceil(durations[kind] * sampleRate))
  let noiseSeed = 84769,
    fast = 0,
    slow = 0
  for (let i = 0; i < samples.length; i++) {
    const t = i / sampleRate
    noiseSeed = (Math.imul(noiseSeed, 1664525) + 1013904223) >>> 0
    const noise = noiseSeed / 2147483648 - 1
    fast += 0.56 * (noise - fast)
    slow += 0.16 * (fast - slow)
    const grain = fast - slow
    let value: number
    if (kind === 'paper') {
      // Paper bends, then its free edge brushes the next sheet.
      value = grain * (0.28 * stroke(t, 0, 0.115) + 0.16 * stroke(t, 0.092, 0.117))
    } else if (kind === 'delivery') {
      // A folder lands on the desk and its cover settles.
      value =
        0.18 * knock(t, 236, 0.024) +
        0.1 * grain * stroke(t, 0.007, 0.086) +
        0.07 * knock(t - 0.089, 321, 0.014)
    } else {
      // Two muted footsteps; both decay before the new scene is read.
      value =
        0.15 * knock(t, 123, 0.027) +
        0.13 * knock(t - 0.15, 107, 0.035) +
        0.13 * slow * (stroke(t, 0.005, 0.086) + stroke(t, 0.156, 0.11))
    }
    const fade = Math.min(1, (samples.length - 1 - i) / (sampleRate * 0.012))
    samples[i] = value * fade
  }
  return samples
}

let level = 0,
  lastPlayed = -Infinity,
  generation = 0
let context: AudioContext | undefined, master: GainNode | undefined
let active: AudioBufferSourceNode | undefined
const samples = new Map<Sound, AudioBuffer>()

function foreground() {
  return document.visibilityState === 'visible' && document.hasFocus()
}

export function setSoundVolume(volume: number) {
  level = Number.isFinite(volume) ? Math.max(0, Math.min(100, volume)) / 100 : 0
  if (master && context) master.gain.setTargetAtTime(level, context.currentTime, 0.008)
  if (!level) silence()
}

export function silence() {
  generation++
  active?.stop()
  active = undefined
  if (context?.state === 'running') void context.suspend().catch(() => {})
}

/** Called by user gestures so delayed, confirmed world changes can sound in WebKit. */
export function enableSound() {
  if (!level || !foreground()) return
  try {
    if (!context) {
      context = new AudioContext({ latencyHint: 'interactive' })
      master = context.createGain()
      master.gain.value = level
      master.connect(context.destination)
    }
    if (context.state === 'suspended') void context.resume().catch(() => {})
  } catch {
    /* Some devices have no available audio output. */
  }
}

export function cue(kind: Sound | undefined) {
  if (!kind || !context || !master || !level || !foreground()) return
  const audio = context,
    output = master,
    requested = performance.now(),
    version = generation
  const play = () => {
    const now = performance.now()
    if (
      version !== generation ||
      !level ||
      !foreground() ||
      audio.state !== 'running' ||
      now - requested > 200 ||
      now - lastPlayed < 450
    )
      return
    let buffer = samples.get(kind)
    if (!buffer) {
      const waveform = soundSamples(kind)
      buffer = audio.createBuffer(1, waveform.length, sampleRate)
      buffer.copyToChannel(waveform, 0)
      samples.set(kind, buffer)
    }
    const voice = audio.createBufferSource()
    voice.buffer = buffer
    voice.connect(output)
    voice.onended = () => {
      voice.disconnect()
      if (active === voice) active = undefined
    }
    lastPlayed = now
    active = voice
    voice.start()
  }
  try {
    if (audio.state === 'running') play()
    else if (navigator.userActivation?.isActive)
      void audio
        .resume()
        .then(play)
        .catch(() => {})
  } catch {
    /* Presentation failures never interrupt play. */
  }
}
