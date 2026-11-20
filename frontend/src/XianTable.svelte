<script lang="ts">
  type Guest = 'nanking' | 'xian' | 'civil'
  type Choice = { id: string; label: string }
  type GuestCard = {
    name: string; seat: string; gesture: string; clue: string; asks: [string, string, string]
    replies: Record<string, string>; witness: string
  }
  export let sceneId: string
  export let choices: Choice[]
  export let marks: string[] = []
  export let disabled = false
  export let onChoose: (id: string) => void

  const guests: Record<Guest, GuestCard> = {
    nanking: {
      name: '南京来客', seat: '窗下的圈椅', gesture: '用指甲慢慢刮着碗沿',
      clue: '“我亲眼看见飞机离地。至于你们事先讲过些什么，我隔着整条跑道呢。你若一定要我签名，得容我把这句也写进去。”',
      asks: ['你从跑道上看见了什么？', '你肯保我一路平安么？', '哪一段是你没看见的？'],
      witness: '02',
      replies: {
        '01': '“看见飞机起了飞。”听到后半句，他把笔帽套回去，“可没看见你往后坐哪一架。”',
        '02': '他用左手把茶碗推开，腾出一小块地方。“这就好写了。先写我看见的，下面空四个字，写我不知道的。我拿这张去南京。保你出境那一份，你得找别人签。你肯给我一张纸吗？”',
        '10': '“先答应保你，再来问我看见什么？”他撂下茶盖，“那不管我瞧见什么，也得挑好听的写了。”',
        '12': '“连明天的车是往南还是往东，我都没瞧见。拿什么保你一路平安？”他只把你后半句记在了手心。',
        '20': '“开口就问我没看见什么，像在审一个人。”他伸手把笔拿近了一点，“我可以从那架飞机讲起，你再问我隔了多远。”',
        '21': '他用笔杆从桌这边量到另一边。“隔这么远，我也不敢保这碗茶到你手里还是烫的。”',
      },
    },
    xian: {
      name: '西安老同僚', seat: '灶边的歪椅', gesture: '把一只肉饺子裹进了油纸',
      clue: '“柏嫂替咱赊了一锅肉。你上来就说由你请，账上便再也找不回她。先把名字问准，再问我肯不肯带账去南京。”',
      asks: ['愿意把这本账带去南京吗？', '那盘肉赊在谁的名下？', '今晚的欠账我付，好么？'],
      witness: '10',
      replies: {
        '01': '“你先叫我带去南京，我还当你要我替你报功。”他抖开油纸，“先问欠谁的，我才好当着她的面点头。”',
        '02': '“带去销账，还是带去给你撑面子？”他把账本扣在膝上。灶后有人问肉饺子还给不给孩子。',
        '10': '“柏嫂。不是‘厨房’，是柏嫂。”他用笔端点着那两个字，问门外借了根绳，“柏嫂肯认，我就带账去南京。至于你走了谁来接手，今儿我可没工夫替你叫人来议了。把账还我？”',
        '12': '“你倒记住她了。”他把纸包递给学徒，“可你一开钱，她赊东西给咱们吃的那一笔，还算谁的？”',
        '20': '“先说你付，再叫我去。到了南京我只好给人讲少帅请过一顿饭。”他解开油纸包，又重新折了一次。',
        '21': '“账主听着呢。”他冲门外抬下巴，“你先替她把钱垫了，如今叫人怎么说是她赊的？”',
      },
    },
    civil: {
      name: '裁缝许秋眉', seat: '门边的小凳', gesture: '拿顶针抵住滚到桌边的钥匙',
      clue: '“这钥匙天天在我男人腰上。你得先叫他进屋，把钥匙拿回自己手里，再问他明天想站哪一边。他这辈子没空着手答过你。”',
      asks: ['我替你们两口子买票吧？', '明天你想坐哪一边？', '把车钥匙交我，好不好？'],
      witness: '21',
      replies: {
        '01': '她丈夫从门外接话：“票都替我买了，你还问我想往哪边坐？”许师傅用手背掩了一下嘴。',
        '02': '“两张票换一把钥匙？”她笑了，“你俩做了一桩生意。我男人还是少帅的司机，只不过换开到码头去。”',
        '10': '“我坐——”门里有人插话说票有人买，他便住了嘴。许师傅拿剪刀柄叩叩门框：“好容易挤出来的半句话，又给堵了回去。”',
        '12': '“问得早了一口气。”他举起钥匙，“它还在我手里，你问我愿不愿意，我嘴上除了愿意，还能说个啥？”',
        '20': '钥匙碰着桌面响了一声。他把手放进口袋，还没捂热，听见要给买票，又把手拿出来了。“少帅，先容我说一回呢？”',
        '21': '钥匙交到我手里。他反倒跨进门槛，把小凳转了半边。“我想坐在能让人问我话的地方。坐司机的位置，人人只会问我车在哪儿。”许师傅把针插回线轴里：“他去了南京，还上什么船？少帅，你也得少算一家。”',
      },
    },
  }
  const seatOrder: Guest[] = ['nanking', 'xian', 'civil']
  const seatKeys: Record<Guest, string> = { nanking: 'chair_n', xian: 'chair_x', civil: 'chair_c' }
  const terms: Record<Guest, [string, string, string]> = {
    nanking: ['西安·来客肯认跑道上那一眼', '西安·让获释与护送分开', '带走了削好的笔'],
    xian: ['西安·同僚肯带当晚的饭账', '西安·西安自己推继任人', '把饭账揣进了怀里'],
    civil: ['西安·司机肯带自己的钥匙出庭', '西安·跟来的人也能自己走', '把车钥匙放到了桌上'],
  }
  let sequence: number[] = []
  let spoken = ''
  let heard = false
  $: seatSelection = sceneId === 'xian_wait' || sceneId.startsWith('xian_second_')
  $: guest = sceneId.split('_')[1] as Guest
  $: person = guests[guest]
  $: isFirst = sceneId === 'xian_wait' || sceneId.endsWith('_first')
  $: options = choices.filter(choice => choice.id !== 'offer_word')
  $: offer = choices.find(choice => choice.id === 'offer_word')
  function seatChoice(who: Guest, options: Choice[]) {
    return options.find(choice => choice.id === who || choice.id === seatKeys[who])
  }
  function afterMeeting(who: Guest, carried: string[]) {
    const [witness, promise, object] = terms[who]
    if (carried.includes(witness)) return object
    if (carried.includes(promise)) return '已经把话定下了'
    return '起身去了饭厅'
  }
  function togglePhrase(index: number) {
    if (disabled) return
    sequence = sequence.includes(index) ? sequence.filter(i => i !== index) : [...sequence, index]
    spoken = ''
  }
