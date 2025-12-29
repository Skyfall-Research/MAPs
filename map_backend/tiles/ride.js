import { Tile } from "./tile.js";
import config from "../config.js"
import { CommandResult } from "../utils.js"

class Ride extends Tile {
    /**
     * @param {number} x - Grid X coordinate
     * @param {number} y - Grid Y coordinate
     * @param {string} subtype - e.g., "roller_coaster", "ferris_wheel"
     * @param {number} capacity - How many guests per cycle
     * @param {number} ticket_price - Price to ride
     * @param {number} excitement - How much happiness boost (0-10)
     * @param {number} intensity - How intense the ride is (affects guest preferences)
     */
    constructor(x, y, subtype, subclass, ticket_price, park) {
        super(x, y, 'ride');
        this.subtype = subtype;
        this.subclass = subclass;
        this.out_of_service = false;
        this.remaining_repair_time = 0;
        this.price = ticket_price;
        this.cost_per_operation = config.rides[subtype][subclass].cost_per_operation;
        this.capacity = config.rides[subtype][subclass].capacity;
        this.excitement = config.rides[subtype][subclass].excitement;
        this.intensity = config.rides[subtype][subclass].intensity;
        this.num_adjacent_water_tiles = park.grid.numTilesAdjacentToWater(this);
        this.excitement += this.num_adjacent_water_tiles;
        // To hold waiting guests
        this.queue = [];
        this.boarded_guests = [];
        // Chance of breaking down each operation
        this.breakdown_rate = config.rides[subtype][subclass].breakdown_rate;
        this.uptime = 1.0;
        this.countdown_until_run = -1;
        this.countdown_until_done = 3;
        this.phase = "waiting";
        this.operating_cost = 0;
        this.revenue_generated = 0;
        this.guests_entertained = 0;
        this.times_operated = 0;
        this.total_guests_queued = 0;
        this.total_wait_time = 0;
    }
    
    static fromRide(ride, park){
        const new_ride = new Ride(ride.x, ride.y, ride.subtype, ride.subclass, ride.ticket_price, park)
        if(ride.id !== undefined){
            new_ride.id = ride.id
        }
        new_ride.setState(ride)
        return new_ride
    }

    setState(ride){
        this.out_of_service = ride.out_of_service;
        this.remaining_repair_time = ride.remaining_repair_time;
        this.cleanliness = ride.cleanliness;
        this.guests_entertained = ride.guests_entertained;
        this.operating_cost = ride.operating_cost;
        this.revenue_generated = ride.revenue_generated;
        this.times_operated = ride.times_operated;
        this.total_guests_queued = ride.total_guests_queued;
        this.avg_wait_time = ride.avg_wait_time;
        this.avg_guests_per_operation = ride.avg_guests_per_operation;
        this.total_wait_time = ride.total_wait_time;
        this.uptime = ride.unnorm_uptime;
    }

    static checkParameters(subtype, subclass, ticket_price, available_entities) {
        if (!config.rides.hasOwnProperty(subtype)) {
            return new CommandResult(false, "Invalid ride type: " + subtype + ". Valid types: " + Object.keys(config.rides).sort().join(", "));
        }
        if (!config.rides[subtype].hasOwnProperty(subclass)) {
            return new CommandResult(false, "Invalid ride subclass: " + subclass + ". Valid subclasses: " + Object.keys(config.rides[subtype]).sort().join(", "));
        }
        if (!available_entities.includes(subclass)) {
            return new CommandResult(false, "Ride has not been researched yet: " + subclass + ". Researched subclasses: " + available_entities.join(", "));
        }
        return Ride.checkPrice(subtype, subclass, ticket_price)
    }

    static checkPrice(subtype, subclass, ticket_price) {
        if(ticket_price && !Number.isInteger(ticket_price)) {
            return new CommandResult(false, "Ticket price must be an integer. Received: " + ticket_price);
        }
        if (ticket_price < 0) {
            return new CommandResult(false, "Ticket price cannot be negative: " + ticket_price);
        }
        if ((ticket_price > config.rides[subtype][subclass].max_ticket_price)) {
            return new CommandResult(false, "Invalid ticket price: " + ticket_price + ". Max ticket price: " + config.rides[subtype][subclass].max_ticket_price);
        }
        return new CommandResult(true, "Valid ride parameters");
    }

    /**
     * Adds a guest to the ride's queue if there's space.
     * @param {object} guest - The guest object.
     * @returns {boolean} True if the guest was added.
     */
    queueGuest(guest) {
        guest.waiting = true;
        guest.ride_waiting_for = this;
        this.total_guests_queued += 1;
        this.queue.push(guest);
    }

