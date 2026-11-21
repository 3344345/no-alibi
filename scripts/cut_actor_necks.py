"""Photographic neck inserts. Coordinates were marked on the actual cast originals.

Each edge is (left x, left y, right x, right y), measured on a 200 × 235
reference grid. The optional fifth value lowers the middle of a curved collar.
Only the area between the lower jaw and the clothing is sampled. The stage
draws the head and collar in front of the resulting 2:1 texture.
"""
import numpy as np
from PIL import Image

# The middle of the upper edge can sit a little inside the chin: after the
# head overlays it, the actual transition from jaw to throat becomes visible.
CUTS = {
    'woman-young':      ((78,156,129,156), (82,181,126,184,9)),
    'woman-mid':        ((77,156,128,156), (83,181,123,184,13)),
    'woman-elder':      ((76,156,128,156), (83,176,122,181,12)),
    'girl':             ((78,159,129,159), (83,192,125,196,9)),
    'man-young':        ((74,158,128,158), (77,197,125,201,10)),
    'man-mid':          ((75,153,132,152), (88,177,121,178,7)),
    'man-elder':        ((74,159,132,158), (83,186,124,187,10)),
    'driver':           ((73,158,134,158), (79,193,128,198,12)),
    'boy':              ((77,171,128,171), (82,188,123,190,8)),
    'teen-boy':         ((74,161,129,162), (77,200,125,202,8)),
    'apprentice':       ((71,167,131,166), (77,197,124,198,10)),
    'seamstress':       ((74,168,131,166), (80,193,124,194,9)),
    'fish-counter':     ((74,167,130,167), (78,196,125,194,10)),
    'puppet-master':    ((66,161,136,160), (77,184,125,188,10)),
    'granny':           ((68,172,133,171), (78,189,124,190,9)),
    'girl-child':       ((79,169,129,169), (83,190,125,191,8)),
    'art_bian_zhongyun':((69,151,128,157), (80,173,124,183,10)),
    'art_chen_xitian':  ((85,153,135,146), (94,184,127,178,8)),
    'art_deng_shiping': ((75,145,137,143), (88,178,127,181,10)),
    'art_gao_qinrong':  ((73,151,126,149), (84,179,122,188,10)),
    'art_hu_fuming':    ((77,150,139,151), (84,170,130,169,14)),
    'art_jiang_yanyong':((77,152,132,153), (83,175,127,177,13)),
    'art_lin_zhao':     ((78,150,127,150), (83,178,124,183,7)),
    'art_liu_qingshan': ((76,150,128,151), (91,168,116,169,5)),
    'art_shang_aiyun':  ((80,154,129,154), (87,182,124,184,3)),
    'art_wang_jingyao': ((86,155,135,153), (95,175,127,177,11)),
    'art_yan_hongchang':((71,150,132,155), (83,180,125,187,7)),
    'art_yuan_geng':    ((73,151,135,148), (81,173,128,170,11)),
    'chiang_ching_kuo': ((78,130,130,132), (93,144,122,147,5)),
    'deng_xiaoping':    ((72,150,132,147), (88,159,126,161,6)),
    'li_peng':          ((83,125,120,119), (91,140,115,133,5)),
    'mao_zedong':       ((73,142,126,167), (83,171,120,183,3)),
    'sha_qianli':       ((68,162,124,163), (84,184,115,186,7)),
    'xu_zhiyong':       ((76,145,137,163), (94,165,131,180,3)),
    'zhang_naiqi':      ((56,163,143,153), (77,187,135,179,12)),
    'zhao_ziyang':      ((71,132,132,131), (84,151,125,148,8)),
    'zhou_enlai':       ((72,142,125,130), (77,161,113,143,4)),
    'zou_taofen':       ((89,170,140,154), (95,178,130,167,4)),
}

