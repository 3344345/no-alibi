"""Build transparent, riggable heads from the cast art with macOS Vision.

The game consumes prebuilt WebP and JSON. Requires Pillow, NumPy, and Apple's
Swift compiler and Vision at build time. Originals of the historical cast stay
in frontend/public/cast; the fictional neighbours share two source sheets.
Also rebuilds the photographed neck inserts used beneath the stage portraits.
"""
import argparse
import hashlib
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFilter

from cut_actor_necks import export_necks


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'frontend/public'
SHEET = ROOT / 'assets/cast-source/family-contact.webp'
GEOMETRY = ROOT / 'frontend/src/faceGeometry.json'
RESAMPLE = Image.Resampling.LANCZOS
NEIGHBOURS = ('woman-young','woman-mid','woman-elder','girl',
              'man-young','man-mid','man-elder','driver')
EXTRA = ('boy','teen-boy','apprentice','seamstress','fish-counter','puppet-master','granny','girl-child')
BOBS = {'woman-young', 'girl', 'girl-child', 'art_bian_zhongyun', 'art_shang_aiyun', 'art_lin_zhao'}


# Several archival photos contain faces elsewhere in the background or a
# low-contrast vignette. These hand-traced silhouettes belong ONLY to these
# specific source editions; a replaced original goes through Vision afresh.
SILHOUETTES = {
    '237c33ade593': [(x/181, y/245) for x,y in [(38, 62), (39, 46), (45, 31), (55, 23), (73, 18), (95, 17), (112, 23), (126, 32), (132, 47), (135, 64), (133, 76), (134, 83), (130, 92), (123, 100), (120, 117), (114, 133), (101, 148), (88, 151), (74, 145), (62, 132), (55, 117), (51, 101), (46, 95), (40, 83)]],
    '76aebbc90fce': [(x/203, y/245) for x,y in [(55, 68), (55, 52), (57, 36), (63, 24), (77, 18), (96, 16), (111, 19), (127, 26), (136, 37), (140, 53), (142, 67), (141, 91), (134, 104), (129, 106), (125, 119), (114, 131), (102, 139), (90, 140), (77, 136), (66, 126), (61, 110), (57, 95), (54, 88), (55, 78)]],
    'a728a7b081bb': [(x/96, y/117) for x,y in [(13, 41), (14, 27), (18, 19), (24, 13), (34, 9), (45, 7), (57, 10), (64, 15), (71, 25), (77, 33), (80, 40), (81, 47), (85, 52), (86, 57), (84, 62), (84, 68), (82, 74), (81, 80), (76, 85), (71, 89), (61, 92), (50, 90), (37, 86), (29, 81), (27, 71), (22, 66), (18, 60), (17, 53), (14, 49)]],
    'cd0fe4da72ae': [(x/163, y/245) for x,y in [(13, 87), (12, 66), (13, 45), (22, 32), (37, 23), (59, 16), (81, 13), (102, 15), (121, 24), (133, 37), (142, 55), (149, 74), (148, 86), (142, 94), (137, 99), (132, 111), (126, 127), (119, 146), (107, 164), (91, 176), (79, 178), (63, 173), (46, 163), (31, 150), (24, 132), (16, 120), (11, 110), (9, 99)]],
    '2e0b3f3fbca6': [(x/165, y/245) for x,y in [(24, 90), (21, 73), (21, 46), (25, 30), (37, 19), (58, 11), (79, 6), (99, 2), (116, 1), (133, 2), (140, 7), (145, 19), (148, 32), (149, 56), (146, 72), (151, 78), (151, 91), (147, 109), (138, 122), (133, 125), (130, 143), (125, 156), (115, 170), (101, 181), (87, 184), (73, 182), (58, 171), (44, 155), (37, 138), (33, 123), (29, 112)]],
    'c2eff9342bb9': [(x/164, y/245) for x,y in [(28, 90), (29, 70), (30, 48), (31, 36), (44, 23), (61, 16), (79, 13), (104, 15), (125, 22), (139, 34), (147, 47), (149, 63), (144, 82), (142, 96), (139, 104), (139, 119), (135, 135), (131, 148), (120, 162), (105, 173), (91, 179), (78, 179), (64, 172), (52, 159), (44, 143), (40, 132), (33, 123), (27, 114), (24, 99)]],
    '39e61194d8a0': [(x/166, y/245) for x,y in [(28, 95), (28, 75), (30, 57), (34, 32), (42, 21), (60, 13), (80, 11), (99, 12), (116, 17), (131, 29), (139, 48), (142, 66), (140, 88), (139, 100), (134, 112), (131, 123), (122, 145), (111, 159), (99, 170), (84, 173), (69, 168), (55, 159), (46, 145), (40, 127), (33, 118), (27, 102)]],
    '166cbbf5ab55': [(x/61, y/85) for x,y in [(18, 28), (19, 20), (22, 13), (29, 9), (36, 8), (42, 9), (48, 13), (53, 19), (55, 26), (55, 32), (54, 36), (55, 41), (54, 47), (51, 51), (50, 55), (45, 59), (39, 60), (33, 57), (28, 52), (24, 45), (21, 43), (20, 39), (18, 35)]],
    'fd860d1a4acf': [(x/186, y/245) for x,y in [(32, 85), (33, 61), (39, 44), (49, 29), (65, 18), (80, 11), (95, 13), (101, 17), (112, 15), (125, 20), (133, 31), (137, 46), (138, 64), (146, 69), (147, 78), (144, 91), (138, 103), (133, 106), (131, 127), (121, 151), (111, 165), (102, 179), (91, 196), (84, 209), (77, 217), (72, 205), (69, 196), (64, 192), (61, 172), (55, 158), (51, 144), (44, 134), (38, 118), (35, 105)]],
    '9db464234121': [(x/341,y/450) for x,y in [
        (15,155),(22,114),(32,90),(45,74),(68,59),(97,47),(128,37),(167,35),
        (199,40),(224,45),(246,56),(266,74),(271,91),(269,103),(277,122),(282,144),
        (288,163),(286,177),(282,184),(284,193),(293,205),(307,220),(318,228),
        (319,235),(315,244),(304,250),(302,257),(307,267),(309,276),(302,280),
        (300,290),(305,291),(304,297),(296,309),(292,318),(291,331),(284,343),
        (275,352),(258,359),(239,359),(222,356),(207,349),(190,338),(169,324),
        (152,311),(132,298),(110,286),(94,277),(79,275),(68,283),(50,283),
        (35,276),(27,263),(25,235),(20,217),(18,185)]],
    '08638ef7daa3': [
        (.145,.237),(.157,.176),(.194,.125),(.240,.092),(.307,.067),(.383,.053),
        (.426,.044),(.486,.047),(.522,.037),(.578,.043),(.625,.056),(.685,.062),
        (.747,.087),(.808,.121),(.864,.181),(.886,.236),(.892,.310),(.883,.360),
        (.887,.416),(.900,.474),(.889,.551),(.855,.615),(.820,.655),(.771,.687),
        (.735,.747),(.692,.777),(.625,.796),(.560,.795),(.485,.777),(.412,.745),
        (.352,.704),(.302,.637),(.272,.574),(.248,.538),(.231,.515),(.218,.478),
        (.206,.424),(.195,.396),(.178,.345),(.160,.294)],
    '24c09198bdb7': [
        (.185,.196),(.204,.145),(.238,.103),(.301,.064),(.372,.043),(.447,.046),
        (.505,.030),(.583,.039),(.652,.061),(.704,.105),(.736,.156),(.747,.221),
        (.731,.277),(.736,.316),(.719,.366),(.690,.399),(.641,.455),(.608,.470),
        (.585,.519),(.548,.568),(.496,.601),(.421,.621),(.350,.618),(.286,.606),
        (.228,.580),(.212,.547),(.202,.518),(.198,.481),(.184,.459),(.168,.444),
        (.189,.415),(.179,.381),(.169,.345),(.167,.302),(.179,.254)],
    '83c9e942ad83': [
        (.273,.247),(.283,.196),(.298,.153),(.341,.120),(.412,.104),(.495,.105),
        (.569,.112),(.656,.121),(.721,.136),(.792,.157),(.853,.189),(.891,.224),
        (.913,.283),(.903,.325),(.852,.344),(.787,.361),(.729,.366),(.695,.384),
        (.661,.415),(.615,.439),(.554,.458),(.497,.472),(.443,.469),(.406,.451),
        (.388,.429),(.368,.412),(.354,.387),(.367,.371),(.337,.361),(.342,.341),
        (.350,.321),(.333,.310),(.307,.308),(.288,.289)],
    'a251b31556db': [
        (.250,.610),(.258,.526),(.278,.468),(.314,.423),(.367,.387),(.443,.355),
        (.527,.337),(.611,.333),(.706,.344),(.769,.364),(.808,.403),(.812,.444),
        (.829,.491),(.853,.535),(.870,.586),(.873,.611),(.856,.631),(.871,.660),
        (.907,.698),(.942,.724),(.941,.745),(.911,.763),(.900,.774),(.909,.803),
        (.913,.834),(.899,.867),(.905,.897),(.896,.937),(.872,.980),(.865,.998),
        (.715,.998),(.638,.959),(.564,.922),(.496,.896),(.435,.865),(.393,.874),
        (.334,.875),(.282,.850),(.264,.788),(.257,.713)],
}


