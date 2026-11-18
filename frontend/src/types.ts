export type Value = string | number | boolean
export type JsonValue = Value | null | JsonValue[] | { [key: string]: JsonValue }
export type Attempt = { id: string; kind: string; args: Record<string, JsonValue>; depends_on: string[] }
export type AttemptResult = { id: string; status: string; text: string }
export type Data = Record<string, unknown>
export type Row = Data & {
  id?: string
  name?: string
  title?: string
  description?: string
  status?: string
}
export interface Field {
  name: string
  label: string
  type: 'text' | 'textarea' | 'select' | 'number' | 'checkbox'
  options?: Array<{ label: string; value: Value } | string>
  min?: number
  max?: number
  maxLength?: number
  default?: Value
  required?: boolean
}
export interface Action {
  confirmation_token?: string
  kind: string
  args?: Record<string, Value>
  label: string
  description?: string
  cost?: string | number
  enabled?: boolean
  reason?: string
  category?: string
  fields?: Field[]
  confirm?: boolean | string
}
export interface Policy {
  target: string
  effective: number
  version: number
  parameter_package_hash: string
  transition_end: number
  trajectory?: { minute: number; start: number; target: string; version: number }[]
}
export interface Entry {
  id: string
  minute: number
  kind: string
  title: string
  text: string
  actor?: string
  refs?: string[]
}
export interface View {
  world_id: string
  id?: string
  name: string
  start: string
  revision: number
  minute: number
  quarter: number
  policy: Policy
  timeline: Entry[]
  appointments: Array<{ id: string; due: number; title: string }>
  player: Row
  location: Row
  projects: Row[]
  documents: Row[]
  cases: Row[]
  people: Row[]
  notebook: Row & { accessible?: boolean; location?: string; entries?: Row[] }
  commitments: Row[]
  finances: Row
  ending?: Row | null
  actions: Action[]
  last_action_results?: AttemptResult[]
  parent?: { world_id: string; revision: number } | null
  locations?: Row[]
  scenes?: Row[]
  arcs?: Row[]
  quarter_reports?: Row[]
  offers?: Row[]
  reports?: Row[]
  family?: Row
  busy?: Row | null
  opening?: string
}
export interface World {
  id: string
  world_id?: string
  name: string
  start?: string
  revision: number
  minute?: number
  quarter?: number
}
export interface Start {
  id: string
  name: string
  role: string
  age: number
  authority: string
  obligation: string
  known: string
  blind: string
}
export interface Choice {
  cost?: string | number
  fields?: Field[]
  confirm?: boolean | string
  label: string
  kind: string
  args: Record<string, Value>
}
export interface Command {
  confirmation_token?: string
  command_id: string
  expected_revision: number
  kind: string
  args: Record<string, JsonValue>
}
export type Page = '办公桌' | '行动' | '日程' | '档案' | '人事与地点' | '记事本' | '设置'
