<script lang="ts">
  import { onMount } from "svelte";
  import { GUI } from "$lib/map_js/gui/GUI.js";
  import * as AlertDialog from "$lib/components/ui/alert-dialog/";
  import { buttonVariants } from "$lib/components/ui/button";
  import Documentation from "$lib/components/documentation.svelte";
  import Button from "$lib/components/ui/button/button.svelte";
  import Container from "$lib/components/container.svelte";
  import { cn } from "$lib/utils";
  import { Loader2, Volume2, VolumeX, Maximize, Minimize, BookOpen } from "@lucide/svelte";
  import { createGameState } from "$lib/map_js/game-state.svelte";
  import { AUTO, Game } from "phaser";
  import HumanSubmissionDialog from "$lib/components/leaderboard/human-submission-dialog.svelte";

  import audio from "$lib/assets/game_music.mp3";

  // Receive server-fetched data
  let { data } = $props();

  let audioRef = $state<HTMLAudioElement | null>(null);
  let isMuted = $state(false);

  let gameState = createGameState();
  let fullscreen = $state(false);
  let game = $state<Game | null>(null);
  let containerRef = $state();
  let gameContainerRef = $state();
  let documentationOpen = $state(false);
  let fsDocumentationOpen = $state(false);
  let firstDocumentationRef = $state();

  // Exit fullscreen when submission dialog opens
  $effect(() => {
    const showPopup = gameState.leaderboardSubmissionState.getShowPopup();
    if (showPopup && fullscreen && document.fullscreenElement) {
      // Exit fullscreen mode before showing the submission dialog
      document.exitFullscreen().then(() => {
        fullscreen = false;
        setTimeout(() => resizeGameToContainer(false), 150);
      });
    }
  });

  // Reactive container dimensions
  let containerWidth = $derived(containerRef?.clientWidth ?? 0);
  let containerHeight = $derived(containerRef?.clientHeight ?? 0);

  // Create the game
  onMount(async () => {
    // Apply scaling based on window size: max height is window height - 300px or 70% of window height, max width is 90% of window width.
    // controls the scaling using $lib/map_js/scaling.ts
    gameState.loadingState.setState(true);

    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get("mode");
    const difficulty = urlParams.get("difficulty");
    if (mode) {
      gameState.modeState.setState(mode);
    }
    if (difficulty) {
      gameState.difficultyState.setState(difficulty);
    }
    console.log("Using Mode: ", gameState.modeState.getState());
    console.log("Using Difficulty: ", gameState.difficultyState.getState());

    // Set thresholds from server-fetched data
    gameState.thresholdsState.setThresholds(data.thresholds || {});
    console.log("Loaded leaderboard thresholds from server:", data.thresholds);

    createGame();
    resizeGameToContainer();
  });

  function createGame() {
    const config = {
      type: AUTO,
      width: 1330,
      height: 700,
      parent: "game-container",
      backgroundColor: "#262626",
      fps: {
        target: 150, // Target FPS (matches startGameLoop frequency)
        forceSetTimeOut: false, // Set to true for more consistent timing
      },
      pixelArt: false, // turn OFF for smoothing
      render: { antialias: true },
      physics: {
        default: "arcade",
        arcade: {
          gravity: { y: 0 },
          debug: false,
        },
      },
    };

    game = new Game(config);
    game.scene.add("GUI", GUI);
    game.scene.start("GUI", {
      scaleFactor: 0.7,
      gameState: gameState,
      mode: gameState.modeState.getState() || "unlimited",
      difficulty: gameState.difficultyState.getState() || "medium",
    });
  }

  function resizeGameToContainer(fullScreen = false) {
    if (!game || !game.canvas) return;

    // Force a reflow to get fresh dimensions
    void containerRef?.offsetHeight;

    // Get the actual container dimensions at this moment
    const actualWidth = containerRef?.clientWidth || containerWidth;
    const actualHeight = containerRef?.clientHeight || containerHeight;

    // Reset styles to prevent inconsistencies
    game.canvas.style.width = "";
    game.canvas.style.height = "";

    if (actualWidth > (actualHeight * 1900) / 1000) {
      // Width is constraining factor - fit to height
      if (fullScreen) {
        game.canvas.style.height = actualHeight - 80 + "px"; // Extra space for buttons
      } else {
        game.canvas.style.height = actualHeight - 24 + "px";
      }
      game.canvas.style.width = "auto";
      game.canvas.style.borderRadius = "4px";
    } else {
      // Height is constraining factor - fit to width
      if (fullScreen) {
        game.canvas.style.width = actualWidth - 24 + "px"; // Extra space for padding
      } else {
        game.canvas.style.width = actualWidth - 24 + "px";
      }
      game.canvas.style.height = "auto";
      game.canvas.style.borderRadius = "4px";
    }
  }

  async function toggleFullscreen() {
    fullscreen = !fullscreen;
    if (fullscreen) {
      await containerRef.requestFullscreen();
      // Use requestAnimationFrame for better timing
      requestAnimationFrame(() => {
        requestAnimationFrame(() => resizeGameToContainer(true));
      });
    } else {
      await document.exitFullscreen();
      requestAnimationFrame(() => {
        requestAnimationFrame(() => resizeGameToContainer(false));
      });
    }
  }

  // Handle fullscreen changes to resize game properly
  function handleFullscreenChange() {
    const isFullscreen = !!document.fullscreenElement;
    fullscreen = isFullscreen;
    // Use requestAnimationFrame to ensure container dimensions are updated
    requestAnimationFrame(() => {
      requestAnimationFrame(() => resizeGameToContainer(isFullscreen));
    });
  }
