import type { ActingScene,CastMember,Turn } from './performance'
import type { FaceImage } from './actorFace'
type G=CanvasRenderingContext2D
type P=[number,number]
function fill(g:G,path:string,paint:string|CanvasGradient,edge?:string){const p=new Path2D(path);g.fillStyle=paint;g.fill(p);if(edge){g.strokeStyle=edge;g.lineWidth=1.3;g.stroke(p)}}
function stroke(g:G,path:string,colour:string,width=1){g.strokeStyle=colour;g.lineWidth=width;g.lineCap='round';g.lineJoin='round';g.stroke(new Path2D(path))}
function gradient(g:G,stops:string[],x1:number,y1:number,x2:number,y2:number){const grad=g.createLinearGradient(x1,y1,x2,y2);stops.forEach((s,i)=>grad.addColorStop(i/(stops.length-1),s));return grad}
function circle(g:G,x:number,y:number,r:number,c:string){g.fillStyle=c;g.beginPath();g.arc(x,y,r,0,Math.PI*2);g.fill()}
const smooth=(x:number)=>{x=Math.min(1,Math.max(0,x));return x*x*(3-2*x)}
function hand(g:G,reach:number,pose:string,time:number){
  g.save();g.rotate(-.13+reach*.17)
  const skin=gradient(g,['#845b40','#b38968','#c2a181','#9b7355'],0,0,17,19)
  fill(g,'M-6 -5 Q2 -10 12 -7 Q19 -9 25 -4 L28 1 Q26 7 18 9 L7 13 Q0 13 -6 6 Z',skin,'#6e5442')
  const pointing=pose==='inspect'||pose==='sign'
  for(let i=3;i>=0;i--){
    const y=-5+i*3.5, x=16-i*.8, bend=(pointing&&i>0?6:2.7)+i*1.4-3*reach+Math.sin(time+i)*.35
    const len=[20,21,18,13][i]-(pointing&&i>0?5:0)
    g.lineCap='round';g.lineWidth=4.7-i*.30;g.strokeStyle='#78583f'
    const p=new Path2D();p.moveTo(x,y);p.bezierCurveTo(x+len*.36,y-2,x+len*.7,y+bend*.5,x+len,y+bend)
    g.stroke(p);g.save();g.translate(0,-.8);g.strokeStyle=i===0?'#caac89':'#b99574';g.lineWidth-=1.15;g.stroke(p);g.restore()
  }
  stroke(g,'M5 0 Q13 -4 17 -13 Q20 -16 22 -14 Q24 -12 17 -4 Q15 1 12 4','#b18b68',5.3)
  stroke(g,'M6 7 Q11 3 14 1','#87654e',.85)
  g.restore()
}
function sleeve(g:G,from:P,to:P,thick:number,coat:string){
  const dx=to[0]-from[0],dy=to[1]-from[1],l=Math.max(1,Math.hypot(dx,dy))
  g.save();g.translate(...from);g.rotate(Math.atan2(dy,dx))
  const grad=gradient(g,['#272e2c',coat,coat,'#303831'],0,-thick,0,thick)
  fill(g,`M-3 ${-thick} Q${l*.37} ${-thick*1.16} ${l+1} ${-thick*.60} Q${l+8} 0 ${l+1} ${thick*.63} Q${l*.52} ${thick*.85} -4 ${thick} Q${-thick} 0 -3 ${-thick}Z`,grad,'#31372e')
  for(const [a,b] of [[.14,.76],[.51,.52],[.86,.79]])stroke(g,`M${l*a} ${-thick*.7} q${thick*.55} ${thick*b} ${thick*.65} ${thick*1.25}`,'#c0b6a039',1.4)
  g.restore()
}
function arm(g:G,shoulder:P,end:P,coat:string,amount:number,pose:string,t:number,far:boolean,delicate=false,costume='jacket'){
  const dx=end[0]-shoulder[0],dy=end[1]-shoulder[1],length=Math.max(1,Math.hypot(dx,dy))
  const extension=Math.min(1,Math.max(0,(end[0]-shoulder[0])/77))
  const elbow:P=[shoulder[0]+20+extension*15,shoulder[1]+Math.min(74,Math.max(33,(dy+106)*.40))-extension*9]
  const grasp=amount<.15?'rest':pose==='refuse'?'halt':pose==='sign'?'write':pose==='pass'?(delicate?'take':'offer'):pose==='inspect'||pose==='tune'?'pinch':'rest'
  const photographed=clothing('arm-'+grasp),cloth=clothing(costume)
  if(photographed&&cloth&&!far){
    const ax=elbow[0]-shoulder[0],ay=elbow[1]-shoulder[1],upper=Math.hypot(ax,ay)
    g.save();g.translate(...shoulder);g.rotate(Math.atan2(ay,ax)-Math.PI/2)
    const cap=new Path2D('M-19 6 Q-19 -10 -5 -13 Q11 -15 19 -2 Q23 3 22 17 L14 '+upper+' Q3 '+(upper+10)+' -13 '+(upper+1)+' Q-17 '+(upper*.49)+' -19 6Z')
    g.clip(cap)
    g.drawImage(cloth,cloth.width*.747,cloth.height*.18,cloth.width*.12,cloth.height*.51,-20,-14,44,upper+25)
    g.restore()
    const wx=end[0]-elbow[0],wy=end[1]-elbow[1]
    const fore=Math.hypot(wx,wy),angle=Math.atan2(wy,wx)
    // A single photographed forearm, cuff, wrist and hand turns at the elbow.
    // Its sleeve starts inside the upper sleeve so the joint stays covered.
    g.save();g.translate(...elbow);g.rotate(angle)
    const length=Math.max(65,Math.min(115,fore+37)),height=length*.402
    g.beginPath();g.roundRect(-12,-height*.50,length+12,height,Math.min(12,height*.38));g.clip()
    g.drawImage(photographed,-14,-height*.51,length+14,height)
    g.restore();return
  }
  sleeve(g,shoulder,elbow,far?16:21,coat)
  sleeve(g,elbow,end,far?12:16,coat)
  g.save();g.translate(...end);g.rotate(Math.atan2(end[1]-elbow[1],end[0]-elbow[0])*.46)
  hand(g,amount,pose,t);g.restore()
}
function prop(g:G,x:number,y:number,type:ActingScene['object'],angle=0){
  g.save();g.translate(x,y);g.rotate(angle)
  const photo=clothing('prop-'+type)
  if(photo){
    const width={paper:83,tea:35,radio:58,film:56,lamp:28,cloth:58}[type]
    const height=width*photo.height/photo.width
    g.drawImage(photo,-width/2,-height*.71,width,height)
    g.restore();return
  }
  if(type==='radio'||type==='film'){
    fill(g,'M-28 -10 L23 -10 L29 -6 L29 13 L-27 13Z',gradient(g,['#63594b','#302e29'],0,-10,0,14),'#282522')
    for(const n of [-15,12]){circle(g,n,0,6,'#a89173');circle(g,n,0,3,'#383331')}
    stroke(g,'M-16 8 L15 8','#dfc9a3',1)
  }else if(type==='tea'){
    fill(g,'M-18 -8 Q0 -12 17 -8 L13 11 Q0 19 -12 11Z',gradient(g,['#787b70','#d8ccaa','#aaa895'], -18,0,18,0),'#54594e')
    g.strokeStyle='#a69e84';g.lineWidth=3;g.beginPath();g.ellipse(18,0,7,6,0,0,7);g.stroke()
    fill(g,'M-18 -8 Q0 -15 17 -8 Q0 -3 -18 -8Z','#6a614f')
  }else if(type==='lamp'){
    fill(g,'M-17 10 Q-5 6 -4 -1 L-5 -11 L4 -11 L3 0 Q5 8 15 10Z','#9c805b');circle(g,0,-14,6,'#e2bf80')
  }else if(type==='cloth'){
    fill(g,'M-28 -4 Q-7 2 -2 -10 Q8 -15 27 -6 L21 10 Q7 14 -2 6 Q-11 2 -26 9Z','#935e4c','#633e31')
    stroke(g,'M-18 2 Q-7 -2 7 3 T23 1','#bd9878',2)
  }else{
    fill(g,'M-34 -8 L19 -10 L34 6 L-21 12Z','#c2ad86','#7e7058')
    stroke(g,'M-25 -5 L9 -6 M-22 -2 L15 -3 M-17 2 L6 1','#85745b',.9)
  }
  g.restore()
}
const wardrobe=new Map<string,HTMLImageElement>()
function clothing(id:string){
  let img=wardrobe.get(id)
  if(!img){img=new Image();img.src=id.startsWith('/')?id:'/wardrobe/'+id+'.webp';wardrobe.set(id,img)}
  return img.complete&&img.naturalWidth?img:null
}
function mouthAmount(t:number){return Math.max(0,Math.sin(t*12.7)*.58+Math.sin(t*20.2)*.38+.14)}
function blinkAt(t:number,seed:number){const p=(t+seed)%4.9;return p<.16?Math.sin(p/.16*Math.PI):0}
export function paintActor(g:G,actor:CastMember,face:FaceImage|null,x:number,facing:number,t:number,event:Turn,other:boolean,item:ActingScene['object'],still:boolean){
  const seed=actor.name.codePointAt(0)!%13/3
  const moving=event.phase!=='idle',elapsed=moving?Math.max(0,(performance.now()-event.start)/1000):0
  const own=event.phase==='action'?!other:event.phase==='reply'&&other
  const gesture=event.gesture
  const pulse=still?Number(moving):moving?smooth(elapsed/.38)*(1-.60*smooth((elapsed-.69)/.9)):0
  const release=event.phase==='reply'&&!other&&!still?1-smooth(elapsed/.46):0
  const exert=own?pulse:release
  const breath=still?0:Math.sin(t*1.3+seed)*1.05
  const lean=exert*(gesture==='refuse'?-5:3.4)+(other&&moving&&!own?-1.6:0)
  const guarded=other&&event.phase==='reply'&&event.mood==='guarded'
  const sway=still?0:Math.sin(t*.55+seed)*.7
  g.save();g.translate(x,253);g.scale(facing,1);g.rotate((lean+sway)*.009);g.translate(0,breath)
  const coat=actor.coat,skin=gradient(g,['#715544','#a58364','#bb9975','#8f745d'],-19,0,18,0)
  // Back arm, neck and collar sit behind the near shoulder.
  if(!clothing(actor.costume))arm(g,[-56,4],[5,95+breath],coat,.3,'hold',t,true)
  fill(g,'M-17 -43 L18 -42 L24 -7 L11 2 L-24 -9Z',skin)
  const garment=clothing(actor.costume)
  if(!garment){
  const torso=gradient(g,['#272f30',coat,coat,'#353a35'],-87,0,79,0)
  fill(g,'M-19 -24 Q-42 -18 -63 -8 Q-80 -6 -86 19 L-106 139 L80 145 Q71 66 62 12 Q60 2 43 -4 L20 -23 Q0 -12 -19 -24Z',torso,'#333930')
  if(actor.collar==='stand'){
    fill(g,'M-19 -27 L-1 -18 L21 -26 L23 -8 L5 0 L-21 -11Z',coat,'#2e352f')
    stroke(g,'M5 0 Q2 67 10 133 M-54 49 L-28 47 M27 44 L49 41','#242d29',2)
    for(const h of [10,37,65,96]){circle(g,6,h,2.7,'#292e29');circle(g,5.5,h-.7,1.1,'#8b887a')}
  }else{
    fill(g,'M-25 -23 L-5 -14 L-1 62 L-42 -4Z','#6c7368','#3d453b')
    fill(g,'M18 -24 L27 -11 L4 12 L-3 -13Z','#969483','#424a40')
    stroke(g,'M-1 5 Q3 71 11 135 M15 53 Q37 52 52 45 M-57 55 L-37 57','#2b362f',2)
    for(const h of [33,66,99])circle(g,3+h/25,h,2.3,'#29342d')
  }
  for(const [x1,y1,x2,y2] of [[-66,1,-61,34],[-72,27,-59,62],[47,14,44,37],[27,72,40,116],[-30,82,-21,122]])
    stroke(g,`M${x1} ${y1} Q${x1+8} ${y1+13} ${x2} ${y2}`,'#aca89935',1.5)
  }
  if(garment){
    g.save()
    // Leave the far sleeve on the photographed jacket. The near sleeve has an
    // articulated elbow, so its hanging shape must be cut out of the torso.
    const silhouette=new Path2D('M-142 -47 L125 -47 L127 1 Q100 -3 81 9 Q65 18 62 38 Q58 64 64 103 L70 183 L-143 183Z')
    g.clip(silhouette);g.drawImage(garment,-128,-31,250,247);g.restore()
    // The exposed neck joins the actual collar opening, tucked behind the chin.
    g.save()
    const neckShape=new Path2D('M-21 -45 Q-15 -31 -19 -24 Q-10 -18 0 -14 Q14 -21 20 -26 Q14 -34 19 -45Z')
    g.clip(neckShape);g.fillStyle=skin;g.fillRect(-22,-48,44,43)
    if(face)g.drawImage(face.neck,-22,-40,44,27)
    g.restore()

  }
  const nod=still?0:((event.phase==='reply'&&other?Math.sin(Math.min(elapsed,.62)*10)*Math.max(0,1-elapsed/.7)*2:0)+Math.sin(t*.71+seed)*.49)
  g.save();g.translate(1+exert*2,-24);g.rotate((nod+(guarded?-3:own?2:0))*.014);g.transform(1,0,(still?0:Math.sin(t*.35+seed)*.012)+exert*.018,1,0,0)
  if(face){
    // Faces preserve the source's handedness even when the body faces left.
    g.scale(facing,1)
    const h=108,w=h*face.base.width/face.base.height
    const rect:[number,number,number,number]=[-w/2,-h+7,w,h]
    g.drawImage(face.base,...rect)
    const blend=(v:number,img:HTMLCanvasElement)=>{if(v<.015)return;g.globalAlpha=Math.min(1,v);g.drawImage(img,...rect)}
    if(!still)blend((Math.sin(t*.69+seed)*.22+.65),face.glance)
    if(own)blend(guarded?.72:event.mood==='open'?.55:.2,guarded?face.worry:face.smile)
    if(own&&elapsed<1.9)blend(still?.20:mouthAmount(elapsed+seed)*.9,face.voice)
    blend(still?0:blinkAt(t,seed),face.blink);g.globalAlpha=1
  }
  g.restore()
  let target:P=[87,107+breath], reach=exert
  if(own||release>0){
    const positions:Record<typeof gesture,P>={pass:[54,85],hold:[58,65],speak:[75,46],listen:[55,7],sign:[72,87],refuse:[62,26],inspect:[53,35],depart:[72,94],tune:[81,75]}
    const p=positions[gesture];target=[87+(p[0]-87)*exert,107+(p[1]-107)*exert]
  }else if(moving&&other){target=[87+3*pulse,107-9*pulse]}
  if(other&&event.phase==='reply'&&gesture==='pass')target=[87-38*exert,107-28*exert]
  if(gesture==='sign'&&own&&!still)target[0]+=Math.sin(elapsed*20)*2.3*pulse
  arm(g,[68,12],target,coat,reach,gesture,t,false,/woman|girl|vautrin|aiyun|lin_zhao/.test(actor.face),actor.costume)
  if(own&&['pass','hold','inspect','tune'].includes(gesture)&&exert>.14)
    prop(g,target[0]+24,target[1]+1,item,-.13*exert)
  if(own&&gesture==='sign')stroke(g,`M${target[0]+24} ${target[1]-10} l-7 24`,'#d1b084',2.5)
  g.restore()
}
export function paintTable(g:G){
  fill(g,'M0 361 Q500 345 1000 361 L1000 400 L0 400Z',gradient(g,['#665843','#504635','#342f29'],0,346,0,400))
  const wood=clothing('/reading/work-surface.webp')
  if(wood){
    g.save();g.clip(new Path2D('M0 361 Q500 345 1000 361 L1000 400 L0 400Z'))
    g.drawImage(wood,0,345,1000,55);g.restore()
  }
  stroke(g,'M0 362 Q500 346 1000 362','#af967268',1.5)
  for(let i=0;i<9;i++){const x=i*127;stroke(g,`M${x-50} ${371+i%3*5} q40 -3 101 -1`,'#b29b7b25',1)}
}