def matte_by_hand(points,size):
    control=np.asarray(points,dtype=float)
    path=[]
    for j in range(len(control)):
        a,b,c,d=(control[k%len(control)] for k in (j-1,j,j+1,j+2))
        for t in np.linspace(0,1,12,endpoint=False):
            xy=.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t**3)
            path.append(tuple(xy*np.asarray(size)))
    mask=Image.new('L',size)
    ImageDraw.Draw(mask).polygon(path,fill=255)
    return mask.filter(ImageFilter.GaussianBlur(max(.48,min(size)/720)))


def neighbours():
    for source,actors in ((SHEET,NEIGHBOURS),(SHEET.with_name('neighbours-contact.webp'),EXTRA)):
        sheet=Image.open(source).convert('RGB')
        w,h=sheet.size
        for index,name in enumerate(actors):
            col=index%4
            row=index//4
            yield name,sheet.crop((round(w*col/4),round(h*row/2),round(w*(col+1)/4),round(h*(row+1)/2)))


def eye(marks,side):
    region=marks[side+'Pupil'] or marks[side+'Eye']
    return np.mean(region,axis=0)


def landmarks(marks):
    eyes=sorted([eye(marks,'left'),eye(marks,'right')],key=lambda xy:xy[0])
    # Use center of the lip seam. For the nose use the midpoint of the nostrils.
    lips=np.array(marks['lips'])
    mouth=(lips.max(axis=0)+lips.min(axis=0))*.5
    nose=np.array(marks['nose'])
    nose=nose[nose[:,1]>=np.median(nose[:,1])].mean(axis=0)
    return np.array(eyes),mouth,nose


