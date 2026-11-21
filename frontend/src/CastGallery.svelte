<script lang="ts">
  import historic from './historicalCast.json'
  import original from './originalCast.json'

  const photos = Object.entries(historic).map(([name, credit]) => ({ name, group:'历史照片' as const, credit }))
  const drawings = Object.entries(original).map(([name, credit]) => ({ name, group:'原创戏剧造型' as const, credit }))
  const cast = [...photos, ...drawings]
  const groups = ['全部', '历史照片', '原创戏剧造型'] as const
  let group: (typeof groups)[number] = '全部'
  let query = ''
  let picked = '毛泽东'
  $: people = cast.filter(person => (group === '全部' || person.group === group) && person.name.includes(query.trim()))
  $: selected = people.find(person => person.name === picked) ?? people[0]
</script>

<section class="cast-gallery" aria-label="人物资料">
  <div class="tools">
    <label for="cast-query">找人物</label>
    <input id="cast-query" type="search" bind:value={query} placeholder="输入姓名" autocomplete="off" />
    <div class="groups" role="group" aria-label="肖像类别">
      {#each groups as item}
        <button type="button" aria-pressed={group === item} on:click={() => (group = item)}>{item}</button>
      {/each}
    </div>
  </div>
  {#if selected}
    <div class="catalog">
      <article aria-label={selected.name + '的肖像资料'}>
        <figure aria-label="我手里的相册"><img src={'/cast/' + selected.credit.file + '.webp'} alt={selected.name + ' · ' + selected.group} /></figure>
        <div class="credit">
          <small>{selected.group}</small><h3>{selected.name}</h3>
          {#if selected.group === '历史照片'}
            <p>{selected.credit.author}</p>
            <p class="changes">{selected.credit.changes}</p>
            <div class="links">
              <a href={selected.credit.source} target="_blank" rel="noopener noreferrer">查看照片来源 ↗</a>
              <a href={selected.credit.licenseUrl} target="_blank" rel="noopener noreferrer">{selected.credit.license} ↗</a>
            </div>
          {:else}
            <p>{selected.credit.author}</p>
            <p class="changes">{selected.credit.source}。{selected.credit.description}</p>
          {/if}
        </div>
      </article>
      <nav aria-label="人物名单">
        {#each people as person}
          <button type="button" aria-pressed={selected.name === person.name} on:click={() => (picked = person.name)}>
            <img loading="lazy" src={'/cast/' + person.credit.file + '.webp'} alt="" />
            <span>{person.name}<small>{person.group}</small></span>
          </button>
        {/each}
      </nav>
    </div>
  {:else}
    <p role="status">没有找到符合条件的人物。</p>
    <button type="button" on:click={() => { query = ''; group = '全部' }}>查看全部人物</button>
  {/if}
</section>

<style>
  :global(dialog[aria-label='人物与出处']) {max-width:min(1040px,calc(100% - 24px));padding:clamp(16px,2.5vw,32px);}
  .cast-gallery {color:#292f27;}
  .tools,.groups,.links {display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
  .tools {padding-bottom:14px;border-bottom:1px solid #b8b6a6;margin-bottom:18px;}
  .tools label {font-size:.85rem;}
  input {width:clamp(125px,22vw,230px);border:1px solid #a3a594;padding:8px;background:#fffdf5;color:#21382d;}
  .groups {margin-left:auto;gap:5px;}
  button {cursor:pointer;}
  .groups button {background:transparent;border:1px solid #a6a794;border-radius:3px;padding:6px 11px;min-height:38px;color:#303a30;}
  .groups button[aria-pressed='true'] {color:#fff6df;background:#294236;border-color:#294236;}
  .catalog {display:grid;grid-template-columns:minmax(0,1.85fr) minmax(200px,1fr);gap:clamp(12px,2.7vw,35px);}
  article {min-width:0;}
  figure {position:relative;margin:0;background:#564335 url('/viewer/album.webp') center / contain no-repeat;display:flex;align-items:center;justify-content:center;width:100%;aspect-ratio:1672/941;overflow:hidden;}
  figure img {position:absolute;inset:0;margin:auto;display:block;width:auto;height:auto;max-width:58%;max-height:75%;object-fit:contain;box-sizing:content-box;border:3px solid #e5ddc7;box-shadow:1px 2px 4px #46361f75;transform:rotate(-.5deg);}
  .credit {padding-top:12px;}
  .credit small {font-size:.8rem;color:#635e50;}
  h3 {margin:0;font:600 clamp(1.7rem,3.5vw,2.5rem)/1.3 var(--serif);}
  p {margin:5px 0;line-height:1.55;}
  .changes {color:#625f53;font-size:.9rem;}
  .links {margin-top:10px;gap:6px 18px;font-size:.9rem;}
  a {color:#355847;text-underline-offset:3px;}
  nav {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));align-content:start;max-height:clamp(240px,58dvh,565px);overflow:auto;border-top:1px solid #b8b6a6;gap:0 6px;}
  nav button {display:flex;min-width:0;align-items:center;gap:7px;text-align:left;padding:6px 3px;background:transparent;border:0;border-bottom:1px solid #c8c5b6;color:#2f382f;}
  nav button[aria-pressed='true'] {background:#e3dec8;}
  nav img {width:34px;height:41px;object-fit:cover;object-position:50% 25%;background:#323b32;}
  nav span {overflow-wrap:anywhere;line-height:1.32;}
  nav small {display:block;color:#706956;font-size:.66rem;}
  button:focus-visible {outline:2px solid #976d32;outline-offset:-2px;}
  @media(max-width:760px){.catalog{grid-template-columns:minmax(0,1.5fr) minmax(140px,.9fr)}nav{grid-template-columns:1fr}.groups{margin-left:0}}
  @media(max-width:540px){.catalog{grid-template-columns:1fr}.tools{margin-bottom:12px}.groups{flex-basis:100%}.groups button{font-size:.85rem;padding:4px 8px;min-height:34px}nav{grid-template-columns:repeat(2,minmax(0,1fr));max-height:185px}.credit{padding-top:6px}.links{margin-top:6px;}.tools input{flex:1;}}
</style>
