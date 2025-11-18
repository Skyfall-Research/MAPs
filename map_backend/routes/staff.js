import { Router } from "express";
import { CommandResult } from "../utils.js";

const router = Router();

export const staffRouter = ({parks, io}) => {
    router.get("/", (req, res) => {
        const {parkId} = req.query;
        const staff = parks[parkId].staff.map(staff => staff.format());
        res.status(200).json({ data: staff, message: "Success" });
    });

    router.get("/:x/:y", (req, res) => {
        let { x, y } = req.params;
        x = Number(x);
        y = Number(y);
        const {parkId} = req.query;
        const staff = parks[parkId].staff.filter(staff => staff.x === x && staff.y === y).map(staff => staff.format())?.[0];
        if (staff) {
            res.status(200).json({ data: staff, message: "Success" });
        } else {
            res.status(400).json({ data: {}, message: "Staff not found" });
        }
    });

    router.post("/", (req, res) => {
        const { parkId, x, y, subtype, subclass } = req.body;
        // Apply action
        let result = parks[parkId].hireStaff(x, y, subtype, subclass);
        // Emit action
        if(io.sockets.sockets.size > 0){
            io.emit("action", {
                "name" : "hire_staff",
                "params" : req.body
            })
        }
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.put("/:x/:y", (req, res) => {
        let { x, y } = req.params;
        x = Number(x);
        y = Number(y);
        const {parkId, subtype, subclass, new_x, new_y} = req.body;
        // Apply action
        let result = parks[parkId].moveStaff(subtype, subclass, x, y, new_x, new_y);
        // Emit action
        if(io.sockets.sockets.size > 0){
            io.emit("action", {
                "name" : "move_staff",
                "params" : {...req.params, ...req.body}
            })
        }
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.delete("/:x/:y", (req, res) => {
        let { x, y } = req.params;
        x = Number(x);
        y = Number(y);
        const { subtype, subclass, parkId } = req.body;
        
        // Apply action
        let result = parks[parkId].fireStaff(subtype, subclass, x, y);
        
        // Emit action
        if (io.sockets.sockets.size > 0) {
            io.emit("action", {
                "name": "fire_staff",
                "params": { ...req.params, ...req.query }
            });
        }
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    return router;
};