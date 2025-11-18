<script lang="ts">
    /*
     * Placeholder page for the game page.
     */

    import { marked } from "marked";
    import { gfmHeadingId } from "marked-gfm-heading-id";
    import { onMount } from "svelte";
    import Container from "$lib/components/container.svelte";
    import ScrollArea from "$lib/components/ui/scroll-area/scroll-area.svelte";
    import * as AlertDialog from "$lib/components/ui/alert-dialog/";
    import { buttonVariants } from "$lib/components/ui/button";
    import { cn } from "$lib/utils";
    import Button from "$lib/components/ui/button/button.svelte";

    let gameDocs = $state<string>("");
    let documentationOpen = $state(false);

    onMount(() => {
        loadDocumentation();
    });
    marked.use(
        gfmHeadingId({
            prefix: "",
        }),
    );
    const html = $derived(marked.parse(gameDocs));

    function loadDocumentation() {
        fetch("/documentation.md")
            .then((res) => res.text())
            .then((text) => {
                gameDocs = text;
            });
    }
</script>

<ScrollArea class="bg-skyfall-card rounded-[8px] p-3 h-[60vh] border">
    <div class="markdown">
        {@html html}
    </div>
</ScrollArea>
