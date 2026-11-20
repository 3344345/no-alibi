<script lang="ts">
  import { features, type Feature } from './features'
  export let play: (story: Feature) => void
  let current = 0
  $: story = features[current]
</script>

<section class="feature" aria-label="长篇选集">
  <div class="frame">
    {#key story.title}<img src={story.image} alt="" fetchpriority="high" />{/key}
    <div class="vignette"></div>
    <div class="feature-copy" aria-live="polite">
      <span>{story.setting}</span>
      <h2>{story.title}</h2>
      <p>{story.pitch}</p>
      <button class="enter" on:click={() => play(story)}>{story.action} <b aria-hidden="true">→</b></button>
    </div>
  </div>
  <div class="strip" aria-label="挑选长篇">
    {#each features as item, i}
      <button aria-pressed={current === i} on:click={() => (current = i)}>{item.title}</button>
    {/each}
  </div>
</section>

<style>
  .feature { max-width:1400px; margin:0 auto clamp(1.2rem,3vw,2.8rem); }
  .frame {position:relative;isolation:isolate;min-height:clamp(315px,45vh,560px);display:flex;align-items:flex-end;overflow:hidden;background:#171b19;}
  .frame img,.vignette{position:absolute;inset:0;width:100%;height:100%;z-index:-2;object-fit:cover;object-position:center 45%;}
  .vignette{z-index:-1;background:linear-gradient(90deg,#111714ef 0%,#141a16ad 32%,transparent 76%),linear-gradient(0deg,#10141084,transparent 70%);}
  .feature-copy{max-width:35em;padding:clamp(1.2rem,3vw,3.5rem);color:#fff5e4;}
  .feature-copy span{color:#f1d5ac;font-size:.88rem;letter-spacing:.12em;}
  .feature-copy h2{margin:.22em 0 .14em;font:560 clamp(2.3rem,5vw,4.6rem)/1.12 var(--serif);letter-spacing:.035em;text-wrap:balance;}
  .feature-copy p{font:1rem/1.8 var(--serif);margin:.6rem 0 1.1rem;color:#f4eee3;}
  .enter{background:#f2e4c8; color:#25271f; padding:.6rem 1rem; min-height:44px;border:1px solid #f4dfaf; font-weight:650;}
  .enter b{margin-left:.5em;} .strip{display:flex;overflow-x:auto; border-bottom:1px solid #534f43;}
  .strip button{background:transparent;color:#bfbab0;white-space:nowrap;min-height:44px;padding:.7rem clamp(.65rem,1.75vw,1.6rem);border:0;border-bottom:2px solid transparent;}
  .strip button[aria-pressed=true]{color:#f1d7a7;border-bottom-color:#cda66e;}
  button:hover,button:focus-visible {filter:brightness(1.15);}
  button:focus-visible {outline:2px solid #d7b471;outline-offset:-4px;}
  @media (max-width:600px){.frame{min-height:330px}.frame img{object-position:54% 35%}.vignette{background:linear-gradient(0deg,#0c110ff5,#101813ad 53%,#10181305 87%);}.feature-copy{padding:1rem}.feature-copy p{line-height:1.55;}}
</style>
