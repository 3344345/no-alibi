"""Render the eleven county location films, sound and captions.

Requires Python 3.9+, Pillow, NumPy, FFmpeg with libx264 and a Chinese serif
font (set COUNTY_MOTION_FONT to override the macOS/Linux default). Run
`python scripts/render_county_motion.py all` or pass individual location IDs.
"""
import argparse
import math
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

from county_motion_art import ART, PUBLIC, render


FPS, SR = 24, 48000
# Captions describe the hands and the actual timed sounds and remain available
# to a player who keeps the device muted.
CAPTIONS = {
    'L01': [('00:00.180','00:02.500','我从窗边取回木印，手腕悬在登记簿上。'),('00:02.600','00:06.700','咚。我抬起印底，来文栏里多了一圈红印。')],
    'L02': [('00:00.200','00:03.000','我隔着便道看水尺，把手里的细绳慢慢放长。'),('00:03.100','00:06.800','指尖一松。铅坠入水，浮子碰出两圈小波纹。')],
    'L03': [('00:00.200','00:02.900','三本申请册摆在我面前。我推开红褐色那本，封底擦过桌面。'),('00:03.050','00:06.800','我拿起笔，在预算表右栏打了一个短勾。')],
    'L04': [('00:00.160','00:02.850','我的指尖搭上玻璃转盘，小菜碟随它缓缓转来。'),('00:03.000','00:06.700','盘底碰在我面前。碟子底下，露出红纸的一角。')],
    'L05': [('00:00.180','00:02.620','我在接待台按下铜铃，指尖一抬，清响还在。'),('00:02.820','00:06.700','登记簿旁滑来一块会客牌，我伸手接住。')],
    'L06': [('00:00.160','00:02.400','我低头握住球杆。杆头轻轻磕在白球上。'),('00:02.450','00:06.750','我的目光跟着白球绕过斜坡。还差半个球，停住了。')],
    'L07': [('00:00.150','00:02.450','我低头看培训通知，右手的笔尖悬在旁边的日历上。'),('00:02.480','00:06.750','我圈下日期。搪瓷杯还冒着热气。')],
    'L08': [('00:00.180','00:03.400','茶杯旁是我的手。我从泛黄的封套里抽出旧信。'),('00:03.520','00:06.700','我的食指沿着字迹往下，停在落款的日期旁。')],
    'L09': [('00:00.180','00:03.200','我把上回聚餐的老照片推向对席。'),('00:03.300','00:06.750','对方捏住另一角。我松手，又看了一眼照片里的人。')],
    'bus': [('00:00.180','00:02.700','雨水滑过面前的车窗。我把夜班车票递过去，拇指抵住票角。'),('00:02.750','00:06.750','验票钳在我手边咔哒一合。票的右上角多了一个孔。')],
    'cinema': [('00:00.200','00:03.550','放映机在我手边转动。我伸手去摸拨杆，指腹碰到金属。'),('00:03.690','00:06.700','我拨动机件，眼前的银幕白了一下。椅子换成了观众席里的孩子。')],
}


