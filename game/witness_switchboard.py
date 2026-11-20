"""The two callers and their optional 1992 reunions in the fictional Night Line."""

from copy import deepcopy

BAKER = "约在炉火熄前给罗师傅回电"
CONDUCTOR = "约在首班车前给冯巧回电"
PAPER = "孩子自己画的油纸招牌"
SLICE = "给晚班人留下的一角蛋糕"
BELL = "由乘客决定的一声车铃"
NAME = "冯巧用自己的口音报站"


def choice(key, label, result, destination, *, marks=(), requires=()):
    return dict(id=key, label=label, result=result, next=destination,
                marks=list(marks), requires=list(requires))


def echo(mark, body):
    return {"mark": mark, "body": body}


def with_switchboard(base_scenes):
    """Build a chapter-local copy so standard and serial editions can coexist."""
    scenes = deepcopy(base_scenes)
    index = {item["id"]: item for item in scenes}
    board = index["night_switchboard"]
    guests = (
        ("baker", "罗师傅", BAKER, "唐棠把回拨条压在搪瓷杯下。蛋糕房还亮着灯。"),
        ("conductor", "冯巧", CONDUCTOR, "唐棠把回拨条别在表带里。车场那头要在头班车开走前接着。"),
    )
    for original in tuple(board["choices"]):
        for guest_id, name, mark, receipt in guests:
            label = "阿年进直播间" if original["id"] == "public" else "让阿年单独跟唐棠说"
            board["choices"].append(choice(
                f"patch_{original['id']}_{guest_id}", f"{label}，收播后回拨给{name}",
                original["result"] + receipt, original["next"], marks=(*original["marks"], mark),
            ))

    immediate = [
        echo(BAKER, "昨夜收播，唐棠照约回过去，罗师傅把写坏的奶油字刮进自己嘴里。孩子只肯让爸爸付一个字的钱。师傅琢磨半天，说：那我垫另一个。女孩在后屋打了个喷嚏，原来她从爹出门就躲在这儿等。车场那一线已经收了。"),
        echo(CONDUCTOR, "昨夜收播才接通车场。冯巧在电话那边走了两步。她给爸爸留的不是一句问候，是新学的上岗报站。她头回念得太像别人，第二回带出了家乡口音。唐棠留了第二回。再给蛋糕房摇铃，已经打烊了。"),
    ]
    index["night_depot"]["echoes"].extend(immediate)

    for loss in (False, True):
        doorway = index["night_loss_autumn_glass" if loss else "night_platform"]
        bakery = "night_loss_patch_bakery" if loss else "night_patch_bakery"
        tram = "night_loss_patch_bell" if loss else "night_patch_bell"
        doorway["echoes"].extend([
            echo(BAKER, "台阶下面蹲着个捧蛋糕盒的胖子。罗师傅用鞋尖一顶，盖儿翘起一条缝。阿年家姑娘打里头掏出一张油纸，冲你招手：“当年电话我也听见了。来，帮我按一下这个角。”"),
            echo(CONDUCTOR, "街沿上停着一辆空车，售票员招呼你上来，叫出了你的姓。她是三年前托唐棠回电的冯巧。车座上搁着个硬壳小本，头一页写得像个小学生：爸，今天坐前排。"),
        ])
        doorway["choices"].extend([
            choice("visit_bakery", "蹲下来替小姑娘按住油纸，看看盒里是什么",
                   "罗师傅索性把围裙铺到台阶上。“您也蹲下，站着看都好，蹲下才看得见毛病。”", bakery, requires=(BAKER,)),
            choice("ride_with_feng", "坐进空车的前排，陪冯巧排一回首班",
                   "冯巧把车钥匙原样留在司机座上，顺手拉上车门。“咱不走。您坐我爸当年坐的地方。”", tram, requires=(CONDUCTOR,)),
        ])
        next_offer = "night_loss_autumn_stool" if loss else "night_contract"
        next_neighbors = "night_loss_autumn_stool" if loss else "night_lease"
        counter = "夏家的门洞" if loss else "旧售票亭"
        bakery_story = (
            f"盒里是个用碎蛋糕边垒起来的{counter}。奶油屋檐塌了半边，姑娘一点也不急，拿小勺在底下接着吃。"
            "罗师傅却急。街对面等着拍照，照片登出去，他的铺子够热闹一个月。\n\n"
            "三年前他借给小姑娘一角钱，替她写了个“家”。姑娘当时问得他没法答：怎么写几个字就算知道里头住了谁？"
            "今天她自己画了一整夜的油纸小牌，空了一扇窗。邻居可以写想说的话，嫌丑也可以揭走。"
            "罗师傅讲实话，裱花笔是她使的，蛋糕是他起五更打的。等车来的人更实在，问照完这蛋糕归谁吃。\n\n"
            "有人在马路对面举相机。姑娘想先给窗口贴牌，罗师傅想先给一早出门、赶不及拍照的人切一块。奶油顺着勺柄往下流。"
        )
        scenes.append(dict(id=bakery, title="四幕 · 会化的屋檐", body=bakery_story, choices=[
            choice("pin_paper", "替她挡一下镜头，让街坊先把纸牌写好", "纸上第一个字是个“借”。写字的说，他家那盏灯从这屋借走三年了，灯罩还在。等相片洗出来，蛋糕上只剩半边屋顶，那个歪字倒是清清楚楚。", next_neighbors, marks=(PAPER,)),
            choice("cut_slice", "把相机请到旁边，跟罗师傅先分掉缺口的一角", "头一块分给要去上晚班的人。小姑娘拿牙签往蛋糕里一插，纸片写着“已经有人吃过了”。等拍照的人过来，她终于肯跟那个缺了角的房子合个影。", next_offer, marks=(SLICE,)),
        ]))
        bell_story = (
            "冯巧把一本乘车小本放到前座。三年前她爸听了广播，特意来坐闺女头班车。到了他该下的站，他没动。"
            "她事后才知道，车一跑，后排根本听不清她费劲练的那套腔。可她爸不好意思说，还一路冲她点头。\n\n"
            "她走到你座位背后，又念了一次。一句叫卖，一句问谁买过票，前面有人开窗，后半个地名就飞了。"
            "隔壁座一位老人把她喊过来，提议到自己那站就让他拉一下铃。第二天就下车的人呢？姑娘指指喉咙，说还有个笨法子，她用从小叫惯的小地名再喊一遍，怕的是车队说她土。\n\n"
            "“爸那天多坐了四站。我光顾着高兴，以为他就是想多陪我一会儿。”她递来那本子，要你帮她把明天的办法记在头页。"
        )
        scenes.append(dict(id=tram, title="四幕 · 多坐了四站的人", body=bell_story, choices=[
            choice("pull_bell", "记下前排乘客的办法，让要下车的人摇一次手铃", "老人先替全车摇了一遍。冯巧叫他再来，他这才放轻了手。隔条过道试了三次，没惊醒怀里的娃，也能让她听见。", next_neighbors, marks=(BELL,)),
            choice("home_name", "请冯巧坐到最后一排，把自己的报站话念给她听", "她听你照着本子念，乐得直摆手，抢过本来。她用家里的叫法又喊了一遍。后车门那位一路没吭声的乘客接了下半句，果然是一个地方出来的。", next_offer, marks=(NAME,)),
        ]))

    after_reunion = [
        echo(PAPER, "窗边贴出一张油纸牌，背面还透着奶油印。写了“借”字的那家人果然把灯罩还来了。"),
        echo(SLICE, "迟到的夜班工塞来一只洗干净的小碟。那一角蛋糕是他跟女儿分着吃的，孩子嚷着要他把碟还给做蛋糕的姐姐。"),
        echo(BELL, "靠门的人从兜里拿出一只铜手铃，那是冯巧借给他的。老人用手掌托住铃口，他说这样摇时，睡着的小孩不会醒。"),
        echo(NAME, "有人冲门口喊了一声老地名。冯巧坐在最后面应声，刚想改口，又把家里那套叫法大大方方喊了一遍。"),
    ]
    for key in ("night_coach", "night_room", "night_loss_winter_counter"):
        index[key]["echoes"].extend(after_reunion)
    return scenes
