// Blocking notes for the illustrated stage. Each cue places someone physically
// in the shot. A correspondent, a name on paper and a voice on a telephone
// never acquire a second body by matching a word in the script.
type Cast = { player: string; other: string | null; otherFace?: string; playerFace?: string }
type Chapter = { player: string; partner: Record<string, string> }

function chapter(player: string, scenesByPartner: Record<string, string> = {}): Chapter {
  const partner: Record<string,string> = {}
  for (const [name, cues] of Object.entries(scenesByPartner)) {
    for (const cue of cues.split(/\s+/)) {
      if (Object.prototype.hasOwnProperty.call(partner,cue)) throw new Error('Duplicate stage cue: '+player+'/'+cue)
      partner[cue]=name
    }
  }
  return {player,partner}
}

const company: Record<string,Chapter> = {
  may_fourth: chapter('周禾',{
    街头学生:'forme desk_return',阿纪:'sorts',田嫂的女儿:'corner',邻居:'errand',田嫂:'reading',
    万守仁:'shadow_bill shadow_oil shadow_box',万小满:'shadow_tail shadow_terms shadow_pack',茶铺老板:'shadow_seats',
    小圆:'birthday_door birthday_morning face_shoes face_seat face_platform',沈玉枝:'birthday_soup',费二娘:'birthday_quilt',
    桂喜:'face_box face_lid face_screen face_bird face_settle face_bench',董掌柜:'face_laugh',门口的孩子:'face_door',
    董掌柜的随从:'face_sold',码头脚夫:'face_quay',印铺掌柜:'desk_inspect',
  }),
  shanghai_workers: chapter('钟至诚',{
    小钱:'sack coat desk_return',寻亲的母亲:'shutters',等雨的人:'kettle',顾嫂:'door',周芸:'evening',
    阿福:'lamp_claim lamp_tickets',白铁匠:'lamp_tin',阿绣:'lamp_stage',茶棚老师:'lamp_lessons',
    万小满:'lamp_farewell',来问信的女客:'desk_inspect',
  }),
  mukden_september: chapter('唐素琴',{
    父亲:'thimble window morning street desk_return',孙家的哥哥:'little_sleeve',赵伯:'basket',
    高百顺:'hands_threshold hands_terms hands_practice',阿筠:'hands_signal hands_sleeve',沈婆婆:'hands_stool hands_walk',
    取棉袄的老人:'desk_inspect',
  }),
  nantao_refuge: chapter('袁月芬',{
    候坐的老人:'benches desk_return',伢儿:'child names',梁嫂:'crock',阿婆:'night',方伯:'host',
    来取包袱的人:'bundle',万小满:'matinee_bowl matinee_terms matinee_after',小菊:'matinee_chestnut matinee_quiet',
    谭福根:'matinee_outside',小圆:'birthday_flour',金师傅:'birthday_work birthday_bowl',素娥:'birthday_nest',
  }),
  gold_yuan: chapter('季阿锦',{
    顾嫂:'measure sleeves desk_inspect desk_return',药铺伙计:'scraps',读报的顾客:'headline',队尾孩子:'queue',
    来兑定钱的老人:'receipts',万小满:'rights_hinges rights_drawers rights_terms',冯显荣:'rights_hall',取货伙计:'rights_small_sale',
    小菊:'rights_trial rights_permission',金素娥:'birthday_window',阿双:'birthday_counter',阿信:'birthday_peg birthday_seam',
    小圆:'birthday_guest',
  }),
  river_grain: chapter('柴素兰',{
    兰婶:'stove sack desk_return',桂枝:'bread payday bench hands_on_scale',领工:'supper',
    孩子:'winter boat_child',小六:'boat_lamp empty_bowls',许掌柜:'white_noodles split_stoves',母亲:'return_flour',
  }),
  school_album: chapter('顾兰',{
    小莺:'threshold shelf visit family entrust blue_stitch door_song siblings desk_return',老看门人:'kitchen',
    借相片的年轻人:'album',老同事:'loan',顾师傅:'sewing_box',小莺的弟弟:'spectacles pocket_song',
    退休老师:'late_visitor',孩子:'desk_inspect',
  }),
  household_field: chapter('冯巧',{
    母亲:'earth loom desk_return',赵婶:'seed visitor',牛倌:'bell',女儿:'harvest child_patch mill',卖雨鞋的摊主:'market',
    外乡亲戚:'next_spring',姑妈:'seed_cart one_hand water_rota rice_roof',
  }),
  june_workshop: chapter('赵海成',{
    小唐:'lathe coal desk_return',老钳工的儿子:'tool',打磨工的姐姐:'noon lamp desk_inspect',
    门口接电话的人:'phone',寻人的家属:'room',嫂子:'alley_stove supper_shift',孩子:'picture_book',老工人:'quiet_yard',
    同班女工:'named_visit',
  }),
  factory_minutes: chapter('沈仲林',{
    厂办主任:'shift deadline question move_out desk_return',宋梅:'home union_copy',车队老板:'dinner canteen_coupon night_dispatch',
    工头:'offer',新主任:'handover',母亲:'radiator',阿萍:'drivers_queue',老费:'sacked_driver',
  }),
  school_ground: chapter('向楠',{
    周师傅:'cones desk_return',体育委员:'corridor',监工:'drain',旧校友:'later old_students',店老板:'kettle',
    新器材员:'last_bell returned_jacket',器材商:'shoe_booth',供货人:'remittance',罗杏:'odd_sizes lost_runner',
    女儿:'home_budget',前任器材员:'desk_inspect',
  }),
  witness_tan_sitong: chapter('谭嗣同',{访客:'inn',送信人:'letter',求学人:'lessons',李闰:'reunion'}),
  witness_zhan_tianyou: chapter('詹天佑',{练习生:'platform shift opening apprentice',货商:'passengers',摄影师:'historic'}),
  witness_sun_yatsen: chapter('孙中山',{公署职员:'vote',参议员:'deputies',袁世凯:'south'}),
  witness_chen_duxiu: chapter('陈独秀',{记录员:'roll',来接的亲友:'september',家人:'summer'}),
  witness_gu_zhenghong: chapter('顾正红',{工友:'shift table ward',工人家属:'supper',顾家亲属:'loss'}),
  witness_shen_junru: chapter('沈钧儒',{辩护律师:'six benches december',史良:'outside all_free',家属:'hearing home_first'}),
  witness_zhang_xueliang: chapter('张学良',{
    谈判人:'xian',同行人:'luoyang',赵一荻:'transfer family long_years',
    南京来客:'xian_nanking_first xian_second_x xian_second_c xian_nanking_second',
    西安老同僚:'xian_xian_first xian_second_n xian_xian_second',许秋眉:'xian_civil_first xian_civil_second',
    厨子:'xian_supper',木匠老葛:'xian_fog xian_square',调停人:'xian_bargain',
    年轻旁听者:'xian_hall',船上乐师:'xian_steamer',船主:'xian_purse',商人:'xian_harbor',
    邀请的人:'xian_future_port',杨虎城:'xian_crack',
  }),
  witness_minnie_vautrin: chapter('魏特琳',{程瑞芳:'classroom roster rest',求助的妇女:'mat',来登记的人:'december',母亲:'reunite'}),
  witness_chongqing_talks: chapter('张治中',{毛泽东:'house',周恩来:'guests',教育界来客:'visitor',桂园来客:'step_aside'}),
  witness_shanghai_prices: chapter('蒋经国',{
    米店伙计:'rice',商界代表:'supply',列席居民:'hearing',莲生:'tram_dawn',阿伍:'tram_night tram_terms tram_run',
    老裘:'tram_barge tram_map',月娥:'tram_lane',
  }),
  witness_liu_qingshan: chapter('刘青山',{锁柱:'allowance kitchen repayment',乔师傅:'arrival'}),
  witness_lushan_peng: chapter('彭德怀',{与会代表:'measure walk',誊稿人:'letter',会务员:'meeting',办公室来人:'office',记账员:'audit'}),
  witness_lin_zhao: chapter('林昭',{妹妹:'table',朋友:'poem',家属:'names visit',值班人:'review'}),
  witness_bian: chapter('王晶垚',{
    卞仲耘:'morning early_care',孩子:'home_note',许萍:'threshold noon corridor',办公室老师:'staff',医务员:'clinic',
    教员:'next_term',蒋禾:'sky_day sky_yard sky_lamp sky_half sky_shift sky_gap sky_fog sky_close sky_last',
    阿砚:'sky_step',修钟师傅:'sky_stall',裁缝的女儿:'sky_stool',罗树:'sky_guest',罗树的儿子:'sky_far',
  }),
  witness_entrance_exam: chapter('邓小平',{
    查全性:'summer',丈夫:'calendar',师傅:'access',林朝安:'loose_wire swap_stools',
    姜天佑:'air_stage air_cut air_monitor air_button air_knot',钱老师:'air_store air_dorm',天佑母亲:'air_flash air_mother',
    丁家父亲:'air_class',矿工:'air_fitting',女儿:'form winter air_curtain',
  }),
  witness_hu_fuming: chapter('胡福明',{学生:'chalk',改稿人:'proof',夜校老师:'seminar'}),
  witness_xiaogang: chapter('严宏昌',{严立学:'dues',同队农户:'lamp meeting two_harvests',严金昌:'full'}),
  witness_yuan_geng: chapter('袁庚',{修理工:'ticket',装卸工:'garage',工资员:'backpay',班组工人:'team'}),
  witness_deng_xiaoping: chapter('邓小平',{
    接访人:'briefs',接待员:'forum',同学:'may',传达员:'law',梁桂兰:'heard',小许:'studio',
    女儿:'rent',秘书:'mandates',记录员:'minutes may_return',编稿人:'ownership',主持人:'switchboard',
    唐棠:'night_loss_autumn_tape reel_lobby reel_kitchen',乔师傅:'night_loss_june_dark',剪片员:'cutting_room',
    播音员:'night_coins',老司机:'night_depot',来认票的老太太:'night_punch',门房:'night_memo',
    唐守义:'night_reel night_return',当年的孩子:'night_eye',摄影师的儿子:'night_frame',修琴师傅:'night_harmonica',
    戴老花镜的街坊:'night_answer',乔素琴:'night_platform night_room night_supper',何鹏:'night_contract',阿年:'night_lease',
    调度员:'night_meeting',外地来客:'night_empty',老乘客:'night_coach',手臂受伤的陌生人:'night_loss_june_cup',
    阿年的女儿:'night_loss_june_birthday night_patch_bakery night_loss_patch_bakery',老板:'night_loss_autumn_glass',
    夏嫂:'night_loss_autumn_stool',冯巧:'night_patch_bell night_loss_patch_bell',
    桂枝:'reel_keys reel_booth reel_landing reel_morning reel_open',杏儿:'reel_hinge reel_yard',宣美芬:'reel_sale reel_ticket',
    卡车司机:'reel_truck reel_brass',送货员:'reel_shop',
  }),
  witness_southern_tour: chapter('陈锡添',{邓小平:'panorama',同事:'street',排版编辑:'galley'}),
  witness_shang_aiyun: chapter('尚爱云',{材料整理人:'supper',辩护人:'file',丈夫:'family',亲友:'door',熟人:'retrial'}),
  witness_gao: chapter('高勤荣',{
    乔秀英:'water field_demo readback bank_pump bank_fork bank_tail',第二户农民:'second_field',夜版编辑:'copy bank_layout',
    家人:'review years',女儿:'home bank_home',米三:'bank_mason bank_after',看管工:'bank_number',工人:'bank_wages',
    收料员:'bank_yard',池主:'bank_owner',接班记者:'bank_byline',
  }),
  witness_deng: chapter('邓世平',{体育老师:'inspection',总务处同事:'colleague',家属:'family'}),
  witness_xu_zhiyong: chapter('许志永',{学生:'morning',外地青年:'school',家属:'phone',记者:'august'}),
  witness_jiang_yanyong: chapter('蒋彦永',{科室同事:'colleagues',记者:'interview'}),
}

