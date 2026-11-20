"""Generate the two synchronized microphones of the fictional farewell screening."""

import json
import subprocess
from pathlib import Path

import numpy as np

RATE = 44100
DURATION = 12
HOME = Path(__file__).resolve().parents[1] / "frontend"
OUT = HOME / "public/chronicle/sound"
rng = np.random.default_rng(19921011)


def seconds(n):
    return np.arange(round(RATE * n)) / RATE


def noise(n, lo, hi):
    samples = rng.normal(size=len(n))
    freq = np.fft.rfftfreq(len(n), 1 / RATE)
    band = np.minimum(1, (freq / lo) ** 2) / (1 + (freq / hi) ** 4)
    return np.fft.irfft(np.fft.rfft(samples) * band, len(n))


def place(track, when, source, pan=0):
    i = round(when * RATE)
    n = min(len(source), len(track) - i)
    gains = np.sqrt(np.array([1 - pan, 1 + pan]) / 2)
    track[i:i+n] += source[:n, None] * gains


def piano(freq, length, weight):
    t = seconds(length)
    y = noise(t, 160, 2400) * np.exp(-t * 65) * .17
    for k in range(1, 16):
        partial = freq * k * (1 + .00009 * k * k)
        envelope = (1 - np.exp(-t * 210)) * np.exp(-t * (1.12 + k * .43))
        # Paired strings gradually go out of phase after the hammer falls.
        y += envelope * (np.sin(2*np.pi*partial*t) + .67*np.sin(2*np.pi*(partial+.52*k)*t)) / k**1.46
    return y * weight


def strike(bases, seconds_long, force, metallic=False):
    t = seconds(seconds_long)
    y = noise(t, 650, 7600 if metallic else 2400) * .75 * np.exp(-t*185)
    for i, hz in enumerate(bases):
        rate = (8 if metallic else 20) + 6*i
        y += np.sin(2*np.pi*hz*t) * np.exp(-t*rate) / (2+i)
    return y * force


def room(dry, delays):
    wet = dry.copy()
    for delay, gain, flip in delays:
        i = round(delay*RATE)
        src = dry[:, ::-1] if flip else dry
        wet[i:] += src[:-i] * gain
    return wet


def render():
    stage = np.zeros((DURATION*RATE, 2))
    hall = np.zeros_like(stage)
    for when, hz, weight in ((.65, 246.94, .37), (1.74, 293.66, .48), (3.47, 220, .44)):
        place(stage, when, piano(hz, 3.25, weight), -.19)
    place(stage, 2.78, strike([390, 640, 1050], .2, .14))
    # Folding seats fall in batches. Each seat hits both the spring and its back.
    for i,(when,pan) in enumerate(((4.48,-.76),(4.97,-.48),(5.14,-.16),(5.39,-.05),(5.78,.17),(6.12,.51),(6.63,.75))):
        scale = rng.uniform(.86, 1.12)
        place(hall,when,strike([scale*f for f in (172,390,740)], .31, .73),pan)
        place(hall,when+.085+.014*(i%3),strike([510,1380,2310], .22, .21, True),pan)
    for when,pan,level in ((7.42,.8,.27),(8.05,.68,.39),(8.55,.40,.45),(8.94,.26,.50)):
        t=seconds(.23)
        shoe = noise(t,60,1000)*np.exp(-t*28) + .52*np.sin(2*np.pi*(82*t+1.7*(1-np.exp(-12*t))))*np.exp(-t*25)
        place(hall,when,shoe*level,pan)
    t=seconds(.64)
    bolt = noise(t,240,2400)*np.maximum(0,np.sin(np.pi*t/.64))**2*.24
    place(hall,9.97,bolt,.71)
    place(hall,10.61,strike([91,147,512,910],.7,.95,True),.76)
    stage=room(stage,[(.024,.17,False),(.045,.14,True),(.092,.1,True),(.147,.052,False),(.24,.033,True)])
    hall=room(hall,[(.033,.23,True),(.062,.14,False),(.108,.08,True),(.202,.055,False),(.305,.028,True)])
    front, rear=stage+hall*.095, hall+stage*.16
    t=seconds(DURATION)
    for channel in (0,1):
        front[:,channel]+=noise(t,75,6400)*.007
        rear[:,channel]+=noise(t,90,3800)*.01+.003*np.sin(2*np.pi*50*t)
    average=(front+rear)*.78
    overall=max(np.max(np.abs(w)) for w in (front,rear,average))
    fade=np.minimum(1,np.minimum(t/.045,(DURATION-t)/.18))[:,None]
    waveform={}
    OUT.mkdir(parents=True,exist_ok=True)
    for key,track in [('stage',front),('door',rear),('sum',average)]:
        track=track*(.83/overall)*fade
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','f32le','-ar',str(RATE),'-ac','2','-i','pipe:0','-c:a','libmp3lame','-b:a','128k','-metadata','title=倒带七秒','-metadata','artist=局中事',str(OUT/f'reel_{key}.mp3')],input=track.astype('<f4').tobytes(),check=True)
        window=track.reshape(120,-1)
        peak=np.sqrt(np.mean(window**2,axis=1))
        waveform[key]=[round(float(v),2) for v in (peak/np.max(peak))**.52]
    (HOME/'src/reelWaves.json').write_text(json.dumps(waveform,separators=(',',':'))+'\n')


if __name__=='__main__':
    render()
