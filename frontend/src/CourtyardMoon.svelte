<script lang="ts">
  export let disabled = false
  export let onChoose: (id: string) => void
  let angle = 90
  let drawn: string[] = []
  const spots = [
    { id: 'jiang', degrees: 225, name: '蒋禾', line: '蒋禾把铅笔递过来：“你瞧，就这么一条，画粗了都不像。”' },
    { id: 'yan', degrees: 45, name: '阿砚', line: '阿砚没接铅笔，先拿手比了个圆，又掐掉一小边：“这才是我刚才瞧见的。”' },
  ]
  $: spot = spots.find(s => Math.abs(angle - s.degrees) <= 9)
  $: rad = angle * Math.PI / 180
  $: bright = (1 + Math.cos(rad)) / 2
  $: phase = bright < .03 ? '几乎全暗' : bright < .42 ? '一弯月牙' : bright < .58 ? '半轮亮面' : bright < .97 ? '鼓起来的月亮' : '一轮圆月'
  // Each horizontal slice projects the edge of the lit hemisphere to the
  // same fraction across the apparent disc. The lit limb flips at conjunction.
  function silhouette(a: number) {
    const cos = Math.cos(a), side = Math.sin(a) >= 0 ? -1 : 1
    const edge: string[] = [], seam: string[] = []
    for (let i = 0; i <= 64; i++) {
      const t = Math.PI * i / 64
      const x = 52 * Math.sin(t) * side, y = 76 - 52 * Math.cos(t)
      edge.push((87 + x).toFixed(2) + ',' + y.toFixed(2))
      seam.unshift((87 - cos * x).toFixed(2) + ',' + y.toFixed(2))
    }
    return 'M' + [...edge, ...seam].join('L') + 'Z'
  }
  function sketch() {
    if (spot && !drawn.includes(spot.id)) drawn = [...drawn, spot.id]
  }
</script>

<section class="bench" aria-label="院里的月相桌">
  <h2>一盏灯，两双鞋</h2>
  <p class="hint">球插在筷子上。沿着粉笔圈走走，到两个孩子脚边，各描一张给他们看。</p>
  <div class="table">
    <svg viewBox="0 0 248 153" role="img" aria-label="俯看小院，灯在左边，脚步沿球四周移动">
      <defs><radialGradient id="yard-light"><stop stop-color="#facb76" stop-opacity=".35"/><stop offset="1" stop-color="#edbb65" stop-opacity="0"/></radialGradient></defs>
      <ellipse cx="37" cy="76" rx="72" ry="73" fill="url(#yard-light)"/>
      <ellipse cx="141" cy="76" rx="76" ry="54" stroke="#b5ab91" stroke-width="1.2" stroke-dasharray="3 6" fill="none"/>
      <path d="M22 89h20l-4-5h-12z M25 82c-5-9 6-19 7-23 2 7 11 16 6 23z" fill="#edc97d"/>
      <text x="32" y="109">灯</text>
      <circle cx="141" cy="76" r="11" fill="#333934"/><path d="M141 65a11 11 0 0 0 0 22z" fill="#f3e4bc"/>
      {#each spots as s}
        {@const a = s.degrees * Math.PI / 180}
        <circle cx={141 - 76 * Math.cos(a)} cy={76 + 54 * Math.sin(a)} r="6" fill="#252c27" stroke="#c1aa81"/>
        <text x={141 - 76 * Math.cos(a)} y={76 + 54 * Math.sin(a) + (s.degrees > 180 ? -12 : 23)}>{s.name}</text>
      {/each}
      <path d={'M141 76L' + (141-76*Math.cos(rad)) + ' ' + (76+54*Math.sin(rad))} stroke="#e8ba79" stroke-dasharray="2 4"/>
      <circle cx={141-76*Math.cos(rad)} cy={76+54*Math.sin(rad)} r="4.4" fill="#f6d58a"/>
    </svg>
    <figure>
      <svg viewBox="0 0 174 144" role="img" aria-label={'从这里看见' + phase}>
        <defs><radialGradient id="ball-lit" cx="38%" cy="32%" r="72%"><stop stop-color="#fff4d3"/><stop offset=".72" stop-color="#e1d0a3"/><stop offset="1" stop-color="#b4a17b"/></radialGradient></defs>
        <path d="M85 119h4v24h-4z" fill="#ab8660"/>
        <circle cx="87" cy="76" r="52" fill="#393b35" stroke="#626253" stroke-width=".7"/>
        <path d={silhouette(rad)} fill="url(#ball-lit)"/>
      </svg>
      <figcaption>{phase}</figcaption>
    </figure>
  </div>
  <label>沿粉笔圈挪步 <input type="range" min="0" max="360" step="1" bind:value={angle} {disabled} aria-valuetext={(spot?.name ?? '院中') + '，' + phase}/></label>
  <div class="spots">{#each spots as s}<button {disabled} aria-pressed={spot?.id === s.id} on:click={() => angle = s.degrees}>站到{s.name}的脚印里</button>{/each}</div>
  <p aria-live="polite" class="line">{spot?.line ?? '蒋禾扶着灯座，等你站稳。阿砚把两张烟盒纸翻到白的一面。'}</p>
  <div class="desk">
    <button disabled={disabled || !spot || drawn.includes(spot.id)} on:click={sketch}>{spot && drawn.includes(spot.id) ? '这张已经画好' : '把眼前的月样描在纸上'}</button>
    <span>{drawn.length ? drawn.map(id => id === 'jiang' ? '蒋禾的月牙' : '阿砚的胖月亮').join('、') : '烟盒纸还空着'}</span>
  </div>
  {#if drawn.length === 2}<button class="keep" {disabled} on:click={() => onChoose('sky_keep_sketch')}>把两张月样对折，鞋尖朝向也画上去 →</button>{/if}
</section>

<style>
  .bench{margin:1.1rem 0 1.5rem;padding:clamp(14px,3vw,24px);background:#26312d;color:#eee5d4;border:1px solid #384640;border-radius:5px}
  h2{margin:0;font-size:1.4rem;color:#fff0d4;font-family:serif}
  .hint,.line{font-size:.94rem;line-height:1.65}.hint{color:#d0cbb9;margin:.4rem 0 .9rem}.line{min-height:2.8em;margin:.8rem 0}
  .table{display:grid;grid-template-columns:1.55fr 1fr;align-items:center;background:#1d2723;border:1px solid #465048;border-radius:3px}
  svg{width:100%;display:block}svg text{text-anchor:middle;fill:#d6c9af;font-size:12px}figure{margin:0;border-left:1px solid #455148;padding:.2rem .4rem .45rem}
  figcaption{text-align:center;color:#eddbb0;font-size:.82rem}label{display:flex;align-items:center;gap:.8rem;margin:.8rem 0;font-size:.9rem}input{flex:1;min-width:0;accent-color:#e8c78b}
  .spots,.desk{display:flex;align-items:center;flex-wrap:wrap;gap:.5rem}.bench button{cursor:pointer;border:1px solid #97876b;background:#35403a;color:#f5e9d0;font:inherit;font-size:.88rem;padding:.55rem .7rem;border-radius:3px;text-align:left}
  .bench button[aria-pressed=true]{background:#5a503d;border-color:#e3c78d}.bench button:disabled{opacity:.55;cursor:default}.bench :focus-visible{outline:2px solid #f7d99c;outline-offset:2px}
  .desk{border-top:1px solid #53594d;padding-top:.7rem}.desk span{font-size:.81rem;color:#d8ccb3}.bench .keep{display:block;background:#e3c78d;color:#242c25;margin-top:.8rem;font-weight:bold}
</style>