def extract(name,rgb,marks,matte):
    eyes,mouth,nose=landmarks(marks)
    jaw=np.array(marks['jaw'])
    chin=jaw[np.argmax(jaw[:,1])]
    jaw=jaw[np.argsort(jaw[:,0])]
    eye_y=eyes[:,1].mean()
    face_height=chin[1]-eye_y
    jaw_w=jaw[-1,0]-jaw[0,0]
    x_mid=eyes[:,0].mean()
    iw,ih=rgb.size
    yy,xx=np.ogrid[:ih,:iw]
    xpos=xx[0]/iw
    # Keep the ear and hair outside the jaw, but cut the collar and throat away.
    # The original art determines hair silhouette via the segmentation matte.
    edge=np.interp(xpos,jaw[:,0],jaw[:,1])
    lateral=np.clip(np.abs((xpos-x_mid)/(jaw_w*.5)),0,2)
    ear=eye_y+face_height*.56
    if name in BOBS:
        ear=eye_y+face_height*np.clip(1.00-.36*(lateral-1.08)**2,.66,1.)
    bottom=np.maximum(edge+.016*face_height,ear)
    top=eye_y-1.70*face_height
    side_ok=(np.abs(xpos-x_mid) < jaw_w*.93)
    coverage=np.clip((bottom[None,:]-yy/ih)*ih+.5,0,1)*np.clip((yy/ih-top)*ih+.5,0,1)
    coverage*=side_ok[None,:]
    alpha=np.asarray(matte.resize(rgb.size,RESAMPLE).convert('L')).astype('float32')
    alpha=np.clip((alpha-5)*255/247,0,255)*coverage
    mask=Image.fromarray(np.uint8(alpha))
    if name not in NEIGHBOURS and name not in EXTRA:
        source_hash=hashlib.sha256((PUBLIC/'cast'/(name+'.webp')).read_bytes()).hexdigest()[:12]
        if source_hash=='a728a7b081bb':
            # The original is a small, angled group-photo crop. At full size,
            # the right eye is inside the temple rather than on the silhouette.
            eyes=np.array([[62/96,45/117],[76.5/96,43.5/117]])
            nose=np.array([78/96,57/117])
            mouth=np.array([73.5/96,68.2/117])
        if source_hash=='9db464234121':
            # A strict profile shows just one pupil. Duplicate the location
            # instead of inventing an anatomical landmark in the background.
            eyes=np.array([[260/341,199/450],[260/341,199/450]])
            mouth=np.array([292/341,292/450])
            nose=np.array([306/341,244/450])
        contour=SILHOUETTES.get(source_hash)
        if contour:
            mask=matte_by_hand(contour,rgb.size)
    bbox=mask.point(lambda v:255 if v>=60 else 0).getbbox()
    if bbox is None: raise ValueError('Empty head matte: '+name)
    x0,y0,x1,y1=bbox
    x0,y0,x1,y1=max(0,x0-3),max(0,y0-3),min(iw,x1+3),min(ih,y1+3)
    head=rgb.copy();head.putalpha(mask)
    head=head.crop((x0,y0,x1,y1))
    scale=352/max(head.size)
    head=head.resize((round(head.width*scale),round(head.height*scale)),RESAMPLE)
    def relative(pt):
        x,y=pt
        result=[round(float((x*iw-x0)/(x1-x0)),5),round(float((y*ih-y0)/(y1-y0)),5)]
        if any(v<=0 or v>=1 for v in result): raise ValueError('Landmark outside '+name)
        return result
    return head,{'eyes':[relative(e) for e in eyes],'mouth':relative(mouth),'nose':relative(nose)}


