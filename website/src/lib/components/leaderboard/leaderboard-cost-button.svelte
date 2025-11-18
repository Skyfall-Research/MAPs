<script lang="ts">
    /*
     * Simple component to render a button as the header for the cost column.
     * Toggles the sorting of the cost column.
     */
    import type { ComponentProps } from "svelte";
    import { ArrowUp, ArrowDown } from "@lucide/svelte";
    import { Button } from "$lib/components/ui/button";
    import type { Column } from "@tanstack/table-core";
    import SortingIcon from "./sorting-icon.svelte";
    let {
        variant = "skyfall",
        column,
        ...restProps
    }: ComponentProps<typeof Button> & {
        column: Column<any>;
    } = $props();

    // isAscending determines the direction of the sorting icon and helps toggle the sorting in the column.
    let isAscending = $derived(column.getIsSorted() === "asc");

    // show is true when the cost column is sorted. If true, the MoveUp or MoveDown icon is shown.
    // If false, the ArrowUpDown icon is shown to indicate that no sorting is applied.
    let show = $derived(column.getIsSorted());
</script>

<!-- We apply the restProps so that the button can be styled from the parent component-->
<Button
    {variant}
    {...restProps}
    onclick={() => {
        isAscending = !isAscending;
        column.toggleSorting(!isAscending);
    }}
    class="bg-skyfall-cardforeground hover:bg-skyfall-card border-none rounded flex w-fit ml-auto"
>
    <span class="text-[16px]">Cost</span>
    {#if show}
        {#if isAscending}
            <div class="w-4 h-8 flex items-center justify-center">
                <ArrowUp class="size-4 stroke-3" />
            </div>
        {:else}
            <div class="w-4 h-8 flex items-center justify-center">
                <ArrowDown class="size-4 stroke-3" />
            </div>
        {/if}
    {:else}
        <SortingIcon />
    {/if}
</Button>