</script>

<svelte:window
  onresize={() => {
    resizeGameToContainer(fullscreen);
    if (!document.fullscreenElement) {
      fullscreen = false;
      fsDocumentationOpen = false;
    }
  }}
/>

<svelte:document onfullscreenchange={handleFullscreenChange} />

<audio src={audio} autoplay loop bind:this={audioRef}></audio>
<Container title="Mini Amusement Parks">
  {#snippet buttons()}
    <div class="flex justify-end gap-2">
      <Button
        variant="skyfall"
        class="rounded-[8px] h-7"
        onclick={() => {
          if (!audioRef) return;
          isMuted = !isMuted;
          audioRef.muted = isMuted;
          console.log("Muted: ", isMuted);
          if (isMuted) {
            audioRef.pause();
          } else {
            audioRef.play();
          }
        }}
      >
        {#if isMuted}
          <VolumeX />
        {:else}
          <Volume2 />
        {/if}
      </Button>
      <Button
        variant="skyfall"
        class="rounded-[8px] h-7"
        onclick={() => {
          toggleFullscreen();
        }}
      >
        {#if fullscreen}
          <Minimize />
        {:else}
          <Maximize />
        {/if}
      </Button>
      <AlertDialog.Root bind:open={documentationOpen}>
        <AlertDialog.Trigger
          class={cn(
            buttonVariants({ variant: "skyfall" }),
            "rounded-[8px] h-7",
          )}
        >
          <BookOpen />
        </AlertDialog.Trigger>
        <AlertDialog.Content
          class="flex flex-col gap-4 min-w-[80vw] rounded-[8px] bg-skyfall-bg z-[150]"
        >
          <AlertDialog.Header class="flex justify-between flex-row">
            <AlertDialog.Title>Game Documentation</AlertDialog.Title>
            <Button
              variant="skyfall"
              class="rounded-[8px] h-7"
              onclick={() => (documentationOpen = false)}>Close</Button
            >
          </AlertDialog.Header>
          <Documentation bind:this={firstDocumentationRef} />
        </AlertDialog.Content>
      </AlertDialog.Root>
    </div>
  {/snippet}
  {#snippet children()}
    <div
      bind:this={containerRef}
      class="flex flex-col justify-center items-center p-1 bg-skyfall-card rounded-[8px] relative {fullscreen
        ? 'w-screen h-screen max-w-none max-h-none'
        : 'max-w-[95vw] max-h-[98vh]'}"
    >
      {#if gameState.loadingState.getState()}
        <div class="absolute top-1/2 flex flex-col items-center gap-2 z-10">
          <Loader2 class="size-10 animate-spin" />
          <span>Loading...</span>
        </div>
      {/if}

      <div
        bind:this={gameContainerRef}
        id="game-container"
        class="border-hidden rounded-[4px] gap-4 flex flex-col justify-center items-end relative"
        style="padding: {fullscreen ? '0' : '12px'};"
      >
        {#if fullscreen}
          {#if fsDocumentationOpen}
            <!-- Imitate alert dialog content -->
            <div
              class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[150] border-1"
            >
              <div
                class="flex flex-col gap-4 bg-skyfall-bg p-6 rounded-[8px] w-400 max-w-[90vw]"
              >
                <div class="flex justify-between flex-row">
                  <h2 class="text-2xl font-bold">Game Documentation</h2>
                  <Button
                    variant="skyfall"
                    class="rounded-[8px] h-7"
                    onclick={() => (fsDocumentationOpen = false)}>Close</Button
                  >
                </div>
                <Documentation />
              </div>
            </div>
          {/if}
          <div class="flex justify-end gap-2">
            <Button
              variant="skyfall"
              class="rounded-[8px] h-7 bg-skyfall-cardforeground hover:bg-skyfall-cardforeground/60"
              onclick={() => {
                toggleFullscreen();
              }}><Minimize /></Button
            >
            <Button
              variant="skyfall"
              class="rounded-[8px] h-7 bg-skyfall-cardforeground hover:bg-skyfall-cardforeground/60"
              onclick={() => {
                fsDocumentationOpen = true;
              }}><BookOpen /></Button
            >
          </div>
        {/if}
      </div>
    </div>
  {/snippet}
</Container>

<!-- Leaderboard submission popup for high scores -->
<HumanSubmissionDialog {gameState} />