def process(item,work,exe):
    name,image=item
    folder=work/name;folder.mkdir()
    source=folder/'source.png'
    image.save(source)
    marksfile=folder/'face.json'; mattefile=folder/'mask.png'
    subprocess.run([str(exe),str(source),str(marksfile),str(mattefile)],check=True,capture_output=True)
    if not marksfile.is_file() or not mattefile.is_file(): raise ValueError('No Vision face/matte: '+name)
    head,geometry=extract(name,image,json.loads(marksfile.read_text()),Image.open(mattefile))
    dest=PUBLIC/'faces'/(name+'.webp')
    head.save(dest,'WEBP',quality=94,method=6,exact=True)
    return name,geometry


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--vision-bin',type=Path,help='Reuse a compiled portrait_landmarks.swift')
    parser.add_argument('--necks-only',action='store_true',help='Refresh photographic neck inserts using the existing heads')
    parser.add_argument('ids',nargs='*',help='Rebuild only selected cast IDs')
    args=parser.parse_args()
    (PUBLIC/'faces').mkdir(exist_ok=True)
    items=dict(neighbours())
    for path in sorted((PUBLIC/'cast').glob('*.webp')):
        items[path.stem]=ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    originals=items.copy()
    if args.ids: items={key:items[key] for key in args.ids}
    if args.necks_only:
        export_necks(originals,items,json.loads(GEOMETRY.read_text()),PUBLIC)
        print('Prepared',len(items),'neck textures.')
        return
    existing=json.loads(GEOMETRY.read_text()) if args.ids and GEOMETRY.exists() else {}
    with tempfile.TemporaryDirectory(prefix='jzs-head-atlas-') as tmp:
        work=Path(tmp)
        exe=args.vision_bin or (work/'vision')
        if not args.vision_bin:
            subprocess.run(['swiftc','-O',str(ROOT/'scripts/portrait_landmarks.swift'),'-o',str(exe)],check=True)
        with ThreadPoolExecutor(max_workers=2) as pool:
            for name,geometry in pool.map(lambda item:process(item,work,exe),items.items()):
                existing[name]=geometry
    GEOMETRY.write_text(json.dumps(existing,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    export_necks(originals,items,existing,PUBLIC)
    print('Prepared', len(items),'portraits and neck textures.')


if __name__=='__main__':
    main()