// Some sequences cut from the decision-maker to the people living with the
// decision. Their letters and telephones do not transport the player to them.
const cutaways: Record<string,Record<string,string>> = {
  witness_gu_zhenghong: {'loss':'工友'},
  witness_deng: {'silence':'邓家亲属'},
  witness_entrance_exam: {
    calendar:'邵梅',access:'邵梅',form:'邵梅',later:'邵梅',winter:'邵梅',bench:'邵梅',loose_wire:'邵梅',
    swap_stools:'邵梅',workshop_college:'邵梅',night_course:'邵梅',
    air_stage:'丁小满',air_store:'丁小满',air_cut:'丁小满',air_monitor:'丁小满',air_button:'丁小满',
    air_flash:'丁小满',air_knot:'丁小满',air_list:'丁小满',air_dorm:'丁小满',air_class:'丁小满',
    air_factory:'丁小满',air_fitting:'丁小满',air_letter:'丁小满',air_mother:'丁小满',air_curtain:'姜天佑',air_after:'丁小满',
  },
  witness_deng_xiaoping: {
    label:'小许',forum:'梁桂兰',may:'小许',law:'小许的母亲',heard:'小许',rent:'梁桂兰',studio:'梁桂兰',
    switchboard:'梁桂兰',cutting_room:'梁桂兰',workers_budget:'梁桂兰',city_frequency:'外地女工',civil:'小许',
    night_coins:'值班编辑',night_screen:'唐棠',night_return:'唐棠',night_supper:'阿年',night_room:'来取录音的老人',
  },
}

