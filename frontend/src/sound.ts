/** Short local interface cues. Volume and sound never enter the world simulation. */
let audio: AudioContext | undefined
export function cue(volume: number, place = 'L01') {
  if (!volume) return
  try {
    audio ??= new AudioContext()
    const context = audio
    const tones: Record<string, [number, number]> = {
      L01: [330, 392],
      L02: [220, 294],
      L03: [294, 370],
      L04: [349, 440],
      L05: [261, 330],
      L06: [392, 494],
      L07: [330, 440],
      L08: [247, 330],
      L09: [294, 392],
    }
    void context
      .resume()
      .then(() => {
        for (const [i, freq] of (tones[place] ?? tones.L01).entries()) {
          const osc = context.createOscillator(),
            gain = context.createGain()
          osc.type = 'sine'
          osc.frequency.value = freq
          const t = context.currentTime + 0.08 * i
          gain.gain.setValueAtTime(0.0001, t)
          gain.gain.exponentialRampToValueAtTime(Math.max(0.001, volume * 0.0005), t + 0.008)
          gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.17)
          osc.connect(gain).connect(context.destination)
          osc.start(t)
          osc.stop(t + 0.18)
        }
      })
      .catch(() => {})
  } catch {
    /* Cues are optional on platforms with audio disabled. */
  }
}
