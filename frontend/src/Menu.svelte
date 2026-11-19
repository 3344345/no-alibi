<script lang="ts">
  import { starts, stamp, balanceString } from './game'
  import Balance from './Balance.svelte'
  import type { World } from './types'
  export let profiles = starts
  export let worlds: World[] = []
  export let busy = false
  export let loading = false
  export let unavailable = false
  export let create: (data: { start: string; name: string; balance: string; seed?: string }) => void
  export let resume: (id: string) => void
  export let openChronicle: () => void
  export let selectMode: () => void
  export let importFile: () => void
  export let reload: () => void
  let creating = false,
    selected = 'S01',
    name = '新任联络员',
    balance = '0.500000',
    seed = ''
  $: selectedStart = profiles.find((s) => s.id === selected)!
  function submit() {
    const value = balanceString(balance)
    if (!value || !name.trim()) return
    create({
      start: selected,
      name: name.trim(),
      balance: value,
      ...(seed.trim() ? { seed: seed.trim() } : {}),
    })
  }
</script>

<div class="menu-shell">
  <header class="menu-nav">
    <button class="brand" aria-label="局中事 主菜单" on:click={() => (creating = false)}
      ><img alt="" src="./seal.svg" />局中事</button
    >
    <div class="place">江岚省<span>／</span>临江市<span>／</span>澄川县</div>
    <button class="plain" disabled={busy} on:click={selectMode}>模式选择</button>
    <button class="link-button" disabled={busy} on:click={importFile}
      >导入存档 <span aria-hidden="true">↗</span></button
    >
  </header>
  <main class="menu-content" id="main">
    {#if !creating}
      <div class="cover">
        <img src="./county-office.jpg" alt="阳光落在澄川县办公室桌上的一摞档案上" />
        <div class="cover-copy">
          <p class="cover-label">澄川县 · 县域生涯模拟</p>
          <h1>局中事</h1>
          <p>一份材料，几方说法。<br />在澄川县，接手你的第一件事。</p>
          <div class="button-row">
            {#if worlds.length}<button
                class="button gold"
                disabled={busy}
                on:click={() => resume(worlds[0].id)}>继续生涯 <span aria-hidden="true">→</span></button
              >{/if}
            <button
              class={'button ' + (worlds.length ? 'outline-light' : 'gold')}
              disabled={busy}
              on:click={() => (creating = true)}>建立生涯 <span aria-hidden="true">→</span></button
            >
            <button class="button outline-light" on:click={openChronicle}>市井家书 <span aria-hidden="true">→</span></button>
          </div>
        </div>
      </div>
      <section class="saves">
        <div class="section-title">
          <div>
            <p class="kicker">本机记录</p>
            <h2>生涯档案</h2>
          </div>
          <button class="link-button" on:click={reload} disabled={busy || loading}>刷新档案</button>
        </div>
        {#if loading}<p class="subtle">正在读取档案…</p>
        {:else if worlds.length}<div class="save-grid">
            {#each worlds as world}
              <button class="save" on:click={() => resume(world.id)} disabled={busy}>
                <span class="folder-icon" aria-hidden="true"></span><span
                  ><strong>{world.name}</strong><small
                    >{starts.find((s) => s.id === world.start)?.role ?? '生涯档案'} · {stamp(
                      world.minute ?? 0,
                    )}</small
                  ></span
                ><b aria-hidden="true">→</b>
              </button>
            {/each}
          </div>
        {:else if unavailable}<p class="empty">档案列表暂时无法读取。连接恢复后可刷新。</p>
        {:else}<p class="empty">尚无本机档案。建立生涯后，每次已确认的行动都会自动保存。</p>{/if}
      </section>
    {:else}
      <button class="back" on:click={() => (creating = false)}>← 返回主菜单</button>
      <div class="page-heading">
        <div>
          <p class="kicker">澄川县 · 人事档案</p>
          <h1>建立生涯</h1>
        </div>
      </div>
      <form class="setup-grid" on:submit|preventDefault={submit}>
        <section class="paper setup-card">
          <div class="section-title">
            <h2>选择起点</h2>
            <small>八种任职经历</small>
          </div>
          <div class="origin-list" role="radiogroup" aria-label="任职经历">
            {#each profiles as s}
              <label class:chosen={selected === s.id} class="origin">
                <input type="radio" name="start" value={s.id} bind:group={selected} />
                <span><b>{s.name}</b><small>{s.role}</small></span><span
                  class="radio-dot"
                  aria-hidden="true"
                ></span>
              </label>
            {/each}
          </div>
        </section>
        <section class="paper setup-card">
          <div class="section-title">
            <div>
              <p class="kicker">{selectedStart.id} · {selectedStart.age} 岁</p>
              <h2>{selectedStart.role}</h2>
            </div>
          </div>
          <dl class="sheet">
            <dt>岗位权限</dt>
            <dd>{selectedStart.authority}</dd>
            <dt>已有材料</dt>
            <dd>{selectedStart.known}</dd>
            <dt>待回应</dt>
            <dd>{selectedStart.obligation}</dd>
            <dt>待核实</dt>
            <dd>{selectedStart.blind}</dd>
          </dl>
          <label class="field"
            >角色称谓<input
              required
              maxlength="32"
              placeholder="输入你在局中的称谓"
              bind:value={name}
              autocomplete="off"
            /></label
          >
          <Balance bind:value={balance} prefix="new" />
          <details class="extra">
            <summary>世界种子（可选）</summary><label class="field"
              >种子<input maxlength="96" bind:value={seed} placeholder="留空时由引擎生成" /></label
            >
          </details>
          <button class="button primary full" disabled={busy || !name.trim() || !balanceString(balance)}
            >{busy ? '正在建立…' : '进入办公室'} <span aria-hidden="true">→</span></button
          >
        </section>
      </form>
    {/if}
  </main>
</div>
