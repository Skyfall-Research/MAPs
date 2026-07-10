import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

/**
 * API Route: POST /api/leaderboard/manual
 *
 * Handles manual leaderboard submissions with trajectory file uploads.
 * Proxies submissions from the client to the backend service.
 */
export const POST: RequestHandler = async ({ request }) => {
    try {
        const body = await request.json();

        const parkId = body.parkId as string;
        const name = body.name as string;
        const resourceSetting = body.resource_setting as string;
        const cost = body.cost as number | null;
        const repoLink = body.repoLink as string | null;
        const paperLink = body.paperLink as string | null;
        const trajectory = body.trajectory as string | undefined;
        const trajectoryFilename = body.trajectoryFilename as string | undefined;

        console.log("Manual submission received:", {
            parkId,
            name,
            resourceSetting,
            cost,
            hasTrajectory: !!trajectory
        });

        if (!trajectory || trajectory.length === 0) {
            return json({
                message: "Trajectory file is required"
            }, { status: 400 });
        }

        console.log("Trajectory received, length:", trajectory.length);

        // Prepare payload for backend
        const payload = {
            parkId,
            is_human: false,
            name,
            resource_setting: resourceSetting,
            cost: cost ?? null,
            repoLink: repoLink || null,
            paperLink: paperLink || null,
            validated: false,
            trajectory,
            trajectoryFilename,
            saveLocal: false,
            saveToCloud: true
        };

        // Determine backend URL
        const backendUrl = process.env.THEME_PARK_BACKEND_URL ||
                          (process.env.NODE_ENV === 'production' ? 'http://backend:3000' : 'http://localhost:3000');

        console.log("Proxying manual submission to:", `${backendUrl}/v1/leaderboard`);

        // Forward to backend
        const response = await fetch(`${backendUrl}/v1/leaderboard`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            console.error("Backend submission failed:", response.status, data);
            return json(data, { status: response.status });
        }

        console.log("Manual submission successful");
        return json({
            success: true,
            message: "Submission successful! Your entry has been added to the leaderboard.",
            data
        }, { status: 200 });

    } catch (err) {
        console.error("Error proxying manual submission:", err);

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

        return json(errorDetails, { status: 500 });
    }
};
