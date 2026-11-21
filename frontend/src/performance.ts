import { writable } from 'svelte/store'
import type { View } from './types'
import realCast from './historicalCast.json'
import dramaticCast from './originalCast.json'
import {directedCast} from './stageCasting'
import {sceneSetting} from './chronicleScene'

export type Gesture = 'pass'|'hold'|'speak'|'listen'|'sign'|'refuse'|'inspect'|'depart'|'tune'
export type Phase = 'idle'|'action'|'reply'
export type CastMember = {name:string; face:string; coat:string; collar:'stand'|'work'|'open'; costume:string}
export type ActingScene = {id:string; place:string; title:string; picture:string; film:string; player:CastMember; other:CastMember|null; opening:string; excerpt:string; object:'paper'|'tea'|'radio'|'film'|'lamp'|'cloth'; crop?:string}
export type ActingChoice = {id:string; label:string; disabled?:boolean; group?:string}
export type Turn = {phase:Phase; label:string; reply:string; gesture:Gesture; mood:'open'|'guarded'|'listen'; start:number; scene?:ActingScene}
export const quietTurn = ():Turn=>({phase:'idle',label:'',reply:'',gesture:'listen',mood:'listen',start:0})
export const playback = writable<Turn>(quietTurn())
export const presenting=writable(false)
export const filmOpen = writable(false)
export const inTheatre = writable(false)
let current = 0
let finishWait: (()=>void)|undefined
let skip = false
export function skipPerformance(){skip=true; finishWait?.()}
function wait(ms:number){return new Promise<void>(resolve=>{const done=()=>{clearTimeout(timer);if(finishWait===done)finishWait=undefined;resolve()};const timer=setTimeout(done,ms);finishWait=done})}
export function clearPerformance(){current++;skipPerformance();presenting.set(false);playback.set(quietTurn())}
export function firstLine(text:string,limit=58) {
  const source=text.trim().replace(/\s+/gu,' ')
  const first=source.match(/^.{4,}?[。！？][”」]?/u)?.[0] ?? source
  return first.length>limit?first.slice(0,limit-1)+'…':first
}
export function gestureFor(label:string,kind=''):Gesture{
  const s=label+' '+kind
  if(/不收|推开|退回|拒|放弃|婉辞|婉拒|收回|谢绝|不签|不去|不答应|挡住/.test(s))return 'refuse'
  if(/录音|开播|调台|重播|放带|倒带|剪片|放映|换台|影杆|操纵|按键|扳动/.test(s))return 'tune'
  if(/签|落款|写|画|抄|填|盖章|记下|批注|编号|落笔|记录/.test(s))return 'sign'
  if(/递|交给|放进|交回|捎给|转交|还给|送给|塞给|交还|出示|传给/.test(s))return 'pass'
  if(/看|察|核对|翻|查看|比对|查验|丈量|清点|摸|inspect/.test(s))return 'inspect'
  if(/听|等|守|静|留在|沉默|wait|advance/.test(s))return 'listen'
  if(/离开|回家|走到|去找|出门|赶去|上车|动身|回去|travel|return/.test(s))return 'depart'
  if(/接住|收下|拿|握|抱|接过|留下|保存|按住/.test(s))return 'hold'
  return 'speak'
}
export function startTurn(scene:ActingScene,label:string,kind=''){
  finishWait?.();const serial=++current; skip=false
  const t:Turn={phase:'action',scene,label,gesture:gestureFor(label,kind),reply:'',mood:'listen',start:performance.now()}
  playback.set(t);presenting.set(true)
  const reduced=document.documentElement.classList.contains('reduce-motion')
  return {
    cancel(){if(serial===current)clearPerformance()},
    async resolve(result:string,tone='',reaction?:ActingScene){
      if(!reduced&&!skip&&serial===current)await wait(Math.max(0,620-(performance.now()-t.start)))
      if(serial!==current)return
      const mood=tone==='setback'||/拒|迟疑|摇头|不肯|转开|沉默|收回|气得/.test(result)?'guarded':/笑|点头|接过|道谢|递|答应|同意/.test(result)?'open':'listen'
      playback.set({...t,scene:reaction??scene,phase:'reply',reply:firstLine(result||'事情有了下文。',74),mood,start:performance.now()})
      if(!reduced&&!skip)await wait(1040)
      if(serial===current)presenting.set(false)
      // Keep the authenticated reply on screen until another decision or a new scene.
    }
  }
}

