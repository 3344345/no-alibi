<!-- Leave the movie rectangle intact. The four edges of the room surround
     its native controls, so captions, keyboard navigation and seeking work. -->
<div class="seat" role="group" aria-label="我的放映席">
  <slot />
</div>

<style>
  .seat {
    background:#100f0c;
    border-style:solid;
    border-color:#211a14;
    border-width:clamp(9px,1.4vw,19px) clamp(11px,3vw,34px) clamp(25px,5.1vw,72px) clamp(13px,3.4vw,40px);
    border-image-source:url('/viewer/auditorium.webp');
    border-image-slice:93 154 312 195;
    border-image-repeat:stretch;
  }
  .seat :global(video) {display:block;width:100%;object-fit:contain;background:#171612;}
  @media(max-width:520px) {
    .seat {border-width:9px 10px 28px 12px;}
  }
</style>
