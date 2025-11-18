import { Router } from "express";
import { DynamoDbReader, DynamoDBWriter } from "../node_utils/dynamo_db.js";
import { S3Writer } from "../node_utils/s3.js";
import { REGION, TRAJECTORY_SAVE_BUCKET, LEADERBOARD_TABLE } from "../config.js";
import config from "../config.js";
const router = Router();

/**
 * Parse TSV trajectory content into an array of objects
 * @param {string} tsvContent - The TSV content to parse
 * @returns {Array} Parsed trajectory data
 */
function parseTrajectoryTSV(tsvContent) {
    const lines = tsvContent.trim().split('\n');

    if (lines.length < 2) {
        throw new Error('Trajectory file is empty or has no data rows');
    }

    const headers = lines[0].split('\t');
    const trajectory = [];

    for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split('\t');
        const entry = {};

        for (let j = 0; j < headers.length; j++) {
            const header = headers[j];
            let value = values[j];

            // Parse JSON fields
            if (header === 'end_state' || header === 'info') {
                try {
                    value = JSON.parse(value);
                } catch (e) {
                    throw new Error(`Failed to parse ${header} at step ${i}: ${e.message}`);
                }
            } else if (header === 'step' || header === 'duration' || header === 'reward') {
                value = parseFloat(value);
            } else if (header === 'action_valid') {
                value = value === 'true';
            }

            entry[header] = value;
        }

        trajectory.push(entry);
    }

    return trajectory;
}

/**
 * Normalize resource_setting to backend format
 * @param {string} resourceSetting - Any format
 * @returns {string} Backend format (lowercase with hyphens)
 */
function normalizeResourceSetting(resourceSetting) {
    if (!resourceSetting) return resourceSetting;
    const normalized = resourceSetting.toLowerCase().replace(/\s+/g, '');
    // Handle variations
    if (normalized === 'few-shot+docs' || normalized === 'few-shotdocs') {
        return 'few-shot+docs';
    }
    return normalized;
}

