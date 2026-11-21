"""The eleven county inserts. Coordinates are on a 960 × 540 stage.

Illustrated props are drawn in their own local coordinate systems. Floor and
tabletop props share the light of each location's existing establishing plate.
"""
import math
import os
import random
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

PUBLIC = Path(__file__).resolve().parents[1] / "frontend" / "public"
W, H, SCALE = 960, 540, 1.25
SIZE = int(W*SCALE), int(H*SCALE)
INK = (58, 51, 43)
PAPER = (199, 185, 150)
BRASS = (177, 143, 83)


def smooth(x):
    x = max(0, min(1, x))
    return x*x*(3-2*x)


def cue(t, start, seconds):
    return smooth((t-start)/seconds)


def shade(rgb, value):
    return tuple(max(0, min(255, round(c*value))) for c in rgb)


@lru_cache
def font(size):
    options = (os.environ.get("COUNTY_MOTION_FONT", ""), "/System/Library/Fonts/Supplemental/Songti.ttc",
               "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc")
    for option in options:
        if option and Path(option).is_file():
            return ImageFont.truetype(option, round(size*SCALE))
    raise RuntimeError("Set COUNTY_MOTION_FONT to a Chinese serif font file.")


class Pen:
    def __init__(self, layer, x=0, y=0, angle=0, scale=1):
        self.d = ImageDraw.Draw(layer)
        self.layer = layer
        self.x, self.y = x, y
        self.a = math.radians(angle)
        self.s = scale

    def xy(self, pt):
        x, y = pt
        co, si = math.cos(self.a), math.sin(self.a)
        return (round(SCALE*(self.x+self.s*(x*co-y*si))), round(SCALE*(self.y+self.s*(x*si+y*co))))

    def poly(self, pts, color):
        self.d.polygon([self.xy(p) for p in pts], fill=color)

    def line(self, pts, color, width=1):
        self.d.line([self.xy(p) for p in pts], fill=color, width=max(1, round(width*SCALE*abs(self.s))), joint="curve")

    def oval(self, x, y, rx, ry, color):
        if abs(self.a) < 1e-7:
            a=self.xy((x-rx, y-ry)); b=self.xy((x+rx, y+ry))
            self.d.ellipse((a,b),fill=color)
        else:
            self.poly([(x+rx*math.cos(i*math.tau/44), y+ry*math.sin(i*math.tau/44)) for i in range(44)], color)

    def rect(self, x, y, w, h, color):
        self.poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],color)

    def text(self, x, y, value, size, color):
        # Horizontal ink on a physical register, calendar or ticket.
        self.d.text(self.xy((x,y)),value,font=font(size),fill=color,anchor="lt")


BACKGROUND = {"L01":"office", "L02":"canal", "L07":"home", "L09":"home", "bus":"county-nightbus", "cinema":"county-reel"}
TABLE = {"L01":(86,64,42), "L03":(72,68,53), "L04":(84,56,43), "L05":(61,65,64),
         "L07":(109,77,48), "L08":(78,59,39), "L09":(95,58,49)}
HORIZON = {"L01":276,"L03":253,"L04":303,"L05":311,"L07":286,"L08":309,"L09":276}


