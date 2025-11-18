import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * TrajectoryLogger - Logs episode trajectories in TSV format
 * Replaces the simple history array in park.js with full logging capabilities
 */
class TrajectoryLogger {
    constructor(parkId, expName = null) {
        this.parkId = parkId;
        this.expName = expName || this.parkId;

        // Project root is two levels up from map_backend/node_utils/
        this.projectRoot = path.join(__dirname, '..', '..');
        this.logsDir = path.join(this.projectRoot, 'logged_trajectories');

        this.episodeIndex = 0;
        this.trajectoryData = []; // Array of trajectory entries
        this.middayData = []; // Array of midday state entries
        this.prevTime = null;
    }

    ensureLogsDirectory() {
        if (!fs.existsSync(this.logsDir)) {
            fs.mkdirSync(this.logsDir, { recursive: true });
        }
    }

    /**
     * Start a new episode with initial state
     * @param {Object} startState - The initial state of the park
     */
    newEpisode(startState) {
        this.prevTime = Date.now();
        this.episodeIndex += 1;

        // Initialize trajectory with header and reset entry
        this.trajectoryData = [
            {
                step: 0,
                action_valid: true,
                duration: 0,
                action: "reset()",
                end_state: startState,
                reward: 0,
                info: {}
            }
        ];

        // Reset midday data for new episode
        this.middayData = [];
    }

    /**
     * Log a trajectory step
     * @param {number} step - Current step number
     * @param {string} action - Action taken
     * @param {Object} end_state - Resulting state
     * @param {number} reward - Reward received
     * @param {Object} info - Additional info (may contain 'error' key)
     */
    log(step, action_valid, action, end_state, reward, info) {
        const currentTime = Date.now();
        const duration = this.prevTime ? currentTime - this.prevTime : 0;
        this.prevTime = currentTime;

        this.trajectoryData.push({
            step,
            action_valid,
            duration,
            action,
            end_state,
            reward,
            info
        });
    }

    /**
     * Log midday states for a given step
     * @param {Array} midday_states - Array of midday state objects (one per tick)
     */
    log_midday_states(midday_states) {
        const step = this.trajectoryData.length > 0 ? this.trajectoryData[this.trajectoryData.length - 1].step : 0;

        this.middayData.push({
            step,
            midday_states
        });
    }

    /**
     * Get the full history of states (for backward compatibility with old history array)
     * @returns {Array} Array of all end states
     */
    getHistory() {
        return this.trajectoryData.map(entry => entry.end_state);
    }

    /**
     * Get the last state in history
     * @returns {Object} The most recent state
     */
    getLastState() {
        if (this.trajectoryData.length === 0) {
            return null;
        }
        return this.trajectoryData[this.trajectoryData.length - 1].end_state;
    }

    /**
     * Remove the last trajectory entry (for undo functionality)
     */
    popLastEntry() {
        if (this.trajectoryData.length > 1) {
            this.trajectoryData.pop();
        }
    }

    /**
     * Get the time taken to complete the entire episode
     * @returns {number} Time taken to complete the episode in milliseconds
     */
    getTimeTaken() {
        return this.trajectoryData.reduce((acc, entry) => acc + entry.duration, 0);
    }

    /**
     * Generate TSV content from trajectory data
     * @returns {string} TSV-formatted trajectory
     */
    getTrajectoryTSV() {
        if (this.trajectoryData.length === 0) {
            return "";
        }

        const lines = [];

        // Header
        lines.push(["step", "action_valid", "duration", "action", "end_state", "reward", "info"].join("\t"));

        // Data rows
        for (const entry of this.trajectoryData) {
            const row = [
                entry.step,
                entry.action_valid,
                entry.duration,
                entry.action,
                JSON.stringify(entry.end_state),
                entry.reward,
                JSON.stringify(entry.info)
            ];
            lines.push(row.join("\t"));
        }

        return lines.join("\n");
    }

