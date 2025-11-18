<script lang="ts">
    /*
     * A difficult selector component
     * Has three hardcoded difficulties: easy, medium, hard
     */
    import { Button } from "$lib/components/ui/button";
    import { ChevronDown } from "@lucide/svelte";
    import * as Popover from "$lib/components/ui/popover";
    import { cn } from "$lib/utils";
    let {
        selectorState = $bindable(""),
        class: className = "",
        variant,
    }: {
        selectorState: string;
        class?: string;
        variant:
            | "difficulty"
            | "humanMachineCombined"
            | "humanMachine"
            | "resource_setting"
            | "layout";
    } = $props();
    let open = $state(false);
    let options = (() => {
        switch (variant) {
            case "difficulty":
                return ["Easy", "Medium", "Hard"];
            case "humanMachineCombined":
                return ["Combined", "AI", "Human"];
            case "humanMachine":
                return ["AI", "Human"];
            case "resource_setting":
                return ["Docs", "Few-shot", "Few-shot + Docs", "Unlimited"];
            case "layout":
                return ["All", "The Islands", "Ribs", "Zig Zag"];
        }
    })();

    // Convert display name to database format (lowercase with underscores/hyphens)
    function toDbFormat(displayName: string, variantType: string): string {
        if (variantType === "resource_setting") {
            // Special handling for resource_setting
            const map: Record<string, string> = {
                "Docs": "docs",
                "Few-shot": "few-shot",
                "Few-shot + Docs": "few-shot+docs",
                "Unlimited": "unlimited"
            };
            return map[displayName] || displayName.toLowerCase();
        }
        if (variantType === "layout") {
            // Special handling for layout
            const map: Record<string, string> = {
                "All": "all",
                "The Islands": "the_islands",
                "Ribs": "ribs",
                "Zig Zag": "zig_zag"
            };
            return map[displayName] || displayName.toLowerCase().replace(/\s+/g, '_');
        }
        // For difficulty
        return displayName.toLowerCase().replace(/\s+/g, '_');
    }

    // Convert database format to display format
    function toDisplayFormat(dbName: string, variantType: string): string {
        if (variantType === "difficulty") {
            const map: Record<string, string> = {
                "easy": "Easy",
                "medium": "Medium",
                "hard": "Hard"
            };
            return map[dbName] || dbName;
        }
        if (variantType === "layout") {
            const map: Record<string, string> = {
                "all": "All",
                "the_islands": "The Islands",
                "zig_zag": "Zig Zag",
                "ribs": "Ribs"
            };
            return map[dbName] || dbName;
        }
        if (variantType === "resource_setting") {
            const map: Record<string, string> = {
                "docs": "Docs",
                "few-shot": "Few-shot",
                "few-shot+docs": "Few-shot + Docs",
                "unlimited": "Unlimited"
            };
            return map[dbName] || dbName;
        }
        return dbName;
    }

    // Get current display value
    let displayValue = $derived((variant === "difficulty" || variant === "layout" || variant === "resource_setting")
        ? toDisplayFormat(selectorState, variant)
        : selectorState);
</script>

<Popover.Root bind:open>
    <Popover.Trigger>
        <Button
            variant="skyfall"
            class={cn("rounded-[8px] h-7 flex justify-between", className)}
        >
            <span>{displayValue}</span>
            <ChevronDown class="size-4" /></Button
        >
    </Popover.Trigger>
    <Popover.Content
        class={cn(
            "flex flex-col gap-2 px-2 py-2 rounded-[8px] w-fit bg-skyfall-card",
            className,
        )}
    >
        {#each options as option}
            <Button
                variant="skyfall"
                class={cn("rounded flex justify-between h-7", className)}
                onclick={() => {
                    selectorState = (variant === "difficulty" || variant === "layout" || variant === "resource_setting")
                        ? toDbFormat(option, variant)
                        : option;
                    open = false;
                }}>{option}</Button
            >
        {/each}
    </Popover.Content>
</Popover.Root>
