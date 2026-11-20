export type Beat = { text: string; kind: 'story' | 'consequence' }
export type PropCue = 'cup_rim' | 'paper_rods' | 'piano_wire' | 'rain_tin'
export type Prop = { name: string; detail: string; cue: PropCue }
export type Shot = { image: string; position: string; caption: string; prop?: Prop }

export function sceneBeats(text: string, lastResult = ''): Beat[] {
  const beats: Beat[] = []
  function split(source: string, kind: Beat['kind']) {
    for (const paragraph of source.split(/\n+/u).filter(Boolean)) {
      let line = ''
      // Keep the full authored passage and its closing quotation marks in order.
      const clauses = paragraph.match(/[^。！？；，、…]+[。！？；，、…]*[”’」』）]*|./gu) ?? []
      for (const clause of clauses) {
        if (line && (line.length + clause.length > 82 || (line.length >= 30 && /[。！？][”’」』）]*$/u.test(line)))) {
          beats.push({ text: line, kind })
          line = ''
        }
        line += clause
      }
      if (line) beats.push({ text: line, kind })
    }
  }
  if (lastResult) split(lastResult, 'consequence')
  split(text, 'story')
  return beats
}

const cup: Prop = { name: '听茶盖', cue: 'cup_rim', detail: '盖沿在碗口碰了两下。对面的人松开手，等你把话问完。' }
const paper: Prop = { name: '听影杆', cue: 'paper_rods', detail: '两根细杆擦过布面。坐在前排的人听得见，后排只看见影子点了一下头。' }
const piano: Prop = { name: '听琴弦', cue: 'piano_wire', detail: '松开指头以后，那根弦还在响。靠在琴边才能听见最后一点余音。' }
const rain: Prop = { name: '听檐下的雨', cue: 'rain_tin', detail: '雨点打在铁皮边，先是东头响了两声，接着落到你身边。' }

export function directedShot(scene: string): Shot | undefined {
  if (/^xian_(nanking_(first|second)|second_n)$/.test(scene))
    return { image: 'still_xian', position: '65% 42%', caption: '情境插画 · 西安窗下的来客', prop: cup }
  if (scene.startsWith('face_')) {
    if (['face_quay','face_bench','face_platform','face_letter'].includes(scene))
      return {image:'still_letter',position:'64% 50%',caption:'情境插画 · 留在印铺的影人'}
    const audience = ['face_laugh','face_bird','face_door','face_seat','face_settle'].includes(scene)
    return { image: audience ? 'still_audience' : 'still_shadow', position: audience ? '64% 40%' : '57% 47%', caption: audience ? '情境插画 · 喜棚的前排' : '情境插画 · 白布后面的两个人', ...(audience ? {} : {prop: paper}) }
  }
  if (scene.startsWith('reel_')) {
    if (['reel_kitchen','reel_morning','reel_shop','reel_yard','reel_landing'].includes(scene))
      return {image:'still_lastkeys',position:'58% 46%',caption:'架空场景 · 那架琴的后来',prop:piano}
    const inStudio = ['reel_lobby','reel_mix','reel_open','reel_sale','reel_booth','reel_ticket'].includes(scene)
    return { image: inStudio ? 'still_radio' : 'still_piano', position: inStudio ? '65% 40%' : '63% 47%', caption: inStudio ? '架空场景 · 夜班放音间' : '架空场景 · 散场后的旧钢琴', ...(inStudio ? {} : {prop: piano}) }
  }
  if (['sky_rain','sky_last'].includes(scene))
    return { image:'still_sky', position:'63% 40%', caption:'情境插画 · 那个没看到彗星的雨夜', ...(scene === 'sky_rain' ? {prop: rain} : {}) }
  if (['bank_ridge','bank_up','bank_measure','bank_trace'].includes(scene))
    return { image:'still_ridge', position:'68% 46%', caption:'情境插画 · 走到池墙背后' }
}