// County cutscenes arrive as localized titles in old saves and as keys in action previews.
const cinemaCast = chapter('',{
  '冉卉':'foyer booth offer crowd family month kept 六排四座站着个人 门缝底下露着一只鞋 三千块买哪句话 取号纸从中间撕开 妈妈没回头的那天 小窗里面的票要不要收 最后一个付钱的人',
  '冯香':'old_ticket spool returned home 椅子底下刻的是工资 从哪一格重新放 一张真正的退票 哪天在街上再碰见',
  '小柳':'paid ordinary open 你自己的脸比银幕还亮 凳子空着也会响 那一排开着灯',
  '柳家的孩子':'chair 柳家的座位能不能坐',
})
const busCast = chapter('',{
  '伍琴':'curb cab deed dispatch_rehearsal dispatch_live dispatch_platform canal dispatch_late end_lantern 车门只开了一半 空车也要报满 路在地契上吗 把表拨给我听 末班车，等哪一分钟 还剩七分钟 早先修的那条路 接班车的尾灯 有人举着灯',
  '马素芹':'shoes shift microphone 一双鞋走了两趟 一个没赶上的人 她自己说了名字',
  '陆经理':'last_stop morning settle end_count 末班车的来信 这碗钱谁付 月底是什么意思 一趟是一趟',
  '老杜':'tin end_contract 红铁盒里有什么 小满开始发工资',
  '护工':'punch dark_walk 缺了一角的月牙 一个人的叫醒服务',
  '小海':'van trial turn end_light 没有车标的七路 会移动的灯 卷帘门头一次升到顶 灯下留一把空椅',
  '小满':'account daughter fare end_chalk counter_riders counter_van proof 签字的那只手 小满认四张 凭哪半张兑钱 可以擦掉的数字 有人不等于有大巴 三趟油钱不等于三次领款 成对的证据',
  '库管':'keys chorus 挂钩里的白漆 两个话筒只有一个响',
  '末班乘客':'walk 最后两百米',
  '换班工友':'bridge_stop 两站之间',
  '老张嫂子':'widow end_north 针线筐里的一张存折 多出来的四百七十米',
  '复核员':'inquiry 第一笔和最后一笔',
  '接班车司机':'dispatch_doors 别把这两分钟花了',
})

