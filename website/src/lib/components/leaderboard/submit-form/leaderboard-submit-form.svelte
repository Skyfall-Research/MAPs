<script lang="ts">
    /*
     * The form component for submitting to the leaderboard.
     * Submits to the /api/leaderboard/manual API route which proxies to the backend.
     *
     * The form fields are:
     * - Park ID
     * - AI Model Name
     * - Resource Setting selector
     * - Cost
     * - Trajectory TSV file upload
     * - Repository Link
     * - Paper Link
     *
     * Note: Difficulty, Layout, and Score are extracted from the trajectory file by the backend.
     *
     * Each form field has a label and an input field.
     */
    import { Input } from "$lib/components/ui/input";
    import { Button } from "$lib/components/ui/button";
    import { Label } from "$lib/components/ui/label";
    import Selector from "$lib/components/leaderboard/selector.svelte";

    // Form state
    let parkId = $state("");
    let name = $state("");
    let resourceSetting = $state("docs");
    let cost = $state<number | null>(null);
    let repoLink = $state("");
    let paperLink = $state("");
    let selectedFile = $state<File | null>(null);
    let fileInputRef: HTMLInputElement;

    // Submission state
    let submitting = $state(false);
    let errorMessage = $state("");
    let successMessage = $state("");
    let showSuccess = $state(false);

    // Field errors
    let errors = $state<Record<string, string>>({});

    // Function handle the input of the cost field. Generated using Cursor.
    function handleCostInput(event: Event) {
        const input = event.target as HTMLInputElement;
        const value = input.value;

        // Check if there's a decimal point and more than 2 digits after it
        if (value.includes(".")) {
            const parts = value.split(".");
            if (parts[1] && parts[1].length > 2) {
                input.value = parseFloat(value).toFixed(2);
            }
        }
    }

    // Handle trajectory file selection
    function handleFileSelect(event: Event) {
        const input = event.target as HTMLInputElement;
        if (input.files && input.files.length > 0) {
            selectedFile = input.files[0];
        }
    }

    // Trigger file input click
    function triggerFileInput() {
        fileInputRef?.click();
    }

    // Validate form
    function validateForm(): boolean {
        errors = {};

        if (!parkId.trim()) {
            errors.parkId = "Park ID is required!";
        }
        if (!name.trim()) {
            errors.name = "Name is required!";
        }
        if (name.length > 50) {
            errors.name = "Name can't be more than 50 characters.";
        }
        if (cost !== null && cost < 0) {
            errors.cost = "Cost can't be negative!";
        }
        if (!selectedFile) {
            errors.trajectoryFile = "Trajectory file is required!";
        }

        return Object.keys(errors).length === 0;
    }

    // Handle form submission
    async function handleSubmit(event: Event) {
        event.preventDefault();

        if (!validateForm()) {
            return;
        }

        submitting = true;
        errorMessage = "";
        successMessage = "";
        showSuccess = false;

        console.log("Submitting manual leaderboard entry");

        try {
            const formData = new FormData();
            formData.append('parkId', parkId);
            formData.append('name', name);
            formData.append('resource_setting', resourceSetting);
            if (cost !== null) {
                formData.append('cost', cost.toString());
            }
            if (repoLink.trim()) {
                formData.append('repoLink', repoLink);
            }
            if (paperLink.trim()) {
                formData.append('paperLink', paperLink);
            }
            if (selectedFile) {
                formData.append('trajectoryFile', selectedFile);
            }

            console.log("Sending request to /api/leaderboard/manual");

            const response = await fetch('/api/leaderboard/manual', {
                method: 'POST',
                body: formData
            });

            console.log("Response received:", response.status);

            if (!response.ok) {
                const errorData = await response.json();
                console.error("Submission failed:", errorData);
                errorMessage = errorData.message || "Failed to submit entry";
                submitting = false;
                return;
            }

            const data = await response.json();
            console.log("Submission successful:", data);

            successMessage = data.message || "Submission successful!";
            showSuccess = true;

            // Clear form
            parkId = '';
            name = '';
            cost = null;
            repoLink = '';
            paperLink = '';
            resourceSetting = 'docs';
            selectedFile = null;
            if (fileInputRef) {
                fileInputRef.value = '';
            }

            // Hide success message after 5 seconds
            setTimeout(() => {
                showSuccess = false;
            }, 5000);

            submitting = false;
        } catch (error) {
            console.error("Error submitting:", error);
            errorMessage = "Failed to connect to server";
            submitting = false;
        }
    }
</script>

<form
    class="flex flex-col gap-4 items-start w-full"
    onsubmit={handleSubmit}
