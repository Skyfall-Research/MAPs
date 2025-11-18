<script lang="ts">
    /*
     * Success page for the leaderboard submit form.
     */
    import Container from "$lib/components/container.svelte";
</script>

<Container title="Success!">
    {#snippet children()}
        <div
            class="flex justify-center px-10 bg-skyfall-card rounded-[8px] p-10"
        >
            <p>Your entry has been submitted successfully.</p>
        </div>
    {/snippet}
</Container>