const types: Record<string,string> = {}
function assign(face:string,actors:string) {
  for(const actor of actors.split(' ')) types[actor]=face
}
// Roles without a photographic source use the fictional company's faces.
// Props, collars, period clothing and scene lighting are handled by the stage.
assign('man-young','周禾 阿纪 小许 小钱 工友 锁柱 练习生 读报的顾客 学生 林朝安 外地青年 来客 候车乘客 夜班工人 记录员 阿信 学徒 码头脚夫 接班记者')
assign('apprentice','桂喜 阿福 阿双 摄影师的儿子 老钳工的儿子 供货人 小六 阿伍 店伙')
assign('teen-boy','少年工 姜天佑 阿砚 体育委员 孙家的哥哥 罗树的儿子')
assign('boy','孩子 门口的孩子 伢儿 队尾孩子 小莺的弟弟 当年的孩子 厨房学徒')
assign('girl-child','田嫂的女儿 小菊 莲生 阿年的女儿 杏儿 女儿')
assign('girl','阿筠 小莺 蒋禾 罗杏 金素娥 素娥 裁缝的女儿')
assign('woman-young','唐素琴 冯巧 小圆 许萍 阿绣 同班女工 妹妹 赵婶')
assign('seamstress','丁小满 万小满 邵梅 袁月芬 小唐 周芸 李闰 年轻母亲')
assign('woman-mid','季阿锦 顾兰 唐棠 宣美芬 母亲 月娥 许秋眉 宋梅 顾嫂 史良 程瑞芳 阿萍 同事的妻子 女客')
assign('fish-counter','柴素兰 梁桂兰 乔秀英 桂兰 秀英 锦嫂 家属 嫂子 费二娘 金师傅 打磨工的姐姐 外地女工')
assign('woman-elder','桂枝 聂桂枝 乔素琴 乔师傅 沈婆婆 兰婶 阿婆 退休女教师 天佑母亲 来认票的老太太')
assign('granny','沈玉枝 姑妈 小许的母亲 蒋家母亲 夏嫂 阿年母亲')
assign('fish-counter','冉卉 伍琴')
assign('granny','冯香 老张嫂子')
assign('woman-young','小满')
assign('woman-mid','马素芹')
assign('apprentice','小海')
assign('man-elder','老杜')
assign('boy','柳家的孩子')
assign('man-mid','小柳 陆经理 钟至诚 沈仲林 高勤荣 王晶垚 邓世平 阿年 工头 冯显荣 老裘 何鹏 商人 接待员')
assign('driver','赵海成 向楠 高百顺 卡车司机 老司机 米三 木匠老葛 修理工 工人 泥瓦匠 牛倌 顶班司机 体育老师')
assign('man-elder','父亲 赵伯 方伯 老看门人 顾师傅 老冯 严金昌 老工人 退休老师 老费 唐守义 老乘客')
assign('puppet-master','万守仁 印铺掌柜 董掌柜 师傅 老同僚 修钟师傅 修琴师傅 茶铺老板 库管')

