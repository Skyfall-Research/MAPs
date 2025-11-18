import { json, Router } from "express";
import { CommandResult } from "../utils.js";

const router = Router();

export const shopRouter = ({parks, io}) => {
    router.get("/", (req, res) => {
        const {parkId} = req.query
        const shops = parks[parkId].shops.map(shop => shop.format());
        res.status(200).json({ data: shops, message: "Success" });
    });

    router.get("/:x/:y", (req, res) => {
        let { x, y } = req.params;
        x = Number(x);
        y = Number(y);
        const {parkId} = req.query
        const tile = parks[parkId].grid.getTile(x, y);
        if (tile.type === "shop") {
            res.status(200).json({ data: tile.shop.format(), message: "Success" });
        } else {
            res.status(400).json({ data: {}, message: "Shop not found" });
        }
    });

    router.post("/", (req, res) => {
        const {parkId,  x, y, subtype, subclass, price, order_quantity } = req.body;
        // Apply action
        let result = parks[parkId].addShop(x, y, subtype, subclass, price, order_quantity);
        // Emit action
        if(io.sockets.sockets.size > 0){
            io.emit("action", {
               "name" : "place_shop",
               "params" : req.body
            })

       }
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    router.put("/:x/:y", (req, res) => {
        let { x, y } = req.params;
        x = Number(x);
        y = Number(y);
        const {parkId, type, subtype, subclass, price=undefined, order_quantity=undefined, new_x=undefined, new_y=undefined} = req.body;
        let result = new CommandResult(false, "Invalid request");
        // Apply action
        if (price !== undefined) {
            result = parks[parkId].modifyAttraction(type, subtype, subclass, x, y, price, order_quantity);
        }
        else if (new_x !== undefined && new_y !== undefined) {
            result = parks[parkId].moveAttraction(type, subtype, subclass, x, y, new_x, new_y);
        }
        // Emit action
        if(io.sockets.sockets.size > 0){
            let name = ""
            if((x!=undefined  && x!=null) || (y!=undefined & y!=null)){
                name = "move"
            }
            
            if(price!=undefined){
                name = "modify"
            }
            
            io.emit("action", {
                'name' : name,
                'params' : {...req.params, ...req.body }
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
                "name": "sell_shop",
                "params": { ...req.params, ...req.query }
            });
        }
        // Send response
        res.status(result.success ? 200 : 400).json({ data: {}, message: result.message });
    });

    return router;
};