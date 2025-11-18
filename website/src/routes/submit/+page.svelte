<script lang="ts">
    import LeaderboardSubmitForm from "$lib/components/leaderboard/submit-form/leaderboard-submit-form.svelte";
    import Container from "$lib/components/container.svelte";
    import ScrollArea from "$lib/components/ui/scroll-area/scroll-area.svelte";
</script>

<Container title="Submit a new entry">
    {#snippet children()}
        <ScrollArea
            class="bg-skyfall-card rounded-[8px] p-3 h-[40vh] flex justify-center"
        >
            <div class="w-full flex justify-center">
                <div class="p-10 w-150">
                    <LeaderboardSubmitForm />
                </div>
            </div>
        </ScrollArea>
    {/snippet}
</Container>