type PortraitCredit={file:string;source:string;author:string;license:string;licenseUrl:string}
export const credits=realCast as Record<string,PortraitCredit>
const ordinary:Record<string,string>={
  街头学生:'teen-boy',
  周禾:'man-young',桂喜:'man-young',小圆:'girl',桂枝:'woman-elder',聂桂枝:'woman-elder',杏儿:'girl',唐棠:'woman-mid',宣美芬:'woman-mid',
  钟至诚:'man-mid',唐素琴:'woman-young',袁月芬:'woman-mid',季阿锦:'woman-mid',柴素兰:'woman-mid',顾兰:'woman-mid',冯巧:'woman-young',赵海成:'driver',沈仲林:'man-mid',向楠:'man-mid',
  蒋禾:'girl',阿砚:'man-young',丁小满:'woman-mid',天佑:'man-young',司机:'driver',母亲:'woman-mid',新娘:'girl',师傅:'man-elder',老师傅:'man-elder',女儿:'girl',
}
const tones=['#505b5a','#655c48','#3e5059','#674f45','#505547','#615458']
function hash(s:string){let v=0;for(const ch of s)v=(v*31+ch.charCodeAt(0))>>>0;return v}
function cast(name:string,defaultFace='man-mid',year=''):CastMember {
  const portrait=(credits as Record<string,{file:string}>)[name] ?? (dramaticCast as Record<string,{file:string}>)[name]
  const fallback=Object.keys(ordinary).find(k=>name===k)
  const face=portrait?.file||(fallback&&ordinary[fallback])||defaultFace||'man-mid'
  const n=hash(name),prewar=parseInt(year)<1945
  const statesman=/^(邓小平|毛泽东|周恩来|孙中山|蒋介石|蒋经国|彭德怀|张治中|张学良)$/.test(name)
  const feminine=/woman|girl|vautrin|aiyun|lin_zhao|zhongyun/.test(face)
  const costume=statesman?'tunic':feminine?(/girl/.test(face)?'rust':prewar?'cotton':'indigo'):prewar?'gown':n%3===0?'tunic':'jacket'
  return {name,face,coat:tones[n%tones.length],costume,collar:statesman||prewar?'stand':n%3===0?'open':'work'}
}
function distinguish(player:CastMember,other:CastMember|null){
  if(!other||other.name===player.name||other.face!==player.face)return
  const alternatives:Record<string,string>={'man-mid':'driver','driver':'man-mid','man-young':'apprentice','apprentice':'teen-boy','teen-boy':'man-young','man-elder':'puppet-master','puppet-master':'man-elder','woman-young':'seamstress','woman-mid':'fish-counter','woman-elder':'granny','girl':'woman-young','boy':'teen-boy','girl-child':'girl','seamstress':'woman-young','fish-counter':'woman-mid','granny':'woman-elder'}
  other.face=alternatives[other.face]??other.face
  if(player.costume===other.costume)other.costume=player.costume==='gown'?'cotton':player.costume==='tunic'?'jacket':player.costume==='indigo'?'rust':player.costume
}
function excerpt(text:string){
  const quote=Array.from(text.matchAll(/“([^”]{3,66})”/gu)).find(m=>/[？。！]/u.test(m[1]))
  return quote?quote[0]:firstLine(text)
}
function sceneObject(id:string,body:string):ActingScene['object']{
  if(/^(face_|air_)/.test(id))return 'cloth'
  if(/^(night_|reel_)/.test(id)||/电话|听筒|播音/.test(body.slice(0,64)))return 'radio'
  if(/琴|灯火|灯罩/.test(body.slice(0,38)))return 'lamp'
  if(/茶|茶杯|碗/.test(body.slice(0,60)))return 'tea'
  return 'paper'
}
function setPicture(chapter:string,scene:string,title:string,year:string){
  const key=chapter+'/'+scene, words=scene+' '+title
  let room=parseInt(year)<1949?'inn':'office'
  if(/reel_(lobby|mix|keys|booth|sale|open|ticket|hinge)|night_(switchboard|exchange|listen|clock|answer)|studio|broadcast/.test(key))room='studio'
  else if(/reel_(morning|kitchen|landing)|birthday_|school_album|sky_(half|yard|home|last)|household_field|小院|厨房|家里|堂屋/.test(key+words))room='house'
  else if(/face_(quay|platform)|zhan_tianyou|站台|火车/.test(key+words))room='rail'
  else if(/face_(box|screen|laugh|bird|door|seat|settle)|reel_(yard|truck|shop)|剧场|礼堂|戏棚/.test(key+words))room='theatre'
  else if(/night_(depot|punch|window|last|garage)|tram_|车库|电车/.test(key+words))room='depot'
  else if(/bank_(ridge|map|up|measure|trace)|工地|跑道|水池|稻田|地头/.test(key+words))room='field'
  else if(/医院|病房|医生|急诊|witness_jiang_yanyong/.test(key+words))room='clinic'
  else if(/xian_|重庆|庭审|法庭|法院|shen_junru|会场/.test(key+words))room='court'
  else if(/air_|shanghai_workers|may_fourth|gu_zhenghong|工厂|印铺|车间/.test(key+words))room='press'
  else if(/sky_|school_ground|街头|门外|院子|校门/.test(key+words))room='yard'
  return '/sets/'+room+'.webp'
}
export function libraryFilm(chapter:string,scene:string){return scene.startsWith('reel_')?'seven-seconds':scene.startsWith('face_')?'shadow-play':chapter}
export function historyStage(ch:{id:string;year:string;place:string;role:string},s:{id:string;title:string;body:string;role?:string},displayPlace?:string):ActingScene{
  const set=sceneSetting(ch.id,s.id,s.title,ch)
  const body=s.body, direction=directedCast(ch.id,s.id,s.role||ch.role,body)
  const player=cast(direction.player,direction.playerFace??'man-mid',ch.year)
  const other=direction.other?cast(direction.other,direction.otherFace??'driver',ch.year):null
  distinguish(player,other)
  return {id:ch.id+'/'+s.id,place:set.year+' · '+(displayPlace||set.place),title:s.title,picture:setPicture(ch.id,s.id,s.title,ch.year),film:libraryFilm(ch.id,s.id),
    player,other,
    opening:firstLine(body),excerpt:excerpt(body),object:sceneObject(s.id,body)}
}
const countyArt:Record<string,string>={L01:'/scenes/office.webp',L02:'/scenes/canal.webp',L03:'/sets/court.webp',L04:'/sets/inn.webp',L05:'/sets/office.webp',L06:'/sets/field.webp',L07:'/scenes/home.webp',L08:'/sets/house.webp',L09:'/sets/house.webp'}
export function countyStage(v:View,context='',actionLabel=''):ActingScene{
  const id=v.location.id??'L01',hasShow=context==='aftershow',bus=context==='night_bus'
  const story=hasShow?v.aftershow:bus?v.night_bus:null
  const present=v.people.filter(p=>p.present&&typeof p.name==='string')
  const person=present.find(p=>actionLabel.includes(p.name??'—'))??present[0]
  const stage=story?directedCast(hasShow?'aftershow':'night_bus',story.title,v.name??'你',story.body):null
  const player=cast(stage?.player??v.name??'你',stage?.playerFace??'man-mid')
  const other=stage?(stage.other?cast(stage.other,stage.otherFace??'driver'):null):person?cast(person.name??'在场人','driver'):null
  distinguish(player,other)
  return {id:'county/'+(story?context+'/'+story.title:id),place:v.location.name??'澄川',title:story?.title??v.location.name??'澄川',film:'county-'+(hasShow?'cinema':bus?'bus':id),
    picture:hasShow?'/sets/theatre.webp':bus?'/sets/depot.webp':countyArt[id]??'/sets/office.webp',
    player,other,
    opening:firstLine(story?.body??v.location.description??''),excerpt:excerpt(story?.body??v.location.description??''),object:hasShow?'film':bus?'radio':['L04','L07','L09'].includes(id)?'tea':'paper'}
}