    /**
     * Generate TSV content from midday data
     * @returns {string} TSV-formatted midday states
     */
    getMiddayTSV() {
        if (this.middayData.length === 0) {
            return "";
        }

        const lines = [];

        // Header
        lines.push(["step", "midday_states"].join("\t"));

        // Data rows - one row per step, with all tick states as JSON array
        for (const entry of this.middayData) {
            const row = [
                entry.step,
                JSON.stringify(entry.midday_states)
            ];
            lines.push(row.join("\t"));
        }

        return lines.join("\n");
    }

    /**
     * Save trajectory to local file system
     * @returns {string} Path to saved file
     */
    saveLocal() {
        this.ensureLogsDirectory();

        const filename = `${this.expName}_${this.episodeIndex}.tsv`;
        const filepath = path.join(this.logsDir, filename);

        const tsvContent = this.getTrajectoryTSV();
        fs.writeFileSync(filepath, tsvContent, 'utf8');

        console.log(`Trajectory saved locally to ${filepath}`);

        // Also save midday states if available
        if (this.middayData.length > 0) {
            this.saveMiddayLocal();
        }

        return filepath;
    }

    /**
     * Save midday states to local file system
     * @returns {string} Path to saved file
     */
    saveMiddayLocal() {
        this.ensureLogsDirectory();

        const filename = `${this.parkId}_midday.tsv`;
        const filepath = path.join(this.logsDir, filename);

        const tsvContent = this.getMiddayTSV();
        fs.writeFileSync(filepath, tsvContent, 'utf8');

        console.log(`Midday states saved locally to ${filepath}`);
        return filepath;
    }

    /**
     * Save leaderboard entry to shared leaderboard.tsv file
     * @param {Object} params - Leaderboard entry parameters
     * @param {string} params.parkId - Park ID
     * @param {string} params.mode - Mode
     * @param {string} params.username - Username
     * @param {number} params.score - Final score (money - startingMoney)
     * @param {string} params.layout - Park layout name
     * @param {string} params.difficulty - Difficulty level
     * @param {number} params.timeTaken - Time taken to complete the episode in milliseconds
     * @returns {string} Path to leaderboard file
     */
    saveLeaderboardEntry({parkId, mode, username, score, layout, difficulty, timeTaken}) {
        // Leaderboard file is in the root logged_trajectories directory
        const leaderboardDir = path.join(this.projectRoot, 'logged_trajectories');
        const leaderboardPath = path.join(leaderboardDir, 'leaderboard.tsv');

        // Ensure the directory exists
        if (!fs.existsSync(leaderboardDir)) {
            fs.mkdirSync(leaderboardDir, { recursive: true });
        }

        // Check if file exists to determine if we need to write header
        const fileExists = fs.existsSync(leaderboardPath);

        // Create the entry
        const entry = [parkId, mode, username, score, layout, difficulty, timeTaken].join('\t');

        // If file doesn't exist, write header first
        if (!fileExists) {
            const header = ['parkId', 'mode', 'username', 'score', 'layout', 'difficulty', 'timeTaken'].join('\t');
            fs.writeFileSync(leaderboardPath, header + '\n', 'utf8');
        }

        // Append the entry
        fs.appendFileSync(leaderboardPath, entry + '\n', 'utf8');

        console.log(`Leaderboard entry saved to ${leaderboardPath}`);
        return leaderboardPath;
    }


    /**
     * Load trajectory from local file
     * @param {number} episodeIndex - Episode number to load
     * @returns {Array} Trajectory data as array of objects
     */
    loadTrajectory(episodeIndex) {
        const filename = `${this.expName}_${episodeIndex}.tsv`;
        const filepath = path.join(this.logsDir, filename);

        if (!fs.existsSync(filepath)) {
            throw new Error(`Trajectory file not found: ${filepath}`);
        }

        const content = fs.readFileSync(filepath, 'utf8');
        const lines = content.trim().split('\n');

        if (lines.length < 2) {
            return [];
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
                        // Keep as string if parsing fails
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
}

export default TrajectoryLogger;
