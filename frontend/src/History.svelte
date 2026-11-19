<script lang="ts">
  import {onMount} from 'svelte'
  import {api,message} from './api'
  import Timeline from './Timeline.svelte'
  import type {Entry} from './types'
  export let worldId:string, revision:number, detailed=true
  let next:string|null=null, knownRevision=-1, loading=true, error='', alive=true, entries:Entry[]=[]
  async function load(before:string|undefined=undefined) {
    loading=true;error=''
    try {
      const query=before?'?before='+encodeURIComponent(before):''
      const result=await api<{events:Entry[];next:string|null;revision:number}>('/worlds/'+worldId+'/history'+query)
      if(!alive)return
      entries=before?[...result.events,...entries]:result.events
      next=result.next
      if(!before) knownRevision=result.revision
    }catch(e){error=message(e)}finally{loading=false}
  }
  onMount(()=>{void load();return ()=>{alive=false}})
</script>
{#if !loading&&knownRevision>=0&&revision>knownRevision}<button class="link-button" on:click={()=>load()}>读取最新经过 →</button>{/if}
{#if error}<p class="error" role="alert">{error}</p><button class="button compact" on:click={()=>load(next??undefined)}>重试读取</button>{/if}
{#if loading&&!entries.length}<p class="helper" role="status">正在读取经过…</p>{:else}<Timeline {entries} {detailed}/>{/if}
{#if next}<button class="button compact" disabled={loading} on:click={()=>load(next!)}>{loading?'正在读取…':'读取更早经过'}</button>{/if}
