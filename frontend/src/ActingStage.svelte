<script lang="ts">
  import {onMount,onDestroy,tick} from 'svelte'
  import BackButton from './BackButton.svelte'
  import LiveCast from './LiveCast.svelte'
  import { playback,presenting,quietTurn,skipPerformance,inTheatre,filmOpen,type Turn,type ActingScene,type ActingChoice } from './performance'
  export let scene:ActingScene
  export let choices:ActingChoice[]=[]
  export let embeddedControls=false
  export let controlsArea:HTMLElement|undefined=undefined
  let panel:HTMLElement
  let category='',listPage=0
  $: groups=[...new Set(choices.map(c=>c.group).filter((s):s is string=>!!s))]
  $: matching=category&&groups.includes(category)?choices.filter(c=>c.group===category):choices
  $: page=Math.min(listPage,Math.max(0,Math.ceil(matching.length/6)-1))
  $: visibleChoices=matching.slice(page*6,page*6+6)
  function moveControls(container:HTMLElement,area:HTMLElement|undefined){
    let home:Comment|undefined,current:HTMLElement|undefined
    function restore(){if(home?.parentNode&&current?.parentNode===container)home.parentNode.insertBefore(current,home);home?.remove();current=undefined;home=undefined}
    function move(next:HTMLElement|undefined){if(current===next)return;restore();if(next?.parentNode){home=document.createComment('scene controls');next.parentNode.insertBefore(home,next);container.appendChild(next);current=next}}
    move(area)
    return {update:move,destroy:restore}
  }
  export let decide:(id:string)=>void=()=>{}
  export let seeControls:()=>void=()=>{}
  export let volume=0
  export let toggleAudio:()=>void=()=>{}
  export let reduced=false
  export let busy=false
  let theatre=false,movie=false,video:HTMLVideoElement,element:HTMLElement,launch:HTMLButtonElement,exitButton:HTMLButtonElement|undefined
  let failed=false,denied=false,postcard=false
  let version='',prevFilm='',sample:Turn|null=null
  let duration:ReturnType<typeof setTimeout>|undefined
  function endSample(){clearTimeout(duration);duration=undefined;sample=null}
  function listen(){
    if(performing||movie)return
    endSample()
    const watching=!!active.other,listener=active.player.name
    sample={phase:'action',label:active.transmission?'你停下来，重新留意手边的'+active.transmission+'。':watching?'你停下来，等对面的人。':'你停下来，仔细看了一眼。',reply:'',gesture:'listen',mood:'listen',start:performance.now()}
    duration=setTimeout(()=>{
      sample={phase:'reply',label:listener,reply:active.excerpt||active.opening,gesture:'speak',mood:'listen',start:performance.now()}
      duration=setTimeout(endSample,4200)
    },reduced?0:540)
  }
  $: if(performing&&sample)endSample()
  $: performing=busy||$presenting
  $: during=performing&&$playback.phase!=='idle'
  $: active=during&&$playback.scene?$playback.scene:scene
  $: turn=sample??(($playback.scene?.id===active.id||during)?$playback:quietTurn())
  $: if(version!==active.id){version=active.id;endSample();category='';listPage=0;if(prevFilm!==active.film)closeFilm();prevFilm=active.film}
  $: if(turn.phase==='idle'||!performing)postcard=false
  $: if(performing&&turn.phase==='action'&&!theatre&&!movie) considerPop(turn.start)
  $: if(video){video.volume=Math.max(0,Math.min(volume/100,1));video.muted=volume===0}
  let dismissed=-1
  let seenAction=-1
  function considerPop(start:number){
    if(!element||seenAction===start)return
    seenAction=start;const r=element.getBoundingClientRect()
    postcard=r.bottom<55||r.top>innerHeight-65
  }
  async function immerse(){
    theatre=true;inTheatre.set(true);await tick();exitButton?.focus()
  }
  async function leave(){
    closeFilm();theatre=false;inTheatre.set(false);await tick();launch?.focus({preventScroll:true})
  }
  function closeFilm(){if(movie){video?.pause();movie=false;filmOpen.set(false)}failed=false;denied=false}
  export function backLayer() {
    if(movie){closeFilm();return true}
    if(theatre){void leave();return true}
    return false
  }
  async function playFilm(){
    movie=true;failed=false;denied=false;filmOpen.set(true);await tick()
    if(!video)return
    video.volume=volume/100;video.muted=volume===0
    try{await video.play()}catch(e){if(movie&&!(e instanceof DOMException&&e.name==='AbortError'))denied=true}
  }
  function mediaReady(){if(video?.textTracks[0])video.textTracks[0].mode='showing'}
  async function controls(){if(theatre&&embeddedControls&&panel){panel.focus();return}if(theatre)await leave();if(movie)closeFilm();await tick();seeControls()}
  function key(e:KeyboardEvent){
    const topDialog=Array.from(document.querySelectorAll<HTMLDialogElement>('dialog[open]')).at(-1)
    if(topDialog && !topDialog.contains(element))return
    if(e.target instanceof HTMLInputElement||e.target instanceof HTMLTextAreaElement||e.target instanceof HTMLSelectElement)return
    if(!theatre||e.ctrlKey||e.altKey||e.metaKey||e.isComposing)return
    if(e.key==='Escape'){
      e.preventDefault()
      e.stopPropagation()
      if(!e.repeat)backLayer()
      return
    }
    if(e.key==='Tab'){
      const nodes=Array.from(element.querySelectorAll<HTMLElement>('button:not(:disabled),video[controls],[tabindex="0"]')).filter(n=>n.offsetParent!==null)
      if(nodes.length&&e.shiftKey&&document.activeElement===nodes[0]){nodes.at(-1)?.focus();e.preventDefault()}
      else if(nodes.length&&!e.shiftKey&&document.activeElement===nodes.at(-1)){nodes[0].focus();e.preventDefault()}
      return
    }
    if(movie||e.repeat)return
    if(!performing&&e.code==='KeyQ'){e.preventDefault();listen();return}
    if(performing&&e.code==='Space'){skipPerformance();e.preventDefault();return}
    if(!performing&&/^[1-9]$/.test(e.key)){const c=visibleChoices[Number(e.key)-1];if(c&&!c.disabled){e.preventDefault();decide(c.id)}}
  }
  onMount(()=>{document.addEventListener('keydown',key,true);return()=>document.removeEventListener('keydown',key,true)})
  onDestroy(()=>{endSample();if(theatre)inTheatre.set(false);closeFilm()})
