const televisionScenes = new Set(['studio', 'switchboard', 'cutting_room', 'summer_broadcast', 'city_frequency'])
const sharedArt: Record<string, string> = {
  witness_liu_qingshan: 'river_grain',
  witness_xiaogang: 'household_field',
}

const screening = new Set(['night_screen', 'night_eye', 'night_frame','night_reel'])
const garage = new Set(['night_depot','night_punch','night_window','night_platform','night_contract','night_lease','night_empty','night_last','night_coach'])
const tailorBench = new Set(['air_store', 'air_cut', 'air_monitor', 'air_button', 'air_list', 'air_class', 'air_factory', 'air_fitting'])
const backstage = new Set(['air_curtain', 'air_mother','air_letter','air_after'])

export function picture(id: string, scene = '') {
  if (scene.startsWith('birthday_')) {
    if (id === 'may_fourth') return '/chronicle/family_quilt.webp'
    if (id === 'nantao_refuge') return '/chronicle/family_kitchen.webp'
    if (id === 'gold_yuan') return '/chronicle/family_room.webp'
  }
  if (id === 'witness_gao' && scene === 'bank_serial_table') return '/chronicle/serial_table.webp'
  if (id === 'witness_gao' && scene.startsWith('bank_')) return '/chronicle/bank_ridge.webp'
  if (id === 'witness_zhang_xueliang' && scene.startsWith('xian_')) return '/chronicle/xian_chairs.webp'
  if (id === 'witness_bian' && scene.startsWith('sky_')) return '/chronicle/sky_yard.webp'
  if (id === 'witness_entrance_exam' && scene.startsWith('air_')) {
    if (backstage.has(scene)) return '/chronicle/coat_theatre.webp'
    if (tailorBench.has(scene)) return '/chronicle/coat_pattern.webp'
    return '/chronicle/coat_trial.webp'
  }
  if (id === 'witness_shanghai_prices') {
    if (['tram_night', 'tram_run', 'tram_dawn'].includes(scene)) return '/chronicle/tram_dining.webp'
    if (scene === 'rice' || scene.startsWith('tram_')) return '/chronicle/shanghai_tram.webp'
  }
  if (id === 'witness_deng_xiaoping') {
    if (screening.has(scene)) return '/chronicle/night_screen.webp'
    if (garage.has(scene)) return '/chronicle/night_depot.webp'
    if (scene.startsWith('night_loss_')) return '/chronicle/witness_deng_xiaoping.webp'
    if (scene.startsWith('night_')) return '/chronicle/night_exchange.webp'
    if (televisionScenes.has(scene)) return '/chronicle/beijing_live.webp'
  }
  return '/chronicle/' + (sharedArt[id] ?? id) + '.webp'
}

export function pictureCaption(chapter: string, scene: string) {
  if (chapter === 'witness_gao' && scene === 'bank_serial_table') return '情境插画 · 小莲给孙女当了一回尺'
  // These drawings depict a particular moment even when they accompany a later life.
  if (chapter === 'witness_bian' && scene.startsWith('sky_'))
    return '情境插画 · 1966年在院里画月亮的孩子'
  if (chapter === 'witness_zhang_xueliang' && scene.startsWith('xian_'))
    return '情境插画 · 1936年的西安谈判桌'
  if (chapter === 'witness_deng_xiaoping' && scene.startsWith('night_') && !scene.startsWith('night_loss_')) {
    if (screening.has(scene)) return '情境插画 · 床单上的旧胶片'
    if (garage.has(scene)) return '情境插画 · 当年十七线的车库'
    return '情境插画 · 唐棠值守的接线间'
  }
  if (chapter === 'witness_entrance_exam' && scene.startsWith('air_')) {
    if (backstage.has(scene)) return '情境插画 · 多年后的父女合奏'
    if (tailorBench.has(scene)) return '情境插画 · 丁小满的裁衣案'
    return '情境插画 · 天佑试穿少年时的蓝上衣'
  }
  if (chapter === 'may_fourth' && scene.startsWith('birthday_')) return '情境插画 · 费家给小圆缝的被面'
  return '年代情境插画'
}
