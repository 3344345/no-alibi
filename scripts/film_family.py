"""Render the family opening films as practical paper theatre, with original Foley.

Requires Pillow, NumPy, and ffmpeg with libx264. Run this script from any directory.
The establishing plates are the original chapter illustrations shipped with the game.
A close-up follows the actions of hands, documents and household objects at the table.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import math
import shutil
from pathlib import Path
import subprocess
import tempfile
import wave

import numpy as np
from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'frontend/public/chronicle'
DEST = ROOT / 'frontend/public/motion'
W, H = 960, 540
SIZE = (W, H)
FPS, RATE, DURATION = 24, 48000, 7.5
FRAMES = round(FPS * DURATION)
RESAMPLE = Image.Resampling.LANCZOS
TAU = 2 * math.pi

# Close-up captions give silent players the same material clues as the soundtrack.
SHOTS = {
    'may_fourth': ('半版铅字', '周禾把一枚反字从字盘里拣出来。', '它落进缺的那一格。剩下半版，还给谁？', '#5c4835', (310, 610, 950)),
    'shanghai_workers': ('桥边修伞人', '小钱推过来半袋信。', '这一封只写着“桥边修伞人”。', '#574b3c', (210, 525, 970)),
    'mukden_september': ('滚走的顶针', '隔墙忽然响了。唐素琴的黄铜顶针掉在地上。', '它在床沿下打了最后一个转。', '#523d35', (585, 1060, 1495)),
    'nantao_refuge': ('长凳往哪边挪', '门边的人等着坐。灶边的人等着搁碗。', '长凳挪过来，碗底轻轻一磕。', '#4e4737', (160, 430, 690)),
    'gold_yuan': ('一尺蓝布', '两只手同时按住细蓝布。', '木尺比好了，剪刀却停在那儿。', '#544530', (260, 845, 1400)),
    'river_grain': ('头一锅', '柴素兰掀锅盖，门口有个孩子踮着脚。', '一只空碗递到灶边。', '#433c30', (174, 462, 592)),
    'school_album': ('夹进相册', '两张相纸只够洗两张照片。', '小莺亲手把相片收进册子。', '#514437', (264, 367, 645)),
    'household_field': ('一头牛，三户人', '几粒豆种落在桌上。一家有种，一家有力气。', '堂屋里传来牛铃声。', '#53412b', (422, 710, 1068)),
    'june_workshop': ('夜班收音机', '一只手拧着旋钮，指针划过刻度。', '电流声里，邻桌把凳子挪近了一点。', '#434641', (247, 624, 1110)),
    'factory_minutes': ('空着的签字格', '宋梅还在养伤。汇总上已经写了“已复工”。', '笔尖悬在签字格上，洇下一滴墨。', '#535042', (184, 540, 1105)),
    'school_ground': ('白线到这里停', '雨落在操场。划线的小轮向前滚。', '白线在泥地里断了。', '#504438', (127, 340, 540)),
    'shadow-play': ('借我一张脸', '喜棚后，桂喜先把两根竹杆递进灯影。', '两位影人转过脸，台下的新娘也看见了。', '#996b3d', (175, 703, 1280)),
}


def ease(x):
    x = min(1., max(0., x))
    return x*x*(3.-2.*x)


def color(value):
    return ImageColor.getrgb(value)


def ink(draw, points, fill, width):
    draw.line(points, fill=fill, width=width, joint='curve')


def oval(draw, x, y, a, b, fill, edge=None, width=1):
    draw.ellipse((x-a, y-b, x+a, y+b), fill, edge, width)


@lru_cache(maxsize=32)
def font(size):
    candidates = [
        '/System/Library/Fonts/Supplemental/Songti.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
        'C:/Windows/Fonts/simsun.ttc',
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    raise RuntimeError('Install a Chinese Songti or Noto Serif CJK font to render these films.')


def label(draw, xy, txt, size=16, fill='#413726'):
    draw.text(xy, txt, fill, font(size))


@lru_cache(maxsize=32)
def type_glyph(letter):
    stamp=Image.new('RGBA',(50,51))
    label(ImageDraw.Draw(stamp),(3,-1),letter,37,'#cfc19d')
    return ImageOps.mirror(stamp)


def hand(draw, x, y, scale=1., side=1, glove=False, from_top=False):
    """A cuff and articulated hand entering from the bottom corner, index extended."""
    def coords(points):
        return [(x + side*dx*scale, y + (-1 if from_top else 1)*dy*scale) for dx,dy in points]
    skin = '#a98563' if not glove else '#39382e'
    shade = '#745842' if not glove else '#242821'
    draw.polygon(coords([(0,212),(-63,148),(-80,97),(-77,48),(-64,23),(-60,7),(-51,-3),
                         (-45,0),(-46,26),(-40,39),(-21,19),(25,-14),(36,-16),(44,-11),(40,-3),
                         (3,27),(35,14),(49,15),(51,21),(20,43),(44,37),(55,42),(51,49),
                         (26,65),(43,63),(47,70),(16,95),(20,125),(69,175)]), skin, outline=shade)
    for path in [[(-61,35),(-64,50),(-60,66)], [(-38,54),(-20,42),(3,27)],
                 [(22,-7),(27,-3),(34,-9)], [(14,57),(26,48)], [(4,78),(13,72)]]:
        ink(draw, coords(path), shade, max(1,round(scale*2)))
    draw.polygon(coords([(-51,115),(23,92),(121,190),(369,555),(420,920),(164,920),(-48,302),(-82,149)]),'#333c39',outline='#232b28')
    ink(draw, coords([(-59,126),(-24,124),(23,105)]),'#77746a',max(1,round(4*scale)))
    for path in [[(-38,158),(-12,154),(6,139)],[(23,120),(37,134),(46,141)], [(-22,193),(19,189),(57,169)],[(10,217),(51,207),(85,193)],[(47,259),(71,247),(95,244)]]:
        ink(draw,coords(path),'#49504a',max(1,round(2*scale)))


def envelope(d,x,y,s=1.):
    def p(points):
        return [(x+dx*s,y+dy*s) for dx,dy in points]
    d.polygon(p([(-138,-65),(134,-66),(140,64),(-133,72)]),'#ba9d72',outline='#6c5740')
    ink(d,p([(-138,-65),(-6,13),(134,-66)]),'#8a7352',2)
    ink(d,p([(-133,72),(-52,-8)]),'#9a8058',1)
    for n in range(4):
        d.line(p([(-114,-34+n*11),(-88,-34+n*11)]),'#796344',1)


def puppet(d,x,y,facing,age,t):
    """The head and jointed arms have separate pivots, pierced leather lace and rods."""
    bob=math.sin(2.4*t+age)*4
    nod=.12*math.sin(t*2+age)+.17*ease((t-.48)/.37)
    y+=bob
    def local(points):
        return [(x+facing*a,y+b) for a,b in points]
    dark,mid,light='#382418','#854221','#dfad58'
    # Control rod for the neck, followed by skirt and leather bodice.
    ink(d,local([(0,-17),(-28,193),(-43,285)]),'#684d2b',3)
    d.polygon(local([(-18,0),(14,0),(28,28),(45,96),(69,137),(-62,132),(-39,78)]),mid,outline=dark)
    d.polygon(local([(-15,5),(5,19),(23,3),(33,32),(12,68),(-32,55)]),dark)
    for row in range(5):
        for col in range(row+3):
            a=-21-row*5+col*12
            yy=52+row*15
            oval(d,x+facing*a,y+yy,2+row*.25,4,light)
    for offset in (0,7,14):
        ink(d,local([(-58+offset,124-offset),(1,130-offset),(61-offset,131-offset)]),dark,3)
    head=[(-13,4),(-24,-24),(-31,-48),(-24,-73),(-1,-76),(17,-65),(21,-47),
          (33,-40),(24,-35),(26,-28),(19,-24),(22,-19),(17,-15),(7,-14),(7,1)]
    def head_at(a,b):
        return x+facing*(a*math.cos(nod)-b*math.sin(nod)), y+a*math.sin(nod)+b*math.cos(nod)
    d.polygon([head_at(a,b) for a,b in head], '#a9572c',outline=dark)
    ink(d,[head_at(2,-48),head_at(15,-45)],dark,3)
    for a,b,r in [(-18,-73,14),(-6,-77,11),(-26,-61,13),(-31,-52,9)]:
        px,py=head_at(a,b); oval(d,px,py,r,r,dark);oval(d,px,py,r/2,r/2,light)
    lift=math.sin(1.8*t+age)*12 + 30*ease((t-.30)/.49)
    elbow=(43,30-lift*.2); wrist=(81,9-lift)
    limb=[(7,10),(22,1),(elbow[0]+10,elbow[1]-6),(wrist[0]-2,wrist[1]-7),
          (wrist[0]+5,wrist[1]+5),(elbow[0]+3,elbow[1]+14),(elbow[0]-8,elbow[1]+16),(2,30)]
    d.polygon(local(limb),'#994d27',outline=dark)
    for a,b in [(14,11),elbow,wrist]:
        oval(d,x+facing*a,y+b,4,4,light,dark)
    ink(d,local([wrist,(wrist[0]+28,206),(wrist[0]+31,265)]),'#775634',2)
    ink(d,local([wrist,(wrist[0]+9,wrist[1]-2),(wrist[0]+16,wrist[1]-8)]),dark,4)


def scene(id, d, im, p):
    t=p*5.3
    slide=ease((p-.10)/.53)
    reach=math.sin(math.pi*ease(p/.87))
    contact=ease((p-.32)/.22)
    if id=='may_fourth':
        d.rounded_rectangle((150,96,765,416),8,fill='#373831',outline='#996746',width=9)
        for row in range(3):
            for col,c in enumerate(('京師北平城','山東印校樣','刊字日報紙')[row]):
                if row==1 and col==1: continue
                x,y=204+102*col,138+77*row
                d.rectangle((x,y,x+65,y+54),'#504f43',outline='#827c62',width=2)
                letter=type_glyph(c)
                im.paste(letter,(int(x+8),int(y+2)),letter)
        x=384-78*slide;y=393-178*slide-62*reach
        d.rectangle((x+4,y+7,x+68,y+61),'#302d26')
        d.rectangle((x,y,x+64,y+53),'#736e5a',outline='#c3b898',width=2)
        # An individual block carries reversed type until it reaches paper.
        mirror=type_glyph('東')
        im.paste(mirror,(int(x+8),int(y+2)),mirror)
        hand(d,x-35-130*ease((p-.72)/.26),y+29+150*ease((p-.72)/.26),.85)
    elif id=='shanghai_workers':
        for i in range(5):
            envelope(d,450+i*11,289-i*11,.97)
        x=456-151*slide;y=224+45*slide
        envelope(d,x,y,1.07)
        d.rectangle((x-83,y-21,x+109,y+26),'#c5aa83')
        label(d,(x-80,y-13),'橋邊修傘人  收',21)
        hand(d,x+130+80*(1-reach),y+61,.85,-1)
    elif id=='mukden_september':
        for j in range(2):
            d.polygon([(72,407+j*18),(790,371+j*18),(801,387+j*18),(63,423+j*18)],'#302b25')
        x=255+388*ease(p/.88)
        y=300-75*abs(math.sin(min(1,p/.75)*math.pi*2.4))*max(0,1-p/.72)
        oval(d,x+7,309,47,9,'#352d24')
        a=.15+3.25*slide
        def turn(u,v):
            return (x+u*math.cos(a)-v*math.sin(a),y+u*math.sin(a)+v*math.cos(a))
        d.polygon([turn(-31,40),turn(-22,-30),turn(-10,-42),turn(13,-42),turn(24,-31),turn(30,40)],'#ad8a52',outline='#4a3725')
        ink(d,[turn(-32,34),turn(31,34)],'#e2bc77',5)
        for j in range(6):
            for k in range(5):
                px,py=turn(-17+8*k+(j%2)*2,-28+j*10);oval(d,px,py,2.8,2.4,'#59462e')
        hand(d,193+157*reach,493-121*reach,.67)
    elif id=='nantao_refuge':
        def bench(x,y):
            for dx in (-162,154):
                d.polygon([(x+dx,y+17),(x+dx+18,y+17),(x+dx+10,y+105),(x+dx-12,y+105)],'#51402c')
            d.polygon([(x-187,y),(x+172,y-22),(x+201,y-7),(x-167,y+18)],'#a47c47',outline='#4d3828')
            ink(d,[(x-164,y+13),(x+199,y-10)],'#705236',6)
        bench(292,214);x=450+154*slide;bench(x,309)
        bowlx=704-100*contact;bowly=193+88*contact
        vessel(d,bowlx,bowly,.65)
        hand(d,bowlx+47+145*ease((p-.62)/.3),bowly+30,.75,-1)
    elif id=='gold_yuan':
        d.polygon([(121,90),(809,116),(774,395),(110,376)],'#42535b',outline='#282e2f')
        for j in range(54):
            ink(d,[(122,93+j*5),(798,117+j*5)],'#4d5b60',1)
        d.polygon([(168,305),(726,219),(735,251),(174,341)],'#ba9565',outline='#695138')
        for j in range(53):
            x,y=179+j*10,308-j*1.55
            ink(d,[(x,y),(x+2,y+(15 if j%5==0 else 7))],'#5b4430',2)
        x=762-183*slide;y=310-57*slide
        angle=.28-.17*contact
        for slope in (-angle,angle):
            dx,dy=math.cos(slope),math.sin(slope)
            end=(x-148*dx,y-148*dy)
            d.polygon([(x,y-6),end,(x-37,y+8)],'#a4aaa0',outline='#414a48')
            oval(d,x+47*dx,y+47*dy,24,13,None,'#402e28',6)
        oval(d,x,y,5,5,'#c0aa74')
        hand(d,x+81,y+34,.82,-1)
    elif id=='river_grain':
        oval(d,413,326,194,77,'#242822')
        d.polygon([(219,308),(608,304),(576,404),(535,428),(292,426),(247,397)],'#34372d')
        oval(d,412,310,194,58,'#686956','#33392e',7)
        oval(d,412,310,165,39,'#958163')
        for k in range(46):
            a=k*2.4;r=(k/46)**.5
            oval(d,412+150*r*math.cos(a),309+34*r*math.sin(a),2.8,1.6,'#bbaa80')
        lidy=300-148*slide
        oval(d,412,lidy,195,45,'#66685a','#a09b7e',5)
        oval(d,414,lidy-20,30,12,'#333a30')
        for k in range(5):
            a=k*.87
            points=[(335+k*29+math.sin(a+t*2+j*.38)*9,298-j*6) for j in range(int(17*slide))]
            if len(points)>1: ink(d,points,'#b2ac91',2)
        hand(d,450,lidy-12,.7,-1,from_top=True)
        vessel(d,722-43*slide,371,.73)
    elif id=='school_album':
        d.rounded_rectangle((195,117,751,419),8,'#3b423b',outline='#847c60',width=6)
        d.rectangle((216,137,469,399),'#b39e7a')
        d.rectangle((474,134,727,395),'#c4b08a')
        x=int(543-44*slide);y=int(72+105*slide)
        d.rectangle((x-3,y-3,x+194,y+150),'#ded0ae')
        im.paste(album_photo(),(x+3,y+3))
        for dx,dy in ((0,0),(165,0),(0,121),(165,121)):
            d.polygon([(x+dx,y+dy),(x+dx+26,y+dy),(x+dx,y+dy+22)],'#716953')
        cover=232*ease((p-.57)/.36)
        if cover>2:
            d.polygon([(468,132),(468+cover,145),(468+cover,398),(468,402)],'#586052',outline='#3f483d')
            ink(d,[(476,143),(476,385)],'#8e8d71',2)
        hand(d,696+93*(1-reach),y+153,.7,-1)
    elif id=='household_field':
        d.polygon([(158,104),(653,126),(639,381),(141,355)],'#b79a70',outline='#776549')
        for q in range(4):
            ink(d,[(221+q*82,132+q*3),(203+q*82,337+q*4)],'#907d59',2)
        label(d,(194,139),'春',23)
        for k in range(20):
            spread=ease((p-.15-(k%5)*.035)/.36);a=k*2.399
            x=407+140*math.cos(a)*spread; y=160+(117+55*math.sin(a))*spread-21*math.sin(spread*math.pi)
            oval(d,x+3,y+4,8,4,'#766048');oval(d,x,y,7,5,'#b79c61','#756036');ink(d,[(x-2,y),(x+2,y+1)],'#897044',1)
        x=733+14*math.sin(8*t)*math.exp(-max(0,p-.58)*8)
        ink(d,[(720,19),(x,149)],'#765d40',4)
        d.polygon([(x-12,138),(x+14,138),(x+29,204),(x-34,205)],'#a3834d',outline='#473e2b')
        oval(d,x-2,204,31,6,'#564629');oval(d,x+4,206,5,7,'#ae8b4a')
        hand(d,377-82*slide,181+155*ease((p-.56)/.38),.72)
    elif id=='june_workshop':
        d.rounded_rectangle((151,121,773,403),21,'#433c30',outline='#857252',width=8)
        d.rounded_rectangle((175,147,749,248),6,'#242f2b',outline='#ab9565',width=4)
        for j in range(64):
            x=196+j*8.25
            ink(d,[(x,190),(x,190+(18 if j%5==0 else 7))],'#c1af80',2)
        for j,num in enumerate(['55','70','90','110','140','160']):
            label(d,(196+94*j,160),num,15,'#d2c7a1')
        x=273+290*slide
        ink(d,[(x,163),(x,225)],'#c68048',3)
        for j in range(10):
            ink(d,[(188,274+j*9),(516,274+j*9)],'#202721',4)
        oval(d,646,320,52,52,'#282a23','#8b8166',6)
        a=-2.6+3.5*slide
        ink(d,[(646+30*math.cos(a),320+30*math.sin(a)),(646+44*math.cos(a),320+44*math.sin(a))],'#d9c492',4)
        hand(d,682+92*ease((p-.71)/.26),347+82*ease((p-.71)/.26),.72,-1)
    elif id=='factory_minutes':
        for x,y in [(222,107),(203,118)]:
            d.polygon([(x,y),(714,y-15),(723,408),(x+14,418)],'#c1b696',outline='#968c72')
        label(d,(258,148),'车间出勤汇总',31)
        for j in range(5):
            ink(d,[(259,212+j*31),(670,206+j*31)],'#817c66',1)
        for j in range(3):
            ink(d,[(259+j*180,211),(264+j*180,332)],'#817c66',1)
        label(d,(275,223),'宋梅',21);label(d,(462,221),'已复工',20)
        label(d,(453,345),'签字',18)
        x=594-25*slide;y=310+31*slide
        d.polygon([(x-2,y),(x+3,y-19),(x+91,y-120),(x+102,y-111),(x+13,y-12)],'#302f28')
        d.polygon([(x-2,y),(x+4,y-21),(x+14,y-13)],'#afaa90')
        oval(d,x-2,y+9,1+3*contact,1+2*contact,'#3b3a31')
        hand(d,x+87,y-94,.67,-1)
    elif id=='school_ground':
        for j in range(96):
            x=(j*347)%950;y=(j*109)%460+38
            ink(d,[(x,y),(x+4,y+2)],'#756950',2)
        x=225+411*slide
        for j in range(385):
            if j> x-224: break
            y=326+7*math.sin(j*.013)
            oval(d,224+j,y,2,3+math.sin(j*.64),'#b7b099')
        ink(d,[(x+1,277),(x+107,123),(x+158,121)],'#3c4137',8)
        oval(d,x,287,42,43,'#53574a','#343c33',6)
        for j in range(6):
            a=TAU*j/6+slide*9
            ink(d,[(x,287),(x+34*math.cos(a),287+34*math.sin(a))],'#8d8f79',4)
        d.polygon([(x-45,182),(x+52,181),(x+28,263),(x-23,260)],'#9a9981',outline='#565a4a')
        hand(d,x+164,119,.58,-1,from_top=True)
        for k in range(42):
            xx=(k*337+18*t)%960; yy=(k*161+t*266)%530
            ink(d,[(xx,yy),(xx-3,yy+10)],'#928d77',1)
    elif id=='shadow-play':
        for x in (84,871):
            ink(d,[(x,30),(x+(3 if x<100 else -4),465)],'#5b3924',10)
        puppet(d,363+30*slide,226,1,0,t)
        puppet(d,598-18*slide,236,-1,2.8,t)
        for j in range(6):
            x=110+j*144
            yy=502+14*math.sin(.6*t+2*j)
            oval(d,x,yy,34,46,'#443528')
            oval(d,x,yy+62,70,52,'#443528')


def vessel(d,x,y,s):
    oval(d,x,y,65*s,18*s,'#aaa998','#504e40',3)
    d.polygon([(x-65*s,y),(x-43*s,y+41*s),(x-22*s,y+54*s),(x+25*s,y+54*s),(x+49*s,y+37*s),(x+65*s,y)],'#b9b7a2',outline='#585b50')
    oval(d,x,y,63*s,12*s,'#8b9182','#626b62',3)
    ink(d,[(x-50*s,y+25*s),(x-14*s,y+33*s),(x+35*s,y+29*s)],'#708172',3)


@lru_cache(maxsize=1)
def album_photo():
    plate=Image.open(ART/'school_album.webp')
    still=ImageOps.fit(plate,(183,137))
    return ImageOps.colorize(ImageOps.grayscale(still),'#47483e','#c9c5af')


def stock(id):
    index=list(SHOTS).index(id)
    rng=np.random.default_rng(970+index)
    y,x=np.indices((H,W))
    lamp=1.-.43*((x-W*.43)/W)**2-.56*((y-H*.36)/H)**2
    grain=rng.normal(0,1.8,(H,W))
    broad=rng.normal(0,1.5,(H,1))+1.5*np.sin(y*.18+np.sin(x*.021)*.54)
    if id=='shadow-play':
        lamp=1.34-.47*((x-W*.50)/(W*.52))**2-.58*((y-H*.42)/(H*.73))**2
        broad=.9*np.sin(y*1.56)+.9*np.cos(x*1.6)
    base=np.asarray(color(SHOTS[id][3]))
    backdrop=lamp[:,:,None]*base[None,None,:]+(grain+broad)[:,:,None]
    return Image.fromarray(np.uint8(np.clip(backdrop,0,255)))


def make_sound(id,dst):
    rng=np.random.default_rng(1921+list(SHOTS).index(id))
    t=np.arange(round(RATE*DURATION))/RATE
    sound=np.zeros((len(t),2))
    for ch in range(2):
        noise=np.convolve(rng.normal(size=len(t)),np.ones(30)/30,'same')
        sound[:,ch]=noise*.017+.005*np.sin(TAU*(49.9+ch*.08)*t)
    def place(when,signal,pan):
        start=round(RATE*when)
        length=min(len(sound)-start,len(signal))
        gains=np.sqrt([1-pan,1+pan])
        sound[start:start+length]+=signal[:length,None]*gains
    def hit(when,hz,pan,metal=False,amp=.20):
        dt=np.arange(round(RATE*.87))/RATE
        decay=9 if metal else 23
        signal=sum(np.sin(TAU*h*dt)*np.exp(-dt*(decay+i*9))/(1+i)
                   for i,h in enumerate(hz))
        signal+=rng.normal(size=len(dt))*.26*np.exp(-dt*211)
        signal*=amp*(1-np.exp(-dt*940))
        place(when,signal,pan)
        place(when+.044,signal*.15,-pan)
    def brush(when,length,pan,amp,coarse):
        dt=np.arange(round(RATE*length))/RATE
        source=rng.normal(size=len(dt))
        signal=np.convolve(source,np.ones(coarse)/coarse,'same')
        env=np.sin(np.pi*np.clip(dt/length,0,1))**1.6
        place(when,signal*env*amp,pan)
    freqs=SHOTS[id][4]
    hits={
        'may_fourth': [(2.58,.18),(4.55,.42),(4.67,.16)],
        'shanghai_workers': [(2.34,.15),(4.33,.12)],
        'mukden_september': [(2.57,.42),(3.40,.30),(4.07,.21),(4.54,.15),(4.86,.12),(5.13,.09)],
        'nantao_refuge': [(2.72,.22),(4.42,.40),(4.57,.15)],
        'gold_yuan': [(2.64,.15),(4.63,.28),(5.32,.16)],
        'river_grain': [(3.02,.25),(4.25,.13),(5.36,.33)],
        'school_album': [(2.84,.10),(4.17,.16),(6.15,.22)],
        'household_field': [(2.83,.18),(3.05,.13),(3.18,.14),(4.92,.34),(5.13,.19)],
        'june_workshop': [(2.70,.19),(4.15,.09),(4.53,.11),(5.90,.15)],
        'factory_minutes': [(2.51,.15),(3.71,.10),(5.67,.22)],
        'school_ground': [(2.66,.16),(3.39,.14),(4.08,.16),(4.76,.13),(5.52,.16)],
        'shadow-play': [(2.4,.27),(3.30,.15),(4.19,.24),(5.86,.33)],
    }[id]
    metallic=id in {'mukden_september','gold_yuan','household_field','shadow-play'}
    for i,(when,amp) in enumerate(hits):
        hit(when,tuple(h*(1+.035*math.sin(i*1.7)) for h in freqs),-.45+.15*(i%6),metallic,amp)
    if id in {'shanghai_workers','school_album','factory_minutes','gold_yuan','school_ground','nantao_refuge'}:
        brush(2.65,1.5,-.43,.28,13)
        brush(4.63,.85,.38,.18,9)
    if id in {'river_grain','june_workshop','school_ground'}:
        brush(2.25,4.65,.1,.12,2 if id=='june_workshop' else 8)
    sound*=np.minimum(1,np.minimum(t/.38,(DURATION-t)/.56))[:,None]
    with wave.open(str(dst),'wb') as wav:
        wav.setparams((2,2,RATE,0,'NONE',''))
        wav.writeframes(np.int16(np.clip(sound,-.92,.92)*32767).tobytes())


def photographic_light(id):
    # Raking side light and fixed grain make the relief of cut paper visible.
    y,x=np.indices((H,W))
    dx=(x-W*.42)/(W*.68); dy=(y-H*.39)/(H*.75)
    exposure=np.clip(1.12-.17*dx**2-.15*dy**2, .63,1.18)
    if id in ('june_workshop','mukden_september','factory_minutes'):
        exposure-=.06*(np.sin(.024*x+.011*y)+.3)
    rng=np.random.default_rng(339+list(SHOTS).index(id))
    shade=np.clip(209*exposure[:,:,None]*np.array([1.01,1,.975]),0,255).astype('uint8')
    ink_grain=rng.normal(0,3.,(H,W)) + .9*np.sin(.63*y+.29*x)+.58*np.cos(x*2.8)
    return Image.fromarray(shade),Image.fromarray(np.uint8(np.clip(ink_grain+128,0,255)),'L').convert('RGB')


def finish(im,base,light,grain,id,p):
    diff=ImageChops.difference(base,im)
    bands=diff.split()
    mask=ImageChops.lighter(ImageChops.lighter(bands[0],bands[1]),bands[2]).point(lambda n: min(255,n*255))
    cast=ImageChops.offset(mask,7,8).filter(ImageFilter.GaussianBlur(4.2)).point(lambda v:int(v*.56))
    plate=Image.composite(Image.new('RGB',SIZE,'#241e16'),base,cast)
    plate.paste(im,(0,0),mask)
    relief=mask.filter(ImageFilter.EMBOSS).convert('RGB')
    plate=Image.blend(plate,ImageChops.add(plate,relief,1,-128),.35)
    graded=ImageEnhance.Contrast(ImageChops.multiply(plate,light)).enhance(1.12)
    result=ImageChops.add(graded,grain,1,-128)
    amount=(.049 if id=='shadow-play' else .084)+.018*ease(p)
    left=int(W*amount); top=int(H*amount)
    return result.crop((left,top,W-left,H-top)).resize(SIZE,Image.Resampling.BICUBIC)


def render(id):
    plate=Image.open(ART/(('still_shadow' if id=='shadow-play' else id)+'.webp')).convert('RGB')
    plate=ImageEnhance.Color(ImageOps.fit(plate,(1000,565),method=RESAMPLE)).enhance(.87)
    table=stock(id)
    if id in ('school_ground','river_grain','nantao_refuge','mukden_september'):
        room=ImageOps.fit(plate,SIZE).filter(ImageFilter.GaussianBlur(12))
        room=ImageEnhance.Color(room).enhance(.45)
        room=ImageEnhance.Brightness(room).enhance(.7)
        yy=np.arange(H)[:,None]
        opacity=np.clip((255-yy)*.78,0,165) * np.ones((1,W))
        table=Image.composite(room,table,Image.fromarray(np.uint8(opacity)))
    light,grain=photographic_light(id)
    table_d=ImageDraw.Draw(table)
    if id not in ('shadow-play','school_ground','river_grain'):
        for y in (102,407):
            ink(table_d,[(0,y+4),(272,y+1),(548,y+2),(959,y-8)],'#41392f',2)
            ink(table_d,[(0,y+6),(272,y+3),(548,y+4),(959,y-6)],'#675849',1)
        rnd=np.random.default_rng(7214)
        for j in range(317):
            x,y=rnd.integers([0,0],[W,H]);size=int(rnd.integers(2,24))
            ink(table_d,[(x,y),(x+size,y+int(rnd.integers(-1,2)))],'#605444' if j%3 else '#493d31',1)
    with tempfile.TemporaryDirectory(prefix='jzs-family-film-') as temp:
        tmp=Path(temp)
        make_sound(id,tmp/'sound.wav')
        encoder=subprocess.Popen(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
            '-f','rawvideo','-pix_fmt','rgb24','-s','960x540','-r',str(FPS),'-i','pipe:0','-i',str(tmp/'sound.wav'),
            '-c:v','libx264','-threads','2','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','112k',
            '-movflags','+faststart','-metadata','title='+SHOTS[id][0],str(tmp/'film.mp4')],stdin=subprocess.PIPE)
        try:
            for f in range(FRAMES):
                sec=f/FPS; cross=ease((sec-1.57)/.53)
                if cross<1:
                    x=17*ease(sec/2.1);y=6*ease(sec/2.1)
                    frame=plate.crop((x,y,x+960,y+540))
                if cross>0:
                    close=table.copy()
                    progress=max(0,min(1,(sec-1.75)/5.48))
                    scene(id,ImageDraw.Draw(close),close,progress)
                    close=finish(close,table,light,grain,id,progress)
                    if cross==1: frame=close
                    else: frame=Image.blend(frame,close,cross)
                encoder.stdin.write(frame.tobytes())
        finally:
            encoder.stdin.close()
        if encoder.wait()!=0: raise RuntimeError('Encoding failed for '+id)
        shutil.move(str(tmp/'film.mp4'),str(DEST/(id+'.mp4')))
    _,a,b,_,_=SHOTS[id]
    (DEST/(id+'.vtt')).write_text(f'WEBVTT\n\n00:00:00.150 --> 00:00:03.100\n{a}\n\n00:00:03.250 --> 00:00:07.350\n{b}\n',encoding='utf-8')
    return id


if __name__=='__main__':
    args=argparse.ArgumentParser()
    args.add_argument('chapters',nargs='*')
    ids=args.parse_args().chapters or list(SHOTS)
    if any(id not in SHOTS for id in ids): args.error('Unknown chapter')
    DEST.mkdir(exist_ok=True,parents=True)
    with ProcessPoolExecutor(max_workers=3) as pool:
        for name in pool.map(render,ids): print(name,flush=True)