class Foley:
    def __init__(self, key, seconds):
        self.rng = np.random.default_rng(list(ART).index(key)+841)
        self.samples = np.zeros((round(SR*seconds),2))

    def put(self, start, wavelet, gain, pan):
        offset = round(start*SR)
        if offset < 0:
            wavelet = wavelet[-offset:]
            offset = 0
        n = min(len(wavelet),len(self.samples)-offset)
        if n <= 0:
            return
        angle=(pan+1)*math.pi/4
        self.samples[offset:offset+n] += gain*wavelet[:n,None]*[math.cos(angle),math.sin(angle)]

    def resonant(self, at, duration, modes, level=.13, pan=0, click=.07):
        t=np.arange(round(SR*duration))/SR
        raw=np.zeros_like(t)
        for hz,decay,vol in modes:
            raw += vol*np.sin(2*np.pi*hz*t)*np.exp(-t/decay)
        raw += self.rng.normal(0,click,len(t))*np.exp(-t/.012)
        raw *= np.minimum(t/.001+0.04,1)*np.minimum((duration-t)/.012,1)
        self.put(at,raw,level,pan)
        # Early reflections are quiet and short enough to keep the attack clear.
        self.put(at+.046,raw,.105*level,-pan)
        self.put(at+.081,raw,.052*level,pan*.35)

    def friction(self, at, duration, level, pan, smooth=9, flutter=18):
        t=np.arange(round(SR*duration))/SR
        n=len(t);raw=self.rng.normal(0,1,n)
        raw=np.convolve(raw,np.ones(smooth)/math.sqrt(smooth),'same')
        echo=np.roll(raw, max(1,smooth*5))
        raw=.68*raw+.22*echo
        flutter_=.60+.25*np.sin(t*2*np.pi*flutter)+.15*np.sin(t*2*np.pi*flutter*1.61)
        env=np.minimum(t/.055,1)*np.minimum((duration-t)/.10,1)
        self.put(at,raw*flutter_*env,level,pan)

    def wood(self, at, level=.18, pan=0):
        self.resonant(at,.29,[(106,.063,.45),(247,.048,.46),(519,.026,.24),(1371,.015,.075)],level,pan,.22)

    def metal(self, at, pitch, level=.17, pan=0):
        self.resonant(at,1.10,[(pitch,.27,.58),(pitch*2.63,.14,.32),(pitch*4.26,.072,.19)],level,pan,.15)

    def air(self, seconds, level, speed=340):
        for channel,pan in enumerate((-.82,.82)):
            source=self.rng.normal(0,.68,int(seconds*speed)+2)
            t=np.arange(round(seconds*SR))/SR
            air=np.interp(t*speed,np.arange(len(source)),source)
            self.put(0,air*(.8+.16*np.sin(t*.91+channel)),level,pan)


def score(key, path):
    seconds=7; f=Foley(key,seconds)
    f.air(seconds,.013 if key not in ('L02','L06','bus') else .023)
    if key=='L01':
        f.friction(.80,1.25,.027,.2,4,23);f.wood(2.878,.34,.14);f.friction(3.27,.34,.037,.08,5)
        f.wood(5.67,.10,.67)
    elif key=='L02':
        f.friction(0,6.97,.019,-.34,37,2);f.friction(1.01,2.18,.048,.03,5,11)
        f.resonant(3.17,.42,[(319,.05,.55),(191,.093,.52),(805,.016,.20)],.29,.11,.54)
        f.friction(3.19,.46,.046,.19,8,12);f.resonant(3.59,.15,[(499,.019,.8)],.065,-.06)
    elif key=='L03':
        f.friction(1.1,1.78,.048,-.3,13,21);f.wood(2.92,.19,.18);f.friction(3.73,.56,.060,.49,3,31)
        f.friction(4.50,.33,.020,.32,7,10)
    elif key=='L04':
        f.friction(1.18,2.68,.040,-.25,31,9);f.metal(1.27,851,.09,-.40)
        f.resonant(3.82,.73,[(705,.16,.6),(1487,.082,.37),(2308,.08,.16)],.24,.40,.11)
        f.wood(4.03,.08,.35)
    elif key=='L05':
        f.metal(1.84,997,.32,.16);f.resonant(1.84,.99,[(1004,.28,.5),(2662,.18,.28)],.11,.20)
        f.friction(2.98,.89,.048,-.52,5,19);f.wood(3.9,.19,-.43)
    elif key=='L06':
        for k in range(3):
            f.resonant(.58+k*.17,.25,[(1790-k*133,.063,.51),(2250-k*95,.037,.16)],.052,-.62)
        f.resonant(1.61,.22,[(1259,.035,.53),(701,.029,.33),(3903,.012,.13)],.32,-.39,.27)
        f.friction(1.66,2.44,.027,.16,9,24);f.resonant(4.18,.12,[(170,.032,.7)],.045,.5)
    elif key=='L07':
        for at,d,amp in [(2.19,.38,.046),(2.60,.37,.041),(2.96,.51,.054)]:
            f.friction(at,d,amp,.16,3,37)
        f.wood(3.53,.075,.13);f.friction(4.07,.64,.022,.55,13,9)
    elif key=='L08':
        f.friction(.96,2.52,.053,-.16,3,22)
        for at in (1.14,1.81,2.75,3.47):f.friction(at,.13,.071,-.03,3,40)
        f.friction(3.66,1.27,.034,.38,8,12);f.wood(5.05,.09,.29)
    elif key=='L09':
        f.friction(1.58,2.32,.052,-.15,6,13)
        f.friction(3.76,.22,.07,.30,3,18);f.friction(4.12,.49,.040,-.44,3,9)
        f.wood(4.60,.08,-.41)
    elif key=='bus':
        t=np.arange(SR*seconds)/SR
        f.put(0,np.sin(math.tau*(51*t+.45*np.sin(t*1.6)))+.31*np.sin(math.tau*102*t),.024,-.24)
        f.friction(.02,6.94,.023,-.8,6,3);f.friction(1.44,1.62,.044,-.21,3,25)
        f.metal(3.041,782,.24,.29);f.wood(3.049,.19,.24);f.metal(3.49,569,.10,.35)
    elif key=='cinema':
        for i in range(164):
            at=.017+i/24+.00065*math.sin(i*.33)
            f.resonant(at,.038,[(156,.013,.50),(390,.009,.32),(1102,.006,.17)],.12*(1+.18*math.cos(i*.32)),.49,.21)
        f.friction(.02,6.91,.019,.34,12,29);f.metal(3.799,444,.12,.36);f.wood(3.812,.13,.31)
    t=np.arange(len(f.samples))/SR
    f.samples*=np.clip(t/.13,0,1)[:,None]*np.clip((seconds-t)/.38,0,1)[:,None]
    f.samples-=f.samples.mean(axis=0)
    # Match quiet rooms to one another while preserving the gap from an impact.
    # A soft knee catches the short bell and stamp transients before AAC encoding.
    rms=float(np.sqrt(np.mean(f.samples*f.samples)))
    gain=min(5.0,.046/max(.001,rms))
    finished=.82*np.tanh(f.samples*(gain/.82))
    with wave.open(str(path),'wb') as wav:
        wav.setparams((2,2,SR,0,'NONE',''))
        wav.writeframes((32767*finished).astype('<i2').tobytes())


