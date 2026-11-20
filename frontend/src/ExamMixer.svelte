<script lang="ts">
  export let choices: { id: string; label: string }[]
  export let disabled: boolean
  export let onChoose: (id: string) => void

  const patterns = [
    { id: 'wear_neat', name: '照原样收袖', note: '侧缝收进两个指头，放下手时衣身最平整。', result: '弓到了中段，扣着的下摆也跟着往上跑。' },
    { id: 'wear_gusset', name: '腋下嵌三角', note: '把里襟的红布裁下一角，嵌进蓝袖与衣身之间。', result: '袖下的红角张开了。弓走到底，衣摆还贴着凳子。' },
    { id: 'wear_open', name: '侧边留活口', note: '侧缝先不合死，留两根布带，穿衣的人能自己调。', result: '布带松开，手臂抬得最高。放下弓前，他得腾出手来系。' },
  ]
  let pattern = 0
  let arm = 0
  $: sample = patterns[pattern]
  $: angle = 60 - arm * 0.65
  $: lifted = arm > 50
  $: rise = pattern === 0 ? arm * .25 : pattern === 2 ? arm * .035 : 0
  $: decision = choices.find((choice) => choice.id === sample.id)
</script>

<section class="bench" aria-label="裁缝试样台">
  <div class="bench-head"><h2>试样台</h2><span>一块蓝料，三种裁法</span></div>
  <div class="sketch" aria-hidden="true">
    <svg viewBox="0 0 400 170" focusable="false">
      <defs><pattern id="tailorgrid" width="13" height="13" patternUnits="userSpaceOnUse"><path d="M 13 0 H 0 V 13" fill="none" stroke="#686141" opacity=".17"/></pattern></defs>
      <rect width="400" height="170" fill="url(#tailorgrid)"/>
      <g transform="translate(105,0)">
        <path d={'M47 34 L66 26 Q80 44 94 26 L113 34 L120 69 L115 '+(140-rise)+' Q79 '+(150-rise/2)+' 38 143 L45 66 Z'} fill="#3e626a" stroke="#203e49" stroke-width="2"/>
        <path d="M69 31 L79 44 L89 31 M79 44V139" fill="none" stroke="#d1c094" stroke-dasharray="4 3"/>
        <path d="M45 38 L24 102 L38 109 L59 59" fill="#4b6870" stroke="#203e49" stroke-width="2"/>
        {#if pattern === 1}<path d={'M104 50 L'+(127+arm*.1)+' '+(77-arm*.36)+' L113 85Z'} fill="#ac594e" stroke="#ebc99c" stroke-dasharray="2 2"/>{/if}
        <g transform={'rotate('+angle+' 108 47)'}>
          <path d="M102 36 Q120 33 137 38 L195 42 L196 60 L131 66 Q113 65 101 60" fill="#52737b" stroke="#203e49" stroke-width="2"/>
          <path d="M132 61 L190 55 M188 43 L189 58" stroke="#dfcbaa" fill="none" stroke-dasharray="3 4"/>
        </g>
        {#if pattern === 2}<path d="M115 87 L110 128 M112 101 q18 -10 15 3q-4 5 -13 1q8 12 14 9" stroke="#e6c99b" stroke-width="2" fill="none"/>{/if}
      </g>
    </svg>
  </div>
  <div class="samples" role="group" aria-label="选一件样衣">
    {#each patterns as s, i}<button aria-pressed={i===pattern} on:click={() => (pattern=i)} disabled={disabled}>{s.name}</button>{/each}
  </div>
  <p>{sample.note}</p>
  <label for="coat-arm">抬起运弓的手臂</label>
  <input id="coat-arm" type="range" min="0" max="100" bind:value={arm} aria-valuetext={arm === 0 ? '垂手' : lifted ? '把弓拉到头' : '刚起弓'} />
  <p class="fit" aria-live="polite">{lifted ? sample.result : arm === 0 ? '天佑把手垂下来。三件样衣这样看都合身。' : '他慢慢拉弓。留意袖底和衣摆。'}</p>
  {#if decision}<button class="commit" disabled={disabled} on:click={() => onChoose(decision!.id)}>{decision.label} →</button>{/if}
</section>

<style>
  .bench { color:#302d27; background:#eee1c9; border:1px solid #baaa89; margin:1.2rem 0; padding:clamp(.85rem,2vw,1.55rem); }
  .bench-head,.samples { display:flex; align-items:center; flex-wrap:wrap; gap:.45rem; }
  .bench-head {justify-content:space-between; margin-bottom:.65rem}
  .bench-head h2 {font:600 1.35em var(--serif);margin:0;} .bench-head span, label{font-size:.9em;}
  .sketch{background:#e2d3b7;border-block:1px solid #bbaa8a;}
  svg {width:100%;height:clamp(120px,19vh,195px);display:block;}
  .samples {margin-top:.8rem;} button {border:1px solid #98876b;color:#2d332f;background:#f8efdf;padding:.55em .8em;font:inherit;cursor:pointer;}
  button[aria-pressed=true],.commit {background:#30484d;color:#fff7e4;border-color:#30484d;}
  label{font-weight:650;} input[type=range]{width:100%;display:block;accent-color:#435c61;margin:.55rem 0;}
  p{font-size:.95em;line-height:1.7;margin:.65rem 0;} .fit {min-height:1.7em;}
  .commit {width:100%;text-align:left;margin-top:.25rem;} button:focus-visible,input:focus-visible{outline:3px solid #87561c;outline-offset:2px;}
</style>