@lru_cache
def plate(scene):
    if scene in BACKGROUND:
        raw=Image.open(PUBLIC/"scenes"/(BACKGROUND[scene]+".webp")).convert("RGB")
    else:
        raw=Image.open(PUBLIC/"county-locations.jpg").convert("RGB")
        i=int(scene[1:])-1; x=i%3; y=i//3
        raw=raw.crop((round(raw.width*x/3),round(raw.height*y/3),round(raw.width*(x+1)/3),round(raw.height*(y+1)/3)))
    if scene=="L09":
        # Sit on the open side of the family table. The earlier gathering is
        # visible inside the print, never as a head placed in front of our eyes.
        raw=raw.crop((round(raw.width*.42),0,raw.width,round(raw.height*.89)))
    if scene=="L06":
        # The wide establishing plate includes a golfer seen from behind. The
        # playable viewpoint looks down the lane from the grip instead.
        raw=raw.crop((round(raw.width*.31),round(raw.height*.20),round(raw.width*.61),round(raw.height*.72)))
    frame=ImageOps.fit(raw,SIZE,centering=(.49,.44)).filter(ImageFilter.GaussianBlur(1.3*SCALE))
    if scene in TABLE:
        frame=Image.blend(frame,Image.new("RGB",SIZE,(41,36,31)),.12)
        p=Pen(frame); horizon=HORIZON[scene]; col=TABLE[scene]
        p.poly([(0,horizon+18),(960,horizon-38),(960,540),(0,540)],col)
        rng=random.Random(scene)
        for i in range(145):
            y=rng.uniform(horizon+24,590); x=rng.uniform(-180,935); run=rng.uniform(12,240)
            p.line([(x,y),(x+run*.40,y-run*.025+rng.uniform(-2,2)),(x+run,y-run*.057)],shade(col,rng.uniform(.87,1.10)),.9)
        p.line([(0,horizon+19),(960,horizon-37)],shade(col,1.30),2)
        # Long open-pore grain follows the perspective of the near table edge.
        yy,xx=np.mgrid[:SIZE[1],:SIZE[0]]; x=xx/SCALE; y=yy/SCALE
        distance=y-(horizon+18-.058*x)
        phase=(distance+.008*x+2.6*np.sin(x*.012+y*.053)+.000035*(x-470)**2)
        seed=int.from_bytes(scene.encode(),"little")
        grit=np.random.default_rng(seed).normal(0,1.20,x.shape)
        wood=3.3*np.sin(phase*.23)+1.5*np.sin(phase*1.65)+grit
        wood+=8*np.exp(-((x-560)/340)**2-((y-horizon)/130)**2)-5*(x/960)
        if scene=="L05":
            wood=grit+2.4*np.sin(x*.016+y*.037)+2*np.sin(x*.022-y*.022)
        tinted=np.asarray(frame).astype(float)+np.where(distance>2,wood,0)[:,:,None]
        frame=Image.fromarray(np.clip(tinted,0,255).astype("uint8"))
    return frame


@lru_cache
def patina():
    rng=np.random.default_rng(1992); y,x=np.mgrid[:SIZE[1],:SIZE[0]]
    lighting=np.maximum(0,1-((x-SIZE[0]*.53)/(SIZE[0]*.77))**2-((y-SIZE[1]*.59)/(SIZE[1]*.87))**2)
    noise=rng.normal(0,2.5,(SIZE[1],SIZE[0]))
    return Image.fromarray(np.clip(201+48*lighting+noise,0,255).astype("uint8"))


# Contact point, cuff direction, source-to-stage ratio. Each pose is calibrated
# to the left/right fingers in the supplied player-facing wardrobe atlas.
CONTACT = {
    ('offer','right'): ((8,198),(194,345),.53), ('offer','left'): ((248,251),(86,420),.52),
    ('write','right'): ((57,237),(206,385),.54), ('write','left'): ((194,204),(85,416),.55),
    ('rest','right'): ((54,244),(183,427),.53), ('rest','left'): ((208,295),(90,430),.61),
    ('halt','right'): ((95,66),(172,360),.49), ('halt','left'): ((241,309),(97,435),.54),
}


