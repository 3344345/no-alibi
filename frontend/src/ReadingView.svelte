<script lang="ts">
  import { propImage, type ReadingCamera } from './readingView'
  export let camera: ReadingCamera
  export let close = false
  $: atDesk = !camera.baked && !camera.frame && !!camera.prop && /\/sets\/(office|court|press|inn|house|studio)\.webp$/.test(camera.room)
  $: prop = close ? (camera.focus ?? camera.prop) : camera.prop
</script>

<div class="eyes" class:close class:baked={camera.baked} class:projection={camera.frame?.type==='screen'} data-viewer={camera.person} data-prop={prop} style={'--look:'+(camera.position ?? '50% 50%')}>
  <div class="viewfinder"><div class="image-plane">
    <img class="reading-space" src={camera.room} alt={camera.person+'眼前的场景'} decoding="async"/>
    {#if camera.frame}
      <div class="physical-frame" class:cover={camera.frame.type==='cover'} class:screen={camera.frame.type==='screen'}>
        <img src={camera.frame.src} alt={camera.frame.alt} decoding="async"/>
      </div>
    {/if}
  </div></div>
  {#if atDesk}<div class="work-surface"></div>{/if}
  {#if !camera.baked}
    {#if prop}<div class="near-object"><img src={propImage(prop)} alt="" decoding="async"/></div>{/if}
    <img class="own left" src={'/wardrobe/'+(camera.hands ?? 'pov')+'-rest-left.webp'} alt="" decoding="async"/>
    <img class="own right" src={'/wardrobe/'+(camera.hands ?? 'pov')+'-rest-right.webp'} alt="" decoding="async"/>
  {/if}
</div>

<style>
  .eyes{position:absolute;inset:0;overflow:hidden;isolation:isolate;pointer-events:none;background:#282b24}
  .viewfinder,.image-plane{position:absolute;inset:0}
  .reading-space{width:100%;height:100%;display:block;object-fit:cover;object-position:var(--look);transform-origin:var(--look);transition:transform .6s ease,filter .6s ease}
  .eyes.baked .reading-space{object-fit:cover;object-position:var(--look)}
  .work-surface{position:absolute;inset:74% -2% -2%;background:#493a2d url('/reading/work-surface.webp') center/100% 100%;border-top:2px solid #7a6550;box-shadow:0 -2px 5px #30281c33;transform:rotate(-.8deg)}
  .near-object{position:absolute;left:50%;bottom:7%;width:42%;height:37%;transform:translateX(-50%);transform-origin:center 84%;transition:transform .6s ease,bottom .6s ease;filter:drop-shadow(2px 6px 5px #20180fa0)}
  .near-object img{width:100%;height:100%;object-fit:contain;object-position:bottom}
  .own{position:absolute;bottom:-2%;width:36%;height:35%;object-fit:contain;object-position:bottom;filter:brightness(.87) saturate(.87);transition:transform .6s ease}
  .own.left{left:4%;transform-origin:bottom left}.own.right{right:4%;transform-origin:bottom right}
  .close .reading-space{transform:scale(1.045);filter:blur(1.5px)}
  .close.baked .reading-space{transform:scale(1.12);filter:none}
  .close .near-object{bottom:16%;transform:translateX(-50%) scale(1.48)}
  .close .own{height:43%;width:40%}.close .own.left{left:12%;transform:rotate(-5deg)}.close .own.right{right:12%;transform:rotate(5deg)}
  .physical-frame{position:absolute;display:grid;place-items:center;overflow:hidden;box-sizing:border-box}
  .physical-frame img{width:100%;height:100%;object-fit:contain;display:block}
  .physical-frame.cover{left:24%;top:15%;width:55%;height:58%;background:#b9a687;border:5px solid #cbbca0;box-shadow:-5px 4px 0 #76583b,2px 6px 12px #241b1399;transform:rotate(-3deg)}
  .physical-frame.cover img{object-fit:cover}
  /* Keep the film and the photographed screen on the same 16:9 plane. */
  .projection{container-type:size}
  .projection .viewfinder{inset:auto;left:50%;top:50%;width:min(100cqw,177.7778cqh);aspect-ratio:16/9;transform:translate(-50%,-50%);overflow:hidden}
  .projection .image-plane{inset:auto;left:-27%;top:-61%;width:260%;height:260%}
  .physical-frame.screen{left:14.375%;top:29.25926%;width:30.20834%;height:29.62963%;background:#201f1b}
  @media(prefers-reduced-motion:reduce){.reading-space,.near-object,.own{transition:none}}
  :global(.reduce-motion) .reading-space,:global(.reduce-motion) .near-object,:global(.reduce-motion) .own{transition:none}
</style>