const handPoses=['rest','offer','write','halt'] as const
type HandPose=typeof handPoses[number]
const prepared=new Map<string,Promise<void>>()
export type HandSet='pov'|'pov-elder'|'pov-young'
export function viewpointHands(scene:ActingScene):HandSet{
  const {face,name}=scene.player
  if(/elder|granny|puppet-master|shang_aiyun/.test(face)||name==='邓小平'&&/(197[7-9]|198[0-9]|199[0-9])/.test(scene.place))return 'pov-elder'
  if(/woman|girl|boy|seamstress|fish-counter|lin_zhao|vautrin|zhongyun/.test(face))return 'pov-young'
  return 'pov'
}
export function prepareWardrobe(handSet:HandSet,costume?:string){
  const ids=handPoses.flatMap(pose=>['left','right'].map(side=>handSet+'-'+pose+'-'+side))
  ids.push('/reading/work-surface.webp',...['paper','tea','radio','film','lamp','cloth'].map(kind=>'prop-'+kind))
  if(costume)ids.push(costume,...['rest','offer','take','write','pinch','halt'].map(pose=>'arm-'+pose))
  return Promise.all(ids.map(id=>{
    if(!prepared.has(id)){
      clothing(id)
      const asset=wardrobe.get(id)!
      prepared.set(id,asset.decode().then(()=>{},()=>{}))
    }
    return prepared.get(id)!
  }))
}

