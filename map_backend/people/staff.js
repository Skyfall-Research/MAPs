import config from "../config.js";
import { Person } from "./person.js";

export class Staff extends Person {
    constructor(x, y, subtype, subclass, grid, step) {
        super(x, y, "staff", grid)
        this.subtype = subtype;
        this.subclass = subclass
        this.salary = config.staff[subtype][subclass].salary;
        this.operating_cost = 0;
        this.id = `${subtype}-${step}`;
        this.success_metric_value = 0;
    }

    setState(state){
       this.x = state.x
       this.y = state.y 
       this.type = state.type
       this.subtype = state.subtype
       this.subclass = state.subclass
       this.success_metric_value = state.success_metric_value
       this.operating_cost = state.operating_cost
       if(state.id !== undefined){
            this.id = state.id
        }
    }

    format() {
        return {
            ...super.format(),
            id: this.id,
            subtype: this.subtype,
            subclass: this.subclass,
            salary: this.salary,
            operating_cost: this.operating_cost,
            success_metric: this.success_metric,
            success_metric_value: Math.round(this.success_metric_value * 100, 2) / 100,
            tiles_traversed: this.tiles_traversed,
        }
    }

    midday_format() {
        return this.format();
    }
}
    
export class Janitor extends Staff {
    constructor(x, y, subclass, grid, step) {
        super(x, y, "janitor", subclass, grid, step);
        this.curr_target = null;
        this.success_metric = "amount_cleaned";
        this.success_metric_value = 0;
        this.tiles_traversed = 0;
    }

    static fromEmployee(employee, grid, step){
        const new_janitor = new Janitor(employee.x, employee.y, employee.subclass, grid, step)
        new_janitor.setState(employee)
        new_janitor.success_metric_value = employee.success_metric_value
        new_janitor.tiles_traversed = employee.tiles_traversed
        new_janitor.curr_target = employee.curr_target
        return new_janitor
    }

    // Clean the tile if it is dirty (cleanliness < 1.0)
    clean(park) {
        if(this.curr_target == null){
            let possible_targets = []
            let target_weights = []
            for (let tile of this.grid.getAllTiles()) {
                if (tile.cleanliness < config.staff.janitor[this.subclass].cleaning_threshold && this.grid.routing_table[this.x]?.[this.y]?.[tile.x]?.[tile.y] !== undefined) {
                    possible_targets.push(tile)
                    target_weights.push(1 / (tile.cleanliness + 0.001))
                }
            }
            this.selectNewTarget(possible_targets, park.rng, target_weights)
        }

        const curr_tile = this.grid.getTile(this.x, this.y)

        const cleaning_rate = config.staff.janitor[this.subclass].clean_rate

        if (this.curr_target === null) {
            // No expense to the park occurs in this case
            // Do nothing, everything in the park is clean
        }
        // Clean the target tile if we've reached it
        else if (this.x === this.curr_target.x && this.y === this.curr_target.y) {
            // Track tiles cleaned
            if (park.money < 1) {
                return;
            }
            this.success_metric_value += cleaning_rate;
            park.money --;
            this.operating_cost++;
            park.expenses++;

            this.curr_target.cleanliness = Math.min(1.2, this.curr_target.cleanliness + cleaning_rate);
            if (this.curr_target.cleanliness >= config.staff.janitor[this.subclass].cleaning_threshold) {
                this.curr_target = null;
            }
        } // Small chance to clean a tile on the way to our target if it is dirty
        else if (park.rng.random() < 0.1 && curr_tile.cleanliness < config.staff.janitor[this.subclass].cleaning_threshold) {
            if (park.money < 1) {
                return;
            }
            // Track tiles cleaned
            this.success_metric_value += cleaning_rate;
            park.money --;
            this.operating_cost++;
            park.expenses++;


            curr_tile.cleanliness = Math.min(1.0, curr_tile.cleanliness + cleaning_rate);
        }
        // Otherwise move toward our target
        else {
            this.tiles_traversed += 1;
            this.moveToward(this.curr_target.x, this.curr_target.y);
            if (this.subclass != "yellow" && (this.x != this.curr_target.x || this.y != this.curr_target.y)) {
                this.tiles_traversed += 1;
                this.moveToward(this.curr_target.x, this.curr_target.y);
            }
        }
    }
}