</script>
<section class="perform" class:theatre class:postcard={postcard&&!theatre} bind:this={element} aria-label="人物现场" role={theatre?'dialog':'region'} aria-modal={theatre?true:undefined} data-viewpoint="first-person" data-phase={turn.phase} data-gesture={turn.gesture} data-scene={active.id}>
  <header>
    {#if theatre}<BackButton bind:element={exitButton} back={backLayer} destination={movie?'现场':'本场故事'}/>{/if}
    <span>{active.place}</span><strong>{active.title}</strong>
    {#if !theatre}<button bind:this={launch} on:click={immerse}>进入现场 <b aria-hidden="true">↗</b></button>{/if}
  </header>
  <div class="frame" class:film={movie}>
    <div class="set" style:background-image={'url("'+active.picture+'")'} style:background-size={active.crop?'300% 300%':'cover'} style:background-position={active.crop??'50% 45%'}></div>
    <div class="shade"></div>
    <LiveCast scene={active} {turn} {reduced} paused={movie}/>
    {#if !movie}
      <div class="names" aria-label="在场人物"><span class="own-name">你 · {active.player.name}{#if active.transmission} ／ {active.transmission}{/if}</span>{#if active.other}<span class="other-name">{active.other.name}</span>{/if}</div>
      {#if turn.phase==='action'}
        <div class="bubble from-player" role="status" data-speaker="player"><small>{active.player.name}</small><span>{turn.label}</span></div>
      {:else if turn.phase==='reply'}
        {#if active.transmission || (sample&&!active.excerpt.startsWith('“'))}
          <div class="narration" role="status" data-speaker="narrator">{#if active.transmission}<small>{active.transmission}</small>{/if}{turn.reply}</div>
        {:else}
          <div class="bubble" class:from-other={!!active.other} class:from-player={!active.other} role="status" data-speaker="reply"><small>{sample?'场内对白':active.other?'现场回应':'此刻'}</small><span>{turn.reply}</span></div>
        {/if}
      {:else if theatre && active.opening}
        <div class="narration">{active.opening}</div>
      {/if}
    {:else}
      <video playsinline controls bind:this={video} preload="auto" aria-label={'剧情动画 · '+active.title}
        src={'/motion/'+active.film+'.mp4'} on:loadedmetadata={mediaReady} on:play={()=>denied=false}
        on:ended={closeFilm} on:error={()=>{failed=true;denied=false}}>
        <track kind="captions" srclang="zh" label="中文声画字幕" src={'/motion/'+active.film+'.vtt'} default/>
      </video>
      {#if failed||denied}<div class="media-notice" role="status">{failed?'这段动画暂时读不到。':'点播放即可看片。'} <button on:click={failed?closeFilm:playFilm}>{failed?'回到现场':'播放此片'}</button></div>{/if}
    {/if}
  </div>
  <footer>
    {#if movie}<button on:click={closeFilm}>跳过短片</button><button on:click={toggleAudio} aria-pressed={volume>0}>{volume?'关闭片中声音':'打开放映声音'}</button>
    {:else if performing}<span class="moving">正在行动</span><button on:click={skipPerformance}>略过动作</button>
    {:else}<div class="tool-pair"><button on:click={listen} aria-label="听现场"><i aria-hidden="true">◌</i> {active.other?'听现场':'留意眼前'}</button><button on:click={playFilm} aria-label="观看本场动画"><i aria-hidden="true">▶</i> 看本场短片</button></div>
      {#if !theatre}<button on:click={controls}>回到操作 ↓</button>{:else}<button on:click={toggleAudio} aria-pressed={volume>0}>{volume?'现场音效开':'现场音效关'}</button>{/if}
    {/if}
  </footer>
  {#if !performing&&!movie&&!sample&&$playback.phase==='reply'&&dismissed!==$playback.start}
    <aside class="exchange" aria-label="刚才的决定与回应" aria-live="polite">
      <div><small>刚才的决定</small><span>{$playback.label}</span></div>
      <div><small>随后</small><span>{$playback.reply}</span></div>
      <button aria-label="收起这一来一回" on:click={()=>dismissed=$playback.start}>收起</button>
    </aside>
  {/if}
  {#if theatre&&!movie}
    {#if embeddedControls}
      <div class="on-stage-controls" tabindex="-1" aria-label="现场操作台" role="region" bind:this={panel} use:moveControls={controlsArea}></div>
    {:else}
    {#if choices.length>6 && groups.length>1}<nav class="categories" aria-label="现场行动分类">
      <button aria-pressed={category===''} on:click={()=>{category='';listPage=0}}>全部</button>
      {#each groups as group}<button aria-pressed={category===group} on:click={()=>{category=group;listPage=0}}>{group}</button>{/each}
    </nav>{/if}
    <div class="decisions" role="group" aria-label="现场选择">
      {#each visibleChoices as c,i}<button disabled={performing||c.disabled} on:click={()=>decide(c.id)}><kbd>{i<9?i+1:'·'}</kbd>{c.label}</button>{/each}
      <button class="tools" on:click={controls}>回到本场操作 →</button>
      {#if matching.length>6}<div class="pages"><button aria-label="上一页行动" disabled={page===0} on:click={()=>listPage=page-1}>←</button> {page+1}/{Math.ceil(matching.length/6)} <button aria-label="下一页行动" disabled={(page+1)*6>=matching.length} on:click={()=>listPage=page+1}>→</button></div>{/if}
    </div>{/if}
  {/if}
</section>
<style>
  .perform{max-width:1400px;margin:.7rem auto 1rem;background:#1c2522;color:#f3ead6;isolation:isolate;overflow:hidden;border:1px solid #726a56;text-align:left;box-sizing:border-box}
  header,footer{position:relative;display:flex;align-items:center;gap:clamp(.45rem,2vw,1.6rem);padding:.38rem clamp(.7rem,2vw,1.35rem);min-height:2.65rem}
  header span{color:#cab898;font-size:.8rem}header strong{font:500 clamp(.92rem,2vw,1.26rem)/1.2 var(--serif);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
  .perform button{border:1px solid #897d63;background:#242e29;color:#f1e7cd;min-height:35px;padding:.25rem .67rem;font:inherit;font-size:.85rem;cursor:pointer}
  .perform button:hover,.perform button:focus-visible{background:#3b4438;color:white;outline:2px solid #d4b77f;outline-offset:-2px}.perform button:disabled{opacity:.52;cursor:default}
  .frame{position:relative;width:100%;height:clamp(250px,39vh,430px);background:#222925;overflow:hidden}
  .set,.shade{position:absolute;inset:0}.set{filter:saturate(.82) brightness(.91)}.shade{background:linear-gradient(0deg,#161d1b69,transparent 43%),linear-gradient(90deg,#1b221e5e,transparent 44%,#191d1a41)}
  .names{position:absolute;inset:auto 20% .46rem;display:flex;justify-content:space-between;color:#f4e9d1;pointer-events:none;font:500 .92rem var(--serif);text-shadow:0 2px 4px #171a15,0 0 10px #151811}
  .bubble,.narration{position:absolute;z-index:1;color:#272920;background:#f2ecdbf5;box-shadow:0 3px 14px #1117;padding:.48rem .75rem;max-width:min(46%,28em);font:500 clamp(.85rem,1.4vw,1.06rem)/1.48 var(--serif)}
  .bubble{top:4%;border-radius:6px 6px 5px 2px}.from-player{left:6%}.from-other{right:6%}.bubble:after{content:'';position:absolute;bottom:-8px;left:15%;border-top:10px solid #f2ecdbf5;border-right:11px solid transparent}.from-other:after{left:auto;right:15%;transform:scaleX(-1)}
  .narration small{display:block;color:#ddc797;font:.7rem/1.4 var(--sans)}.bubble small{display:block;color:#6c624d;font:600 .70rem/1.45 sans-serif}.bubble span{display:block}.narration{left:50%;transform:translateX(-50%);bottom:4%;max-width:80%;width:max-content;background:#161d1ce8;color:#f4eada}
  footer{justify-content:space-between;background:#222b26}.moving{font:inherit;font-size:.83rem;color:#e2cba1}i{font-style:normal;font-size:.7em;color:#e9c681}
  .theatre{position:fixed;inset:0;z-index:1000;max-width:none;margin:0;border:0;display:flex;flex-direction:column;overflow-y:auto;background:#131a17;padding:env(safe-area-inset-top) 0 env(safe-area-inset-bottom)}
  .theatre header{position:sticky;top:0;z-index:3;background:#19221c}
  .theatre .frame{height:auto;flex:1 1 40vh;min-height:180px;max-height:72vh}.theatre header,.theatre footer,.decisions{padding-left:clamp(1rem,5vw,5rem);padding-right:clamp(1rem,5vw,5rem)}
  .exchange{display:flex;align-items:start;gap:1rem;background:#30372f;color:#ede4cf;padding:.65rem 1rem;border-top:1px solid #5d6656;font:.86rem/1.5 var(--serif)}
  .exchange div{flex:1;min-width:0}.exchange small{display:block;font:.68rem/1.45 sans-serif;color:#d3bd92;letter-spacing:.07em}.exchange button{align-self:center}
  @media(max-width:620px){.exchange{gap:.6rem;padding:.5rem}.exchange button{padding:.2rem .25rem}}
  .decisions{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,17rem),1fr));gap:.5rem;padding-block:.65rem;max-height:36vh;overflow:auto}
  .decisions button{text-align:left;line-height:1.5}.decisions kbd{display:inline-block;color:#d9b982;border-right:1px solid #6e715e;margin-right:.55rem;padding-right:.55rem}.decisions .tools{border-color:transparent}
  .postcard{position:fixed;bottom:1rem;right:1rem;width:min(540px,92vw);z-index:65;margin:0;box-shadow:0 8px 35px #0006}.postcard .frame{height:200px}.postcard header,.postcard footer{min-height:2rem}
  .tool-pair{display:flex;gap:.46rem;align-items:center}
  .on-stage-controls{max-height:43vh;min-height:8rem;overflow:auto;background:#f5efdf;color:#2d2c25;padding:.85rem clamp(.7rem,3vw,2.2rem);overscroll-behavior:contain}
  .categories{display:flex;gap:.36rem;overflow:auto;flex-shrink:0;padding:.35rem clamp(.7rem,5vw,5rem)}
  .categories button{white-space:nowrap}.categories [aria-pressed=true]{background:#d8c69d;color:#242a23}
  .pages{display:flex;gap:.6rem;align-items:center}.pages button{min-width:44px}
  video{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;background:#111}.media-notice{position:absolute;bottom:30%;left:50%;transform:translateX(-50%);background:#17211d;padding:.65rem}.film{height:clamp(230px,54vh,650px)}
  @media(max-width:620px){.frame{height:235px}.theatre .frame{max-height:51vh;flex:1 1 34vh}.theatre .decisions{max-height:42vh}.bubble{max-width:64%;font-size:.86rem}.names{inset-inline:4%}.from-player{left:3%}.from-other{right:3%}.postcard{bottom:.25rem;right:2%;width:96%}}

  .names{inset:0;display:block}.own-name,.other-name{position:absolute;border-radius:2px;background:#1a201bd9;padding:.12rem .45rem;font:500 .8rem/1.45 var(--sans)}
  .own-name{bottom:3%;left:2.4%}.other-name{left:54%;top:70%;transform:translateX(-50%)}
  .bubble.from-player{top:auto;bottom:12%;left:4%;right:auto;max-width:min(57%,29em)}
  .bubble.from-other{top:13%;left:61%;right:auto;max-width:35%}.from-other:after{left:-9px;right:auto;bottom:auto;top:52%;border:0;border-top:8px solid transparent;border-bottom:4px solid transparent;border-right:12px solid #f2ecdbf5;transform:none}
  @media(max-width:620px){.bubble.from-other{top:4%;left:auto;right:2%;max-width:47%}.bubble.from-player{max-width:74%}.other-name{top:69%}}
</style>
