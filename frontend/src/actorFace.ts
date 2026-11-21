import geometry from './faceGeometry.json'
export interface FacePoints {eyes:number[][];mouth:number[];nose:number[]}
const landmarks=geometry as Record<string,FacePoints>
const images=new Map<string,Promise<FaceImage|null>>()
export type FaceImage={neck:HTMLCanvasElement;glance:HTMLCanvasElement;base:HTMLCanvasElement;blink:HTMLCanvasElement;voice:HTMLCanvasElement;worry:HTMLCanvasElement;smile:HTMLCanvasElement}
function canvas(w:number,h:number){const c=document.createElement('canvas');c.width=w;c.height=h;return c}
function vary(base:HTMLCanvasElement, points:FacePoints, kind:string){
  const c=canvas(base.width,base.height),g=c.getContext('2d')!
  g.drawImage(base,0,0)
  const w=c.width,h=c.height, original=g.getImageData(0,0,w,h), out=new ImageData(new Uint8ClampedArray(original.data),w,h)
  const eyes=points.eyes.map(([x,y])=>[x*w,y*h]).sort((a,b)=>a[0]-b[0])
  const gap=Math.hypot(eyes[1][0]-eyes[0][0],eyes[1][1]-eyes[0][1])
  const d=gap<5?Math.max(15,Math.abs(points.nose[1]*h-eyes[0][1])*1.45):gap
  if(gap<5)eyes.pop()
  function change(cx:number,cy:number,rx:number,ry:number,shape:(x:number,y:number,a:number)=>[number,number,number]){
    for(let y=Math.max(0,Math.floor(cy-ry));y<Math.min(h,cy+ry);y++)for(let x=Math.max(0,Math.floor(cx-rx));x<Math.min(w,cx+rx);x++){
      const nx=(x-cx)/rx,ny=(y-cy)/ry,r=nx*nx+ny*ny;if(r>=1)continue
      const [dx,dy,shade]=shape(nx,ny,(1-r)**2)
      const sx=Math.max(0,Math.min(w-1.001,x+dx)),sy=Math.max(0,Math.min(h-1.001,y+dy))
      const ix=Math.floor(sx),iy=Math.floor(sy),a=sx-ix,b=sy-iy,p=(iy*w+ix)*4,target=(y*w+x)*4
      for(let ch=0;ch<3;ch++)out.data[target+ch]=shade*((1-b)*((1-a)*original.data[p+ch]+a*original.data[p+4+ch])+b*((1-a)*original.data[p+w*4+ch]+a*original.data[p+w*4+4+ch]))
    }
  }
  if(kind==='glance')for(const [x,y] of eyes)change(x,y,d*.23,d*.135,(_x,_y,a)=>[-d*.037*a,0,1])
  if(kind==='blink')for(const [x,y] of eyes)change(x,y,d*.307,d*.19,(_x,ny,a)=>[0,ny<.04?-d*.15*a:d*.078*a,1])
  if(kind==='worry'||kind==='smile')for(const [i,[x,y]] of eyes.entries())change(x,y-d*.10,d*.40,d*.37,(nx,ny,a)=>[0,(kind==='worry'?(i===0?nx:-nx)*.09:-.033)*d*a,1])
  const mx=points.mouth[0]*w,my=points.mouth[1]*h
  if(kind==='voice')change(mx,my+d*.025,d*.50,d*.31,(nx,ny,a)=>{
    const opening=Math.min(1,Math.max(0,1-Math.abs(ny+.04)*8))*(1-nx*nx)**3
    return [0,-a*d*(ny>-.05?.08:-.032),1-.57*opening]
  })
  if(kind==='smile'||kind==='worry')change(mx,my,d*.53,d*.32,(nx,ny,a)=>[0,d*a*Math.abs(nx)*(kind==='smile'?.24:-.19),1])
  g.putImageData(out,0,0);return c
}
// Bring a monochrome source into the light of the set without smoothing the
// photographed features. Colour portraits and the gallery originals stay intact.
function warmMonochrome(source:HTMLCanvasElement){
  const g=source.getContext('2d')!,pixels=g.getImageData(0,0,source.width,source.height),d=pixels.data
  let colour=0,samples=0
  for(let i=0;i<d.length;i+=44){
    if(d[i+3]<190)continue
    colour+=Math.max(d[i],d[i+1],d[i+2])-Math.min(d[i],d[i+1],d[i+2]);samples++
  }
  if(!samples||colour/samples>10)return
  for(let i=0;i<d.length;i+=4){
    if(!d[i+3])continue
    const light=d[i]*.299+d[i+1]*.587+d[i+2]*.114
    const warmth=Math.max(0,Math.sin(Math.PI*light/255))
    d[i]=light*.95+warmth*13;d[i+1]=light*.90+warmth*3;d[i+2]=light*.86-warmth*5
  }
  g.putImageData(pixels,0,0)
}
function viewFromSeat(source:HTMLCanvasElement,p:FacePoints,direction:number){
  const w=source.width,h=source.height,gap=Math.abs(p.eyes[1][0]-p.eyes[0][0])
  // Shift the nearer facial planes more than the ears as the actor looks across
  // the table. A photographed profile keeps its one visible eye and silhouette.
  if(direction===0||gap<.13)return {base:source,p}
  const mid=(p.eyes[0][0]+p.eyes[1][0])/2, turn=direction*.068
  function depth(x:number,y:number){
    const dx=(x-mid)/.49,dy=(y-p.nose[1])/.63
    const edge=Math.max(0,1-dx*dx-dy*dy)
    const nx=(x-p.nose[0])/.17,ny=(y-p.nose[1])/.28
    return edge*(.42+Math.exp(-nx*nx-ny*ny)*.54)
  }
  const result=canvas(w,h),ctx=result.getContext('2d')!,raw=source.getContext('2d')!.getImageData(0,0,w,h)
  const output=ctx.createImageData(w,h)
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const u=x/w,v=y/h
    const sx=Math.max(0,Math.min(w-1.001,x-turn*w*depth(u-turn*depth(u,v),v)))
    const i=Math.floor(sx),t=sx-i,k=(y*w+i)*4,d=(y*w+x)*4
    for(let c=0;c<4;c++)output.data[d+c]=raw.data[k+c]*(1-t)+raw.data[k+4+c]*t
  }
  ctx.putImageData(output,0,0)
  const move=([x,y]:number[])=>[x+turn*depth(x,y),y]
  return {base:result,p:{eyes:p.eyes.map(move),mouth:move(p.mouth),nose:move(p.nose)}}
}
export function faceImage(id:string,direction=1):Promise<FaceImage|null>{
  const key=id+'/'+direction
  if(!images.has(key))images.set(key,new Promise(resolve=>{
    const img=new Image()
    img.onload=()=>{
      try{
        const w=Math.min(256,img.width),h=Math.round(img.height*w/img.width),source=canvas(w,h)
        source.getContext('2d')!.drawImage(img,0,0,w,h)
        warmMonochrome(source)
        const {base,p}=viewFromSeat(source,landmarks[id]??{eyes:[[.35,.47],[.64,.47]],mouth:[.5,.73],nose:[.50,.60]},direction)
        const neck=canvas(64,48),n=neck.getContext('2d')!
        const gap=Math.max(14,Math.abs(p.eyes[1][0]-p.eyes[0][0])*w)
        const cheekX=(p.nose[0]*.46+p.eyes[0][0]*.54)*w
        n.drawImage(base,Math.max(0,cheekX-gap*.09),Math.min(h-gap*.17,p.nose[1]*h),gap*.16,gap*.16,0,0,64,48)
        const shadow=n.createLinearGradient(0,0,35,48)
        shadow.addColorStop(0,'rgba(44,32,25,.57)');shadow.addColorStop(.52,'rgba(58,40,29,.23)');shadow.addColorStop(1,'rgba(38,30,23,.40)')
        n.fillStyle=shadow;n.fillRect(0,0,64,48)
        const naturalNeck=new Image()
        naturalNeck.onload=()=>{n.clearRect(0,0,64,48);n.drawImage(naturalNeck,0,0,64,48)}
        naturalNeck.src='/necks/'+id+'.webp'
        resolve({neck,base,glance:vary(base,p,'glance'),blink:vary(base,p,'blink'),voice:vary(base,p,'voice'),worry:vary(base,p,'worry'),smile:vary(base,p,'smile')})
      }catch{resolve(null)}
    }
    img.onerror=()=>resolve(null); img.src='/faces/'+id+'.webp'
  }))
  return images.get(key)!
}
