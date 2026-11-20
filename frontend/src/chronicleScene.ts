import type { RoomTone, Score, Soundscape, StoryCue } from './sound'

const exchange = new Set([
  'studio',
  'switchboard',
  'cutting_room',
  'summer_broadcast',
  'city_frequency',
  'night_switchboard',
  'night_coins',
  'night_listen',
  'night_clock',
  'night_cabinet',
  'night_answer',
  'night_queue',
])
const screenings = new Set(['night_reel', 'night_screen', 'night_eye', 'night_frame'])
const stops = new Set([
  'night_depot',
  'night_punch',
  'night_window',
  'night_platform',
  'night_patch_bell',
  'night_loss_patch_bell',
  'night_contract',
  'night_lease',
  'night_empty',
  'night_last',
  'night_coach',
])
const streets = new Set(['night_patch_bakery', 'night_loss_patch_bakery', 'night_address', 'night_return', 'night_supper', 'night_harmonica'])
const mourning = new Set(['loss', 'night_clock', 'night_silence', 'night_mother', 'night_address'])
const homecoming = new Set([
  'night_harmonica',
  'night_last',
  'night_room',
  'night_coach',
  'night_supper',
  'city_frequency',
  'workers_budget',
  'civil',
])

export function sceneMix(chapter: string, scene: string, tone?: Score): Soundscape {
  let room: RoomTone = 'room'
  let music: Soundscape['music'] = tone === 'setback' ? 'vigil' : 'question'
  if (scene.startsWith('face_')) {
    return {room: scene === 'face_letter' ? 'room' : 'courtyard', music: 'shadow_duet'}
  }
  if (scene.startsWith('reel_')) {
    return {room: ['reel_lobby','reel_mix','reel_open','reel_sale','reel_booth','reel_ticket'].includes(scene) ? 'exchange' : 'room', music:'empty_hall'}
  }
  if (chapter === 'witness_deng_xiaoping') {
    if (exchange.has(scene)) room = 'exchange'
    else if (screenings.has(scene)) room = 'projector'
    else if (stops.has(scene)) room = 'platform'
    else if (streets.has(scene)) room = 'courtyard'
    if (scene.startsWith('night_loss_') || mourning.has(scene)) music = 'vigil'
    else if (homecoming.has(scene) && tone !== 'setback') music = 'afterlight'
  } else if (chapter === 'witness_shanghai_prices' && scene.startsWith('tram_')) {
    room = 'courtyard'
    if (scene === 'tram_map' && tone !== 'setback') music = 'afterlight'
  } else if (chapter === 'witness_xiaogang' || chapter === 'household_field') {
    room = 'courtyard'
  } else if (chapter === 'witness_entrance_exam' && scene === 'winter' && tone !== 'setback') {
    music = 'afterlight'
  }
  return { room, music }
}

export function outcomeCue(
  chapter: string,
  scene: string,
  choice: string,
  nextScene: string,
  tone?: Score,
): StoryCue | undefined {
  if (scene === 'reel_mix' && choice === 'cut_ad' || scene === 'face_settle' && nextScene === 'face_platform') return 'held_breath'
  if (chapter !== 'witness_deng_xiaoping') return tone
  if (scene.startsWith('night_loss_') || nextScene.startsWith('night_loss_')) return
  if (
    (scene === 'night_supper' && choice === 'music') ||
    (scene === 'night_coach' && choice === 'clockwork')
  )
    return 'kitchen_waltz'
  return tone
}

export function linesOfSpeech(paragraph: string) {
  // Surrounding narration, punctuation and the author's paragraph boundaries stay intact.
  return paragraph.split(/(“[^”\n]+”)/u).filter(Boolean)
}

type Setting = { year: string; place: string }

export function sceneSetting(
  chapter: string,
  scene: string,
  title: string,
  original: Setting,
): Setting {
  if (scene.startsWith('reel_')) {
    const place = ({reel_yard:'北京 · 小院',reel_shop:'北京 · 家具店',reel_truck:'北京 · 礼堂门口',reel_kitchen:'北京 · 灶间',reel_landing:'北京 · 楼梯间'} as Record<string,string>)[scene]
    return {year:'架空的1992年',place:place ?? '北京'}
  }
  if (scene.startsWith('face_')) {
    const place = ({face_quay:'北京 · 通州码头',face_bench:'北京 · 墙根',face_platform:'北京 · 车站',face_letter:'北京 · 印铺'} as Record<string,string>)[scene]
    return {year: scene === 'face_letter' ? '1919年立秋' : '1919',place:place ?? '北京 · 喜棚'}
  }
  if (chapter === 'witness_bian' && scene.startsWith('sky_')) {
    const dates: Record<string, string> = { 一幕: '1966', 二幕: '1972', 三幕: '1978', 四幕: '1986' }
    return { year: dates[title.split(' · ')[0]] ?? original.year, place: '北京' }
  }
  if (chapter === 'witness_zhang_xueliang' && scene.startsWith('xian_')) {
    if (scene === 'xian_future_port') return { year: '架空的1945年', place: '海外港口' }
    if (scene === 'xian_future_trial') return { year: '架空的1946年', place: '探视日' }
    if (scene === 'xian_future_square') return { year: '架空的春天', place: '西安' }
    const places: Record<string, string> = {
      xian_bench: '南京',
      xian_hall: '南京',
      xian_steamer: '上海码头',
      xian_purse: '船上',
      xian_harbor: '海外港口',
    }
    return { year: '1936年冬', place: places[scene] ?? '西安' }
  }
  if (chapter === 'witness_deng_xiaoping') {
    if (['city_frequency', 'workers_budget'].includes(scene))
      return { year: '架空的1992年', place: scene === 'city_frequency' ? '地方电视台' : '厂区' }
    if (scene.startsWith('night_') && /^[四五]幕/.test(title))
      return {
        year: '架空的1992年',
        place: scene.startsWith('night_loss_') ? '北京' : '北京 · 十七线',
      }
  }
  if (chapter === 'witness_entrance_exam') {
    if (scene === 'night_course') return { year: '架空的1985年', place: '夜校' }
    if (scene.startsWith('air_')) {
      if (['air_letter', 'air_mother', 'air_curtain', 'air_after'].includes(scene)) {
        const places: Record<string, string> = {
          air_mother: '姜家',
          air_curtain: '剧团后台',
          air_after: '借衣处',
        }
        return { year: '架空的1997年', place: places[scene] ?? '收信处' }
      }
      if (['air_factory', 'air_fitting'].includes(scene))
        return { year: '架空的1985年', place: scene === 'air_factory' ? '制衣厂' : '裁缝铺' }
      return scene === 'air_dorm'
        ? { year: '架空的1978年', place: '大学' }
        : { year: '架空的1977年', place: '县城' }
    }
  }
  if (chapter === 'witness_shanghai_prices' && scene === 'tram_map')
    return { year: '半年后', place: '上海 · 电车沿线' }
  return original
}
