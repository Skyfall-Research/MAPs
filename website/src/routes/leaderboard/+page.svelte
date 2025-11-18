<script lang="ts">
  /*
   * Main leaderboard page.
   * Contains the leaderboard table and the submit form.
   * The leaderboard table is rendered conditionally based on the difficulty selected.
   * The submit form is rendered below the leaderboard table.
   * The difficulty selector is rendered above the leaderboard table.
   *
   * TODO in the future: make the leaderboard area height fixed.
   * Right now, when changing difficulty, the submission form moves up or down.
   */
  import { columns } from "$lib/components/leaderboard/columns";
  import Leaderboard from "$lib/components/leaderboard/leaderboard.svelte";
  import Container from "$lib/components/container.svelte";
  import { ArrowRight } from "@lucide/svelte";
  import { Button } from "$lib/components/ui/button";
  import Selector from "$lib/components/leaderboard/selector.svelte";
  import trophy from "$lib/assets/Trophy.png";

  const { data } = $props();
  const { leaderBoardEntries } = data;
  let difficulty = $state("easy");
  let selectorState = $state("Combined");
  let resourceSettingState = $state("unlimited");
  let layoutState = $state("all");

  // Hierarchical resource setting filter
  // Returns true if the entry's resource setting should be included based on the selected filter
  function matchesResourceSetting(
    entryResourceSetting: string,
    selectedResourceSetting: string,
  ): boolean {
    if (selectedResourceSetting === "unlimited") {
      // Unlimited includes all: unlimited, few-shot+docs, few-shot, docs
      return true;
    } else if (selectedResourceSetting === "few-shot+docs") {
      // few-shot+docs includes: few-shot+docs, few-shot, docs
      return ["few-shot+docs", "few-shot", "docs"].includes(
        entryResourceSetting,
      );
    } else {
      // docs and few-shot only match exact
      return entryResourceSetting === selectedResourceSetting;
    }
  }
</script>

<div class="flex flex-col gap-4 items-center">
  <Container title="Leaderboard">
    {#snippet icon()}
      <img src={trophy} alt="Trophy" class="size-12" />
    {/snippet}
    {#snippet buttons()}
      <div class="flex flex-col md:flex-row gap-2">
        <div class="flex gap-2">
          <Selector variant="layout" bind:selectorState={layoutState} />
          <Selector
            variant="resource_setting"
            bind:selectorState={resourceSettingState}
          />
        </div>
        <div class="flex gap-2">
          <Selector variant="humanMachineCombined" bind:selectorState />
          <Selector variant="difficulty" bind:selectorState={difficulty} />
        </div>
      </div>
    {/snippet}
    {#snippet children()}
      <div class="flex flex-col gap-1 items-end">
        <Leaderboard
          {columns}
          data={leaderBoardEntries.filter(
            (entry) =>
              entry.difficulty === difficulty &&
              (selectorState === "Combined" ||
                (selectorState === "AI" && !entry.is_human) ||
                (selectorState === "Human" && entry.is_human)) &&
              (entry.is_human ||
                matchesResourceSetting(
                  entry.resource_setting,
                  resourceSettingState,
                )) &&
              (layoutState === "all" || entry.layout === layoutState),
          )}
        />
      </div>
    {/snippet}
  </Container>
  <Button variant="skyfall" href="/submit" class="mt-10 text-md px-6 py-5"
    >Submit your Entry <ArrowRight strokeWidth={3} />
  </Button>
</div>
