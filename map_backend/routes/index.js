import { Router } from "express";
import { rideRouter } from "./ride.js";
import { guestRouter } from "./guest.js";
import { shopRouter } from "./shop.js";
import { staffRouter } from "./staff.js";
import { parkRouter } from "./park.js";
import { leaderBoardRouter } from "./leaderboard.js";

const router = Router();

export const createV1Router = ({parks , io, visUpdateFn}) => {
    // Health check endpoint for ALB
    router.get("/health", (req, res) => {
        res.status(200).json({ status: 'healthy', timestamp: new Date().toISOString() });
    });

    router.use("/ride", rideRouter({parks,io}));
    router.use("/guest", guestRouter({parks}));
    router.use("/staff", staffRouter({parks, io}));
    router.use("/shop", shopRouter({parks, io}));
    router.use("/park", parkRouter(parks, io , visUpdateFn));
    router.use("/leaderboard", leaderBoardRouter({parks}))
    return router;
};