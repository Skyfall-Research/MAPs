
// EXTREMELY IMPORTANT. THIS ENSURES THE PAGE IS NOT SSR'D. THE GAME MUST RUN ON THE CLIENT TO ACCESS DOCUMENT PROPERTIES
export const ssr = false;

/*
 * Load the leaderboard thresholds server-side to ensure reliable backend access in production.
 * The page still renders client-only (ssr = false) but receives this data as props.
 */
export const load = async () => {
    try {
        // Fetch leaderboard thresholds from the backend API
        // In production (docker-compose), use the backend service name
        // In local dev, use localhost:3000
        const backendUrl = process.env.THEME_PARK_BACKEND_URL ||
                          (process.env.NODE_ENV === 'production' ? 'http://backend:3000' : 'http://localhost:3000');
        console.log("Fetching thresholds from:", `${backendUrl}/v1/leaderboard/thresholds`);
        const response = await fetch(`${backendUrl}/v1/leaderboard/thresholds`);

        if (!response.ok) {
            console.error("Failed to fetch leaderboard thresholds:", response.statusText);
            return {
                thresholds: {}
            };
        }

        const data = await response.json();
        console.log("Loaded leaderboard thresholds:", data.thresholds);

        return {
            thresholds: data.thresholds || {}
        };
    } catch (error) {
        console.error("Error fetching leaderboard thresholds:", error);
        return {
            thresholds: {}
        };
    }
}