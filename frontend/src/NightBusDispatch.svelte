<script lang="ts">
  import type { Action, DispatchPlan } from './types'
  export let plans: DispatchPlan[]
  export let choices: Action[]
  export let busy: boolean
  export let choose: (action: Action) => void

  const pencilled = plans.find(p => p.marked)
  let leave = pencilled?.leave ?? plans[0].leave
  let route: DispatchPlan['route'] = pencilled?.route ?? plans[0].route
  $: times = [...new Set(plans.map(p => p.leave))]
  $: routes = plans.filter(p => p.leave === leave)
  $: plan = plans.find(p => p.leave === leave && p.route === route)
  $: action = choices.find(a => a.args?.choice === plan?.key)
  $: rehearsal = plan?.key.startsWith('paper_')
</script>

{#if plan}
  <section class="desk" aria-label="七路调度台">
    <div class="mast"><span>七路夜班</span><strong>{rehearsal ? '铅笔排班表' : '首班调度单'}</strong></div>
    {#if pencilled}<div class="pencil">男孩留的铅笔印还在：{pencilled.leave}发车，{pencilled.label}。</div>{/if}
    <div class="switches">
      <fieldset disabled={busy}>
        <legend>南门发车</legend>
        <div class="picks">{#each times as time}
          <label class:active={leave === time}><input type="radio" name="bus-leave" bind:group={leave} value={time} /><span>{time}</span></label>
        {/each}</div>
      </fieldset>
      <fieldset disabled={busy}>
        <legend>行车路线</legend>
        <div class="picks">{#each routes as p}
          <label class:active={route === p.route}><input type="radio" name="bus-route" bind:group={route} value={p.route} /><span>{p.label}</span></label>
        {/each}</div>
      </fieldset>
    </div>
    <div aria-live="polite" aria-atomic="true">
      <ol class="line" aria-label="预计沿途时刻">
        <li><span class="lamp"></span><b>南门</b><time>{plan.leave}</time></li>
        <li class:off={!plan.bath_at}><span class="lamp"></span><b>{plan.bath_at ? '澡堂' : '河堤'}</b><time>{plan.bath_at ?? '直行'}</time></li>
        <li><span class="lamp"></span><b>北桥</b><time>{plan.arrive}</time></li>
      </ol>
      <ul class="outcome">
        <li><strong>三名护工</strong><span>{plan.nurses === 3 ? '三人都能搭上车' : plan.nurses === 1 ? '小陶赶得上，两位师傅得另走' : '赶到时，车已经开了'}</span></li>
        <li><strong>澡堂老葛</strong><span>{plan.bath_at ? '能在垫脚砖旁上车' : '车从河堤过，老葛还在等'}</span></li>
        <li><strong>三名工友</strong><span>{plan.transfer ? '赶得上 23:00 的接班车' : '到桥时，接班车已经走了'}</span></li>
      </ul>
    </div>
    <button class="sign" disabled={busy || !action} on:click={() => action && choose(action)}>
      {rehearsal ? '把这张表念给伍琴听' : '签下调度单，发车'} <span aria-hidden="true">→</span>
    </button>
  </section>
{/if}

<style>
  .desk { color: #f7f0de; background: #203938; border: 1px solid #354f48; margin: 1.1rem 0 .25rem; padding: clamp(.85rem, 3vw, 1.5rem); border-radius: 3px; }
  .mast { display: flex; align-items: baseline; gap: .8em; border-bottom: 1px solid #67807a; padding-bottom: .6em; }
  .mast span { color: #ead5a0; font-size: .8rem; }
  .mast strong { font-family: var(--serif); font-size: 1.24rem; letter-spacing: .08em; }
  .pencil { margin-top: .6rem; color: #efd9a9; font: .92rem/1.6 var(--serif); }
  .switches { display: flex; flex-wrap: wrap; gap: .75rem 1.5rem; margin-top: .8rem; }
  fieldset { min-width: 0; padding: 0; margin: 0; border: 0; }
  legend { font-size: .85rem; font-weight: 600; line-height: 1.4; color: #e8e9d9; padding: 0 0 .37rem; }
  .picks { display: flex; flex-wrap: wrap; gap: .25em; }
  label { display: inline-flex; position: relative; cursor: pointer; border: 1px solid #81948b; border-radius: 3px; background: #193031; }
  label span { padding: .4rem .55rem; font-variant-numeric: tabular-nums; }
  label.active { background: #e7cd8a; border-color: #e7cd8a; color: #1d302b; font-weight: 650; }
  input { appearance: none; position: absolute; inset: 0; width: 100%; height: 100%; margin: 0; cursor: pointer; border-radius: 3px; }
  input:focus-visible, .sign:focus-visible { outline: 3px solid #fff; outline-offset: 3px; }
  .line { display: flex; list-style: none; margin: 1.1rem 0 .85rem; padding: 0; }
  .line li { position: relative; flex: 1; text-align: center; display: grid; justify-items: center; }
  .line li::before { content: ''; position: absolute; left: -50%; width: 100%; top: .33rem; height: 2px; background: #cfb780; }
  .line li:first-child::before { content: none; }
  .lamp { width: .75rem; height: .75rem; box-sizing: border-box; border-radius: 50%; border: 2px solid #e8cd8a; background: #e8cd8a; z-index: 1; margin-bottom: .35rem; }
  .off .lamp { background: #203938; }
  b { font-size: .9rem; }
  time { color: #e9dbba; font-size: .8rem; font-variant-numeric: tabular-nums; }
  .outcome { list-style: none; margin: .75rem 0; padding: 0; border-top: 1px solid #647a71; }
  .outcome li { display: flex; align-items: baseline; gap: .55rem; padding: .34rem 0; border-bottom: 1px solid #4a625c; font-size: .9rem; }
  .outcome strong { flex: 0 0 auto; color: #e8dbbb; }
  .sign { font: inherit; font-weight: 600; color: #223330; background: #e8d2a4; border: 1px solid #f5dfae; border-radius: 2px; padding: .55rem .8rem; width: 100%; display: flex; align-items: center; justify-content: space-between; gap: .5rem; cursor: pointer; text-align: left; }
  .sign:disabled, fieldset:disabled { opacity: .6; }
</style>
