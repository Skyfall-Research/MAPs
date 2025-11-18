/*
 * Column definitions for the leaderboard table.
 * Defines how to render the table headers and cells.
 */
import type { LeaderboardEntry } from "$lib/types";
import { type ColumnDef } from "@tanstack/table-core";
import { createRawSnippet, mount, unmount } from "svelte";
import { renderComponent, renderSnippet } from "$lib/components/ui/data-table";
import RepoLink from "./repo-link.svelte";
import PaperLink from "./paper-link.svelte";
import LeaderboardCostButton from "./leaderboard-cost-button.svelte";
import LeaderboardScoreButton from "./leaderboard-score-button.svelte";

export const columns: ColumnDef<LeaderboardEntry>[] = [
    // Position column - shows the row number in the current display order (1-based)
    {
        header: "",
        id: "position",
        size: 3,
        minSize: 3,
        maxSize: 3,
        cell: ({row, table}) => {
            // Get the position in the current sorted/filtered view
            const sortedRows = table.getRowModel().rows;
            const position = sortedRows.findIndex(r => r.id === row.id) + 1;
            const positionSnippet = createRawSnippet<[{position: number}]>((getPosition) => {
                const pos = getPosition().position;
                return {
                    render: () => `<div class="text-right w-[3ch] font-spacemono">${pos}</div>`
                };
            })
            return renderSnippet(positionSnippet, {position})
        }
    },
    // For the score, render the LeaderboardScoreButton component as the header (for sorting) and align the cell text to the right.
    {
        header: ({column}) => {
            return renderComponent(LeaderboardScoreButton, { column })
        },
        accessorKey: "score",
        sortingFn: (rowA, rowB) => {
            const scoreA = Number(rowA.getValue("score"));
            const scoreB = Number(rowB.getValue("score"));
            return scoreA - scoreB;
        },
        cell: ({row}) => {
            const cellScoreSnippet = createRawSnippet<[{score: number}]>((getScore) => {
                const score = getScore().score;
                return {
                    render: () => `<div class="font-medium text-right pr-3 font-spacemono">${Number(score).toLocaleString("en-US")}</div>`
                };
            })
            return renderSnippet(cellScoreSnippet, {score: row.getValue("score")})
        }
    },
    // For the name, just render the value.
    {
        header: "Name",
        accessorKey: "name",
    },
    // For the type, render "Human" or "AI"
    {
        header: () => {
            const headerSnippet = createRawSnippet(() => {
                return {
                    render: () => `<div class="text-center">Type</div>`
                };
            })
            return renderSnippet(headerSnippet, {})
        },
        accessorKey: "is_human",
        cell: ({row}) => {
            const cellTypeSnippet = createRawSnippet<[{isHuman: boolean}]>((getType) => {
                const isHuman = getType().isHuman;
                return {
                    render: () => `<div class="text-center">${isHuman ? 'Human' : 'AI'}</div>`
                };
            })
            return renderSnippet(cellTypeSnippet, {isHuman: row.getValue("is_human")})
        }
    },
    // For the validated status, render a checkmark or X
    {
        header: () => {
            const headerSnippet = createRawSnippet(() => {
                return {
                    render: () => `<div class="text-center">Validated</div>`
                };
            })
            return renderSnippet(headerSnippet, {})
        },
        accessorKey: "validated",
        cell: ({row}) => {
            const cellValidatedSnippet = createRawSnippet<[{validated: boolean}]>((getValidated) => {
                const validated = getValidated().validated;
                return {
                    render: () => `<div class="text-center">${validated ? '✓' : '✗'}</div>`
                };
            })
            return renderSnippet(cellValidatedSnippet, {validated: row.getValue("validated")})
        }
    },
    // For the layout, render the formatted layout name
    {
        header: () => {
            const headerSnippet = createRawSnippet(() => {
                return {
                    render: () => `<div class="text-center">Layout</div>`
                };
            })
            return renderSnippet(headerSnippet, {})
        },
        accessorKey: "layout",
        cell: ({row}) => {
            const cellLayoutSnippet = createRawSnippet<[{layout: string}]>((getLayout) => {
                const layout = getLayout().layout;
                const layoutMap: Record<string, string> = {
                    "the_islands": "The Islands",
                    "zig_zag": "Zig Zag",
                    "ribs": "Ribs"
                };
                const displayName = layoutMap[layout] || layout;
                return {
                    render: () => `<div class="text-center">${displayName}</div>`
                };
            })
            return renderSnippet(cellLayoutSnippet, {layout: row.getValue("layout")})
        }
    },
    // For the resource setting, render the formatted resource name
    {
        header: () => {
            const headerSnippet = createRawSnippet(() => {
                return {
                    render: () => `<div class="text-center">Resources</div>`
                };
            })
            return renderSnippet(headerSnippet, {})
        },
        accessorKey: "resource_setting",
        cell: ({row}) => {
            const cellResourceSnippet = createRawSnippet<[{resourceSetting: string}]>((getResource) => {
                const resourceSetting = getResource().resourceSetting;
                const resourceMap: Record<string, string> = {
                    "docs": "Docs",
                    "few-shot": "Few-shot",
                    "few-shot+docs": "Few-shot + Docs",
                    "unlimited": "Unlimited"
                };
                const displayName = resourceMap[resourceSetting] || resourceSetting;
                return {
                    render: () => `<div class="text-center">${displayName}</div>`
                };
            })
            return renderSnippet(cellResourceSnippet, {resourceSetting: row.getValue("resource_setting")})
        }
    },
    // For the cost, render the LeaderboardCostButton component as the header (for sorting) and align the cell text to the right.
    // Also format the cost to render in USD. If the entry is from a human, show "-" instead.
    {
        accessorKey: "cost",
        header: ({column}) => {
            return renderComponent(LeaderboardCostButton, { column })
        },
        cell: ({row}) => {
            const formatter = new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "USD",
            })
            const cellAmountSnippet = createRawSnippet<[{cost: number | null | undefined, isHuman: boolean}]>((getData) => {
                const amount = getData().cost;
                const isHuman = getData().isHuman;
                return {
                    render: () => `<div class="text-right pr-3 font-medium font-spacemono">${isHuman ? '-' : (amount != null ? formatter.format(amount) : 'N/A')}</div>`
                };
            })
            return renderSnippet(cellAmountSnippet, {cost: row.getValue("cost"), isHuman: row.getValue("is_human")})
        }
    },
    // For the time taken, convert from milliseconds and display in HH:MM:SS format.
    {
        header: () => {
            const headerSnippet = createRawSnippet(() => {
                return {
                    render: () => `<div class="text-right pr-3">Time</div>`
                };
            })
            return renderSnippet(headerSnippet, {})
        },
        accessorKey: "timeTaken",
        cell: ({row}) => {
            const cellTimeSnippet = createRawSnippet<[{timeTaken: number | null | undefined}]>((getTime) => {
                const timeMs = getTime().timeTaken;
                let formattedTime = 'N/A';

                if (timeMs != null) {
                    // Convert milliseconds to HH:MM:SS
                    const totalSeconds = Math.floor(timeMs / 1000);
                    const hours = Math.floor(totalSeconds / 3600);
                    const minutes = Math.floor((totalSeconds % 3600) / 60);
                    const seconds = totalSeconds % 60;

                    // Format with leading zeros
                    const hh = String(hours).padStart(2, '0');
                    const mm = String(minutes).padStart(2, '0');
                    const ss = String(seconds).padStart(2, '0');

                    formattedTime = `${hh}:${mm}:${ss}`;
                }

                return {
                    render: () => `<div class="text-right pr-3 font-spacemono">${formattedTime}</div>`
                };
            })
            return renderSnippet(cellTimeSnippet, {timeTaken: row.getValue("timeTaken")})
        }
    },
    // For the code, render the RepoLink component (just a code icon)as the header and align it to the right.
    {
        header: "Code",
        accessorKey: "repoLink",
        cell: ({row}) => {
            const cellRepoLinkSnippet = createRawSnippet<[{repoLink: string}]>((getRepoLink) => {
                const repoLink = getRepoLink().repoLink;
                return {
                    render: () => ( repoLink ? `<div class="flex justify-end"></div>` : `<div hidden></div>`),
                    setup: (node) => {
                        // function to mount the RepoLink component (can't simply include it in the snippet)
                        const comp = mount(RepoLink, {target: node, props: {repoLink}})
                        return () => unmount(comp)
                    }
                };
            })
            return renderSnippet(cellRepoLinkSnippet, {repoLink: row.getValue("repoLink")})
        },
    },
    // For the paper, render the PaperLink component (just a scroll icon) as the header and align it to the right.
    {
        header: "Paper",
        accessorKey: "paperLink",
        cell: ({row}) => {
            const cellPaperLinkSnippet = createRawSnippet<[{paperLink: string}]>(getPaperLink => {
                const paperLink = getPaperLink().paperLink;
                return {
                    render: () => ( paperLink ? `<div class="flex justify-end"></div>` : `<div hidden></div>`),
                    setup: (node) => {
                        // function to mount the PaperLink component (can't simply include it in the snippet)
                        const comp = mount(PaperLink, {target: node, props: {paperLink}})
                        return () => unmount(comp)
                    }
                }
            })
            return renderSnippet(cellPaperLinkSnippet, {paperLink: row.getValue("paperLink")})
        }
    },
]