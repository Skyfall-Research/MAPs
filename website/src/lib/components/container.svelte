<script lang="ts">
  import type { Snippet } from "svelte";

  let {
    title,
    children,
    buttons = null,
    icon = null,
  }: {
    title: string;
    children: Snippet;
    buttons?: Snippet | null;
    icon?: Snippet | null;
  } = $props();
</script>

<div
  class="flex flex-col gap-4 p-3 rounded-[8px] bg-linear-to-tr from-[#50C66E] to-[#0E93C5] z-20 w-full"
>
  <div
    class="flex justify-start sm:justify-between items-start sm:items-end flex-col sm:flex-row"
  >
    <div class="flex items-center gap-2">
      <h1
        class="
                text-4xl
                ml-1
                font-monocraft
                bg-clip-text
                text-transparent
                bg-gradient-to-t
                from-[#50C66E]
                to-[#0E93C5]
                drop-shadow-[-1px_-1px_0_#ffffff,1px_1px_0_#ffffff,-1px_1px_0_#ffffff,1px_-1px_0_#ffffff,0px_2px_0px_rgba(0,0,0,0.5)]"
      >
        {title}
      </h1>
      {@render icon?.()}
    </div>
    {@render buttons?.()}
  </div>
  {@render children?.()}
</div>