# Closed tunics, high collars, long beards, tiny group-photo crops and hats
# leave some archival sitters with no usable neck. Use an age-appropriate
# actor insert, matched to the sitter's own measured skin and print tonality.
STAND_INS = {
    'chen_duxiu': 'driver', 'chiang_kai_shek': 'puppet-master',
    'gu_zhenghong': 'man-young', 'hu_yaobang': 'man-elder',
    'li_gongpu': 'driver', 'minnie_vautrin': 'woman-mid',
    'peng_dehuai': 'man-mid', 'shen_junru': 'puppet-master',
    'shi_liang': 'woman-mid', 'sun_yatsen': 'man-mid',
    'tan_sitong': 'apprentice', 'wang_zaoshi': 'driver',
    'zhan_tianyou': 'driver', 'zhang_xueliang': 'man-young', 'zhang_zhizhong': 'driver',
}


def source_strip(photo, edges):
    height, width = 96,192
    v,u = np.mgrid[0:1:complex(height),0:1:complex(width)]
    def edge_points(edge):
        left_x,left_y,right_x,right_y,*curve=edge
        x=left_x*(1-u)+right_x*u
        y=left_y*(1-u)+right_y*u+(curve[0] if curve else 0)*4*u*(1-u)
        return x,y
    top_x,top_y=edge_points(edges[0]);bottom_x,bottom_y=edge_points(edges[1])
    x=((1-v)*top_x+v*bottom_x)*photo.width/200
    y=((1-v)*top_y+v*bottom_y)*photo.height/235
    pixels=np.asarray(photo.convert('RGB'),dtype=float)
    ix=np.floor(x).astype(int);iy=np.floor(y).astype(int)
    dx=(x-ix)[...,None];dy=(y-iy)[...,None]
    return ((1-dy)*((1-dx)*pixels[iy,ix]+dx*pixels[iy,ix+1])
            +dy*((1-dx)*pixels[iy+1,ix]+dx*pixels[iy+1,ix+1]))


LUMA=np.array([.2126,.7152,.0722])


def archival_tone(strip, head, geometry):
    """Keep the photographed throat's local shading and fine skin texture."""
    pixels=np.asarray(head.convert('RGBA'),dtype=float)
    h,w=pixels.shape[:2]
    eyes=np.asarray(geometry['eyes'])*[w,h]
    nose=np.asarray(geometry['nose'])*[w,h]
    mouth=np.asarray(geometry['mouth'])*[w,h]
    y,x=np.mgrid[:h,:w]
    # Sample the two cheeks below the pupils, clear of eyebrows, lips and hair.
    samples=np.zeros((h,w),dtype=bool)
    for eye in eyes:
        center=eye*.52+nose*.31+mouth*.17
        samples|=((x-center[0])/(.06*w))**2+((y-center[1])/(.036*h))**2<1
    cheek=pixels[samples & (pixels[...,3]>220),:3]
    if len(cheek)<12: raise ValueError('No opaque skin pixels below the eyes')
    skin=np.median(cheek,axis=0)
    original=np.median(strip.reshape(-1,3),axis=0)
    light=strip@LUMA; reference=original@LUMA
    neutral=light[...,None]-reference
    local_chroma=strip-original-neutral
    strength=np.clip(np.ptp(skin)/38,0,1)
    return skin*.80 + neutral*np.clip((skin@LUMA)/max(1,reference),.65,1.4) + local_chroma*strength


def export_necks(originals, ids, geometry, public):
    out=public/'necks'
    out.mkdir(exist_ok=True)
    missing=set(ids)-(CUTS.keys()|STAND_INS.keys())
    if missing: raise ValueError('No verified neck source for '+', '.join(sorted(missing)))
    for name in ids:
        donor=STAND_INS.get(name,name)
        texture=source_strip(originals[donor],CUTS[donor])
        if donor!=name:
            with Image.open(public/'faces'/(name+'.webp')) as head:
                texture=archival_tone(texture,head,geometry[name])
        image=Image.fromarray(np.uint8(np.clip(texture,0,255)+.49)).resize((128,64),Image.Resampling.LANCZOS)
        # The renderer owns the silhouette; opaque edge pixels keep the actor
        # intact even when the texture is projected into a tall collar opening.
        image.save(out/(name+'.webp'),'WEBP',quality=96,method=6)