export function paintOwnHands(g:G,width:number,item:ActingScene['object'],turn:Turn,time:number,still:boolean,handSet:HandSet){
  const elapsed=Math.max(0,(performance.now()-turn.start)/1000)
  const action=turn.phase==='action',reply=turn.phase==='reply'
  const reach=action?(still?1:smooth(elapsed/.43)):reply&&!still?1-smooth(elapsed/.48):0
  const gesture=turn.gesture
  let pose:HandPose='rest'
  if(gesture==='pass'||gesture==='hold'||gesture==='speak')pose='offer'
  if(gesture==='sign'||gesture==='inspect'||gesture==='tune')pose='write'
  if(gesture==='refuse')pose='halt'
  const extend=gesture==='listen'?.19:gesture==='depart'?.52:1
  const sway=still?0:Math.sin(time*.92)*1.3
  const spriteWidth=Math.min(157,width*.29)
  const restingSpread=Math.min(width*.29,194)
  const center=width/2
  const writing=gesture==='sign'&&action&&!still?Math.sin(elapsed*21)*2.2*reach:0
  const lifting=gesture==='inspect'||gesture==='hold'||gesture==='pass'||gesture==='tune'
  const rightReach=reach*extend
  const leftReach=rightReach*(gesture==='refuse'?.18:gesture==='pass'?.84:.53)
  const rightX=center+restingSpread-rightReach*restingSpread*.54+writing
  const leftX=center-restingSpread+leftReach*restingSpread*.47
  const leftBottom=451-leftReach*44+sway
  const rightBottom=451-rightReach*(gesture==='refuse'?55:73)-sway
  function wrist(side:'left'|'right',x:number,bottom:number,amount:number){
    const activePose=reach>.40?pose:'rest'
    const img=clothing(handSet+'-'+activePose+'-'+side)
    if(!img)return
    const w=spriteWidth*(1-amount*.08),h=w*img.height/img.width
    g.save();g.translate(x,bottom)
    g.rotate((side==='right'?1:-1)*(.035+amount*.07))
    // Keep the near sleeve continuous below the eye line even at full extension.
    g.drawImage(img,0,img.height-8,img.width,8,-w/2,-2,w,78)
    const blend=pose==='rest'?1:smooth((reach-.25)/.28)
    if(blend>0&&blend<1){
      const resting=clothing(handSet+'-rest-'+side),active=clothing(handSet+'-'+pose+'-'+side)
      if(resting)g.drawImage(resting,-w/2,-h,w,h)
      g.globalAlpha=blend
      if(active)g.drawImage(active,-w/2,-h,w,h)
    }else g.drawImage(img,-w/2,-h,w,h)
    g.restore()
  }
  wrist('left',leftX,leftBottom,leftReach)
  const propX=center+(lifting?rightReach*(rightX-center)*.47:0)
  const propY=354-(lifting?rightReach*(gesture==='inspect'?63:34):0)
  const passed=reply&&gesture==='pass'
  if(!passed){
    g.save();g.translate(propX,propY);g.scale(1.28+reach*.18,1.28+reach*.18)
    prop(g,0,0,item,-.06+(lifting?.12*rightReach:0))
    g.restore()
  }
  wrist('right',rightX,rightBottom,rightReach)
  if(gesture==='sign'&&rightReach>.45){
    const px=rightX-spriteWidth*.35,py=rightBottom-spriteWidth*.88
    stroke(g,`M${px} ${py} l-12 38`,'#352f26',3.5)
    stroke(g,`M${px-10} ${py+32} l-2 6`,'#b6a183',2)
  }
}
