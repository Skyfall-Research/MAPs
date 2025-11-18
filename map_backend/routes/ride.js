import { Router } from "express";
import { CommandResult } from "../utils.js";

const router = Router();

export const rideRouter = ({parks, io}) => {
    router.get("/", (req, res) => {
        const {parkId, includeQueue = false } = req.query;
        const rides = parks[parkId].rides.map(ride => ride.format({ includeQueue }));
        res.status(200).json({ rides });
    });

    router.get("/:x/:y", (req, res) => {
        let { x, y } = req.params;
        x = Number(x);
        y = Number(y);
        const {parkId, includeQueue = false } = req.query;
        const tile = parks[parkId].grid.getTile(x, y);
        if (tile.type === "ride") {
            res.status(200).json({ data: tile.ride.format({ includeQueue }), message: "Success" });
        } else {
            res.status(400).json({ data: {}, message: "Ride not found" });
        }
    });

    router.post("/", (req, res) => {
        const {parkId, x, y, subtype, subclass, price } = req.body;
        // Apply action
        let result = parks[parkId].addRide(x, y, subtype, subclass, price);
        // Emit action
        if(io.sockets.sockets.size > 0){
            io.emit("action", {
                "name" : "place_ride",
                "params" : req.body
            })
        }
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.put("/:x/:y", (req, res) => {
        let { x, y } = req.params;
        x = Number(x);
        y = Number(y);
        const {parkId, type, subtype, subclass, price=undefined, new_x=undefined, new_y=undefined} = req.body;
        let result = new CommandResult(false, "Invalid request");
        // Apply action
        if (price !== undefined) {
            // Quantity is null for a ride
            result = parks[parkId].modifyAttraction(type, subtype, subclass, x, y, price, null);
        } else if (new_x !== undefined && new_y !== undefined) {
            result = parks[parkId].moveAttraction(type, subtype, subclass, x, y, new_x, new_y);
        }
        // Emit action
        if(io.sockets.sockets.size > 0){
            let name = ""
            if(price !== undefined){
                name = "modify"
            } else {
                name = "move"
            }
            
            io.emit("action", {
                'name' : name,
                'params' : {...req.params, ...req.body}
            })
        }
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.delete("/:x/:y", (req, res) => {
        let { x, y } = req.params;

        x = Number(x);
        y = Number(y);
        const { parkId, type, subtype, subclass } = req.body;
        
        // Apply action
        let result = parks[parkId].sellAttraction(type, subtype, subclass, x, y);
        
        // Emit action
        if (io.sockets.sockets.size > 0) {
            io.emit("action", {
                "name": "sell_ride",
                "params": { ...req.params, ...req.query }
            });
        }
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    return router;
};