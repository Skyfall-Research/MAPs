import type { LeaderboardEntry } from "$lib/types";

/*
 * Load the data into the page.
 */
export const load = async () => {
    try {
        // Fetch leaderboard data from the backend API
        // In production (docker-compose), use the backend service name
        // In local dev, use localhost:3000
        const backendUrl = process.env.THEME_PARK_BACKEND_URL ||
                          (process.env.NODE_ENV === 'production' ? 'http://backend:3000' : 'http://localhost:3000');
        console.log("Fetching leaderboard from:", `${backendUrl}/v1/leaderboard`);
        const response = await fetch(`${backendUrl}/v1/leaderboard`);

        if (!response.ok) {
            console.error("Failed to fetch leaderboard data:", response.statusText);
            return {
                leaderBoardEntries: [] as LeaderboardEntry[]
            };
        }

        const data = await response.json();
        console.log("===== LEADERBOARD DATA FROM DYNAMODB =====");
        console.log("Total entries received:", data.leaderboard?.length || 0);
        console.log("All entries:");
        if (data.leaderboard) {
            data.leaderboard.forEach((entry: LeaderboardEntry, index: number) => {
                console.log(`Entry ${index + 1}:`, JSON.stringify(entry, null, 2));
            });
        }
        console.log("==========================================");

        return {
            leaderBoardEntries: data.leaderboard as LeaderboardEntry[]
        };
    } catch (error) {
        console.error("Error fetching leaderboard:", error);
        return {
            leaderBoardEntries: [] as LeaderboardEntry[]
        };
    }
}