@lru_cache(maxsize=20)
def wrist(pose, side):
    """Place a master sprite in a fingertip-aligned coordinate system.

    The atlas cuts the forearm off at its source edge. Continue an actual cloth
    cross section behind the cuff so it reaches the edge of the camera frame
    for every hand trajectory. No substitute illustration is used for the skin.
    """
    source=Image.open(PUBLIC/'wardrobe'/f'pov-{pose}-{side}.webp').convert('RGBA')
    (ax,ay),(wx,wy),ratio=CONTACT[pose,side]
    theta=math.atan2(wy-ay,wx-ax); co,si=math.cos(theta),math.sin(theta)
    ss=1.4; px=round(49*ss);py=round(104*ss)
    sx,sy=round(262*ss),round(218*ss)
    # The canonical x axis points from the contact point back through the wrist.
    transform=(co/(ratio*ss),-si/(ratio*ss),ax+(-px*co+py*si)/(ratio*ss),
               si/(ratio*ss),co/(ratio*ss),ay+(-px*si-py*co)/(ratio*ss))
    cropped=source.transform((sx,sy),Image.Transform.AFFINE,transform,Image.Resampling.BICUBIC)
    photo=np.array(cropped)
    r,g,b=[photo[:,:,i].astype(float) for i in range(3)]
    textile=(photo[:,:,3]>233)&(r < b*1.13)&(r<158)
    start,end=round(px+93*ss),min(sx-2, round(px+198*ss))
    counts=textile[:,start:end].sum(axis=0)
    # End through the broadest continuous fabric, after the cuff seam.
    cut=int(start+np.argmax(counts))
    covered=np.flatnonzero(textile[:,cut])
    if len(covered)<15:
        raise RuntimeError(f'cannot extend sleeve: {pose} {side}')
    low,high=int(covered[0]),int(covered[-1])
    out=np.zeros((sy,round(1060*ss),4),dtype='uint8')
    out[:,:cut]=photo[:,:cut]
    # Continue the fabric using the sleeve's measured colour, directional
    # weave and just two oblique folds. Repeating a single cuff seam would
    # produce a conspicuous row of identical ridges on the forearm.
    cloth_rgb=np.median(photo[:,:,:3][textile],axis=0)
    rng=np.random.default_rng(400+ord(pose[0])+ord(side[0]))
    coarse=Image.fromarray(rng.integers(45,205,(27,124),dtype='uint8')).resize((out.shape[1],sy),Image.Resampling.BICUBIC)
    weave=(np.asarray(coarse,dtype=float)-128)*.074+rng.normal(0,3.7,out.shape[:2])
    for u in range(cut,out.shape[1]):
        length=(u-cut)/ss
        spread=1+min(.72,length*.00155)
        drift=11*ss*(1-math.exp(-length/260))
        center=(low+high)*.5+drift
        top=max(0,math.floor(center-(high-low)*.5*spread))
        bottom=min(sy-1,math.ceil(center+(high-low)*.5*spread))
        yy=np.arange(top,bottom+1)
        rows=np.rint(np.clip((yy-center)/spread+(high+low)*.5,low,high)).astype(int)
        cross=2*(rows-low)/(high-low)-1
        light=.91+.16*np.cos((cross+.26)*1.55)-.09*cross
        fold=(1-.095*np.exp(-((length-26-cross*13)/4)**2)
                -.12*np.exp(-((length-111+cross*25)/8)**2)
                +.07*np.exp(-((length-102+cross*25)/11)**2))
        offset=(weave[yy,u]+1.65*np.sin(yy*1.9+u*.7))[:,None]
        cloth=cloth_rgb*(light*fold)[:,None]+offset
        mix=smooth(length/25)
        color=(1-mix)*photo[rows,cut,:3]+mix*cloth
        out[yy,u,:3]=np.clip(color,0,255).astype('uint8')
        out[yy,u,3]=np.minimum(1,np.minimum(yy-top+.15,bottom-yy+.15))*255
    # Discard isolated opaque border noise from the original image crop.
    cleaned=Image.fromarray(out,'RGBA')
    a=cleaned.getchannel('A')
    cleaned.putalpha(a.filter(ImageFilter.MedianFilter(3)))
    return cleaned, px,py,ss


def hand(im,x,y,angle=0,s=1,pose='rest'):
    side='left' if math.cos(math.radians(angle))<0 else 'right'
    sprite,px,py,ss=wrist(pose,side)
    theta=math.radians(angle);co,si=math.cos(theta),math.sin(theta)
    f=ss/(SCALE*s); ox=x*SCALE;oy=y*SCALE
    mat=(co*f,si*f,px-f*(ox*co+oy*si),-si*f,co*f,py+f*(ox*si-oy*co))
    layer=sprite.transform(im.size,Image.Transform.AFFINE,mat,Image.Resampling.BILINEAR)
    im.paste(layer,(0,0),layer)


def cup(p,x,y,k=1):
    p.oval(x+4,y+9*k,48*k,12*k,(54,44,36))
    p.oval(x+42*k,y-23*k,17*k,19*k,(172,174,149));p.oval(x+43*k,y-23*k,10*k,12*k,(82,78,65))
    p.poly([(x-36*k,y-47*k),(x+36*k,y-47*k),(x+31*k,y+1*k),(x+23*k,y+7*k),(x-23*k,y+7*k),(x-30*k,y)],(186,186,159))
    p.line([(x-34*k,y-44*k),(x-28*k,y),(x-18*k,y+5*k)],(220,217,188),2*k)
    p.oval(x,y-47*k,36*k,8*k,(84,108,104));p.oval(x,y-47*k,32*k,5*k,(89,64,43))
    p.line([(x-29*k,y-18*k),(x+29*k,y-18*k)],(80,109,105),1.5*k)


def sheet(p,x,y,w,h,fill=PAPER):
    p.poly([(x+3,y+6),(x+w+9,y-1),(x+w-7,y+h+8),(x-6,y+h+13)],(61,51,41))
    p.poly([(x,y),(x+w,y-7),(x+w-11,y+h),(x-10,y+h+7)],fill)
    p.line([(x,y),(x+w,y-7)],shade(fill,1.16),2)


