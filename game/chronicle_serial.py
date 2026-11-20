"""Five full witness stories played as one edition, with its own portable manifest."""

from game.witness_bian_sky import MOVE, TOUCH
from game.witness_xian_chairs import CIVIL

SERIAL_EDITION = "serial_v1"
# Original chapter and scene IDs keep source notes, images and the sound score in sync.
SERIAL_STAGES = (
    ("witness_zhang_xueliang", "xian_wait"),
    ("witness_bian", "sky_day"),
    ("witness_entrance_exam", "air_begin"),
    ("witness_deng_xiaoping", "night_switchboard"),
    ("witness_gao", "bank_ridge"),
)

PATTERN = "袖样·三种公开纸样"
FIT = "袖样·量体的师傅"


def echo(mark, body):
    return {"mark": mark, "body": body}


def serial_chapters(witness):
    chapters = []
    scenes = {}
    for chapter_id, first in SERIAL_STAGES:
        source = witness.chapters[witness.indices[chapter_id]]
        chapter = source.model_dump(exclude={"scenes"})
        # The edition starts at the selected long story, even if a normal save can
        # reach that story by another entrance. Copy before adding edition-only events.
        prefix = first.split("_", 1)[0] + "_"
        levels = {scene.id: scene.model_dump() for scene in source.scenes if scene.id.startswith(prefix)}
        chapter["scenes"] = [levels.pop(first), *levels.values()]
        scenes.update({scene["id"]: scene for scene in chapter["scenes"]})
        chapter["history"] += " 《年代连演》中苏小莲及其家人的经历、旧衣和来往信件均为虚构。各篇从所示年份开场，晚年的场景是本篇人物的后日谈。"
        chapters.append(chapter)

    scenes["xian_wait"]["body"] = (
        "西安，1936年12月。史实中，张学良亲自陪蒋介石去了南京。在这一局里，我把人送到飞机跟前，自己留了下来。\n\n"
        + scenes["xian_wait"]["body"]
        + "\n\n门边还有个扎歪辫的小姑娘，是替裁缝许秋眉送针线的。她叫苏小莲，今年八岁，正把两根冻红的手指伸进我的衣袋。许师傅让她把手拿出来，她却摸出半把花生壳：“我就说这里头没锁。”"
    )
    scenes["air_begin"]["body"] = (
        "1977年8月。院墙上那轮粉笔月亮的故事先搁在这里。北京的科教工作座谈会散了，邵梅把隔壁裁缝店的布信封捎进来。封里只有一只袖子。\n\n"
        + scenes["air_begin"]["body"]
        + "\n\n信封底下垫着一角旧账纸。收件人的名字写在横线上面，下面歪歪扭扭地算着八分钱葱、三分醋，落款是“苏小莲”。四十一年过去，当初送针线的孩子如今给这家裁缝店管零碎账了。"
    )
    scenes["air_begin"]["echoes"].append(echo(
        CIVIL,
        "旧账纸翻过来，还有苏小莲给丁小满写的一行私话：“你要是不想去北京，我替你把回来那趟路费留着。”"
        "她记得自己八岁时，许师傅的丈夫被叫进了屋，第一次有人当面问他到底愿不愿随行。她不好意思把这个写在信里，只往柜台抽屉底压了两张钱。小满来借过一回，从没问过利息。",
    ))
    scenes["night_switchboard"]["body"] = (
        "1989年4月25日，北京。这条推演里，邓小平把今晚一段广播时间留给接线间。离午夜还有七分钟。\n\n"
        + scenes["night_switchboard"]["body"]
    )
    scenes["night_switchboard"]["echoes"].extend([
        echo(MOVE, "唐棠等着回话，拿脚尖把一张矮凳钩到桌子另一头。蒋禾上回来过，说学生光在老师站的地方看，一辈子也看不见自己那头缺了什么。唐棠真坐下试过一次。从这头够不到外线，于是他们给台里添了条长一点的线。今夜她能把电话递到门边由人自己接。"),
        echo(TOUCH, "工作灯一灭，唐棠照样摸得着两部电话。阿砚从前来替他们修铃，在外线听筒贴了块平胶布，内线贴了块带棱的。他小时候摸过一枚顶针，记到现在的是手先明白、眼睛才追上的那一刻。如今唐棠不用开灯，也能把阿年的话接下去。"),
    ])
    scenes["bank_ridge"]["echoes"].extend([
        echo(PATTERN, "秀英弯腰时，裤腰露出一截印着蓝格子的纸。她女儿从学校捎回过丁小满那三张公开的纸样，她没照做整条裤子，找了块旧面袋布，只照着做了个兜。兜口斜着冲下，蹲低了螺帽就掉。她答应今晚给小满写信，头一句已经想好了：“你那图上画的人，从来不蹲着干活？”"),
        echo(FIT, "秀英把找到的螺帽塞回一只小布兜。这兜口做得怪，贴近腰带，弯腰一摸就着。几年前她嫌工作裤抬不起腿，去找丁小满带出来的改衣师傅。师傅跟着她往井房走了一趟，裤子重裁了，顺手才添这只兜。螺帽是今早从坏了的水泵上掉下来的，兜里那一枚早借给隔壁了。"),
    ])
    for scene in chapters[-1]["scenes"]:
        for choice in scene["choices"]:
            if choice["next"] == "END":
                choice["next"] = "bank_serial_table"
    chapters[-1]["scenes"].append({
        "id": "bank_serial_table",
        "title": "尾声 · 手伸得进去",
        "body": (
            "几年后，高勤荣再到运城看乔秀英。吃过饭，院里还有张小桌没收。秀英替邻居苏小莲摆线轴，老太太手腕使不上劲，绕了两匝，线又滑下来。"
            "秀英让你拿拇指压住。老太太是从西安跟儿子搬来的，记性已经漏了好些事，偏记得小时候在一件大衣的口袋里摸出过花生壳。\n\n"
            "她孙女带了件新褂子来，让奶奶摸摸料。老太太两只手在上面找了半天，找不到口袋。孙女这才承认，为省一道工，铺子把那道口做成了假的。"
            "苏小莲忽然笑了：“我八岁就知道怎么验这个。”小姑娘问，那我下周带什么来？\n\n"
            "你本来应邀来写村里井房的后续，下午就得交稿。现在腾出这双手做什么，稿子上不会有一个字。"
        ),
        "echoes": [echo(CIVIL, "小满托人还过来的两张路费，苏小莲一直夹在账本里。如今早买不了一张车票，却是她留给孙女的第一笔学徒钱。她年轻时肯把钱留给一个可能中途回家的姑娘，这回也肯替孙女付学费，学到一半不喜欢就算了。")],
        "choices": [
            {"id": "serial_pocket", "label": "把手借给老太太当尺，请孙女学着给她缝个真正的口袋",
             "result": "她把你的手赶开了：“你手比我大。”最后是她把自己的手搁上去，孙女照着画，拇指旁边多留了一指。下回来信说，新口袋装过两枚鸡蛋，一枚也没破。", "next": "END",
             "marks": ["连演终章 · 能盛两枚鸡蛋的口袋"]},
            {"id": "serial_well", "label": "陪秀英去给下一家送井房钥匙，回来吃剩下的凉饭",
             "result": "你们回来的时候，两个人已经缝好了口袋。苏小莲从里头掏出一截葱，问秀英炒鸡蛋还用不用。你问谁教谁缝的，祖孙俩一齐把筷子伸到菜碗里，谁也没答你。", "next": "END",
             "marks": ["连演终章 · 回来时还有一碗饭"]},
            {"id": "serial_apprentice", "label": "替孙女给丁小满捎信，把当年的两张路费当作头一回学费",
             "result": "你来回跑了两趟。小满把那两张钱装在袖兜里来，第一课教怎么拆。小姑娘拆到一半跑去跟人打球，老太太一点没生气。饭前她又跑回来，把剩下的三针挑了。两张钱还在小满兜里，多年前答应能回头的一趟路，终于有人舍得走了。", "next": "END",
             "requires": [CIVIL], "marks": ["连演终章 · 两张路费教会的第一课"]},
        ],
    })
    return chapters
