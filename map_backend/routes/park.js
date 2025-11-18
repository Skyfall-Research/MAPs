import { Router } from "express";
import { CommandResult } from "../utils.js";
import Park from "../park.js";
import { Mutex } from "async-mutex";
import { v4 as uuidv4 } from 'uuid';
const router = Router();
const mutex = new Mutex();
import TrajectoryLogger from "../node_utils/logger.js";

export const removeGuestListFromState = (state) => {
    delete state['guests'];
    return state;
}

const stringToBool = (variable) => {
   return typeof variable == "string" ? variable.toLocaleLowerCase() == "true" : variable 
}

export const parkRouter = (parks, io, visUpdateFn) => {
    // Track when each park was last referenced
    const park_timers = {};

    // Helper function to update the timer for a park
    const updateParkTimer = (parkId) => {
        if (parkId && parks[parkId]) {
            park_timers[parkId] = Date.now();
        }
    };

    // Helper function to clean up parks that haven't been referenced in over 2 hours
    const cleanupOldParks = () => {
        const twoHoursInMs = 2 * 60 * 60 * 1000;
        const now = Date.now();
        const parksToDelete = [];

        for (const parkId in park_timers) {
            const lastReferenced = park_timers[parkId];
            if (now - lastReferenced > twoHoursInMs) {
                parksToDelete.push(parkId);
            }
        }

        parksToDelete.forEach(parkId => {
            delete parks[parkId];
            delete park_timers[parkId];
            console.log(`Deleted park ${parkId} - not referenced in over 2 hours`);
        });
    };

    router.get("/get_new_park_id", async (req, res) => {
        const release = await mutex.acquire();
        try {
            // Clean up old parks before creating a new one
            cleanupOldParks();
            
            // Loop through i starting at 0 until we reach an id that is not in parks
            let uuid = uuidv4();
            parks[uuid] = new Park(uuid);
            park_timers[uuid] = Date.now();
            console.log(`New park id created: ${uuid}. There are currently ${Object.keys(parks).length} parks.`);
            res.status(200).json({ data: {'parkId': uuid}, message: "Success" });
        } finally {
            release();
        }
    });

    router.get("/", (req, res) => {
        let {parkId, fullState = false, includeGuests = false} = req.query;
        fullState = stringToBool(fullState)
        includeGuests = stringToBool(includeGuests)

        if(parkId == undefined || parks[parkId] == undefined || parkId < 0){
            res.status(400).json({data: {}, message: "Invalid parkId"});
        } else if (!parks[parkId].initialized) {
            res.status(400).json({data: {}, message: "Park has not yet been initialized"});
        } else {
            updateParkTimer(parkId);
            if(fullState){
                var state = parks[parkId].getFullState({includeGuests: includeGuests});
                state['state']['parkId'] = parkId;
                res.status(200).json({ data: state, message: "Success" });            
            } else {
                const state = parks[parkId].getState();
                state['state']['parkId'] = parkId;
                res.status(200).json({ data: state, message: "Success" });
            }
        }
    });

    router.post("/proceed", (req, res) => {
        let {parkId, onlyAdvanceDay = false} = req.body;
        
        updateParkTimer(parkId);
        
        // Apply action
        let done = parks[parkId].proceed({visUpdateFn, parkId, io, onlyAdvanceDay});
        
        // Send response
        res.status(200).json({ data: done, message: "Success" });
    });

    router.post("/set", (req, res) => {
        let {parkId, state} = req.body;
        
        if (parks[parkId] !== undefined) {
            updateParkTimer(parkId);
            parks[parkId].setState(state);
            // Replace the history of the park
            parks[parkId].logger = new TrajectoryLogger(parkId);
            parks[parkId].midday_history = [];
            parks[parkId].logger.newEpisode(parks[parkId].calculateFullState());
            res.status(200).json({ data: {}, message: "Success" });
        } else {
            res.status(400).json({ data: {}, message: "Invalid Park Id" });
        }
    });

    router.post("/reset", (req, res) => {
        let {parkId, layout, difficulty, starting_money, horizon} = req.body;
        if (parks[parkId] !== undefined) {
            updateParkTimer(parkId);
            // Apply action
            let result = parks[parkId].reset({layout, difficulty, starting_money, horizon});
            // Emit action
            if (visUpdateFn) {
                visUpdateFn({io, park: parks[parkId], parkId: parkId, type: "reset"});
            }
            res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
        } else {
            res.status(400).json({ data: {}, message: "Invalid Park Id" });
        }
    });

    router.post("/research", (req, res) => {
        let {parkId, research_speed, research_topics} = req.body;
        // Apply action 
        let result = parks[parkId].setResearch(research_speed, research_topics);
        // Emit action
        if(io.sockets.sockets.size > 0){
            io.emit("action", {
                "name" : "set_research",
                "params" : req.body
            })
        }
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.post("/path", (req, res) => {
        let {parkId, x, y} = req.body;
        // Apply action 
        let result = parks[parkId].addPathTile(x, y);
        // Emit action
        if(io.sockets.sockets.size > 0){
            io.emit("action", {
                "name" : "add path tile",
                "params" : req.body
            })
        }
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.post("/noop", (req, res) => {
        let {parkId} = req.body;
        // Apply action
        let result = parks[parkId].noop();
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.delete("/path/:x/:y", (req, res) => {
        let { x, y } = req.params;
        x = Number(x);
        y = Number(y);
        const { parkId } = req.body;
        
        // Apply action
        let result = parks[parkId].removePathTile(x, y);
        
        // Emit action
        if (io.sockets.sockets.size > 0) {
            io.emit("action", {
                "name": "remove path tile",
                "params": { ...req.params, ...req.body }
            });
        }
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.post("/water", (req, res) => {
        let {parkId, x, y} = req.body;
        // Apply action 
        let result = parks[parkId].addWaterTile(x, y);
        // Emit action
        if (io.sockets.sockets.size > 0) {
            io.emit("action", {
                "name": "add water tile",
                "params": req.body
            });
        }
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.delete("/water/:x/:y", (req, res) => {
        let { x, y } = req.params;
        x = Number(x);
        y = Number(y);
        const { parkId } = req.body;
        
        // Apply action
        let result = parks[parkId].removeWaterTile(x, y);

        // Emit action
        if (io.sockets.sockets.size > 0) {
            io.emit("action", {
                "name": "remove water tile",
                "params": req.body
            });
        }
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.post("/survey_guests", (req, res) => {
        let {parkId, num_guests} = req.body;
        // Apply action
        let result = parks[parkId].setNumGuestsToSurvey(num_guests);
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.post("/undo_day", (req, res) => {
        let {parkId} = req.body;
        // Apply action
        let result = parks[parkId].undoDay();
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.post("/max_money", (req, res) => {
        let {parkId} = req.body;
        // Apply action
        let result = parks[parkId].maxMoney();
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.post("/max_research", (req, res) => {
        let {parkId} = req.body;
        // Apply action
        let result = parks[parkId].maxResearch();
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.post("/seed", (req, res) => {
        let {parkId, seed} = req.body;
        // Apply action
        let result = parks[parkId].setSeed(seed);
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {"seed": seed}, message: result.message });
    });

    router.post("/set_sandbox_mode", (req, res) => {
        let {parkId, sandbox_steps} = req.body;
        // Apply action
        let result = parks[parkId].setSandboxMode(sandbox_steps);
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {"sandbox_steps": sandbox_steps}, message: result.message });
    });

    router.delete("/delete_park/:parkId", (req, res) => {
        const { parkId } = req.params;

        if (parks[parkId] === undefined) {
            res.status(404).json({
                data: {},
                message: "Park not found"
            });
        } else {
            delete parks[parkId];
            delete park_timers[parkId];
            console.log("Park data cleared successfully");
            res.status(200).json({
                data: {},
                message: "Park data cleared successfully"
            });
        }
    });

    return router;
};