def office(im,t):
    p=Pen(im);sheet(p,204,266,467,238);sheet(p,212,262,455,237,(208,198,166))
    p.text(258,282,"来文登记簿",21,INK);p.line([(247,319),(623,313)],(92,96,80),2)
    for k in range(7):
        y=339+k*22; p.line([(241,y),(617,y-7)],(153,148,123),1)
    for x in (285,493,564):p.line([(x,320),(x-7,487)],(158,149,120),1)
    p.text(301,341,"南渠西段",13,INK);p.text(301,365,"便道复核",13,INK)
    # The seal lands on frame 69; the red impression stays on the page.
    hit=cue(t,2.39,.49)-cue(t,3.23,.56)
    if t>=2.88:
        p.oval(530,407,32,13,(141,63,46));p.oval(530,407,29,10,(205,185,152));p.text(515,400,"收讫",12,(151,64,43))
    drift=130*(1-cue(t,.65,1.60)+cue(t,4.15,1.7))
    xx,yy=530+drift,349+hit*58
    st=Pen(im,xx,yy)
    st.oval(0,9,34,8,(122,50,35));st.rect(-34,-7,68,16,(119,54,38));st.oval(0,-7,34,8,(174,92,55))
    st.poly([(-18,-8),(-10,-24),(-12,-52),(12,-52),(10,-24),(18,-8)],(98,51,33));st.oval(0,-55,22,13,(128,71,42))
    hand(im,xx-5,yy-50,35,.93,pose="offer");cup(p,125,342,.84)


def construction(im,t):
    p=Pen(im)
    p.poly([(0,391),(960,326),(960,540),(0,540)],(84,90,79))
    for j in range(16):
        y=375+j*11
        for i in range(7):
            x=(i*143+j*51+t*(3+j%4))%1020-60
            p.line([(x,y),(x+25+j,y-1),(x+55+j*2,y-4)],(116+j%3*6,122+j%4*4,103),1)
    # The surveyor unreels a lead on a braided line and the float meets the surface.
    post=Pen(im,588,259,4);post.poly([(-16,-77),(15,-81),(19,173),(-13,180)],(184,175,138))
    for j in range(18):
        y=-61+j*13;post.rect(-12,y,13 if j%5 else 23,2,(92,66,51))
    for i,num in enumerate("321"):post.text(-8,-56+i*65,num,12,(98,63,46))
    p.line([(27,290),(538,265)],(92,78,57),7);p.line([(27,287),(538,262)],(157,147,109),2)
    for i in range(2):p.poly([(105+i*305,211),(121+i*305,209),(129+i*305,476),(111+i*305,479)],(98,91,65))
    y=288+97*cue(t,1.15,2.02)
    for i in range(3):
        elapsed=t-3.17-i*.38
        if 0<elapsed<2.2:p.oval(510,y+8,9+elapsed*37,2+elapsed*6,(138,146,125));p.oval(510,y+8,7+elapsed*37,1+elapsed*6,(85,92,80))
    p.line([(496,191),(506,246),(510,y-15)],(193,183,142),2)
    p.oval(510,y,9,19,(157,77,48));p.oval(510,y-10,7,7,(216,195,153));p.line([(509,y+17),(509,y+23)],(67,62,51),2)
    hand(im,485,189,40,.82,pose="offer");p.line([(949,87),(759,132)],(112,102,80),1)


def coordination(im,t):
    p=Pen(im);sheet(p,455,264,379,204,(203,192,159));p.text(489,282,"本季预算",20,INK)
    for i in range(8):p.line([(484,320+i*17),(797,314+i*17)],(151,144,119),1)
    for j in range(3):p.line([(564+j*72,318),(557+j*72,444)],(151,144,119),1)
    def book(x,y,w,h,color,title):
        p.poly([(x+3,y+7),(x+w+5,y-12),(x+w+20,y+h-8),(x+15,y+h+14)],(57,52,43))
        p.poly([(x,y),(x+w,y-18),(x+w+15,y+h-15),(x+13,y+h+6)],color)
        p.line([(x+13,y+1),(x+25,y+h+2)],shade(color,1.33),2)
        p.rect(x+31,y+17,79,24,(202,189,150));p.text(x+40,y+22,title,12,INK)
    book(72,330,125,122,(92,114,103),"道路项目");book(174,326,129,128,(114,98,72),"诊疗项目")
    move=cue(t,1.1,1.8);settle=math.sin(math.pi*cue(t,2.74,.5))*3
    xx=270+175*move; yy=351-24*move-settle
    book(xx,yy,143,120,(108,71,58),"南渠工程")
    if t>=3.48:
        length=cue(t,3.7,.58)
        nib_x,nib_y=714+23*length,371-14*length
        if length:
            p.line([(707,369),(714,371),(nib_x,nib_y)],(83,75,52),2)
        away=230*(1-cue(t,3.30,.40)+cue(t,4.45,.66))
        nib_x+=away; nib_y-=away*.24
        p.line([(nib_x,nib_y),(nib_x+35,nib_y-65)],(61,65,56),5)
        p.line([(nib_x+30,nib_y-57),(nib_x+36,nib_y-67)],(175,160,121),3)
        hand(im,nib_x+10,nib_y-23,32,.73,pose="write")
    if t<3.48:
        reset=cue(t,2.85,.62)
        hand(im,xx+140+190*reset,yy+44+178*reset,35,.82)
    cup(p,880,300,.68)


