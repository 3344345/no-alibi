import type { Row, Start, Value } from './types'

const startRows: [string, string, number, string, string, string, string][] = [
  [
    '基层办事经历',
    '县项目协调办办事岗',
    28,
    '起草材料、流转文件、请求会面。',
    '两日内向周成钧补交目录。',
    '南渠报告与办公室的催办要求。',
    '现场实际完成了多少工作。',
  ],
  [
    '乡镇执行经历',
    '乡镇联络岗',
    32,
    '核实辖区情况并安排已获授权的任务。',
    '五日内回复吴静禾的现场问题。',
    '一次南渠现场观察及水务检查日期。',
    '向上汇报时采用的口径。',
  ],
  [
    '专业技术转任',
    '县技术审查岗',
    31,
    '查指定档案并提交技术审查意见。',
    '三日内向梁澈提交审查意见。',
    '程向晚的技术摘要和南渠报告。',
    '谁已根据旧版材料作出判断。',
  ],
  [
    '项目协调履历',
    '县项目协调办副职',
    36,
    '分派本单位工作，提出协调意见和资源方案。',
    '本周向蒋绍衡提交协调方案。',
    '三个项目的请求总量及旧会议纪要。',
    '苏明川最近的人事安排。',
  ],
  [
    '异地交流任职',
    '县部门副职',
    35,
    '在本部门的岗位授权内处理事务。',
    '七日内向陈砚青交一份独立情况稿。',
    '正式交接材料和项目文件。',
    '旧人情如何影响眼前的事情。',
  ],
  [
    '本地长期任职',
    '县部门副职',
    39,
    '按本地辖区及岗位授权处理事务。',
    '向张振了解办理程序。',
    '既有项目承诺和家人的请托。',
    '本轮审查新增的关注点。',
  ],
  [
    '上级机关下派',
    '市级派驻协调岗',
    34,
    '向派出单位正式汇报并协调任务。',
    '十日内向吴承礼反馈材料。',
    '派驻任务书和市级资源摘要。',
    '县里现场的实际缺口。',
  ],
  [
    '组织培养通道',
    '县重点任务负责人',
    30,
    '编排获授任务并提交考核材料。',
    '按期向田文序报告项目实绩。',
    '重点任务书和岗位资格说明。',
    '任命程序中各方意见的实际分量。',
  ],
]
export const starts: Start[] = startRows.map(
  ([name, role, age, authority, obligation, known, blind], i) => ({
    id: 'S0' + (i + 1),
    name,
    role,
    age,
    authority,
    obligation,
    known,
    blind,
  }),
)
export function dateAt(m: number) {
  const days = Math.floor(m / 1440)
  const h = Math.floor(((m + 540) % 1440) / 60),
    min = (m + 540) % 60
  return {
    quarter: Math.floor(days / 90) + 1,
    day: (days % 90) + 1,
    time: [h, min].map((v) => String(v).padStart(2, '0')).join(':'),
  }
}
export function stamp(m: number) {
  const d = dateAt(m)
  return `第 ${d.quarter} 季 · 第 ${d.day} 天 ${d.time}`
}
export function balanceString(value: string) {
  if (!/^(?:0(?:\.\d{0,6})?|1(?:\.0{0,6})?)$/.test(value)) return null
  return Number(value).toFixed(6)
}
export function title(row: Row) {
  return String(row.title ?? row.name ?? row.label ?? row.id ?? '记录')
}
export function str(row: Row | undefined | null, ...keys: string[]) {
  if (!row) return ''
  for (const key of keys) {
    const value = row[key]
    if ((typeof value === 'string' && value.length) || typeof value === 'number') return String(value)
  }
  return ''
}
export function actionId(a: { kind: string; args?: Record<string, Value> }) {
  return a.kind + JSON.stringify(a.args ?? {})
}
export function saveFile(data: Blob, name: string) {
  const url = URL.createObjectURL(data),
    link = document.createElement('a')
  link.href = url
  link.download = name
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 15000)
}