export class Mechanic extends Staff {
    constructor(x, y, subclass, grid, step) {
        super(x, y, "mechanic", subclass, grid, step);
        this.curr_target = null;
        this.tiles_traversed = 0;
        this.success_metric = "repair_steps_performed";
        this.success_metric_value = 0;
    }

    static fromEmployee(employee, grid, step){
        const new_mechanic = new Mechanic(employee.x, employee.y, employee.subclass, grid, step)
        new_mechanic.setState(employee)
        new_mechanic.success_metric_value = employee.success_metric_value
        new_mechanic.tiles_traversed = employee.tiles_traversed
        new_mechanic.curr_target = employee.curr_target
        return new_mechanic
    }

    // Repair broken rides that need maintenance.
    repair(park) {
        if(this.curr_target == null){
            let target_rides = park.rides.filter(ride => ride.out_of_service && 
                (this.grid.routing_table[this.x]?.[this.y]?.[ride.x]?.[ride.y] !== undefined || (ride.x === this.x && ride.y === this.y)))
            this.selectNewTarget(target_rides, park.rng)
        }

        if (this.curr_target != null) {
            const repairs_per_tick = config.staff.mechanic[this.subclass].repair_rate
            if (this.x === this.curr_target.x && this.y === this.curr_target.y && park.money >= repairs_per_tick) {                
                // If reached the ride, repair it
                if(this.curr_target.remaining_repair_time <= 0) {
                    this.curr_target.remaining_repair_time = 0;
                    this.curr_target.out_of_service = false;
                    this.curr_target = null;
                } else {
                    this.curr_target.remaining_repair_time -= repairs_per_tick;
                    park.money -= repairs_per_tick; // Deduct money for repairs (base cost)
                    park.expenses += repairs_per_tick;
                    this.success_metric_value += repairs_per_tick;
                    this.operating_cost += repairs_per_tick;
                }
            } else {
                this.tiles_traversed += 1;
                this.moveToward(this.curr_target.x, this.curr_target.y);
                if (this.subclass != "yellow" && (this.x != this.curr_target.x || this.y != this.curr_target.y)) {
                    this.tiles_traversed += 1;
                    this.moveToward(this.curr_target.x, this.curr_target.y);
                }
            }
        }
    }
}


export class Clown extends Staff {
    constructor(x, y, subclass, grid, step) {
        super(x, y, "specialist", subclass, grid, step);
        this.curr_target = null;
        this.prev_target = null;
        this.tiles_traversed = 0;
        this.success_metric = "guests_entertained";
        this.success_metric_value = 0;
    }

    static fromEmployee(employee, grid, step){
        const new_clown = new Clown(employee.x, employee.y, employee.subclass, grid, step)
        new_clown.setState(employee)
        new_clown.success_metric_value = employee.success_metric_value
        new_clown.tiles_traversed = employee.tiles_traversed
        new_clown.curr_target = employee.curr_target
        new_clown.prev_target = employee.prev_target
        return new_clown
    }

    entertain(park) {
        if(this.curr_target == null){
            // Targets operational rides that are reachable via the routing table or on the same tile as the clown
            let target_rides = park.rides.filter(ride => (this.grid.routing_table[this.x]?.[this.y]?.[ride.x]?.[ride.y] !== undefined || (ride.x === this.x && ride.y === this.y)) && !ride.out_of_service)
            let target_weights = park.rides.map(ride => (ride.queue.length + ride.boarded_guests.length + 0.1))
            this.selectNewTarget(target_rides, park.rng, target_weights)
        }
        else if (this.x === this.curr_target.x && this.y === this.curr_target.y){
            // entertain guests
            for (let guest of this.curr_target.queue.concat(this.curr_target.boarded_guests)) {
                guest.happiness = Math.min(1.0, guest.happiness + config.staff[this.subtype][this.subclass].happiness_boost)
                this.success_metric_value += 1;
            }
            this.prev_target = this.curr_target;
            this.curr_target = null;
            this.next_target = null;
        }
        else {
            this.tiles_traversed += 1;
            this.moveToward(this.curr_target.x, this.curr_target.y);
        }
    }
}

