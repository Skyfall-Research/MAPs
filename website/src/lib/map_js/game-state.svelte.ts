
import { writable } from "svelte/store";

function createLoadingState() {
    let state = $state(true);

    return {
        getState() { return state },
        setState(value: boolean) { state = value },
    }
}

function createModeState(){
    let state = $state<string | null>(null);

    return {
        getState() { return state },
        setState(value: string | null) { 
            if(value !== "few-shot" && value !== "few-shot+docs" && value !== "unlimited") {
                throw new Error("Invalid mode: " + value);
            }
            state = value 
        },
    }
}

function createDifficultyState(){
    let state = $state<string | null>(null);

    return {
        getState() { return state },
        setState(value: string | null) {
            if(value !== "easy" && value !== "medium" && value !== "hard") {
                throw new Error("Invalid difficulty: " + value);
            }
            state = value
        },
    }
}

function createLeaderboardSubmissionState(){
    let showPopup = $state(false);
    let finalScore = $state(0);
    let parkId = $state<string | null>(null);
    let difficulty = $state<string | null>(null);
    let layout = $state<string | null>(null);

    return {
        getShowPopup() { return showPopup },
        setShowPopup(value: boolean) { showPopup = value },
        getFinalScore() { return finalScore },
        setFinalScore(value: number) { finalScore = value },
        getParkId() { return parkId },
        setParkId(value: string | null) { parkId = value },
        getDifficulty() { return difficulty },
        setDifficulty(value: string | null) { difficulty = value },
        getLayout() { return layout },
        setLayout(value: string | null) { layout = value },
    }
}

function createThresholdsState(){
    let thresholds = $state<Record<string, number | null>>({});

    return {
        getThresholds() { return thresholds },
        setThresholds(value: Record<string, number | null>) { thresholds = value },
    }
}

export interface GameState {
    loadingState: ReturnType<typeof createLoadingState>;
    modeState: ReturnType<typeof createModeState>;
    difficultyState: ReturnType<typeof createDifficultyState>;
    leaderboardSubmissionState: ReturnType<typeof createLeaderboardSubmissionState>;
    thresholdsState: ReturnType<typeof createThresholdsState>;
}

export function createGameState(): GameState {
    return {
        loadingState: createLoadingState(),
        modeState: createModeState(),
        difficultyState: createDifficultyState(),
        leaderboardSubmissionState: createLeaderboardSubmissionState(),
        thresholdsState: createThresholdsState(),
    }
}