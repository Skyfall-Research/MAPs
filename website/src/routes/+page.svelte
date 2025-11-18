<script lang="ts">
  /*
   * Home page.
   * Contains the logo, a description of the project and buttons for external links.
   * The description and buttons are placeholders at the moment.
   */
  import Logo from "$lib/components/assets/logo.svelte";
  import Button from "$lib/components/ui/button/button.svelte";
  import { File, Github, NotebookText } from "@lucide/svelte";
  import Container from "$lib/components/container.svelte";
</script>

<div class="flex flex-col gap-10 items-center mx-auto">
  <Container title={"About"}>
    {#snippet children()}
      <div class="bg-skyfall-card rounded-[8px] py-[16px] px-[16px] flex flex-col gap-5">
        <p class="text-center mx-auto">
          🎢 <strong>Mini Amusement Parks (MAPs)</strong> 🎢 
          <br>MAPs is here to here to challenge AI systems and humans alike to run a bustling amusement park: 
          build attractions, hire staff, and research the latest and greatest to attract guests and build the most valuable park around!  
          <br><br>

          Every decision shapes future outcomes, testing a player’s ability to 
          <strong>plan across long horizons</strong>, 
          <strong>actively learn the dynamics of the enviornment</strong>, 
          <strong>be adaptable to stochastic outcomes</strong>, and 
          <strong>reason about spatial relationships</strong>. 
          Built to bridge the gap between simulation and reality, MAP is designed to chart progress of systems toward robust business decision-making.  
          <br><br>
  💡      <strong>Think you can beat leading AI models?</strong> 
          <br>
          Play the game, climb the leaderboard, and see how your strategies compare!
          </p>
        <div class="flex flex-col gap-5">
          <div class="flex justify-center mr-3">
            <Button
              variant="default"
              href="/play"
              class="bg-linear-to-r from-[#2FA1C3] to-[#60A777] border rounded px-8 py-6 text-xl shadow-[0px_3.5px_0px_0px_#1F7644]"
              ><strong>Play Game</strong></Button
            >
          </div>
          <!-- The xs breakpoint is defined in the app.css file under theme-->
          <div
            class="flex flex-col xs:flex-row justify-center items-center gap-5"
          >
            <Button
              class="rounded-[8px] bg-skyfall-cardforeground hover:bg-skyfall-cardforeground/60"
              variant="skyfall"
              href="https://www.google.com"
              ><NotebookText /><span class="text-lg">Blog</span></Button
            >
            <Button
              class="rounded-[8px] bg-skyfall-cardforeground hover:bg-skyfall-cardforeground/60"
              variant="skyfall"
              href="https://openreview.net/forum?id=nJF0A933EO"
              ><File /><span class="text-lg">Paper</span></Button
            >
            <Button
              class="rounded-[8px] bg-skyfall-cardforeground hover:bg-skyfall-cardforeground/60"
              variant="skyfall"
              href="https://github.com/Skyfall-Research/MAPs"
              ><Github /><span class="text-lg">Code</span></Button
            >
          </div>
        </div>
      </div>
    {/snippet}
  </Container>
</div>
