<script lang="ts">
  import { dateAt, str } from './game'
  import type { Action, Row, View } from './types'

  export let view: View
  export let request: Row
  export let deadline: number
  export let select: (action: Action) => void
  export let busy: boolean
  $: author = str(request, 'source')
  $: report = view.documents.find((doc) => doc.id === 'D01-r1')
  $: fieldNote = view.documents.find((doc) => doc.id === 'START-field')
  $: technicalNote = view.documents.find((doc) => doc.id === 'START-tech')
  $: comparison = view.documents.find((doc) => doc.id === 'D01-index')
  $: check = view.documents.filter((doc) => doc.kind === '检查记录' && doc.scope === '西段便道').at(-1)
  $: project = view.projects.find((row) => row.passage)
  $: actions = view.actions.filter((a) =>
    a.enabled !== false && (a.kind === 'passage' || a.kind === 'compare' || a.kind === 'revise'),
  )
</script>

<div class="passage-request">
  <p class="kicker">澄川县 · {str(view.player, 'role')}</p>
  <h2>今天还得绕南渠吗？</h2>
  {#if view.revision <= 1}
    {#if technicalNote}
      <p>卷首夹着{str(technicalNote, 'source')}的技术意见。上面写着：“{str(technicalNote, 'body')}”</p>
    {:else if fieldNote}
      <p>{str(fieldNote, 'body')}</p>
    {:else if view.opening}
      <p>{view.opening}</p>
    {/if}
  {/if}
  <p>社区代表{author}捎来一张便条。她写这张纸的时候，西段路口还拦着，住在渠边的人每天都得绕路。她想带个准信回去。今天傍晚，大伙儿能从这儿过吗？</p>
  {#if check}
    <blockquote>{str(check, 'source')}送回了检查记录。{str(check, 'body')}</blockquote>
  {:else if comparison}
    <blockquote>两份表的日期和范围已经对过。{str(comparison, 'body')}</blockquote>
  {:else if report}
    <blockquote>{str(report, 'source')}送来的简报写着：“{str(report, 'body')}”</blockquote>
  {/if}
  {#if project?.passage === '检查中'}
    <p>程向晚去验路了。她的检查记录还没送回来，{author}眼下能带给居民的消息只有这一条。</p>
  {:else if project?.passage === '待申请' && comparison}
    <p>现在可以给周主任写清楚，这些数字究竟能说明什么。{author}问的那条路，还要程向晚到西段看过，才有话可回。</p>
  {:else if project?.passage === '待申请' && !check}
    <p>周主任{dateAt(deadline).time}收第一轮意见。你可以先翻出上次巡查的那张表，看两张纸上说的是不是同一段工程。也可以请程向晚走一趟，亲眼看看围挡里头能不能过人。</p>
  {:else if project?.passage}
    <p>便道的办理记录刚更新为“{project.passage}”。{project.public_use ? '社区已经可以通行。' : '围挡还没有挪开，居民仍得绕行。'}</p>
  {/if}
  {#if actions.length}<div class="button-row">
    {#each actions as action}
      <button class="button" disabled={busy} on:click={() => select(action)}
        >{action.label} <small>{action.cost}</small></button>
    {/each}
  </div>{/if}
</div>

<style>
  h2 {
    font-size: clamp(1.5rem, 2.3vw, 2.1rem);
    margin: 0.3rem 0 1rem;
  }
  p:not(.kicker), blockquote {
    font-family: var(--serif);
    font-size: 1.06rem;
    line-height: 1.85;
    margin: 0.9em 0;
  }
  blockquote {
    border-left: 2px solid var(--line);
    padding-left: 1rem;
    color: var(--muted);
  }
  small {
    font-weight: normal;
    margin-inline-start: 0.25rem;
  }
</style>
