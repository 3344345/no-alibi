<script lang="ts">
  import {onMount,onDestroy} from 'svelte'
  import {faceImage, type FaceImage} from './actorFace'
  import {paintActor,paintTable} from './actorMovement'
  import type {ActingScene,Turn} from './performance'
  export let scene:ActingScene
  export let turn:Turn
  export let reduced=false
  export let paused=false
  let sheet:HTMLCanvasElement, a:FaceImage|null=null,b:FaceImage|null=null,epoch=0,visible=true,mounted=false
  let frame=0,last=0,poseTime=0,readyIds=''
  function animate(now:number){
    frame=0
    if(!mounted||document.hidden||!visible||paused)return
    if(now-last>=1000/24||reduced){ if(!reduced)poseTime+=Math.min(80,now-last)/1000;last=now;draw() }
    if(!reduced)frame=requestAnimationFrame(animate)
  }
  function restart(){
    cancelAnimationFrame(frame);frame=0
    if(!mounted||paused||document.hidden||!visible)return
    last=performance.now();draw();if(!reduced)frame=requestAnimationFrame(animate)
  }
  function redraw(_scene:ActingScene,_turn:Turn,_reduced:boolean,_paused:boolean){if(mounted)restart()}
  async function loadFaces(first:string,second:string){
    const token=++epoch
    const [one,two]=await Promise.all([faceImage(first),second?faceImage(second,-1):null])
    if(token!==epoch)return
    a=one??await faceImage('man-mid');b=second?(two??await faceImage('woman-mid',-1)):null
    if(token===epoch){readyIds=first+'/'+second;if(mounted)draw()}
  }
  $: void loadFaces(scene.player.face,scene.other?.face??'')
  $: redraw(scene,turn,reduced,paused)
  function draw(){
    const g=sheet?.getContext('2d');if(!g||!sheet.clientWidth||!sheet.clientHeight)return
    const cw=sheet.clientWidth,ch=sheet.clientHeight,ratio=Math.min(window.devicePixelRatio||1,1.6)
    const w=Math.round(cw*ratio),h=Math.round(ch*ratio)
    if(sheet.width!==w||sheet.height!==h){sheet.width=w;sheet.height=h}
    const scale=h/400,space=w/scale
    g.setTransform(scale,0,0,scale,0,0);g.clearRect(0,0,space,400)
    if(!a||readyIds!==scene.player.face+'/'+(scene.other?.face??''))return
    const centre=space/2, gap=Math.min(space*.255,340),t=poseTime
    g.save();g.scale(space/1000,1);paintTable(g,scene.object,turn);g.restore()
    const handroom=space<650?.92:1.29
    function actor(other:boolean){
      const subject=other?scene.other:scene.player
      if(!subject||!g)return
      g.save();g.translate(centre+(other?gap:scene.other?-gap:-gap*.58),400);g.scale(handroom,handroom);g.translate(0,-400)
      paintActor(g,subject,other?b:a,0,other?-1:1,t,turn,other,scene.object,reduced);g.restore()
    }
    actor(true);actor(false)
    const shade=g.createLinearGradient(0,330,0,400);shade.addColorStop(0,'#16171100');shade.addColorStop(1,'#15171372');g.fillStyle=shade;g.fillRect(0,330,space,70)
  }
  onMount(()=>{
    mounted=true
    const sizes=new ResizeObserver(restart);sizes.observe(sheet)
    const inFrame=new IntersectionObserver(e=>{visible=e.some(x=>x.isIntersecting);restart()})
    inFrame.observe(sheet);document.addEventListener('visibilitychange',restart);restart()
    return ()=>{mounted=false;sizes.disconnect();inFrame.disconnect();document.removeEventListener('visibilitychange',restart);cancelAnimationFrame(frame)}
  })
  onDestroy(()=>{epoch++})
</script>
<canvas aria-hidden="true" bind:this={sheet}></canvas>
<style>canvas{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}</style>