def dinner(im,t):
    p=Pen(im);p.oval(419,434,395,99,(53,45,38));p.oval(416,421,397,99,(141,127,100));p.oval(415,415,394,96,(104,105,86))
    p.oval(413,414,366,84,(113,112,91))
    theta=-.73+1.57*cue(t,1.20,2.65)
    for phase in (0,math.pi*.79,math.pi*1.52):
        a=theta+phase;x=417+239*math.sin(a);y=414+57*math.cos(a)
        if phase==0:
            p.poly([(x-55,y-8),(x+39,y-18),(x+61,y+8),(x-42,y+21)],(148,60,42))
            p.line([(x-51,y-6),(x-7,y+4),(x+37,y-14)],(184,90,56),1)
        p.oval(x,y-5,58,17,(69,74,65));p.oval(x,y-9,58,17,(194,192,159));p.oval(x,y-10,46,11,(143,155,137))
        for j in range(7):
            px=x+math.sin(j*2.13)*24;py=y-11+math.cos(j*1.64)*5
            p.oval(px,py,9+j%3,5,(134+j%3*10,95+j%2*13,56))
    px=642+35*cue(t,1.3,1.5)+350*cue(t,3.65,1.1)
    hand(im,px,461,33,.83)
    p.line([(62,501),(183,445)],(87,68,46),5);p.line([(76,505),(196,448)],(161,123,77),4)


def reception(im,t):
    p=Pen(im);sheet(p,171,310,297,130,(181,172,142));p.text(194,330,"访客登记",16,INK)
    for j in range(4):p.line([(192,364+j*17),(432,357+j*17)],(135,132,107))
    p.oval(548,425,82,18,(49,51,47));p.oval(544,413,78,19,(76,70,54))
    p.oval(545,399,68,22,(109,92,60));p.oval(545,385,57,40,(151,126,82));p.oval(530,368,25,10,(182,158,104));p.oval(518,367,10,4,(203,181,130))
    a=cue(t,1.57,.27)-cue(t,2.07,.34);bump=math.sin((t-1.84)*52)*math.exp(-max(0,t-1.84)*11) if t>1.84 else 0
    p.rect(540+bump,331+9*a,8,18,(141,130,101));p.oval(544+bump,333+9*a,17,6,BRASS)
    retreat=465*(1-cue(t,.45,1.1)+cue(t,2.22,.94))
    hand(im,544+retreat,327+9*a,37,.83,pose="offer")
    shift=131*cue(t,2.95,.95)
    q=Pen(im,98+shift,438,1);q.poly([(0,0),(89,-8),(109,11),(79,32),(4,31),(-11,20)],(94,101,85))
    q.oval(5,13,6,5,(151,146,113));q.oval(5,13,3,2,(60,63,53));q.text(22,7,"会 客",13,(211,196,153))
    if t>3.80:
        left=cue(t,3.8,.73)
        hand(im,230-(1-left)*195,455+80*(1-left),143,.68)


