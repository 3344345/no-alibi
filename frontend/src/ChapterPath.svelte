<script lang="ts">
  import { onDestroy } from 'svelte'
  import { enableSound, playScore, stopScore } from './sound'
  export let volume: number
  export let toggleAudio: () => void
  export let entries: {
    chapter_id: string; scene: string; choice?: string
    index: number; title: string; label: string; result: string; marks: string[]
  }[]
  export let busy = false
  export let fork: (revision: number) => void
  let selected = entries.length - 1
  $: page = entries[selected]
  $: recording = page?.chapter_id === 'witness_deng_xiaoping' &&
    page.scene === 'night_supper' && page.choice === 'music'
  function selectPage(index: number) {
    stopScore()
    selected = index
  }
  function listen() {
    if (!volume) toggleAudio()
    enableSound()
    void playScore('kitchen_waltz')
  }
  onDestroy(stopScore)
</script>

{#if page}
  <section class="path" aria-label="本章已走过的场景">
    <label for="played-scenes">回到哪一场</label>
    <select id="played-scenes" value={selected} on:change={(event) => selectPage(Number(event.currentTarget.value))}>
      {#each entries as item,i}
        <option value={i}>{i + 1}　{item.title}</option>
      {/each}
    </select>
    <article>
      <h3>{page.title}</h3>
      <p class="line">{page.label}</p>
      <p class="result">{page.result}</p>
      {#if recording}<button class="recording" on:click={listen}>{volume ? '重听那晚的手风琴' : '开启音效，重听那晚的手风琴'}</button>{/if}
      {#if page.marks.length}
        <ul aria-label="当时留下的线索">
          {#each page.marks as mark}<li>{mark}</li>{/each}
        </ul>
      {/if}
    </article>
    <div class="actions">
      <div>
        <button aria-label="上一场" disabled={selected === 0} on:click={() => selectPage(selected - 1)}>←</button>
        <span aria-live="polite">{selected + 1} / {entries.length}</span>
        <button aria-label="下一场" disabled={selected >= entries.length - 1} on:click={() => selectPage(selected + 1)}>→</button>
      </div>
      <button class="fork" disabled={busy} on:click={() => fork(page.index)}>从这场另走一条路</button>
    </div>
  </section>
{/if}

<style>
  .path { color: #363229 }
  label { display: block; margin-bottom: .4rem; color: #685e4f; font-size: .87rem }
  select { width: 100%; padding: .6rem; border: 1px solid #a59983; color: inherit; background: #fffaf0 }
  article { margin: 1.1rem 0; }
  h3 { font-family: var(--serif); font-weight: 600; margin: 0 0 .8rem }
  .line { padding-left: .7rem; color: #685039; border-left: 2px solid #a38a69; }
  .result { line-height: 1.8; white-space: pre-line }
  ul { margin: .75rem 0; padding-left: 1.25rem; color: #695c4c; font-size: .88rem }
  .actions, .actions div { display: flex; align-items: center; justify-content: space-between; gap: .45rem; flex-wrap: wrap }
  .actions { border-top: 1px solid #c9bfae; padding-top: .55rem }
  .actions span { font-variant-numeric: tabular-nums; font-size: .8rem }
  button { background: transparent; color: inherit; border: 1px solid transparent; min-height: 44px; padding: .5rem .7rem }
  button:disabled { opacity: .35 }
  button:hover:not(:disabled) { border-color: #ab9b81 }
  .recording { border-color: #ab9b81; padding: .5rem .8rem; }
  .fork { text-decoration: underline; text-underline-offset: .25em }
</style>
