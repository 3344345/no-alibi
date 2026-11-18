<script lang="ts">
  import { title, str, stamp } from './game'
  import type { Row } from './types'
  export let rows: Row[] = []
  export let empty = '目前没有已送达的记录。'
  export let openFirst = false
  const labels: Record<string, string> = {
    role: '职务',
    location: '地点',
    source: '来源',
    date: '签发日期',
    scope: '适用范围',
    version: '版本',
    status: '当前状态',
    kind: '材料类别',
    report: '报告口径',
    statement: '陈述',
    body: '正文',
    text: '内容',
    description: '说明',
    next_check: '下次检查',
    deadline: '截止',
    due: '约定时间',
    minute: '记录时间',
    progress: '已知进度',
    groups: '工作组',
    note: '备注',
    condition: '条件',
    position: '岗位',
    result: '结果',
    owner: '经办方',
    party: '对象',
    target: '对象',
    project: '相关项目',
    stage: '阶段',
    outcome: '结果',
    state: '状态',
    route: '路线',
    summary: '摘要',
    time: '时间',
    source_event_id: '来源事件',
    goals: '已知目标',
    from: '来源',
    cost: '代价',
    evidence: '可见材料',
    level: '层级',
    age: '年龄',
    remaining: '可用额度',
    promised: '承诺内容',
    revision: '档案修订',
    amount: '资金',
    requested_groups: '申请工作组',
    requested_yuan: '申请金额（元）',
    funding: '拨款状态',
    approved: '已获批准',
    open: '已开放',
    subject: '事项',
    counterparty: '对象',
    recipient: '对方',
    accessible: '当前可访问',
    progress_claim: '报告陈述',
    holding: '持有人',
    held_by: '持有人',
    at: '时点',
    issued: '签发日期',
    author: '作者',
    type: '类别',
    project_id: '项目编号',
    public_status: '公开状态',
    detail: '已知进展',
    public_use: '已经开放',
    maintenance: '需要维护',
    passage: '便道状态',
    present: '目前在场',
    access: '进入条件',
    creditor: '承诺对象',
    refs: '来源记录',
    location_id: '地点编号',
    inspection: '检查状态',
    report_date: '报告日期',
    report_scope: '报告范围',
    request: '申请',
    request_wan: '申请额度（万元）',
  }
  function value(k: string, v: unknown) {
    if (k === 'request' && typeof v === 'number') return (v / 1000000).toLocaleString('zh-CN') + ' 万元'
    if (k === 'status' && typeof v === 'string')
      return (
        (
          {
            signal: '待核实',
            active: '处理中',
            contested: '存在分歧',
            resolved: '已结',
            dormant: '暂缓',
            reopened: '重新处理',
          } as Record<string, string>
        )[v] ?? v
      )
    if (k === 'type' && v === 'procedure') return '程序性承诺'
    if (typeof v === 'boolean') return v ? '是' : '否'
    if (typeof v === 'number' && ['minute', 'due', 'deadline', 'next_check'].includes(k))
      return stamp(v)
    if (typeof v === 'string' || typeof v === 'number') return String(v)
    if (Array.isArray(v) && v.every((x) => typeof x === 'string' || typeof x === 'number'))
      return v.join('、')
    return ''
  }
  function details(row: Row) {
    return Object.entries(row).filter(([k, v]) => k in labels && value(k, v) !== '')
  }
</script>

{#if rows.length}
  <div class="record-list">
    {#each rows as r, i}
      <details class="record" open={openFirst && i === 0}>
        <summary
          ><span class="record-id">{r.id ?? String(i + 1).padStart(2, '0')}</span><span
            ><strong>{title(r)}</strong>{#if str(r, 'source', 'role', 'status')}<small
                >{value('status', str(r, 'source', 'role', 'status'))}</small
              >{/if}</span
          ><b class="chev" aria-hidden="true">▾</b></summary
        >
        <dl class="sheet record-body">
          {#each details(r) as [k, v]}<dt>{labels[k]}</dt>
            <dd>{value(k, v)}</dd>{/each}
          {#if !details(r).length}<dd>目前可查的记录仅包含名称与编号。</dd>{/if}
        </dl>
      </details>
    {/each}
  </div>
{:else}<p class="empty">{empty}</p>{/if}
