<script lang="ts">
  import { onMount } from 'svelte'
  export let title: string
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
    <h2>{title}</h2>
    <button class="plain close" aria-label="关闭" on:click={onclose}>×</button>
  </div>
  <slot />
</dialog>
