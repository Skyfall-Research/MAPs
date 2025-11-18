import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

/**
 * API Route: POST /api/leaderboard
 *
 * Proxies leaderboard submissions from the client to the backend service.
 * This ensures reliable server-to-server communication in production
 * where the client cannot directly access the backend's internal Docker network.
 */
export const POST: RequestHandler = async ({ request }) => {
    try {
        // Get the submission payload from the client
        const payload = await request.json();

        // Determine backend URL based on environment
        // In production (docker-compose), use the backend service name
        // In local dev, use localhost:3000
        const backendUrl = process.env.THEME_PARK_BACKEND_URL ||
                          (process.env.NODE_ENV === 'production' ? 'http://backend:3000' : 'http://localhost:3000');

        console.log("Proxying leaderboard submission to:", `${backendUrl}/v1/leaderboard`);
        console.log("Payload:", JSON.stringify(payload, null, 2));

        // Forward the request to the backend
        const response = await fetch(`${backendUrl}/v1/leaderboard`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        // Get the response data
        const data = await response.json();

        // If backend returned an error, propagate it with same status code
        if (!response.ok) {
            console.error("Backend leaderboard submission failed:", response.status, data);
            return json(data, { status: response.status });
        }

        console.log("Leaderboard submission successful");
        return json(data, { status: 200 });

    } catch (err) {
        console.error("Error proxying leaderboard submission:", err);

        // Extract detailed error information
        const errorDetails = {
            message: 'Failed to connect to backend server',
            error: err instanceof Error ? err.message : String(err),
            stack: err instanceof Error ? err.stack : undefined,
            backendUrl: process.env.THEME_PARK_BACKEND_URL ||
                       (process.env.NODE_ENV === 'production' ? 'http://backend:3000' : 'http://localhost:3000'),
            nodeEnv: process.env.NODE_ENV,
            errorType: err?.constructor?.name || typeof err
        };

        console.error("Detailed error:", JSON.stringify(errorDetails, null, 2));

        // Return JSON error instead of using error() which can cause CORS issues
        return json(errorDetails, { status: 500 });
    }
};