export const leaderBoardRouter = ({parks}) => {
    // GET leaderboard entries
    router.get("/", async (req, res) => {
        try {
            const limit = req.query.limit ? parseInt(req.query.limit, 10) : 100;
            const reader = new DynamoDbReader(REGION, LEADERBOARD_TABLE);
            const results = await reader.getLeaderboard({limit});
            res.status(200).json(results);
        } catch (error) {
            console.error("Error fetching leaderboard:", error);
            res.status(500).json({
                message: "Failed to fetch leaderboard",
                data: {},
            });
        }
    });

    // GET threshold scores for top 25 human players by layout/difficulty
    router.get("/thresholds", async (req, res) => {
        try {
            const reader = new DynamoDbReader(REGION, LEADERBOARD_TABLE);
            // Fetch all entries (using high limit to get all scores)
            const results = await reader.getLeaderboard({limit: 10000});

            // Filter for human entries only
            const humanEntries = results.leaderboard.filter(entry => entry.is_human === true);

            // Group by layout+difficulty combination
            const grouped = {};
            humanEntries.forEach(entry => {
                const key = `${entry.layout}_${entry.difficulty}`;
                if (!grouped[key]) {
                    grouped[key] = [];
                }
                grouped[key].push(entry.score);
            });

            // Calculate 25th highest score for each combination
            const thresholds = {};
            for (const [key, scores] of Object.entries(grouped)) {
                // Sort scores in descending order
                scores.sort((a, b) => b - a);

                // If there are fewer than 25 scores, return null (will show popup for any score)
                if (scores.length < 25) {
                    thresholds[key] = null;
                } else {
                    // Get the 25th highest score (index 24 in 0-indexed array)
                    thresholds[key] = scores[24];
                }
            }
            res.status(200).json({ thresholds });
        } catch (error) {
            console.error("Error fetching thresholds:", error);
            res.status(500).json({
                message: "Failed to fetch thresholds",
                thresholds: {},
            });
        }
    });

    // POST: Save trajectory and/or create leaderboard entry
    router.post("/", async (req, res) => {
        const {
            parkId,
            is_human,
            name,
            resource_setting,
            validated,
            cost,
            repoLink,
            paperLink,
            trajectory,
            trajectoryFilename,
            difficulty: reqDifficulty,
            layout: reqLayout,
            score: reqScore,
            saveLocal,
            saveToCloud
        } = req.body;

        // Check if this is a form submission (trajectory provided) or game submission
        const isFormSubmission = trajectory !== undefined;

        let score, difficulty, layout, timeTaken, tsvContent;

        if (isFormSubmission) {
            // Form submission: extract data from trajectory file
            if (!name || !parkId || !trajectory) {
                res.status(400).json({
                    message: "Invalid request. Missing required fields for form submission (name, parkId, or trajectory)",
                    data: {},
                });
                return;
            }

            // Validate that trajectory filename starts with parkId
            if (trajectoryFilename) {
                const filenameWithoutExtension = trajectoryFilename.replace(/\.tsv$/i, '');
                if (!filenameWithoutExtension.startsWith(parkId)) {
                    res.status(400).json({
                        message: `Invalid trajectory file: filename must start with parkId '${parkId}'. Your file '${trajectoryFilename}' does not match.`,
                        data: {},
                    });
                    return;
                }
                console.log("Trajectory filename validation PASSED:", trajectoryFilename);
            } else {
                console.warn("Warning: trajectoryFilename not provided, skipping filename validation");
            }

            try {
                // Parse the trajectory TSV
                const trajectoryData = parseTrajectoryTSV(trajectory);

                if (trajectoryData.length === 0) {
                    res.status(400).json({
                        message: "Invalid trajectory: no data rows found",
                        data: {},
                    });
                    return;
                }

                // Extract data from final state
                const finalEntry = trajectoryData[trajectoryData.length - 1];
                const finalState = finalEntry.end_state;

                if (!finalState || !finalState.difficulty || !finalState.layout || !finalState.state) {
                    res.status(400).json({
                        message: "Invalid trajectory: final state is missing required fields (difficulty, layout, or state)",
                        data: {},
                    });
                    return;
                }

                difficulty = finalState.difficulty;
                layout = finalState.layout;
                score = finalState.state.value;

                // Validate step count matches expected horizon for difficulty
                // +1 for the reset step at the beginning of the trajectory
                const expectedSteps = config.horizon_by_difficulty[difficulty] + 1;

                if (trajectoryData.length !== expectedSteps) {
                    console.error("Step count validation FAILED!");
                    res.status(400).json({
                        message: `Invalid trajectory: expected ${expectedSteps} steps for difficulty '${difficulty}', but got ${trajectoryData.length} steps`,
                        data: {},
                    });
                    return;
                }

                // Calculate total time taken by summing all durations
                timeTaken = trajectoryData.reduce((acc, entry) => acc + entry.duration, 0);
                tsvContent = trajectory;

            } catch (error) {
                console.error("Error parsing trajectory:", error);
                res.status(400).json({
                    message: `Failed to parse trajectory: ${error.message}`,
                    data: {},
                });
                return;
            }
        } else {
            // Game submission: extract from park object
            if (!name || !parkId || !parks[parkId]) {
                res.status(400).json({
                    message: "Invalid request. Missing name, parkId, or park does not exist",
                    data: {},
                });
                return;
            }

            const park = parks[parkId];
            score = park.value;
            difficulty = park.difficulty;
            layout = park.layout;
            timeTaken = park.logger.getTimeTaken();
            tsvContent = park.logger.getTrajectoryTSV();
        }

        const results = {};

        try {
            // Save locally if requested (only for game submissions)
            if (saveLocal === true && !isFormSubmission) {
                const park = parks[parkId];
                const localPath = park.logger.saveLocal();
                results.localPath = localPath;

                // Also save to leaderboard.tsv
                const leaderboardPath = park.logger.saveLeaderboardEntry({
                    parkId: parkId,
                    is_human: is_human,
                    name: name,
                    resource_setting: resource_setting,
                    score: score,
                    layout: layout,
                    difficulty: difficulty,
                    timeTaken: timeTaken
                });
                results.leaderboardPath = leaderboardPath;
            }

            // Save to cloud if requested
            if (saveToCloud === true) {
                // Save trajectory to S3 bucket
                const s3Writer = new S3Writer(REGION);
                const s3Result = await s3Writer.saveTrajectory({
                    bucket: TRAJECTORY_SAVE_BUCKET,
                    parkId: parkId,
                    tsvContent: tsvContent
                });
                results.s3 = s3Result;

                // Save metadata to DynamoDB
                const normalizedResourceSetting = normalizeResourceSetting(resource_setting);
                const dynamoWriter = new DynamoDBWriter(REGION, LEADERBOARD_TABLE);
                const dynamodbResult = await dynamoWriter.createLeaderboardEntry({
                    parkId: parkId,
                    is_human: is_human,
                    name: name,
                    resource_setting: normalizedResourceSetting,
                    difficulty: difficulty,
                    layout: layout,
                    score: score,
                    validated: validated !== undefined ? validated : false,
                    cost: cost,
                    timeTaken: timeTaken,
                    repoLink: repoLink,
                    paperLink: paperLink
                });
                results.dynamodb = dynamodbResult;
                console.log(`Metadata saved to DynamoDB for parkId ${parkId}`);
            } else {
                console.log("saveToCloud is not true, skipping cloud save");
            }

            res.status(200).json({
                message: "Trajectory saved successfully",
                data: {parkId: parkId, results: results}
            });
        } catch (error) {
            console.error("Error saving trajectory:", error);
            res.status(500).json({
                message: "Failed to save trajectory",
                data: {},
            });
        }
    });

    return router;
};