"""The last screening at a fictional county cinema, alongside the regular career."""

from dataclasses import dataclass
from .catalog import DAY
from .world_common import action, visible_doc


@dataclass(frozen=True)
class Turn:
    key: str
    label: str
    to: str
    reply: str
    requires: str = ""
    money: int = 0  # Actual household balance, in cents.


@dataclass(frozen=True)
class Scene:
    act: str
    title: str
    body: str
    turns: tuple
    sound: str


def scene(act, title, body, sound, *turns):
    return Scene(act, title, body, turns, sound)


ONE = "第一幕　添一把椅子"
TWO = "第二幕　空出来的四秒"
THREE = "第三幕　散场灯"
FOUR = "尾声　三十天以后"
FEE = 300_000
C = Turn
SCENES = {
    "card": scene(ONE, "散场以后",
        "回声影院重新开门那天，有人把一张对折的旧票塞进你办公室门缝。票背面是铅笔字：“要是请你上台，你先看看六排四座。”", "foyer",
        C("attend", "带上这张票，去回声影院", "foyer", "门口的姑娘在票背面划了半道，摸到背后有字，忙把剩下半道咽进铅笔尖里。")),
    "foyer": scene(ONE, "六排四座站着个人",
        "影院门廊里的爆米花机转得很响，里面一颗玉米都没有。经理冉卉怕冷场，叫人一直开着。今晚她要卖一批认座卡，每张六百，拿卡一年看戏不用再买票。\n"
        "她把给你的红围巾抖开，掉下来一小截线头：“我小时候逃票，我妈拿这个绳头儿拴门。今天我掏钱买下来了，她还不肯坐。”\n"
        "六排四座旁边，老太太一手扶椅背，两只脚站在过道上。大银幕上映着三十年前的她，正弯腰给观众撕票。冉卉叫她“妈”。老太太说：“少套近乎。今天来的是售票员冯香。”", "foyer",
        C("mother", "站到冯香身边，问她怎么不坐", "old_ticket", "你侧着身子挤进第六排，椅面自己翻了回去，露出底下一行歪字。"),
        C("daughter", "跟冉卉去放映间，听她把价钱开出来", "booth", "冉卉拎着鞋爬铁楼梯。她说鞋跟细，卡进去过，上一回是她妈爬上来拽的。")),
    "old_ticket": scene(ONE, "椅子底下刻的是工资",
        "底下刻着个“柳”。老柳是当年搭屋顶的木工。影院断过三个月工资，馆里拿十一把椅子作抵，七个人肯要，四个人宁可等钱。冯香坐的是收款台，她一户户问，老柳的字还是她替刻的。\n"
        "“怎么只有一个字？”你问。她把椅面慢慢压下来：“六排四座老卡裙子。签完字，我拿小刀给他削平过，削剩个姓。”\n"
        "她从大衣里掏出柳家那张旧票，票背面留着擦过的铅笔印。冉卉隔着几排冲你举了一下信封。有人在给她妈化妆，冯香躲开了刷子。", "foyer",
        C("borrow_ticket", "带上柳家的旧票，再去见冉卉", "offer", "冯香把票对折了才递给你：“别人拿过角上会脏，给小柳留点干净的。”"),
        C("leave_ticket", "把票留在她手里，自己上楼", "offer", "她把票藏回袖口：“这回我要自己问她，用不着你替我说。”")),
    "booth": scene(ONE, "门缝底下露着一只鞋",
        "放映间的桌子可劲儿垫过，两份合同叠在一起，咖啡还朝左边流。冉卉把鞋跟塞进短桌腿下面，说她押上房子换幕布那天，签字的桌子也这么晃。\n"
        "“我出钱换过幕布。我妈欠老柳那点钱，三十年了都有人记得。等这场座卡卖了，我赔。”楼梯上咚的一下，门缝底下露出只黑布鞋。冉卉朝门外喊：“妈，我没说你欠！我说的是影院！”那只鞋慢慢退开。", "booth",
        C("fetch_mother", "追到楼梯口，听冯香讲讲那十一把椅子", "old_ticket", "冉卉把接下来的话留在屋里。你穿过前排一股燎头发的气味，又回到六排四座。"),
        C("stay_booth", "等冉卉把卖卡的钱够不够还账算清楚", "offer", "她拿钥匙在桌上划两道，到账、退卡各占一边。划到老职工时，钥匙只能放在中间。")),
    "offer": scene(ONE, "三千块买哪句话",
        "冉卉拉开一只装糖的抽屉。里面是旧电影的散场音乐带，还有一只红封，三千元。她想请你出镜，跟她同坐头排，念一句“县里有人看着，这卡买得放心”。\n"
        "“我确实要你帮我卖。我也确实能用这一晚的钱给十一家结旧账。”她说得太直，连你都替她往门口看了一眼。楼下有人练报幕，把“回声”两个字叫了三遍，一遍比一遍响。\n"
        "如果接钱，这三千进入你的个人积蓄。她也会在认座卡的宣传片里使用你今晚这张脸。你可以推开信封，依然进场；冯香在六排还给你留着地方。", "booth",
        C("take_fee", "收下三千元，答应给这场认座会站台", "paid", "钱进了你的个人账。摄影师给你脸侧补了一盏灯，冉卉把你的姓念给他听，让他把名字打大些。", money=FEE),
        C("stay_guest", "推回红封，今晚就坐普通观众席", "ordinary", "冉卉将三千元锁回去。你进场时她照样招呼，摄影师却跟着她去了另一扇门。")),
    "paid": scene(TWO, "你自己的脸比银幕还亮",
        "幕上的你还没说话，第一张六百元的卡就卖出去了。拿卡的小柳戴了副雾蒙蒙的眼镜，说老柳走时，他还不会签自己的名字，今天早到是想给爸爸买那把椅子。\n"
        "你念完那句广告词，冉卉按下播放。一段旧录像里，冯香低头数了十一个人，说：“他们愿意。”片子到这儿便切到你笑的那一帧。六排的老太太站起来了：“我后头有句话呢？”\n"
        "摄影师还对着你，冉卉把放映间的钥匙移到桌面上。你的三千块已经到账。", "turn",
        C("paid_listen", "当着买卡人的面去找那卷原带", "spool", "有个人跟你一起站起来，左右看看，又坐回去。他把刚买的卡攥弯了一角。"),
        C("paid_quiet", "先让广告播完，趁散场陪冯香去看原带", "spool", "银幕上第二遍响起你自己的声音。冯香看都没看，等最后一排的人走了才上楼。")),
    "ordinary": scene(TWO, "凳子空着也会响",
        "前排的人买了卡，起身去领免费的汽水，一排翻椅哗啦啦立了起来。银幕上是年轻的冯香在数人头：“他们愿意。”老职工跟小柳都看见椅背上的名字了。\n"
        "“我愿意买椅子，没说过愿意把工资搭进去。”有人喊。冉卉拿起话筒，开口喊的却是“妈”。她妈坐在下面，一句话都不接，只点了点放映间那个小窗。\n"
        "放映员把三盘带子摆在门槛上：“只能给你们腾一次换盘的工夫。下场儿童片的票也卖出去了。”", "turn",
        C("seat_with_mother", "陪冯香进放映间，让她自己找那句话", "spool", "她进门先把你的手从机器上拍开：“当年我还兼倒带呢。你坐。”"),
        C("seat_with_daughter", "叫冉卉一起来，把母女的说法放在同一卷里听", "spool", "冉卉磨磨蹭蹭走进来。她妈的膝盖抵在桌子底下，桌面比刚才平了。")),
    "spool": scene(TWO, "从哪一格重新放",
        "机轴上搭着一根断发。冯香指着画面里扎短辫的人：“这儿我是对卖瓜子的小江说话。你别只听声，先看我脸朝哪儿。”\n"
        "原带从售票窗一直收到散场。第一段讲的是赊给影院的钱，第二段是她女儿的犹豫，最后一段里只有老柳和一张空椅子。片子都留着，今晚的幕布只够给你们一段。你得亲手停在想让众人看见的地方。", "booth",
        C("show_wages", "把欠薪那四秒送上银幕", "crowd", "冯香在银幕上说完了：“愿意先开门，没说工资就这样算了。”散场的人又从门口折了回来。"),
        C("show_girl", "让全场听见年轻的冉卉怎么回答父亲", "family", "旧音箱里，小姑娘说想把妈妈领回家吃晚饭。现在的冉卉还站在幕前，一手攥着卖不掉的汽水瓶。"),
        C("show_empty", "请大家静一静，把空椅子的镜头放完", "chair", "三十一秒，一个字都没有。画面快黑时老柳走进来，蹲下身，用手绢擦了擦自己的姓。")),
    "crowd": scene(THREE, "取号纸从中间撕开",
        "有人把刚买的卡扔上舞台，扔歪了，落在黑幕跟前。冉卉没有去捡，蹲在台沿把收据一撕两半。半张给退卡的人排号，半张留给还想留下的。\n"
        "小柳夹在两拨人中间。他想把爸爸的钱拿回来，也想保住周末带儿子看戏的地方。有人替他喊“退”，他用手背把那人的胳膊挡住。你带谁先走，明天排在窗前的就会是那一队。", "turn",
        C("refund_queue","陪第一批退卡的人，在玻璃窗前等到出票","month","你替第一个人按住翘起来的收据。今晚能退的只有当晚收的钱，老柳那一份排在后头。"),
        C("workers_first","让还有旧工资没结的人先来，陪新买卡的人等","month","小柳报完数回过身，才看清等在他后面的姑娘早下班了。她为一张没退成的卡，多花了二十六块打车。")),
    "family": scene(THREE, "妈妈没回头的那天",
        "冉卉将那句话倒过去又放一次。她原以为父亲在幕外问她想要哪把椅子，今晚才听清问的是“你妈几点收工”。冯香坐在角落里，半只手搭在女儿背上，往前挪了两次没落下去。\n"
        "门外的人不肯走。有人想请老太太一户户点名说谁同意过；也有人说冉家母女已经占了整张幕，自己的脸连一秒也没上去。你要给下一个人递话筒了。", "foyer",
        C("give_worker","把话筒递给没在片里出现过的清洁工","month","她把话筒举到嘴边才发觉开关关着。她自己摸到开关：“那我把刚才那两句再说一遍。”"),
        C("give_mother","把最后一分钟还给冯香，让她自己跟女儿说","month","门外等录音的人散了。冯香第一次说自己那年留在影院，是因为这里有人夸她报幕好听。她女儿好长时间没抬头。")),
    "chair": scene(THREE, "柳家的座位能不能坐",
        "老柳的儿媳抱着孩子从最后一排走来。孩子好奇椅面为什么翻起来，伸手一按，卡住了领口上一粒塑料扣。众人七手八脚替他弄开。\n"
        "“爸爸讲过爷爷做了把椅子。拿回家行不行？”孩子问。冉卉说答应了头一家，就得答应十一家。其余座位还坐着人。小柳脸都红了，抓着椅背：“给我爸挂块牌也行啊。”", "foyer",
        C("lift_chair","跟柳家抬走六排四座，空下来的地方今晚就空着","month","几个人拧下椅脚，谁都没顾上拍照。小孩趴在椅面上过了大门，到家前已经睡熟。"),
        C("hang_name","请小柳亲手写上父亲的全名，把座位继续留给观众","month","小柳写完，又把‘木工’两个字添在姓名后头。原来他家谁也没叫过爸爸师傅。")),
    "month": scene(FOUR, "小窗里面的票要不要收",
        "一个月后，你收到两张周五场的手写票。没座号，也没盖章。散场后放映员从里面给你开了小窗。\n"
        "冉卉把那卷带子分在两个纸盒里。一个写着“留给后辈”，另一个没有字。小柳站在门外，他今天要问你，在这影院里，你到底是个什么人。", "after"),
    "returned": scene(FOUR,"一张真正的退票",
        "你把出镜费全额退回。小柳去买票，窗口的人照样收了六百。那天的镜头仍在别人手机里，一退钱它也没跟着消失。\n"
        "散场音乐放到一半，冯香隔着玻璃给你看了两张手写票。她没把票递过来，只拿铅笔在上头各划了一道。她说等你真想来看戏，再照价买一张。", "after"),
    "kept": scene(FOUR,"最后一个付钱的人",
        "三千块仍在你个人账上。冉卉下次做广告，依约可以用那张照片；她把新印的卡递给你，你的脸小了一点，还是在上面。\n"
        "小柳看完这张新卡，掏六百买走最上面的一张。他用指甲把你脸上的金粉刮掉，留了个灰印：“留着吧。哪天有人问我，别又成了我记错。”他自己开的侧门，没替你扶住。", "after"),
    "open": scene(FOUR,"那一排开着灯",
        "你把那张手写票换成了一场老职工自己剪的片。第一场只有十七个人来看，包括你。银幕上小柳把木工两个字写歪了，台下有人笑，他也跟着笑。\n"
        "快收尾时冉卉想关灯好让大家鼓掌。冯香却让最后一排那盏亮着，有人下夜班来看半场，黑黢黢的找不着座。", "after"),
    "home": scene(FOUR,"哪天在街上再碰见",
        "你把票装进没有盖章的纸盒。冉卉没有留你，捡了两把碎爆米花给小柳家的孩子装口袋。\n"
        "小半年后你在市场碰见冯香。她摊子上卖旧碟，放的是儿童片。她看了你好一阵才记起来，递来个小板凳，说想坐就坐。那天下午她一个字也没提县里的事。", "after"),
}

