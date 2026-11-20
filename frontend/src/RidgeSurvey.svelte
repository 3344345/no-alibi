<script lang="ts">
  export let busy = false
  export let pendingChoice = ''
  export let onChoose: (id: string) => void

  const positions = [
    { label: '公路', degrees: 16, tilt: .19, description: '朝坡上看，弧墙挡住了后面。只凭这里的轮廓，数不清它有没有合拢。' },
    { label: '侧坡', degrees: 88, tilt: .43, description: '沿梨树旁转到墙侧，能看见砖墙收口。断碾盘缺齿的一角就在收口外。' },
    { label: '背坡', degrees: 165, tilt: .62, description: '从背坡看，墙只砌了半弧。断碾盘旁是墙口，往东滩去的另一口池是完整的。' },
  ]
  const signs = [
    { id: 'south', label: '南路 · 三号牌', detail: '朝北，右手过断碾盘。池墙缺口正对碾盘的缺齿。' },
    { id: 'north', label: '北路 · 四号牌', detail: '朝南，左手过断碾盘。缺口外那处断齿，朝着同一棵裂梨树。' },
    { id: 'east', label: '东滩 · 饮水池', detail: '沿另一条田埂到东滩，池壁合拢。池沿能搁水瓢，旁边没有断碾盘。' },
  ]
  type Point = [number, number, number]
  type Face = { key: string; fill: string; stroke: string; path: string; depth: number }
  let bearing = positions[0].degrees
  $: position = bearing < 52 ? 0 : bearing < 127 ? 1 : 2
  let pins: string[] = []
  let checked = false
  $: view = positions[position]
  $: same = pins.includes('south') && pins.includes('north')
  $: feedback = same ? '两条路指到同一道缺墙。牌号有两个，实地可确认一座。'
    : '这两处对不上。一处是缺墙和断碾盘，一处是完整池和饮水的牲口。可以换个标记再走。'
  function togglePin(id: string) {
    if (busy || pendingChoice) return
    if (pins.includes(id)) pins = pins.filter(pin => pin !== id)
    else if (pins.length < 2) pins = [...pins, id]
    checked = false
  }

  // Draw the same surveyed geometry from each viewpoint; the road shows the
  // convex face, the hill reveals the open back. Positive Z points to the road.
  function terrain(degrees: number, tilt: number) {
    const angle = degrees * Math.PI / 180, a = Math.cos(angle), b = Math.sin(angle)
    function project([x, y, z]: Point) {
      const depth = z * a + x * b
      return { x: 215 + (x * a - z * b) * 33, y: 94 + (tilt * depth - y) * 29, depth }
    }
    const faces: Face[] = []
    function face(key: string, points: Point[], fill: string, stroke = fill, layer = 0) {
      const screen = points.map(project)
      faces.push({ key, path: 'M' + screen.map(p => p.x.toFixed(1) + ',' + p.y.toFixed(1)).join('L') + 'Z',
        fill, stroke, depth: layer + screen.reduce((n, p) => n + p.depth, 0) / screen.length })
    }
    function path(points: Point[]) {
      return 'M' + points.map(p => { const q = project(p); return q.x + ',' + q.y }).join('L')
    }
    function arcPoint(t: number, radius: number, height: number, x: number, z: number): Point {
      return [x + radius * Math.cos(t), height, z + radius * Math.sin(t)]
    }
    function pool(id: string, x: number, z: number, radius: number, sweep: number, height: number) {
      const steps = sweep === Math.PI ? 18 : 30
      const wall = radius * .13
      for (let i = 0; i < steps; i++) {
        const t = sweep * i / steps, end = sweep * (i + 1) / steps
        const q = (s: number, inset: number, h: number) => arcPoint(s, radius - inset, h, x, z)
        const light = Math.round(53 + 9 * Math.cos(t + .75))
        face(id+'outer'+i, [q(t,0,0),q(end,0,0),q(end,0,height),q(t,0,height)],
          'hsl(30 33% ' + light + '%)', '#785a3f')
        face(id+'inner'+i, [q(t,wall,0),q(end,wall,0),q(end,wall,height),q(t,wall,height)],
          '#896848', '#795d42')
        face(id+'lip'+i, [q(t,0,height),q(end,0,height),q(end,wall,height),q(t,wall,height)],
          '#e6cda6', '#d5b891', .05)
        if (sweep === Math.PI && (i === 0 || i === steps-1)) {
          const edge = i === 0 ? t : end
          face(id+'end'+i, [q(edge,0,0),q(edge,wall,0),q(edge,wall,height),q(edge,0,height)],
            '#c39166', '#795d42', .05)
        }
      }
    }
    pool('ridge', -.55, .15, 1.95, Math.PI, 1.28)
    pool('east', 3.55, -1.8, .72, Math.PI * 2, .37)
    const disk = Array.from({length: 20}, (_,i) => arcPoint(.42 + i * 5.56/19, .61, .12, -.7, -1.9))
    face('broken-stone', [...disk, [-.7, .12, -1.9]], '#827e6a', '#615f53')
    const tree: Point = [-3.28, 0, -.75]
    const t = project(tree)
    faces.push({ key:'split-pear', path:'M'+t.x+','+t.y+'l-2,-19 -12,-16 4,-1 10,10 5,-15 4,1 -4,17 -1,23Z',
      fill:'#574633', stroke:'#574633', depth:t.depth })
    const north = project([.5, .45, -3.15]), south = project([.45, .45, 3.15])
    const east = project([3.55, .6, -1.85])
    const route = path([[.45,0,3.7],[-.2,0,2.85],[-2.95,0,1.4],[-3.05,0,-1],[-1.75,0,-1.8],[.5,0,-3.2]])
    const rows = [-3,-2.6,-2.2,2.6,3,3.4].map(x=>path([[x,0,-3.9],[x-.3,0,-.7],[x+.4,0,3.8]]))
    return { faces: faces.sort((l,r)=>l.depth-r.depth), labels: [south,north,east], route, rows }
  }
  $: tilt = bearing <= positions[1].degrees
    ? .19 + .24 * (bearing - positions[0].degrees) / (positions[1].degrees - positions[0].degrees)
    : .43 + .19 * (bearing - positions[1].degrees) / (positions[2].degrees - positions[1].degrees)
  $: diagram = terrain(bearing, tilt)
