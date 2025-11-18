import { Router } from "express";

const router = Router();

export const guestRouter = ({parks}) => {
    router.get("/", (req, res) => {
        const {parkId} = req.query;
        const guests = parks[parkId].guests.map(guest => guest.format());
        res.status(200).json({ data: guests, message: "Success" });
    });
    
    return router;
};