def golf(im,t):
    p=Pen(im);p.poly([(0,368),(187,348),(405,367),(659,325),(960,335),(960,540),(0,540)],(101,119,75))
    rng=random.Random(46)
    for _ in range(180):
        x=rng.uniform(0,960);y=rng.uniform(373,540)
        p.line([(x,y),(x+3,y-rng.uniform(1,4))],(112+rng.randrange(15),130,83))
    x,y=698,403;p.oval(x+10,y+2,29,6,(89,96,61));p.oval(x,y,17,5,(54,64,43))
    p.line([(x,y-3),(x-2,118)],(196,194,153),3)
    lift=math.sin(t*2.0);flap=[(x-1,118),(x+22,122),(x+45,116+lift*4),(x+70,118+lift*6),(x+56,136+lift*3),(x+26,141),(x-1,142)]
    p.poly(flap,(150,72,46));p.line(flap[:4],(188,106,68),1.3)
    q=cue(t,1.61,2.63);roll=1-(1-q)**1.15
    bx=298+(678-298)*roll;by=442-33*roll-19*math.sin(math.pi*roll)
    p.oval(bx+3,by+2,10-3*roll,3,(75,83,55));p.oval(bx,by-3,8-2*roll,8-2*roll,(216,211,180))
    p.oval(bx-2,by-5,1.5,1.2,(238,229,195))
    swing=cue(t,.54,.69)-2.3*cue(t,1.29,.40)+1.8*cue(t,1.83,.9)
    dx=50*swing-82*cue(t,2.55,1.2)
    club_x=268-dx; club_y=431+4*swing
    head=Pen(im,club_x,club_y,-5+swing*7)
    # We see the knuckles and shaft from above, then follow our ball.
    head.line([(-176,92),(-18,-5)],(94,98,83),6)
    head.line([(-174,90),(-18,-6)],(197,192,158),2)
    head.line([(-176,92),(-96,46)],(46,53,46),11)
    head.poly([(-29,-7),(11,-13),(27,-9),(26,-2),(-13,3),(-29,0)],(71,73,61))
    grip=head.xy((-101,47))
    hand(im,grip[0]/SCALE,grip[1]/SCALE,137+swing*4,.79)


def home(im,t):
    p=Pen(im);sheet(p,170,317,224,143,(197,180,145));p.text(194,334,"外地培训通知",16,INK)
    for j in range(4):p.line([(189,374+j*15),(352-j%2*25,368+j*15)],(145,134,109))
    sheet(p,374,278,318,185,(219,205,169));p.text(408,293,"家 庭 日 历",18,(129,68,50))
    for j in range(6):p.line([(396,333+j*23),(658,328+j*23)],(149,143,115))
    for j in range(8):p.line([(398+j*37,332),(393+j*37,443)],(149,143,115))
    for n in range(21):
        c,r=n%7,n//7;p.text(405+c*37,341+r*23,str(n+1),10,(94,90,73))
    mark=cue(t,2.18,1.28);ang=math.pi*1.73*mark
    path=[(537+13*math.cos(-1.6+ang*i/28),368+9*math.sin(-1.6+ang*i/28)) for i in range(29)]
    if mark>0:p.line(path,(150,68,51),2)
    xx,yy=path[-1];d=200*(1-cue(t,.75,1.36)+cue(t,3.87,1.13));xx+=d;yy-=d*.17
    p.line([(xx,yy),(xx+35,yy-82)],(60,66,59),5);p.line([(xx+29,yy-68),(xx+36,yy-80)],(179,162,116),3)
    hand(im,xx+9,yy-24,43,.73,pose="write");cup(p,802,374,.95)
    for k in range(3):
        pts=[(800+k*7+5*math.sin(i*.8+t+k),322-i*4) for i in range(8)]
        p.line(pts,(155,146,115),1)


def old_house(im,t):
    p=Pen(im);cup(p,191,345,.9)
    p.poly([(269,381),(614,347),(682,451),(325,495)],(145,122,88))
    p.line([(270,381),(476,428),(615,347)],(104,89,64),2)
    move=cue(t,.93,2.65);xx=322+127*move;yy=367-50*move
    sheet(p,xx,yy,254,123,(193,173,132))
    p.text(xx+26,yy+22,"泊山亲启",19,(87,73,52))
    p.text(xx+23,yy+51,"前几日的信收到了。我这边都好。",11,(100,86,64))
    p.text(xx+22,yy+68,"你回来的时候，到家里来坐坐。",11,(104,88,66))
    p.line([(xx+3,yy+89),(xx+238,yy+82)],(179,157,122),1)
    p.text(xx+121,yy+97,"九月初六",13,(91,78,58))
    slide=cue(t,3.6,1.42);hand(im,xx+240-slide*64,yy+54+slide*29,38,.77)
    for j in range(4):
        p.line([(281,461+j),(308,483+j),(396,473+j)],(149,129,94))


@lru_cache
def family_print():
    plate=Image.open(PUBLIC/"county-locations.jpg").convert("L")
    third=plate.crop((round(plate.width*2/3),round(plate.height*2/3),plate.width,plate.height))
    im=ImageOps.fit(third,(round(219*SCALE),round(112*SCALE)),centering=(.5,.38))
    return ImageOps.colorize(im,(62,65,54),(202,191,153)).convert("RGBA")


