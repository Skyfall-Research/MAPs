<script lang="ts">
    /*
     * Simple component to render a paper icon in the paper link column of the leaderboard.
     */
    import { File } from "@lucide/svelte";

    let { paperLink }: { paperLink: string } = $props();
</script>

<a href={paperLink} target="_blank" class="flex justify-start items-center gap-2"><File /></a>