const historicalNames = new Set(Object.entries(company).filter(([key])=>key.startsWith('witness_')).map(([,ch])=>ch.player))
for (const n of ['毛泽东','周恩来','胡耀邦','赵紫阳','李鹏','蒋介石','袁世凯','卞仲耘','丁子霖','杨虎城','史良','查全性','程瑞芳']) historicalNames.add(n)

function face(name:string,chapterId:string,scene:string):string|undefined {
  // The portrait library owns the likeness of a named historical figure.
  if (historicalNames.has(name)) return undefined
  if (name==='小圆' && chapterId!=='may_fourth') return 'woman-mid'
  if (name==='桂枝' && chapterId==='river_grain') return 'seamstress'
  if (name==='万小满' && chapterId==='gold_yuan') return 'fish-counter'
  if (name==='小菊' && chapterId==='gold_yuan') return 'woman-young'
  if (name==='蒋禾' && /^sky_(gap|guest|fog|comet|far|close|rain|last)$/.test(scene)) return 'seamstress'
  if (name==='小莺' && scene==='siblings') return 'woman-mid'
  if (name==='姜天佑' && scene==='air_curtain') return 'man-mid'
  if (name==='乔师傅') return chapterId==='witness_liu_qingshan'?'man-elder':'woman-elder'
  if (types[name]) return types[name]
  if (/祖母|阿婆|老太|婆婆/.test(name)) return 'granny'
  if (/姐姐|姑|女工|妇女|母亲|娘|女客|女教/.test(name)) return 'woman-mid'
  if (/孩子|男孩|幼童/.test(name)) return 'boy'
  if (/女孩|小姑娘/.test(name)) return 'girl-child'
  if (/姑娘|女儿/.test(name)) return 'woman-young'
  if (/退休|老人|老工|老同|老会/.test(name)) return 'man-elder'
  if (/年轻|学生|校友|学徒|青年/.test(name)) return 'man-young'
  if (/司机|工人|脚夫/.test(name)) return 'driver'
  return 'man-mid'
}

export function directedCast(chapterId:string,scene:string,role:string,body:string):Cast {
  const id=chapterId.replace(/^serial_v1\//,'')
  const county = ['aftershow','county-cinema','county/aftershow'].includes(id)
    ? cinemaCast : ['night_bus','county-bus','county/night_bus'].includes(id) ? busCast : undefined
  const ch=company[id] ?? county
  // Outside a rehearsed scene, the actual player's role is the only reliable credit.
  let player=ch?.player || role.split(/[，·]/u)[0]?.trim() || '你'
  let other:string|null=ch?.partner[scene] ?? null
  player=cutaways[id]?.[scene] ?? player
  if(id==='witness_deng_xiaoping' && scene.startsWith('night_') && !cutaways[id]?.[scene]) {
    player='唐棠'
  }
  if(id==='witness_deng_xiaoping' && scene==='civil') other='小许的母亲'
  if(id==='witness_deng_xiaoping' && scene==='night_switchboard') other=null
  if(id==='witness_gao' && scene==='bank_ridge' && body.includes('泥瓦匠')) other='米三'
  if(other===player) other=null
  const cast:Cast={player,other}
  const primary=face(player,id,scene)
  const partner=other?face(other,id,scene):undefined
  if(primary) cast.playerFace=primary
  if(partner) cast.otherFace=partner
  return cast
}
