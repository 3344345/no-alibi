<script lang="ts">
  export let destination: string
  export let back: () => void
  export let disabled = false
  export let pageShortcut = false
  export let element: HTMLButtonElement | undefined = undefined

  function key(event: KeyboardEvent) {
    if (!pageShortcut || disabled || event.defaultPrevented || event.repeat || event.isComposing) return
    if (event.altKey || event.ctrlKey || event.metaKey || event.key !== 'Escape') return
    if (document.querySelector('dialog[open], .perform.theatre') || document.fullscreenElement) return
    if (event.target instanceof HTMLElement && event.target.closest('input, textarea, select, [contenteditable="true"]')) return
    event.preventDefault()
    back()
  }
</script>

<svelte:window on:keydown={key} />
<button type="button" class="return-button" aria-label="返回" title={'返回'+destination}
  {disabled} on:click={back} bind:this={element}><span aria-hidden="true">←</span> 返回</button>

<style>
  .return-button{display:inline-flex;align-items:center;justify-content:center;gap:.35em;flex:none;min-height:40px;padding:.35rem .72rem;border:1px solid currentColor;border-radius:3px;background:transparent;color:inherit;font:600 .94rem/1.25 var(--sans);white-space:nowrap;cursor:pointer}
  .return-button:focus-visible{outline:2px solid currentColor;outline-offset:2px}
  .return-button:disabled{opacity:.5;cursor:default}
</style>