    boardGuests(park) {
        const num_guests_to_board = Math.min(this.capacity - this.boarded_guests.length, this.queue.length);
        // Board queued guests
        // If we go from no guests to some guests, start to countdown time before the ride runs
        // This is sped up with each additional guest (minus two ticks per new guest)
        for (let i = 0; i < num_guests_to_board; i++) {
            const guest = this.queue.shift(); // Pop first element from queue
            guest.money -= this.price;
            guest.money_spent += this.price;
            guest.recordVisit(this);
            park.money += this.price;
            park.revenue += this.price;
            this.revenue_generated += this.price;
            

            this.boarded_guests.push(guest);
        }
        if (this.boarded_guests.length > 0 && this.countdown_until_run <= -1) {
            this.countdown_until_run = Math.round(this.capacity * 2);
        }

        this.countdown_until_run -= this.boarded_guests.length;
    }

    runRide(park) {
        this.times_operated += 1;
        park.money -= this.cost_per_operation;
        park.expenses += this.cost_per_operation;
        this.operating_cost += this.cost_per_operation;

        // Simulate a breakdown. No breakdowns on the first 5 steps to avoid game altering breakdows
        if (park.step > 4 && park.rng.random() < this.breakdown_rate) {
            this.out_of_service = true;
            this.remaining_repair_time = Math.round(config.rides[this.subtype][this.subclass].building_cost * config.ride_repair_cost_percentage);
            for (let guest of this.queue.concat(this.boarded_guests)) {
                guest.waiting = false;
                guest.ride_waiting_for = null;
            }
            this.queue = [];
            this.boarded_guests = [];
            this.phase = "waiting";
            this.countdown_until_run = -1;
        }
    }

    disembarkGuests(park) {
        for (let guest of this.boarded_guests) {
            guest.happiness = Math.min(1.0, guest.happiness + this.excitement / 20); //  a ride with 10 excitement gives 0.5 happiness, or a ride with 2 excitement gives 0.1 happiness
            guest.waiting = false;
            guest.ride_waiting_for = null;
            this.guests_entertained += 1;
        }
        this.boarded_guests = [];
        this.countdown_until_run = -1;
    }

    /**
     * Operate the ride: charge ticket prices, boost guest happiness,
     * then clear the queue. Also, simulate a breakdown.
     * @param {object} park - The park instance for revenue updates and grid access.
     */
    operate(park) {
        if (this.out_of_service) {return};

        this.uptime++;

        // Rides stop operating a few steps before the end of the day
        if (this.phase === "waiting") {
            this.boardGuests(park);
            // If the ride is ready to run, run it
            if (this.countdown_until_run <= 0 && this.boarded_guests.length > 0) {
                this.phase = "running";
            }

        } else if (this.phase === "running") {
            if (park.money < this.cost_per_operation) {
                return;
            }
            this.runRide(park);
            this.phase = "disembarking";
        } 
        
        else if (this.phase === "disembarking") {
            this.disembarkGuests(park);
            this.phase = "waiting";
        }
    }

    format() {
        return {
            ...super.format(),
            subtype: this.subtype,
            subclass: this.subclass,
            out_of_service: this.out_of_service,
            uptime: Math.round((this.uptime / config.ticks_per_day) * 100, 2) / 100,
            unnorm_uptime: this.uptime,
            ticket_price: this.price,
            cost_per_operation: this.cost_per_operation,
            operating_cost: this.operating_cost,
            revenue_generated: this.revenue_generated,
            capacity: this.capacity,
            intensity: this.intensity,
            excitement: this.excitement,
            breakdown_rate: this.breakdown_rate,
            guests_entertained: this.guests_entertained,
            times_operated: this.times_operated,
            total_guests_queued: this.total_guests_queued,
            total_wait_time: this.total_wait_time,
            remaining_repair_time: this.remaining_repair_time,
            avg_wait_time: Math.round((this.total_guests_queued > 0 ? this.total_wait_time / this.total_guests_queued : 0) * 100, 2) / 100,
            avg_guests_per_operation: Math.round((this.times_operated > 0 ? this.guests_entertained / this.times_operated : 0) * 100, 2) / 100,
        }
    }

    midday_format() {
        return {
            ...super.format(),
            out_of_service: this.out_of_service,
            operating_cost: this.operating_cost,
            revenue_generated: this.revenue_generated,
            guests_entertained: this.guests_entertained,
            times_operated: this.times_operated,
            avg_wait_time: Math.round((this.total_guests_queued > 0 ? this.total_wait_time / this.total_guests_queued : 0) * 100, 2) / 100,
            avg_guests_per_operation: Math.round((this.times_operated > 0 ? this.guests_entertained / this.times_operated : 0) * 100, 2) / 100,
            uptime: Math.round((this.uptime / config.ticks_per_day) * 100, 2) / 100,
        }
    }

    startOfDay() {
        this.revenue_generated = 0
        this.operating_cost = 0
        this.guests_entertained = 0
        this.times_operated = 0
        this.total_guests_queued = 0
        this.uptime = 0.0
        this.total_wait_time = 0;
        this.total_guests_queued = 0;
        this.avg_wait_time = 0;
        this.avg_guests_per_operation = 0;
        this.queue = []
        this.boarded_guests = []
    }
}

export default Ride;