FINALS = (
    C("repay", "把三千元出镜费全退回去，请小柳看银行回执", "returned",
      "个人积蓄划出三千元，票房给你开了具名退费回执。", "take_fee", -FEE),
    C("keep", "告诉小柳这笔钱你收了，也准备留下", "kept",
      "你把账上的数报给小柳。他在票背面写下日期，笔尖从薄纸顶到了手指头。", "take_fee"),
    C("screen_workers", "以普通观众的身份帮老职工排一场自己的片", "open",
      "周五晚黄金场还得卖票。冉卉肯匀出早场，谁剪片子，她交给老职工自己定。", "stay_guest"),
    C("close_reel", "把原带交回两家，向冯香道一声晚安", "home",
      "小柳收了铁盒，冯香自己提走录音带，放映间只剩一截擦机布。", "stay_guest"),
)
ECHOES = {
    "spool": {
        "borrow_ticket": "你手里的旧票对着灯能看见椅脚的锈印。冯香把片头晃动的镜头停下，你们对出了同一个‘柳’字。",
        "paid_quiet": "楼下人去了一半。广告词已经播完三次，留下的人把空椅子往一块儿挪，想听个清楚。",
        "seat_with_daughter": "母女俩并肩坐着。冉卉伸手想把妈妈毛衣上的线头剪掉，手又放了回去。",
    },
    "month": {
        "refund_queue": "先退卡的姑娘这回又来了，拎着两杯豆浆。她把一杯塞给窗口当班的人。小柳还在等他爸的钱，喝的是家里带来的凉水。",
        "workers_first": "老柳的三个月旧账终于结清。小柳把爸爸生前爱吃的一小袋酥糖放到票窗。上次没赶上公交的姑娘来取了钱，拒绝了他给的糖。",
        "give_worker": "打扫卫生的江姨在领你们看挂工号的木板。她的名字如今排在售票员下面，一天六十块工钱，一笔也没吞。她还是自己开的麦克风。",
        "give_mother": "冯香带来了母女俩头一张合照，搁在窗台。江姨路过时扫了一眼：“又是她家。”你给她让座，她拎着畚箕走开了。",
        "lift_chair": "六排四座成了一片空地。小柳推来坐轮椅的邻居，量好宽度后，发现过道还差半个巴掌。他们留在最边上看完了。",
        "hang_name": "木工柳世友的名牌擦得锃亮。可第二家已经来问自己的那把怎么没有名字，冉卉只好搬着凳子陪人一道对过去。",
        "take_fee": "小柳把手机屏幕朝向你。画面里你还在头排替人说放心，话底下标着二十七次转发。他问的那句话，冉卉也听见了：“你说这话时，拿的谁的钱？”",
        "stay_guest": "上回红封原样锁回抽屉，账本里给你的出场费一栏空着。冉卉仍留着那条红围巾，这次给冻红鼻头的孩子绕了两圈。",
    },
}
WAITS = {"foyer": 105, "month": 30 * DAY}
RENDEZVOUS = {"foyer": "回声影院开场", "month": "回声影院 · 一个月后的手写票"}


