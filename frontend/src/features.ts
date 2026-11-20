export type Feature = {
  title: string
  setting: string
  pitch: string
  action: string
  image: string
  chapter: string
  opening?: string
  edition?: 'serial_v1'
  campaign: 'family' | 'witness'
}

export const features: Feature[] = [
  {
    title: '年代连演', setting: '五部长篇 · 西安到运城',
    pitch: '1936年，坐进张学良的会客室。六十多年后，走到山西一座只砌了半边的水池。你先后以张学良、王晶垚、邓小平和高勤荣的身份作决定。上一代留下的东西，会跟着你走到最后。',
    action: '从西安的第三把椅子开始', image: '/chronicle/xian_chairs.webp',
    chapter: 'witness_zhang_xueliang', edition: 'serial_v1', campaign: 'witness',
  },
  {
    title: '夜班来电', setting: '北京，1989年春',
    pitch: '女儿七岁生日前夜，一个父亲打进了直播间。他找自己的母亲，已经找了二十一年。今晚，你决定要不要让整座城听见。',
    action: '把话筒交给第一个来电的人', image: '/chronicle/night_exchange.webp',
    chapter: 'witness_deng_xiaoping', opening: 'night_line', campaign: 'witness',
  },
  {
    title: '借一只袖子', setting: '恢复高考，1977—1997',
    pitch: '一个不会写“袖窿”的裁缝学徒，寄来一只蓝袖子。她给主考官出了道题：做一件让少年拉完最后一弓的衣服。',
    action: '拆开裁缝学徒的布信封', image: '/chronicle/coat_trial.webp',
    chapter: 'witness_entrance_exam', opening: 'tailor_exam', campaign: 'witness',
  },
  {
    title: '空出来的第三把椅子', setting: '西安，1936年冬',
    pitch: '你请人作保，他却把茶碗往回推了半寸。换到他的椅子上，听听他敢为哪件事作证。这句话到了南京，还得有人当庭说出口。',
    action: '坐到谈判桌的另一边', image: '/chronicle/xian_chairs.webp',
    chapter: 'witness_zhang_xueliang', opening: 'third_chair', campaign: 'witness',
  },
  {
    title: '粉笔画不圆的月亮', setting: '北京的小院，1966—1986',
    pitch: '蒋禾说是一牙月亮，站在对面的阿砚偏说是圆的。你站进他们的鞋印，各画一张。这两张纸要是留得住，许多年后，还能拿来考考已经当老师的蒋禾。',
    action: '走进王晶垚和孩子们的小院', image: '/chronicle/sky_yard.webp',
    chapter: 'witness_bian', opening: 'sky_long', campaign: 'witness',
  },
  {
    title: '两回生日', setting: '市井家书，1919—1948',
    pitch: '小圆要出嫁了。街坊都问她从哪一家门出。两位母亲养大了她，连她的生日，也各自记着一个。',
    action: '去小圆家喝一杯喜酒', image: '/chronicle/family_quilt.webp',
    chapter: 'may_fourth', opening: 'two_birthdays', campaign: 'family',
  },
  {
    title: '半座水池', setting: '山西运城，渗灌工程调查',
    pitch: '从公路上看，六座水池都立着。绕到背坡，砌池子的泥瓦匠却求你先别发稿。还有七个人没拿到工钱。',
    action: '跟高勤荣走到水池背后', image: '/chronicle/bank_ridge.webp',
    chapter: 'witness_gao', opening: 'bank_long', campaign: 'witness',
  },
]
