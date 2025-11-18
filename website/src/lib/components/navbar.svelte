<script lang="ts">
    /*
     * Simple navbar component
     */
    import Button from "$lib/components/ui/button/button.svelte";
    import Logo from "$lib/components/assets/logo.svelte";
</script>

<div
    class="fixed top-3 left-0 right-0 w-full flex justify-center flex flex-col items-center gap-10 z-50 w-screen"
>
    <div
        class="flex w-full max-w-[95vw] justify-between
        items-center rounded-full md:px-12 px-4 py-2 md:py-4 bg-skyfall-bg hover:translate-y-[-1.5px] z-50"
    >
        <div class="flex items-center gap-8 sm:gap-24">
            <a href="/" class="max-w-30 sm:max-w-none"><Logo height="20px" /></a
            >
            <div class="flex items-center md:gap-4 gap-2">
                <Button
                    variant="link"
                    href="/"
                    class="text-xs sm:text-sm md:text-md">Home</Button
                >
                <Button
                    variant="link"
                    href="/leaderboard"
                    class="text-xs sm:text-sm md:text-md">Leaderboard</Button
                >
            </div>
        </div>
        <div class="flex gap-4">
            <Button
                variant="default"
                href="/play"
                class="bg-linear-to-r from-[#2FA1C3] to-[#60A777] border rounded px-2 shadow-[0px_3.5px_0px_0px_#1F7644]"
                ><strong>Play Game</strong></Button
            >
        </div>
    </div>
</div>