def _turns(node):
    return FINALS if node == "month" else SCENES[node].turns


def options(d):
    arc = d.get("aftershow", {})
    if arc.get("due") is not None:
        return []
    node = arc.get("node", "card")
    return [action("aftershow", t.label, SCENES[node].title, "私人积蓄 " + ("+3000 元" if t.money > 0 else "−3000 元") if t.money else "",
                   "回声影院", {"scene": node, "choice": t.key})
            for t in _turns(node) if (not t.requires or t.requires in arc["history"])
            and d["family"]["savings"] + t.money >= 0]


def project(d):
    arc = d.get("aftershow", {})
    node = arc.get("node", "card")
    s = SCENES[node]
    if not arc and d["ended"]:
        return None
    due = arc.get("due")
    history = set(arc.get("history", ()))
    body = s.body.split("\n")
    body[1:1] = [line for key, line in ECHOES.get(node, {}).items() if key in history]
    if node == "foyer" and d.get("night_bus", {}).get("choices"):
        body.insert(1, "七路的伍琴探头看了一眼空转的铁锅。你跟她打招呼，她指指外头的车，说今天来接走夜场的司机，待不住。")
    if node == "ordinary" and "leave_ticket" in history:
        body.insert(1, "冯香把你留在她手里的票压到小柳掌心里。他翻到背面，看见他爸年轻时写的那个姓。")
    return {"node": node, "title": RENDEZVOUS[node] if due is not None else s.title,
            "act": s.act, "body": "" if due is not None else "\n".join(body),
            "reply": arc.get("last", ""), "due": due,
            "stage": "waiting" if due is not None else "invitation" if not arc else "playing" if _turns(node) else "ending",
            "sound": s.sound}


