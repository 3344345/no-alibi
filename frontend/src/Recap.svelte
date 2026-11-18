<script lang="ts">
  import { onDestroy } from 'svelte'
  import Dialog from './Dialog.svelte'
  import Timeline from './Timeline.svelte'
  import { api, message } from './api'
  import type { Entry } from './types'
  export let worldId: string
  export let revision: number
  export let detailed = true
  let open = false,
    loading = false,
    error = ''
  let segments: Entry[] = []
  let alive = true
  onDestroy(() => { alive = false })
  let displayedRevision = -1, displayedWorld = ''
  $: if (open && (displayedRevision !== revision || displayedWorld !== worldId)) open = false
  async function read() {
    if (loading) return
    loading = true
    error = ''
    const requestedWorld = worldId, requestedRevision = revision
    try {
      const report = await api<{ segments: Entry[]; revision: number }>(
        '/worlds/' + encodeURIComponent(worldId) + '/recap',
      )
      if (!alive || worldId !== requestedWorld || revision !== requestedRevision || report.revision !== revision) return
      displayedWorld = requestedWorld
      displayedRevision = requestedRevision
      segments = [...report.segments].sort((a, b) => a.minute - b.minute)
      open = true
    } catch (e) {
      if (alive && worldId === requestedWorld && revision === requestedRevision) error = message(e)
    } finally {
      loading = false
    }
  }
</script>

<button class="button compact" disabled={loading} on:click={read}
  >{loading ? '正在整理回顾…' : '回顾近期经过'}</button
>
{#if error}<p class="error" role="alert">{error}</p>{/if}
{#if open}
  <Dialog title="近期经过" onclose={() => (open = false)}>
    <Timeline entries={segments} {detailed} />
    <div class="dialog-foot"><button class="button" on:click={() => (open = false)}>返回</button></div>
  </Dialog>
{/if}
