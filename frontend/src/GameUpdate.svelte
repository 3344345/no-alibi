<script lang="ts">
  import { onMount } from 'svelte'
  import { api, ApiError, message } from './api'

  type Update = {
    supported: boolean
    automatic: boolean
    current_version: string
    latest_version: string | null
    phase: 'idle' | 'checking' | 'downloading' | 'ready' | 'current' | 'offline' | 'error'
    message: string
    downloaded_bytes?: number
    total_bytes?: number
  }

  let update: Update | null = null
  let problem = ''
  let sending = false
  let nextPoll: ReturnType<typeof setTimeout>
  let requestNumber = 0

  function working(state: Update) {
    return state.phase === 'checking' || state.phase === 'downloading'
  }

  function statusLine(state: Update) {
    const version = state.latest_version ? ' ' + state.latest_version : ''
    switch (state.phase) {
      case 'checking': return '正在检查新版…'
      case 'downloading': return '正在下载新版' + version
      case 'ready': return '新版' + version + ' 已就绪，下次打开自动更新'
      case 'current': return '已是最新版本'
      case 'offline': return '暂时连不上更新服务'
      case 'error': return '更新未完成'
      default: return ''
    }
  }

  async function refresh(path = '/update', body: unknown = undefined) {
    clearTimeout(nextPoll)
    const number = ++requestNumber
    sending = body !== undefined
    try {
      const response = await api<Update>(path, body)
      if (number !== requestNumber) return
      update = response
      problem = ''
      if (response.supported && working(response)) {
        nextPoll = setTimeout(() => void refresh(), 1800)
      }
    } catch (error) {
      if (number !== requestNumber) return
      if (update?.supported) problem = message(error)
      if (!(error instanceof ApiError) || error.status >= 500) {
        nextPoll = setTimeout(() => void refresh(), 5000)
      }
    } finally {
      if (number === requestNumber) sending = false
    }
  }

  async function setAutomatic(input: HTMLInputElement) {
    await refresh('/update/preferences', { automatic: input.checked })
    if (update) input.checked = update.automatic
  }

  onMount(() => {
    void refresh()
    return () => {
      requestNumber++
      clearTimeout(nextPoll)
    }
  })
</script>

{#if update?.supported}
  <footer aria-label="游戏更新">
    <div class="version">
      <span>当前版本 {update.current_version}</span>
      <span role="status">{problem || statusLine(update)}</span>
    </div>
    <details>
      <summary>更新设置</summary>
      <div class="controls">
        <label>
          <input
            type="checkbox" checked={update.automatic} disabled={sending}
            on:change={(event) => setAutomatic(event.currentTarget)}
          /> 自动检查并下载更新
        </label>
        <button disabled={sending || (working(update) && !problem)}
          on:click={() => refresh('/update/check', {})}>检查更新</button>
      </div>
      {#if update.phase === 'downloading' && update.total_bytes && update.downloaded_bytes !== undefined}
        <progress aria-label="下载进度" max={update.total_bytes} value={update.downloaded_bytes}></progress>
      {/if}
      {#if update.phase === 'downloading' && !update.automatic}
        <p>这次下载会继续。下次打开游戏时，自动检查将保持关闭。</p>
      {/if}
      {#if (update.phase === 'error' || update.phase === 'offline') && update.message && update.message !== statusLine(update)}
        <p>{update.message}</p>
      {/if}
    </details>
  </footer>
{/if}

<style>
  footer {
    max-width: 1400px;
    margin: 1.1rem auto 0;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.3rem 1rem;
    color: #c7c8bb;
    font-size: 0.9rem;
  }
  .version, .controls {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.45rem 1.1rem;
  }
  .version [role='status'] { color: #e7c794; }
  details, .version { max-width: 100%; }
  summary { width: fit-content; margin-left: auto; padding: 0.25rem 0; }
  .controls { margin: 0.6rem 0; }
  label { display: inline-flex; align-items: center; gap: 0.3rem; }
  input { accent-color: #e6c58d; }
  button {
    background: transparent;
    color: #f4ead6;
    border: 1px solid #8a8d7d;
    border-radius: 3px;
    padding: 0.22rem 0.65rem;
  }
  progress { width: 100%; accent-color: #e6c58d; }
  details p { max-width: 33em; }
  @media (max-width: 680px) {
    details { flex-basis: 100%; }
    summary { margin-left: 0; }
  }
</style>