export class Stocker extends Staff {
    constructor(x, y, subclass, grid, step) {
        super(x, y, "specialist", subclass, grid, step);
        this.next_target = null;
        this.curr_target = null;
        this.prev_target = null;
        this.tiles_traversed = 0;
        this.restocks_performed = 0;
        this.carried_inventory = 0;
        this.success_metric = "items_restocked";
    }

    static fromEmployee(employee, grid, step){
        const new_stocker = new Stocker(employee.x, employee.y, employee.subclass, grid, step)
        new_stocker.setState(employee);
        new_stocker.tiles_traversed = employee.tiles_traversed;
        new_stocker.curr_target = employee.curr_target;
        new_stocker.next_target = employee.next_target;
        new_stocker.prev_target = employee.prev_target;
        new_stocker.restocks_performed = employee.restocks_performed;
        new_stocker.carried_inventory = employee.carried_inventory;
        return new_stocker
    }

    stock(park, day_tick) {
        // Don't do any more purchases in the last ticks of the day
        if ((config.ticks_per_day - day_tick) < config.staff.specialist[this.subclass].idle_ticks && this.carried_inventory === 0){
            return;
        }

        if(this.curr_target == null){
            // Target shops that are under 25% inventory
            let target_shops = park.shops.filter(shop => 
                (shop.inventory / shop.order_quantity) < config.staff.specialist[this.subclass].restock_threshold && 
                (this.grid.routing_table[this.x]?.[this.y]?.[shop.x]?.[shop.y] !== undefined || (shop.x === this.x && shop.y === this.y))
            )
            if (target_shops.length == 0) {
                return;
            }
            let target_weights = park.shops.map(shop => (shop.order_quantity / (shop.inventory + 0.1)))
            this.selectNewTarget(target_shops, park.rng, target_weights)

            // Must go to entrance or exit to pick up stock before 
            this.next_target = this.curr_target
            const exit_distance = this.grid.distance_table[this.x][this.y][park.exit.x][park.exit.y]
            const entrance_distance = this.grid.distance_table[this.x][this.y][park.entrance.x][park.entrance.y]
            this.selectNewTarget([park.exit, park.entrance], park.rng, [1 / exit_distance, 1 / entrance_distance])
        }
        else if (this.x === this.curr_target.x && this.y === this.curr_target.y){
            if (this.next_target === null) { //  If next target is null then we're at the shop to restock
                // stock shops with inventory
                this.curr_target.inventory += this.carried_inventory;
                if (this.curr_target.inventory > 0) {
                    this.curr_target.out_of_service = false;
                }
                // Update counters
                this.success_metric_value += this.carried_inventory;
                this.curr_target.number_of_restocks += 1;

                this.carried_inventory = 0;


                // Move to next location
                this.prev_target = this.curr_target;
                this.curr_target = null;
                this.next_target = null;
            } else { // If next target is not null then we're at the entrance/exit 
                const restock_rate = config.staff.specialist[this.subclass].stocking_rate;
                const max_stock_inv = config.staff.specialist[this.subclass].max_inventory;

                // Figure out how many units we can buy.
                // Min of Stocker's carry capacity,
                //        number of units required by the store
                //        number of units park can afford to buy
                //        stocker % of store's max order_quantity
                this.carried_inventory = Math.min(max_stock_inv, 
                    this.next_target.order_quantity - this.next_target.inventory, 
                    Math.floor(this.next_target.order_quantity * restock_rate))
                if (this.next_target.item_cost !== 0){
                    this.carried_inventory = Math.min(Math.floor(park.money/this.next_target.item_cost),
                                                      this.carried_inventory)
                }

                park.money -= this.carried_inventory * this.next_target.item_cost;
                park.expenses += this.carried_inventory * this.next_target.item_cost;
                this.operating_cost += this.carried_inventory * this.next_target.item_cost;

                this.curr_target = this.next_target
                this.next_target = null;
            }
        }
        else {
            this.tiles_traversed += 2;
            this.moveToward(this.curr_target.x, this.curr_target.y);
            this.moveToward(this.curr_target.x, this.curr_target.y);
        }
    }
}