def gathering(im,t):
    p=Pen(im);cup(p,206,367,.77);cup(p,787,293,.56)
    # A print moves across the table. Neither relative lets go immediately.
    move=cue(t,1.56,2.42);xx=263+208*move; yy=372-15*move
    q=Pen(im,xx,yy,-7+8*move)
    q.poly([(-11,-43),(229,-42),(226,95),(-12,94)],(75,53,40))
    q.poly([(-15,-48),(225,-46),(221,91),(-17,90)],(205,192,157));q.rect(-6,-39,219,113,(131,129,103))
    q.rect(-4,-38,216,66,(155,155,129));q.rect(-4,28,216,44,(112,114,92))
    print_image=family_print().rotate(-math.degrees(q.a),Image.Resampling.BICUBIC,expand=True)
    center=q.xy((103.5,17.0))
    im.paste(print_image,(center[0]-print_image.width//2,center[1]-print_image.height//2),print_image)
    q.line([(-2,-36),(79,-37),(128,-34)],(210,200,163),1)
    q.text(44,76,"上回聚餐",10,(104,91,67))
    hand(im,xx-7-220*cue(t,4.1,1.1),yy+27,141,.75,pose="offer")
    approach=205*(1-cue(t,2.45,1.32));hand(im,xx+215+approach,yy+19,-5,.76,pose="offer")


def bus(im,t):
    p=Pen(im)
    # Foreground window, worn handle, a ticket caught at the rubber edge.
    p.poly([(0,353),(960,289),(960,540),(0,540)],(57,65,62));p.line([(0,355),(960,288)],(156,153,120),5)
    for k in range(12):
        p.line([(0,382+k*13),(960,315+k*13)],(63+k%4*3,72,66),1)
    p.poly([(96,-5),(134,-5),(168,347),(128,351)],(71,77,69));p.line([(132,-5),(165,346)],(148,148,119),4)
    slip=cue(t,1.44,1.62);xx=295+86*slip;yy=371-61*slip
    q=Pen(im,xx,yy,-7+3*slip)
    q.rect(-3,3,222,100,(58,61,52));q.rect(0,0,220,96,(203,178,129))
    for i in range(15):q.oval(1,4+i*6.2,2.6,2.1,(71,73,62));q.oval(220,4+i*6.2,2.6,2.1,(71,73,62))
    q.text(17,15,"县 城 客 运",16,(124,66,47));q.text(20,46,"夜班",13,INK);q.text(82,43,"19 : 40",20,INK)
    q.line([(12,37),(209,37)],(151,112,77))
    for j in range(14):q.rect(153+j*3.2,60,1+j%2,18,(92,79,56))
    # Our ticket stays between our thumb and forefinger; the conductor reaches
    # from the opposite side of this same window with a punch.
    hand(im,xx+8,yy+71,139,.82)
    tilt=cue(t,2.77,.27)-cue(t,3.31,.40)
    # Cast-iron conductor's punch closes on the top-right corner of the ticket.
    x=xx+176; y=yy-4
    jaw=Pen(im,x,y,-6);jaw.poly([(0,0),(22,-14),(105,-23),(113,-13),(29,-3),(14,9)],(124,127,106))
    jaw.poly([(3,-24+14*tilt),(21,-30+14*tilt),(106,-44+20*tilt),(113,-33+16*tilt),(25,-20+11*tilt),(12,-13+12*tilt)],(150,151,126))
    jaw.oval(25,-12,4,4,(207,194,149));hand(im,x+80,y-22,-10,.74,pose="write")
    if t>=3.04:q.oval(181,7,4,5,(75,75,60))
    for i in range(18):
        x=(15+i*61-t*3)%960;y=(i*37+t*(6+i%3))%258
        p.line([(x,y),(x-2,y+9)],(128,136,124),1)


@lru_cache
def film_frame(stem):
    im=Image.open(PUBLIC/"scenes"/("county-film-"+stem+".webp")).convert("RGB")
    return ImageOps.fit(im,(round(340*SCALE),round(190*SCALE)))


def cinema(im,t):
    p=Pen(im);p.poly([(46,99),(419,92),(422,316),(44,326)],(39,41,35))
    still=film_frame("chair" if t<3.80 else "girl")
    im.paste(still,(round(61*SCALE),round(111*SCALE)))
    p.line([(52,312),(415,309)],(144,122,87),4)
    p.poly([(638,151),(748,154),(792,383),(627,404)],(48,48,41));p.poly([(604,270),(801,246),(876,526),(591,540)],(61,62,54))
    p.line([(616,405),(820,372)],(119,115,91),4)
    for cx,cy,r,a0 in [(675,113,96,.1),(862,185,117,-1.4)]:
        p.oval(cx+5,cy+6,r,r,(42,43,37));p.oval(cx,cy,r,r,(114,112,90));p.oval(cx,cy,r-5,r-5,(86,88,73))
        a=a0+t*2.75
        for j in range(5):
            rad=a+j*math.tau/5; x=cx+.57*r*math.cos(rad);y=cy+.57*r*math.sin(rad)
            p.oval(x,y,.23*r,.23*r,(56,57,48));p.oval(x+1,y+2,.19*r,.19*r,(45,45,38))
        p.oval(cx,cy,r*.17,r*.17,(144,135,102));p.oval(cx,cy,r*.065,r*.065,(56,56,47))
    p.line([(596,157),(626,282),(678,353),(758,282)],(166,145,108),3)
    for off in range(16):
        yy=(t*39+off*10)%110;p.oval(601+yy*.20,163+yy,1.1,1.5,(194,175,132))
    p.oval(692,419,18,18,(92,91,73));p.oval(692,419,10,10,(48,50,43))
    # Our palm is at the near edge of the projector. The change on the distant
    # screen follows the notch we tip; the spectator stays in the booth.
    notch=cue(t,3.4,.40)-cue(t,4.12,.35)
    p.line([(692,419),(684+17*notch,387)],(157,146,109),5)
    p.oval(684+17*notch,386,8,8,(109,111,91))
    hand(im,684+17*notch+104*(1-cue(t,1.63,1.52)),387+40*(1-cue(t,1.63,1.52)),39,.84,pose="offer")
    if 3.77<t<3.85:p.rect(61,111,340,191,(196,184,146))


ART = {"L01":office,"L02":construction,"L03":coordination,"L04":dinner,"L05":reception,
       "L06":golf,"L07":home,"L08":old_house,"L09":gathering,"bus":bus,"cinema":cinema}


# Endpoint of a first-person lean: the near hand stays on the same side of the
# room. At the cinema the silver screen can fill our view inside the booth.
# (cut time, settle time, x, y, width)
CLOSEUPS = {
    "L01": (2.59, 4.4, 227, 213, 610), "L02": (2.93, 5.3, 310, 207, 515),
    "L03": (3.39, 5.4, 372, 243, 535), "L04": (2.77, 5.0, 327, 264, 583),
    "L05": (1.60, 2.63, 346, 224, 473), "L06": (3.02, 5.2, 460, 283, 492),
    "L07": (2.10, 4.82, 307, 236, 510), "L08": (3.31, 5.47, 383, 244, 441),
    "L09": (3.48, 5.34, 358, 228, 539), "bus": (2.68, 4.37, 331, 193, 508),
    "cinema": (3.65, 5.7, 14, 47, 513),
}


def render(scene, frame, fps):
    from PIL import ImageChops
    base=plate(scene)
    im=base.copy()
    ART[scene](im,frame/fps)
    fg=ImageChops.difference(im,base).convert("L").point(lambda n:255 if n>=2 else 0)
    cast=fg.transform(SIZE,Image.Transform.AFFINE,(1,0,-6,0,1,-9)).filter(ImageFilter.GaussianBlur(4)).point(lambda n:n*0.35)
    under=Image.composite(Image.new("RGB",SIZE,(29,25,19)),base,cast)
    im=Image.composite(im,under,fg)
    at=frame/fps
    cut,settle,x,y,width=CLOSEUPS[scene]
    lean=cue(at,cut-.37,.85)
    if scene=="L05": lean*=1-cue(at,settle,.91)
    if lean>0:
        height=width*H/W
        x=min(W-width,x);y=min(H-height,y)
        # Continuous movement from where the player stands. The interval before
        # the hand reaches the prop gives the eye time to settle on its movement.
        bx=x*lean;by=y*lean
        bw=W+(width-W)*lean;bh=H+(height-H)*lean
        box=tuple(round(a*SCALE) for a in (bx,by,bx+bw,by+bh))
        im=im.crop(box).resize(SIZE,Image.Resampling.BICUBIC)
    im=ImageChops.multiply(im,Image.merge("RGB",(patina(),)*3))
    return im.resize((W,H),Image.Resampling.LANCZOS)