</script>

{#if seatSelection}
  <section aria-label="三把椅子" class="negotiation">
    <header><h2>坐到谁的对面？</h2><span>{isFirst ? '晚饭前 · 还够谈两回' : '锅盖掀起来了 · 最后一回'}</span></header>
    <div class="seating">
      <div class="tabletop" aria-hidden="true"><i></i><i></i><i></i></div>
      {#each seatOrder as who}
        {@const chair = seatChoice(who, choices)}
        {@const card = guests[who]}
        {#if chair}
          <button class={'seat ' + who} aria-label={chair.label} {disabled} on:click={() => onChoose(chair.id)}>
            <small>{card.seat}</small><strong>{card.name}</strong><span>{card.gesture}</span>
          </button>
        {:else}
          <div class={'seat away ' + who}><small>{card.seat} · 空</small><strong>{card.name}</strong><span>{afterMeeting(who, marks)}</span></div>
        {/if}
      {/each}
    </div>
  </section>
{:else if person}
  <section class="negotiation interview" aria-label={'和' + person.name + '换座谈话'}>
    <header><h2>{person.name}坐到你对面</h2><span>{person.seat} · {isFirst ? '头一回' : '末一回'}</span></header>
    <div class="conversation">
      <button class="listen" aria-expanded={heard} {disabled} on:click={() => heard = !heard}>
        {heard ? '收起这段话' : guest === 'civil' ? '让她把话说完' : '让他把话说完'}
      </button>
      {#if heard}<p class="quote">{person.clue}</p>{/if}
      <p class="instruction">挑两句话，按你想问的先后开口。点已选的话可以收回。</p>
      <div class="phrases" role="group" aria-label="想问的话">
        {#each person.asks as phrase, index}
          <button class:selected={sequence.includes(index)} aria-pressed={sequence.includes(index)}
            disabled={disabled || (!sequence.includes(index) && sequence.length >= 2)} on:click={() => togglePhrase(index)}>
            <b aria-hidden="true">{sequence.includes(index) ? sequence.indexOf(index) + 1 : '·'}</b><span>{phrase}</span>
          </button>
        {/each}
      </div>
      <div class="speak">
        <button disabled={disabled || sequence.length !== 2 || spoken === sequence.join('')} on:click={() => spoken = sequence.join('')}>照这个次序问</button>
        {#if sequence.length === 2}<button class="reverse" {disabled} on:click={() => { sequence = [sequence[1], sequence[0]]; spoken = '' }}>两句换个先后</button>{/if}
      </div>
      <div aria-live="polite" aria-atomic="true">{#if spoken}
        <p class="quote response">{person.replies[spoken]}</p>
        {#if spoken === person.witness && offer}
          <button class="accept" {disabled} on:click={() => onChoose(offer.id)}>{offer.label}</button>
        {/if}
      {/if}</div>
    </div>
    <div class="settle"><h3>临起身，你把哪句话定下来？</h3>
      {#each options as choice}
        <button {disabled} on:click={() => onChoose(choice.id)}>{choice.label}<span aria-hidden="true">→</span></button>
      {/each}
    </div>
  </section>
{/if}

<style>
  .negotiation{color:#352c23;border:1px solid #b8a47d;background:#f5eddd;margin:1.15rem 0;font-size:1rem}
  header{display:flex;justify-content:space-between;align-items:baseline;gap:.4rem 1rem;flex-wrap:wrap;padding:.8rem 1rem;border-bottom:1px solid #c8b796}
  h2,h3,p{margin:0} h2,h3,.seat strong{font-family:"Songti SC","Noto Serif CJK SC",serif}
  h2{font-size:1.16em} h3{font-size:1.05em} header>span,.seat small{font-size:.78em}
  button{font:inherit;color:inherit;cursor:pointer} button:disabled{cursor:default}
  button:focus-visible{outline:3px solid #004f76;outline-offset:3px;z-index:1}
  .seating{position:relative;isolation:isolate;display:grid;grid-template-columns:1fr 1fr;gap:1.4rem 1.25rem;padding:1.2rem;background:#3e3029}
  .tabletop{position:absolute;z-index:-1;inset:18% 10% 23%;border:4px double #af815b;border-radius:48%;background:#694935;box-shadow:0 6px 0 #33241c}
  .tabletop i{position:absolute;top:54%;left:45%;width:13px;height:13px;box-sizing:border-box;border:3px double #b8a487;border-radius:50%;background:#ddc9a5}
  .tabletop i+i{left:51%;top:41%}.tabletop i+i+i{left:55%;top:58%}
  .seat{display:flex;flex-flow:column;justify-content:center;align-items:center;text-align:center;gap:.12rem;min-height:4.7rem;min-width:0;padding:.42rem .5rem;border:1px solid #c3aa80;background:#f3e4c7;box-shadow:0 .2rem 0 #2f201a;color:#32271c}
  .seat strong{font-size:1.12em;line-height:1.5}.seat span{font-size:.77em;line-height:1.4}.seat small{color:#6d5133}
  .seat.civil{grid-column:1 / 3;justify-self:center;width:53%}.seat.away{background:#463c31;border-style:dashed;color:#e3d3b9;box-shadow:none}.seat.away small{color:#ddcdae}
  .seat:not(.away):enabled:hover,.phrases button:enabled:hover,.settle button:enabled:hover{background:#ffefd1}
  .conversation,.settle{padding:.85rem 1rem}.listen,.reverse{padding:.35rem 0;border:0;border-bottom:1px solid #856448;background:transparent;color:#6d471d}
  .instruction{margin:.75rem 0 .5rem;font-size:.88em;line-height:1.55}.quote{margin:.65rem 0;padding:.6rem .8rem;border-inline-start:3px solid #8b6747;background:#e9ddc5;line-height:1.65}
  .phrases{display:grid;gap:.35rem}.phrases button,.settle button,.accept{display:flex;align-items:center;gap:.65rem;min-height:2.55rem;padding:.42rem .7rem;border:1px solid #b5a184;text-align:left;line-height:1.5;background:#fff9ec}
  .phrases b{width:1.3rem;border-right:1px solid #b5a184;font-family:Georgia,serif}.phrases .selected{background:#e5d2a8;border-color:#7f633c}.phrases button:disabled:not(.selected){color:#685f50;background:#ede5d6}
  .speak{display:flex;flex-wrap:wrap;gap:.25rem 1rem;margin-top:.65rem}.speak button:first-child,.accept{padding:.5rem .7rem;background:#493c2b;border:1px solid #493c2b;color:#fff1d7}
  .speak button:first-child:disabled{background:#dfd6c3;color:#716956;border-color:#c8bba3}
  .response{margin-bottom:0}.accept{margin-top:.6rem;width:100%}.settle{display:grid;gap:.4rem;border-top:1px solid #c8b796}.settle button{justify-content:space-between}.settle button span{flex-shrink:0}
  @media(max-width:540px){header,.conversation,.settle{padding:.7rem}.seating{padding:.85rem .55rem;gap:1.5rem .45rem}.seat.civil{width:62%}.seat strong{font-size:1em}.seat small,.seat span{font-size:.72em}}
</style>
