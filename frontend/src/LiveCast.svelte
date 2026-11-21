<script lang="ts">
  import {onMount,onDestroy} from 'svelte'
  import {faceImage,type FaceImage} from './actorFace'
  import {paintActor,paintTable,paintOwnHands,prepareWardrobe,viewpointHands,type HandSet} from './actorMovement'
  import type {ActingScene,Turn} from './performance'
  export let scene:ActingScene
  export let turn:Turn
  export let reduced=false
  export let paused=false

  let sheet:HTMLCanvasElement, face:FaceImage|null=null
  let epoch=0,visible=true,mounted=false,frame=0,last=0,poseTime=0,readyFace=''
  function animate(now:number){
    frame=0
    if(!mounted||document.hidden||!visible||paused)return
    if(now-last>=1000/24||reduced){
      if(!reduced)poseTime+=Math.min(80,now-last)/1000
      last=now;draw()
    }
    if(!reduced)frame=requestAnimationFrame(animate)
  }
  function restart(){
    cancelAnimationFrame(frame);frame=0
    if(!mounted||paused||document.hidden||!visible)return
    last=performance.now();draw()
    if(!reduced)frame=requestAnimationFrame(animate)
  }
  function redraw(_scene:ActingScene,_turn:Turn,_reduced:boolean,_paused:boolean){if(mounted)restart()}
  async function seat(other:ActingScene['other'],hands:HandSet){
    const token=++epoch
    const [portrait]=await Promise.all([
      other?faceImage(other.face,0):null,
      prepareWardrobe(hands,other?.costume)
    ])
    if(token!==epoch)return
    face=portrait;readyFace=other?.face??''
    if(mounted)draw()
  }
  $: hands=viewpointHands(scene)
  $: void seat(scene.other,hands)
  $: redraw(scene,turn,reduced,paused)
  function draw(){
    const g=sheet?.getContext('2d')
    if(!g||!sheet.clientWidth||!sheet.clientHeight)return
    const ratio=Math.min(window.devicePixelRatio||1,1.6)
    const w=Math.round(sheet.clientWidth*ratio),h=Math.round(sheet.clientHeight*ratio)
    if(sheet.width!==w||sheet.height!==h){sheet.width=w;sheet.height=h}
    const scale=h/400,space=w/scale
    g.setTransform(scale,0,0,scale,0,0);g.clearRect(0,0,space,400)
    const time=poseTime
    if(scene.other&&face&&readyFace===scene.other.face){
      const distance=Math.min(1.32,Math.max(.98,space/675))
      g.save();g.translate(space*.54,400);g.scale(distance,distance);g.translate(0,-375)
      paintActor(g,scene.other,face,0,-1,time,turn,true,scene.object,reduced)
      g.restore()
    }
    const outdoors=/\/(field|rail|yard|depot|canal|tongzhou-wharf)\.webp$/.test(scene.picture)
    if(!outdoors){
      g.save();g.scale(space/1000,1);paintTable(g);g.restore()
    }
    paintOwnHands(g,space,scene.object,turn,time,reduced,hands)
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
<canvas aria-hidden="true" data-player={scene.player.name} data-player-visible="hands" data-hands={hands} data-face-ready={scene.other?readyFace===scene.other.face:!readyFace} data-counterpart={scene.other?.name??''} bind:this={sheet}></canvas>
<style>canvas{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}</style>