def act(d, kind, args, ctx):
    if kind != "aftershow":
        return False
    arc = d.setdefault("aftershow", {"node": "card", "history": []})
    choice = next(t for t in _turns(arc["node"]) if t.key == args["choice"])
    arc["history"].append(choice.key)
    arc.update(node=choice.to, last=choice.reply)
    ref = ctx.emit(choice.reply, title=choice.label)
    if choice.money:
        d["family"]["savings"] += choice.money
        visible_doc(d, "CIN-" + choice.key, "回声影院 · 出镜费" if choice.money > 0 else "回声影院 · 退费回执",
                    choice.reply, "冉卉", "散场以后", ref=ref)
    if choice.to in WAITS:
        delay = WAITS[choice.to]
        arc["due"] = ctx.minute + delay
        ctx.schedule("aftershow_meet", {"scene": choice.to}, delay, title=RENDEZVOUS[choice.to])
    elif not _turns(choice.to):
        s = SCENES[choice.to]
        final_ref = ctx.emit(s.body, title=s.title, refs=(ref,))
        visible_doc(d, "CIN-ending", s.title, s.body, "回声影院", "散场以后", kind="影片后记", ref=final_ref)
    return True


def complete(d, kind, payload, ctx):
    if kind != "aftershow_meet":
        return False
    arc = d.get("aftershow", {})
    if arc.get("node") == payload["scene"] and arc.get("due") == ctx.minute:
        del arc["due"]
        s = SCENES[arc["node"]]
        ctx.emit(s.body.split("\n")[0], title=s.title)
    return True


def validate(d):
    if "aftershow" not in d:
        return
    arc = d["aftershow"]
    if not isinstance(arc, dict) or not isinstance(arc.get("history"), list) or not arc["history"]:
        raise ValueError("影院行记没有开场。")
    seen = set()
    node = "card"
    for key in arc["history"]:
        t = next((t for t in _turns(node) if t.key == key and (not t.requires or t.requires in seen)), None)
        if t is None:
            raise ValueError("影院行记的选择与当时经历不符。")
        seen.add(key)
        node = t.to
    if arc.get("node") != node or not isinstance(arc.get("last"), str):
        raise ValueError("影院行记缺少有效的最近选择。")
    if "due" in arc and (node not in WAITS or type(arc["due"]) is not int or arc["due"] < d["now"]):
        raise ValueError("影院赴约时间无效。")
