<script lang="ts">
  import BackButton from './BackButton.svelte'
  import { onMount } from 'svelte'
  export let title: string
  export let destination = '上一层'
  export let onclose: () => void
  let dialog: HTMLDialogElement
  onMount(() => {
    const previous = document.activeElement
    dialog.showModal()
    return () => {
      if (previous instanceof HTMLElement && previous.isConnected) previous.focus()
    }
  })
</script>

<dialog
  bind:this={dialog}
  aria-label={title}
  on:cancel={(e) => {
    e.preventDefault()
    onclose()
  }}
>
  <div class="dialog-head">
    <BackButton back={onclose} {destination}/>
    <h2>{title}</h2>
  </div>
  <slot />
</dialog>