>
    <!-- Park ID -->
    <Label for="parkId">Park ID</Label>
    <Input
        type="text"
        placeholder="unique-park-id"
        name="parkId"
        id="parkId"
        class="rounded-[8px] bg-skyfall-bg"
        bind:value={parkId}
    />
    {#if errors.parkId}
        <span class="text-red-500 text-sm">{errors.parkId}</span>
    {/if}

    <!-- AI Model Name -->
    <Label for="name">AI Model Name</Label>
    <Input
        type="text"
        placeholder="Model Name"
        name="name"
        id="name"
        class="rounded-[8px] bg-skyfall-bg"
        bind:value={name}
    />
    {#if errors.name}
        <span class="text-red-500 text-sm">{errors.name}</span>
    {/if}

    <!-- Resource Setting -->
    <Label for="resourceSetting">Resource Setting</Label>
    <Selector
        variant="resource_setting"
        bind:selectorState={resourceSetting}
        class="rounded-[8px] bg-skyfall-bg"
    />
    {#if errors.resource_setting}
        <span class="text-red-500 text-sm">{errors.resource_setting}</span>
    {/if}

    <!--Cost-->
    <Label for="cost">Cost</Label>
    <div class="relative w-full flex">
        <span
            class="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
            >$</span
        >
        <Input
            type="number"
            placeholder="0.00"
            step="0.01"
            min="0"
            class="rounded-[8px] bg-skyfall-bg pl-7"
            id="cost"
            oninput={handleCostInput}
            name="cost"
            bind:value={cost}
        />
    </div>
    {#if errors.cost}
        <span class="text-red-500 text-sm">{errors.cost}</span>
    {/if}

    <!-- Trajectory File Upload -->
    <Label for="trajectoryFile">Trajectory File (.tsv)</Label>
    <div class="flex flex-col gap-2 w-full">
        <!-- Hidden file input -->
        <input
            type="file"
            accept=".tsv"
            name="trajectoryFile"
            id="trajectoryFile"
            bind:this={fileInputRef}
            onchange={handleFileSelect}
            class="hidden"
        />
        <!-- Styled button to trigger file selection -->
        <Button
            type="button"
            variant="skyfall"
            class="rounded-[8px] bg-skyfall-bg w-full justify-start"
            onclick={triggerFileInput}
        >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            {selectedFile ? selectedFile.name : "Click to upload trajectory file (.tsv)"}
        </Button>
        {#if selectedFile}
            <span class="text-sm text-muted-foreground">Selected: {selectedFile.name}</span>
        {/if}
    </div>
    {#if errors.trajectoryFile}
        <span class="text-red-500 text-sm">{errors.trajectoryFile}</span>
    {/if}

    <!-- Repository Link -->
    <Label for="repoLink">Repository Link (Optional)</Label>
    <Input
        type="text"
        placeholder="https://github.com/..."
        class="rounded-[8px] bg-skyfall-bg"
        id="repoLink"
        name="repoLink"
        bind:value={repoLink}
    />
    {#if errors.repoLink}
        <span class="text-red-500 text-sm">{errors.repoLink}</span>
    {/if}

    <!-- Paper Link -->
    <Label for="paperLink">Paper Link (Optional)</Label>
    <Input
        type="text"
        placeholder="https://arxiv.org/..."
        class="rounded-[8px] bg-skyfall-bg"
        id="paperLink"
        name="paperLink"
        bind:value={paperLink}
    />
    {#if errors.paperLink}
        <span class="text-red-500 text-sm">{errors.paperLink}</span>
    {/if}

    <!-- Success message -->
    {#if showSuccess}
        <div class="w-full p-3 rounded-[8px] bg-green-500/10 border border-green-500/20">
            <span class="text-green-500 text-sm font-medium">{successMessage}</span>
        </div>
    {/if}

    <!-- Form-level error message (backend failures) -->
    {#if errorMessage}
        <div class="w-full p-3 rounded-[8px] bg-red-500/10 border border-red-500/20">
            <span class="text-red-500 text-sm font-medium">{errorMessage}</span>
        </div>
    {/if}

    <!-- Submit button. If submitting, then the button is disabled and the text is changed to "Submitting..."-->
    {#if submitting}
        <Button
            type="submit"
            class="rounded-[8px] bg-skyfall-bg"
            disabled
            variant="skyfall">Submitting...</Button
        >
    {:else}
        <Button
            type="submit"
            class="rounded-[8px] bg-skyfall-bg"
            variant="skyfall">Submit</Button
        >
    {/if}
</form>
