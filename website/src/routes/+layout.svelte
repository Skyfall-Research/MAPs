<script lang="ts">
  /*
   * Layout for the entire app.
   * Contains the navbar, dots background animation and the main content.
   */
  import "../app.css";
  import Navbar from "$lib/components/navbar.svelte";
  import Footer from "$lib/components/footer.svelte";
  import Background from "$lib/components/background.svelte";
  import { page } from "$app/state";
  let { children } = $props();
</script>

<svelte:head>
  <link rel="icon" href="/favicon.ico" />
</svelte:head>

<div class=" min-h-screen flex flex-col items-center">
  <Background />
  <Navbar />
  {#if page.url.pathname != "/play"}
    <h1
      class="
			absolute
      lg:text-7xl
      sm:text-6xl
      text-5xl
			w-full
			text-center
			top-30
			fixed
            font-monocraft
            bg-clip-text
            text-transparent
            bg-gradient-to-t
            from-[#50C66E]
            to-[#0E93C5]
            drop-shadow-[-2px_-2px_0_#ffffff,2px_2px_0_#ffffff,-2px_2px_0_#ffffff,2px_-2px_0_#ffffff,0px_4px_0px_rgba(0,0,0,0.5)]"
    >
      Mini Amusement Parks
    </h1>
  {/if}
  <div
    class="h-full min-h-screen flex flex-col gap-15 justify-center items-center md:max-w-[85vw] max-w-[85vw] md:min-w-[70vw] min-w-[90vw]"
    style="padding-top: {page.url.pathname == '/play'
      ? '130px'
      : '260px'}; padding-bottom: {page.url.pathname == '/play'
      ? '120px'
      : '240px'}"
  >
    {@render children?.()}
  </div>
  <Footer />
</div>