</script>

<section class="fieldwork" aria-label="绕池勘察">
  <div class="strip"><h2>绕池勘察</h2><small>运城 · 田野手绘示意</small></div>
  <div class="field">
    <svg viewBox="0 0 430 174" role="img" aria-label={view.label + '观察示意。' + view.description}>
      <defs>
        <linearGradient id="ridge-ground" x1="0" y1="0" x2="0.4" y2="1">
          <stop stop-color="#dbcfaf"/><stop offset="1" stop-color="#eadcba"/>
        </linearGradient>
      </defs>
      <rect width="430" height="174" fill="url(#ridge-ground)" />
      {#each diagram.rows as row}<path d={row} fill="none" stroke="#ab9875" opacity=".43" stroke-width="1.1"/>{/each}
      <path d={diagram.route} fill="none" stroke="#846643" stroke-width="2" stroke-dasharray="4 4" />
      {#each diagram.faces as f (f.key)}<path d={f.path} fill={f.fill} stroke={f.stroke} stroke-width=".65" stroke-linejoin="round" />{/each}
      {#each diagram.labels as point,i}
        <g transform={'translate('+point.x+' '+point.y+')'}>
          <path d="M0 0v-10" stroke="#503d29" stroke-width="1.5" />
          <rect x="-12" y="-24" width="24" height="16" rx="2" fill={pins.includes(signs[i].id) ? '#873e25' : '#443f32'}/>
          <text text-anchor="middle" y="-12.5" fill="#fff5dc" font-size="10.5" font-weight="600">{['三','四','东'][i]}</text>
        </g>
      {/each}
    </svg>
    <div class="bearing"><label for="ridge-bearing">沿田埂移动</label>
      <input id="ridge-bearing" type="range" min={positions[0].degrees} max={positions[2].degrees} step="1"
        bind:value={bearing} aria-valuetext={view.label + '方向，转角' + bearing + '度'} disabled={busy || !!pendingChoice} />
    </div>
    <div class="positions" role="group" aria-label="移动观察位置">
      {#each positions as place, i}
        <button aria-pressed={position === i} disabled={busy || !!pendingChoice} on:click={() => (bearing=place.degrees)}>{place.label}</button>
      {/each}
    </div>
  </div>
  <p class="walk" aria-live="polite">{view.description}</p>
  <p class="task">把你认为指向同一座池的两处标记并在一起。</p>
  <div class="pins" role="group" aria-label="配对沿途标记">
    {#each signs as sign}
      <button aria-pressed={pins.includes(sign.id)} disabled={busy || !!pendingChoice || (pins.length >= 2 && !pins.includes(sign.id))}
        on:click={() => togglePin(sign.id)}>{sign.label}</button>
    {/each}
  </div>
  {#if pins.length}
    <ul>{#each signs.filter(s => pins.includes(s.id)) as s}<li><b>{s.label}</b>　{s.detail}</li>{/each}</ul>
  {/if}
  {#if pins.length === 2 && !checked}
    <button class="record" disabled={busy} on:click={() => (checked=true)}>核对这两处</button>
  {/if}
  <div aria-live="polite">
    {#if checked}
      <p class="finding">{feedback}</p>
      <button class="record" disabled={busy || (!!pendingChoice && pendingChoice !== (same ? 'bank_one' : 'bank_two'))}
        on:click={() => onChoose(same ? 'bank_one' : 'bank_two')}>{same ? '把这两条路记为一座池' : '先向木匠问清编号'}</button>
    {/if}
  </div>
</section>

<style>
  .fieldwork { margin:1.15rem 0; padding:clamp(.85rem,2vw,1.3rem); background:#f2e8d2; border:1px solid #b8a887; color:#373125; }
  .strip { display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:.25em .65em; margin-bottom:.7em; }
  .strip h2 { font:600 1.4rem/1.3 var(--serif); margin:0; }
  small { color:#625341; }
  .field { background:#dfd3b3; border:1px solid #baab86; }
  svg { display:block; width:100%; max-height:190px; }
  .bearing { display:flex; align-items:center; gap:.7em; padding:.3rem .6rem 0; }
  .bearing label { flex-shrink:0; font-size:.82em; color:#514731; }
  .bearing input { flex:1; min-width:0; accent-color:#665437; cursor:pointer; height:24px; }
  .bearing input:focus-visible { outline:2px solid #8b4926; outline-offset:2px; }
  .positions,.pins { display:flex; flex-wrap:wrap; gap:.35rem; }
  .positions { justify-content:center; padding:.35rem .45rem .55rem; }
  button { cursor:pointer; color:#423526; font:inherit; padding:.48em .72em; border:1px solid #9b8666; background:#f9f2e2; border-radius:2px; }
  button:disabled { opacity:.56; cursor:default; }
  button[aria-pressed=true],button.record { color:#fff7e4; background:#5c4531; border-color:#5c4531; }
  button:focus-visible { outline:3px solid #8b4926; outline-offset:2px; }
  .pins button { flex:1 1 auto; }
  .walk,.task,.finding,li { font-size:.96em; line-height:1.6; }
  .walk { margin:.6em 0 1em; color:#594b39; }
  .task { margin:.45em 0; font-weight:600; }
  .finding { margin:.65em 0; padding-left:.65em; border-left:3px solid #946143; }
  ul { margin:.65em 0; padding-left:1.25em; } li { margin:.3em 0; }
  .record { margin-top:.25em; }
  @media(max-width:500px){ button {min-height:43px;} .strip h2 {font-size:1.24rem;} .pins button { flex:1 1 7em; } }
</style>
