import type { ActingScene } from './performance'
import { viewpointHands, type HandSet } from './actorMovement'
import type { Shot } from './sceneReel'

export type ReadingProp = 'paper'|'cup'|'radio'|'cloth'|'keys'|'puppets'|'rain'|'measure'|'grain'|'ticket'|'reel'|'lamp'
export type ReadingCamera = {
  room: string
  person: string
  prop?: ReadingProp
  focus?: ReadingProp
  position?: string
  frame?: {src: string; alt: string; type: 'screen'|'cover'}
  baked?: boolean
  hands?: HandSet
}

const inspectProps: Record<string, ReadingProp> = {
  cup_rim: 'cup', paper_rods: 'puppets', piano_wire: 'keys', rain_tin: 'rain',
}

function objectAtScene(scene: ActingScene, shot?: Shot): ReadingProp | undefined {
  const id=scene.id.split('/').at(-1) ?? ''
  const title=scene.title
  if (shot?.prop) return inspectProps[shot.prop.cue]
  if (/^face_/.test(id)) return /quay|platform/.test(id) ? 'ticket' : 'puppets'
  if (/^reel_/.test(id)) return /keys|landing|shop|morning|brass/.test(id) ? 'keys' : 'reel'
  if (/^tram_/.test(id)) return /dining|bowl|cook/.test(id) ? 'cup' : 'ticket'
  if (/^air_|^birthday_|^rights_|^hands_|衣|布尺|裁衣|被面/.test(id+' '+title)) return 'cloth'
  if (/^bank_|^cones$|排水|丈量/.test(id+' '+title)) return 'measure'
  if (/^sky_|下雨|雨夜/.test(id+' '+title)) return /rain|雨/.test(id+' '+title) ? 'rain' : 'lamp'
  if (/^night_(screen|eye|frame|reel)/.test(id)) return 'reel'
  if (/^night_(depot|punch|window|platform|last|coach)/.test(id)) return 'ticket'
  if (/^(studio|switchboard|cutting_room|summer_broadcast|city_frequency)$/.test(id)) return 'radio'
  if (/播音|收音机|电话|值机/.test(title)) return 'radio'
  if (/秤|种子|豆种|米价|粮|饭锅/.test(title)) return 'grain'
  if (/衣|布料|针线|袖|相纸/.test(title)) return 'cloth'
  if (/票|车库|车站/.test(title)) return 'ticket'
  if (/稿|信|账|证词|电报|纸|登记|签字|名册|材料|印|版/.test(title)) return 'paper'
  if (/茶|锅|碗|饭/.test(title)) return 'cup'
  if (/灯|夜/.test(title)) return 'lamp'
  return ({paper:undefined,tea:'cup',lamp:'lamp',radio:'radio',film:'reel',cloth:'cloth'} as const)[scene.object]
}

export function propImage(prop: ReadingProp): string {
  const common: Partial<Record<ReadingProp,string>>={paper:'paper',lamp:'lamp',cloth:'cloth',reel:'film'}
  return common[prop] ? '/wardrobe/prop-'+common[prop]+'.webp' : '/reading/'+prop+'.webp'
}

export function readingCamera(scene: ActingScene, shot?: Shot): ReadingCamera {
  const position=shot?.position ?? (scene.object==='radio'?'61% 50%':'50% 49%')
  return {room:scene.picture,person:scene.player.name,position,hands:viewpointHands(scene),
    prop:scene.transmission ? (scene.object==='radio'?'radio':'paper') : objectAtScene(scene,shot),focus:shot?.prop ? inspectProps[shot.prop.cue] : undefined}
}

export function countyCamera(id: string, person='你'): ReadingCamera {
  const source=/^L0[1-9]$/.test(id)||id==='bus'||id==='cinema' ? id : 'L01'
  return {room:'/sets/county-'+source+'.webp',person,baked:true,position:'50% 58%'}
}
