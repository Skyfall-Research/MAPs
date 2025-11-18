import z from "zod/v4";

/*
 * Types for the leaderboard data.
 * Schema validation is done using Zod:
 * https://zod.dev/
 * 
 * This allows us to easily validate the form data and get an interface for the leaderboard entries.
 * 
 */

// the schema. Strings indicate the message to display when the conditions aren't met.
export const leaderboardEntrySchema = z.object({
    parkId: z.string(),
    is_human: z.boolean(),
    name: z.string().min(1, "Name can't be empty!").max(50, "Name can't be more than 50 characters."),
    resource_setting: z.enum(["docs", "few-shot", "few-shot+docs", "unlimited"]),
    difficulty: z.enum(["easy", "medium", "hard"]),
    layout: z.enum(["the_islands", "ribs", "zig_zag"]),
    score: z.number().int().nonnegative("Score can't be negative!"),
    validated: z.boolean(),
    cost: z.number().nonnegative("Cost can't be negative!").nullable().optional(),
    timeTaken: z.number().int().nonnegative("Time taken can't be negative!").nullable().optional(), // Time in milliseconds
    repoLink: z.string().regex(/^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/, "Invalid url!").nullable().optional(),
    paperLink: z.string().regex(/^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/, "Invalid url!").nullable().optional(),
})

// the interface for the leaderboard entries.
export interface LeaderboardEntry extends z.infer<typeof leaderboardEntrySchema> {}