def export(scene, folder):
    scene_name='county-'+scene
    with tempfile.TemporaryDirectory(prefix='county-film-') as tmp:
        scratch=Path(tmp); sound=scratch/'mix.wav'; score(scene,sound)
        out=scratch/'film.mp4'
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24',
             '-video_size','960x540','-framerate',str(FPS),'-i','pipe:0','-i',str(sound),'-map','0:v','-map','1:a',
             '-c:v','libx264','-threads','3','-preset','medium','-crf','20','-pix_fmt','yuv420p',
             '-c:a','aac','-b:a','120k','-ar',str(SR),'-movflags','+faststart',str(out)]
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
        try:
            for frame in range(FPS*7):
                proc.stdin.write(render(scene,frame,FPS).tobytes())
        finally:
            proc.stdin.close()
            status=proc.wait()
        if status:
            raise RuntimeError(f'Encoder failed for {scene} (exit {status})')
        (folder/(scene_name+'.mp4')).write_bytes(out.read_bytes())
    text='WEBVTT\n\n'+'\n\n'.join(f'{a} --> {b}\n{line}' for a,b,line in CAPTIONS[scene])+'\n'
    (folder/(scene_name+'.vtt')).write_text(text,encoding='utf-8')
    print(scene_name,flush=True)


# Hold on the action just before the lean or impact. Each thumbnail retains
# spatial context, including the near wrist or the hand holding out the ticket.
POSTER_FRAMES = {"L01":49,"L02":58,"L03":51,"L04":52,"L05":34,"L06":25,
                 "L07":44,"L08":56,"L09":71,"bus":49,"cinema":70}


def poster(scene, source_folder, stills):
    stills.mkdir(parents=True,exist_ok=True)
    name='county-'+scene
    from PIL import Image
    pixels=subprocess.check_output(['ffmpeg','-hide_banner','-loglevel','error','-i',
        str(source_folder/(name+'.mp4')),'-vf',f'select=eq(n\\,{POSTER_FRAMES[scene]})',
        '-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','-'])
    Image.frombytes('RGB',(960,540),pixels).save(stills/(name+'.webp'),quality=89,method=6)



if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scenes',nargs='+',choices=['all',*ART])
    parser.add_argument('--output',type=Path,default=PUBLIC/'motion')
    parser.add_argument('--posters-only',action='store_true',help='Extract selected stills from existing final films')
    parser.add_argument('--stills',type=Path,default=PUBLIC/'sets')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    for scene in ART if 'all' in args.scenes else args.scenes:
        if not args.posters_only:export(scene,args.output)
        poster(scene,args.output,args.stills)
