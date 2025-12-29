import { zod4 } from "sveltekit-superforms/adapters"
import { superValidate } from "sveltekit-superforms/server"
import { fail } from "sveltekit-superforms"
import z from "zod/v4";

/*
 * Form backend for the leaderboard submit form.
 * Built using sveltekit-superforms:
 * https://superforms.rocks/
 */

// Submission form schema (subset of leaderboardEntrySchema)
// Note: difficulty, layout, and score are now extracted from the trajectory file by the backend
const submissionSchema = z.object({
    parkId: z.string().min(1, "Park ID is required!"),
    name: z.string().min(1, "Name is required!").max(50, "Name can't be more than 50 characters."),
    resource_setting: z.enum(["docs", "few-shot", "few-shot+docs", "unlimited"]),
    cost: z.number().nonnegative("Cost can't be negative!").nullable().optional(),
    repoLink: z.string().regex(/^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/, "Invalid url!").nullable().optional(),
    paperLink: z.string().regex(/^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/, "Invalid url!").nullable().optional(),
});

/*
 * Form object for the leaderboard submit form.
 * This object needs to be passed to the client from the load function
 * of +page.server.ts files that intend to use the form.
 */
export const leaderboardSubmitForm = await superValidate(zod4(submissionSchema))


/*
 * Form action for the leaderboard submit form.
 * Validates the form data, reads trajectory file, and submits to backend API.
 * Redirects to the submit success page afterwards.
 * This actions needs to be added to the actions object in the +page.server.ts file.
 */
export const leaderboardSubmit = async({request}: {request: Request}) => {
    const formData = await request.formData();
    const form = await superValidate(formData, zod4(submissionSchema))

    if (!form.valid) {
        return fail(400, {form})
    }

    // Get trajectory file
    const trajectoryFile = formData.get('trajectoryFile') as File;
    if (!trajectoryFile || trajectoryFile.size === 0) {
        return fail(400, {
            form,
            message: "Trajectory file is required!"
        });
    }

    // Read trajectory file content
    const trajectoryContent = await trajectoryFile.text();
    const trajectoryFilename = trajectoryFile.name;

    // Prepare data for backend API
    // Note: difficulty, layout, and score are extracted from the trajectory file by the backend
    // In production (docker-compose), use the backend service name
    // In local dev, use localhost:3000
    const backendUrl = process.env.THEME_PARK_BACKEND_URL ||
                      (process.env.NODE_ENV === 'production' ? 'http://backend:3000' : 'http://localhost:3000');
    const payload = {
        parkId: form.data.parkId,
        is_human: false,
        name: form.data.name,
        resource_setting: form.data.resource_setting,
        cost: form.data.cost || null,
        repoLink: form.data.repoLink || null,
        paperLink: form.data.paperLink || null,
        validated: false,
        trajectory: trajectoryContent,
        trajectoryFilename: trajectoryFilename,
        saveLocal: false,
        saveToCloud: true
    };

    console.log("Submitting to backend:", `${backendUrl}/v1/leaderboard`);
    console.log("Payload:", JSON.stringify({ ...payload, trajectory: `[${payload.trajectory.length} chars]` }, null, 2));

    try {
        // Submit to backend API
        const response = await fetch(`${backendUrl}/v1/leaderboard`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        console.log("Backend response status:", response.status);

        if (!response.ok) {
            const errorData = await response.json();
            console.error("Backend error:", response.status, errorData);
            return fail(response.status, {
                form,
                message: errorData.message || "Failed to submit entry"
            });
        }

        console.log("Submission successful");
        // Return success message instead of redirecting
        return {
            form,
            success: true,
            message: "Submission successful! Your entry has been added to the leaderboard."
        }
    } catch (error) {
        console.error("Error submitting to backend:", error);
        console.error("Error details:", {
            message: error?.message,
            stack: error?.stack,
            backendUrl,
            nodeEnv: process.env.NODE_ENV
        });
        return fail(500, {
            form,
            message: `Failed to connect to backend server: ${error?.message || String(error)}`
        });
    }
}