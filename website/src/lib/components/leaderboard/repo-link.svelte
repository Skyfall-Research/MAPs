<script lang="ts">
    /*
     * Simple component to render a Github icon in the repo link column of the leaderboard.
     */
    import { Github } from "@lucide/svelte";

    let { repoLink }: { repoLink: string } = $props();
</script>

<a href={repoLink} target="_blank" class="flex justify-start items-center gap-2"><Github /></a>