export class ParkCrier extends Staff {
    constructor(x, y, subclass, grid, step) {
        super(x, y, "specialist", subclass, grid, step);
        this.curr_target = null;
        this.prev_target = null;
        this.tiles_traversed = 0;
        this.success_metric = "guests_informed";
    }

    static fromEmployee(employee, grid, step){
        const new_park_crier = new ParkCrier(employee.x, employee.y, employee.subclass, grid, step)
        new_park_crier.setState(employee)
        new_park_crier.success_metric_value = employee.success_metric_value
        new_park_crier.tiles_traversed = employee.tiles_traversed
        new_park_crier.curr_target = employee.curr_target
        new_park_crier.prev_target = employee.prev_target
        return new_park_crier
    }

    inform(park) {
        if(this.curr_target == null){
            let target_rides = park.rides.filter(ride =>
                this.grid.routing_table[this.x]?.[this.y]?.[ride.x]?.[ride.y] !== undefined || (ride.x === this.x && ride.y === this.y)
            )
            let target_weights = park.rides.map(ride => (ride.queue.length + ride.boarded_guests.length + 0.1))
            this.selectNewTarget(target_rides, park.rng, target_weights)
        }
        else if (this.x === this.curr_target.x && this.y === this.curr_target.y){
            for (let guest of this.curr_target.queue.concat(this.curr_target.boarded_guests)) {
                guest.has_status_info = true;
                this.success_metric_value += 1;
            }
            this.prev_target = this.curr_target;
            this.curr_target = null;
            this.next_target = null;
        }
        else {
            this.tiles_traversed += 2;
            this.moveToward(this.curr_target.x, this.curr_target.y);
            this.moveToward(this.curr_target.x, this.curr_target.y);
        }
    }
}

export class Vendor extends Staff {
    constructor(x, y, subclass, grid, step) {
        super(x, y, "specialist", subclass, grid, step);
        this.curr_target = null;
        this.prev_target = null;
        this.tiles_traversed = 0;
        this.success_metric = "guests_served";
    }

    static fromEmployee(employee, grid, step){
        const new_vendor = new Vendor(employee.x, employee.y, employee.subclass, grid, step)
        new_vendor.setState(employee)
        new_vendor.success_metric_value = employee.success_metric_value
        new_vendor.tiles_traversed = employee.tiles_traversed
        new_vendor.curr_target = employee.curr_target
        new_vendor.prev_target = employee.prev_target
        return new_vendor
    }

    sell(park) {
        if(this.curr_target == null){
            let target_rides = park.rides.filter(ride =>
                this.grid.routing_table[this.x]?.[this.y]?.[ride.x]?.[ride.y] !== undefined || (ride.x === this.x && ride.y === this.y)
            )
            let target_weights = park.rides.map(ride => (ride.queue.length + ride.boarded_guests.length + 0.1))
            this.selectNewTarget(target_rides, park.rng, target_weights)
        }
        else if (this.x === this.curr_target.x && this.y === this.curr_target.y){
            // sell food/drinks to guests
            for (let guest of this.curr_target.queue.concat(this.curr_target.boarded_guests)) {
                guest.hunger = Math.max(0.0, guest.hunger - config.staff[this.subtype][this.subclass].hunger_reduction)
                guest.thirst = Math.max(0.0, guest.thirst - config.staff[this.subtype][this.subclass].thirst_reduction)
                this.success_metric_value += 1;
            }
            this.success_metric_value += 1;
            this.prev_target = this.curr_target;
            this.curr_target = null;
            this.next_target = null;
        }
        else {
            this.tiles_traversed += 3;
            this.moveToward(this.curr_target.x, this.curr_target.y);
            this.moveToward(this.curr_target.x, this.curr_target.y);
            this.moveToward(this.curr_target.x, this.curr_target.y);
        }
    }
}

export default Staff;
