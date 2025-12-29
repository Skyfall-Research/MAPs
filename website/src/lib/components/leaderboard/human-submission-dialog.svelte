<script lang="ts">
    import * as AlertDialog from "$lib/components/ui/alert-dialog";
    import { Button } from "$lib/components/ui/button";
    import { Input } from "$lib/components/ui/input";
    import { Label } from "$lib/components/ui/label";
    import type { GameState } from "$lib/map_js/game-state.svelte";

    let {
        gameState
    }: {
        gameState: GameState;
    } = $props();

    let leaderboard_name = $state("");
    let submitting = $state(false);
    let errorMessage = $state("");
    let successMessage = $state("");
    let hasScrolledToBottom = $state(false);
    let agreedToTerms = $state(false);

    async function handleSubmit() {
        if (!leaderboard_name.trim()) {
            errorMessage = "Please enter a leaderboard name";
            return;
        }

        submitting = true;
        errorMessage = "";

        try {
            // Use SvelteKit API route which proxies to backend
            // This works reliably in both development and production
            const payload = {
                parkId: gameState.leaderboardSubmissionState.getParkId(),
                is_human: true,
                name: leaderboard_name.trim(),
                resource_setting: "Unlimited",
                difficulty: gameState.leaderboardSubmissionState.getDifficulty(),
                layout: gameState.leaderboardSubmissionState.getLayout(),
                score: gameState.leaderboardSubmissionState.getFinalScore(),
                cost: null,
                repoLink: null,
                paperLink: null,
                validated: false,
                // trajectory is undefined - backend will extract from logger
                saveLocal: false,
                saveToCloud: true
            };

            console.log("Submitting to leaderboard with payload:", payload);

            const response = await fetch('/api/leaderboard', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            console.log("Response received:", {
                status: response.status,
                statusText: response.statusText,
                headers: Object.fromEntries(response.headers.entries()),
                ok: response.ok
            });

            if (!response.ok) {
                // Try to parse as JSON, but handle cases where it's not JSON
                let errorData;
                const contentType = response.headers.get('content-type');
                console.log("Error response content-type:", contentType);

                try {
                    const responseText = await response.text();
                    console.log("Raw error response:", responseText);

                    try {
                        errorData = JSON.parse(responseText);
                    } catch (jsonError) {
                        console.error("Failed to parse error response as JSON:", jsonError);
                        errorData = { message: responseText };
                    }
                } catch (textError) {
                    console.error("Failed to read error response text:", textError);
                    errorData = { message: "Failed to read error response" };
                }

                console.error("Server returned error:", {
                    status: response.status,
                    statusText: response.statusText,
                    errorData: errorData
                });
                errorMessage = errorData.message || "Failed to submit to leaderboard";
                submitting = false;
                return;
            }

            successMessage = "Successfully submitted to leaderboard!";
            submitting = false;

            // Close dialog after 2 seconds
            setTimeout(() => {
                handleClose();
            }, 2000);
        } catch (error) {
            console.error("Error submitting to leaderboard:", error);
            console.error("Error details:", {
                name: error?.name,
                message: error?.message,
                stack: error?.stack,
                fullError: error
            });
            errorMessage = "Failed to connect to server";
            submitting = false;
        }
    }

    function handleScroll(event: Event) {
        const target = event.target as HTMLElement;
        const scrolledToBottom = target.scrollHeight - target.scrollTop <= target.clientHeight + 1;
        if (scrolledToBottom) {
            hasScrolledToBottom = true;
        }
    }

    function handleClose() {
        gameState.leaderboardSubmissionState.setShowPopup(false);
        leaderboard_name = "";
        errorMessage = "";
        successMessage = "";
        hasScrolledToBottom = false;
        agreedToTerms = false;
    }
</script>

<AlertDialog.Root open={gameState.leaderboardSubmissionState.getShowPopup()}>
    <AlertDialog.Content class="flex flex-col gap-4 rounded-[8px] bg-skyfall-bg max-w-[500px]">
        <AlertDialog.Header>
            <AlertDialog.Title class="text-2xl">
                {successMessage ? "Success!" : "Congratulations!"}
            </AlertDialog.Title>
            <AlertDialog.Description class="text-lg">
                {#if successMessage}
                    {successMessage}
                {:else}
                    You scored {gameState.leaderboardSubmissionState.getFinalScore().toLocaleString()}!
                    <br />
                    Would you like to submit your score to the leaderboard?
                {/if}
            </AlertDialog.Description>
        </AlertDialog.Header>

        {#if !successMessage}
            <div class="flex flex-col gap-4">
                <div class="flex flex-col gap-2">
                    <Label for="leaderboard_name">Leaderboard Name</Label>
                    <Input
                        type="text"
                        id="leaderboard_name"
                        placeholder="Enter your Leaderboard Name"
                        bind:value={leaderboard_name}
                        class="rounded-[8px] bg-skyfall-card"
                        disabled={submitting}
                    />
                    {#if errorMessage}
                        <span class="text-red-500 text-sm">{errorMessage}</span>
                    {/if}
                </div>

                <div class="flex flex-col gap-2">
                    <Label>Terms and Conditions</Label>
                    <div
                        class="h-32 overflow-y-auto border rounded-[8px] p-3 bg-skyfall-card text-sm"
                        onscroll={handleScroll}
                    >
                        <p class="font-semibold mb-2">LEADERBOARD DATA CONSENT & PRIVACY NOTICE</p>

                        <p class="mb-2">
                        By choosing to submit your score to the leaderboard, you agree that limited gameplay data
                        (such as your score, duration, and in-game actions) and a <strong>leaderboard name of your choice</strong>
                        will be collected and displayed publicly.
                        </p>

                        <p class="mb-2">
                        This data is used solely to operate and maintain the leaderboard, detect unfair play, 
                        improve the game experience, and conduct <strong>aggregate analyses comparing human 
                        performance to artificial intelligence (AI) agents</strong>.
                        </p>

                        <p class="mb-2">
                        We do not collect personal information such as real names or email addresses. 
                        All analyses use anonymous or aggregated data only. Your leaderboard entry (leaderboard name and score)
                        will be visible to other players while the leaderboard is active.
                        </p>

                        <p class="mb-2">
                        You may request removal of your leaderboard entry at any time by contacting us at 
                        <a href="mailto:stephane@skyfall.ai" class="text-blue-500 underline">stephane@skyfall.ai</a>.
                        </p>

                        <p class="mb-2">
                        Submitting your score is optional. By clicking the checkbox below and confirming submission,
                        you consent to the collection and public display of your gameplay data and leaderboard name as described above.
                        </p>

                        <p class="mb-2 font-semibold">
                        Leaderboard Moderation
                        </p>

                        <p class="mb-2">
                        We reserve the right to remove any user or entry from the leaderboard at our discretion, 
                        for any reason, including but not limited to inappropriate or offensive leaderboard names, 
                        suspected cheating, data manipulation, or other behavior deemed inconsistent with fair play 
                        and community standards.
                        </p>

                        <p class="text-xs text-gray-500">
                        Last updated: November 10, 2025
                        </p>

                    </div>
                    <div class="flex items-center gap-2">
                        <input
                            type="checkbox"
                            id="terms-agreement"
                            bind:checked={agreedToTerms}
                            disabled={!hasScrolledToBottom || submitting}
                            class="cursor-pointer disabled:cursor-not-allowed"
                        />
                        <Label
                            for="terms-agreement"
                            class="cursor-pointer text-sm {!hasScrolledToBottom ? 'opacity-50' : ''}"
                        >
                            I have read and agree to the terms and conditions outlined above (please scroll to the bottom.)
                        </Label>
                    </div>
                </div>

                <AlertDialog.Footer class="flex gap-2 justify-end">
                    <Button
                        variant="skyfall"
                        class="rounded-[8px]"
                        onclick={handleClose}
                        disabled={submitting}
                    >
                        Cancel
                    </Button>
                    <Button
                        variant="skyfall"
                        class="rounded-[8px]"
                        onclick={handleSubmit}
                        disabled={submitting || !agreedToTerms}
                    >
                        {submitting ? "Submitting..." : "Submit"}
                    </Button>
                </AlertDialog.Footer>
            </div>
        {/if}
    </AlertDialog.Content>
</AlertDialog.Root>
