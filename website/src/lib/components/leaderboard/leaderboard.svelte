<script lang="ts">
    /*
     *  The main table component for the leaderboard.
     *  Uses the TanStack table library with Shadcn Svelte Data Table component.
     *  Most of the code is from the Shadcn Svelte tutorial:
     *  https://shadcn-svelte.com/docs/components/data-table
     */
    import {
        type ColumnDef,
        getCoreRowModel,
        getSortedRowModel,
        type SortingState,
    } from "@tanstack/table-core";
    import {
        createSvelteTable,
        FlexRender,
    } from "$lib/components/ui/data-table";
    import * as Table from "$lib/components/ui/table";
    import type { LeaderboardEntry } from "$lib/types";

    // Define and get the props for the component.
    type DataTableProps<TData> = {
        columns: ColumnDef<TData>[];
        data: TData[];
    };
    let { data, columns }: DataTableProps<LeaderboardEntry> = $props();

    // Sorting state - default sort by score descending.
    let sorting = $state<SortingState>([{ id: "score", desc: true }]);

    // Create the table.
    const table = createSvelteTable({
        get data() {
            return data;
        },
        columns,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        onSortingChange: (updater) => {
            if (typeof updater === "function") {
                sorting = updater(sorting);
            } else {
                sorting = updater;
            }
        },
        state: {
            get sorting() {
                return sorting;
            },
        },
        sortDescFirst: true,
        defaultColumn: {
            size: 10,
            minSize: 10,
            maxSize: 10,
        },
    });
</script>

<div class="rounded-[8px] overflow-hidden w-full min-w-[60vw] max-w-[85vw]">
    <Table.Root>
        <!--
            Table headers
        -->
        <Table.Header
            class="bg-skyfall-cardforeground hover:bg-skyfall-cardforeground"
        >
            <!-- headerGroup.id and header.id are used as keys for the iterator to prevent bloat data creation-->
            {#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
                <Table.Row
                    class="hover:[&,&>svelte-css-wrapper]:[&>th,td]:bg-skyfall-cardforeground text-[16px]"
                >
                    {#each headerGroup.headers as header (header.id)}
                        <Table.Head colspan={header.colSpan}>
                            {#if !header.isPlaceholder}
                                <FlexRender
                                    content={header.column.columnDef.header}
                                    context={header.getContext()}
                                />
                            {/if}
                        </Table.Head>
                    {/each}
                </Table.Row>
            {/each}
        </Table.Header>
        <!--
            Table body
        -->
        <Table.Body>
            {#each table.getRowModel().rows as row (row.id)}
                <Table.Row
                    data-state={row.getIsSelected() && "selected"}
                    class="bg-skyfall-card hover:bg-skyfall-cardforeground"
                >
                    {#each row.getVisibleCells() as cell (cell.id)}
                        <Table.Cell>
                            <FlexRender
                                content={cell.column.columnDef.cell}
                                context={cell.getContext()}
                            />
                        </Table.Cell>
                    {/each}
                </Table.Row>
            {:else}
                <Table.Row
                    class="bg-skyfall-card hover:bg-skyfall-cardforeground"
                >
                    <Table.Cell
                        colspan={columns.length}
                        class="h-24 text-center">No results.</Table.Cell
                    >
                </Table.Row>
            {/each}
        </Table.Body>
    </Table.Root>
</div>
