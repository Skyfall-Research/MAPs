import Grid from "./grid.js";
import { PathTile, WaterTile, EntranceTile, ExitTile } from "./tiles/tile.js";
import Ride from "./tiles/ride.js";
import Shop from "./tiles/shop.js";
import Guest from "./people/guest.js";
import { Janitor, Mechanic, Clown, Stocker, ParkCrier, Vendor } from "./people/staff.js";
import Research from "./research.js";
import config from './config.js';
import { CommandResult, RNG } from "./utils.js";
import TrajectoryLogger from "./node_utils/logger.js";
import fs from 'fs';
import YAML from 'yaml';

const guest_enums = YAML.parse(fs.readFileSync('./shared/guest_enums.yaml', 'utf8'));


class Park {
    constructor(parkId = null) {
        this.parkId = parkId;
        this.size = config.park_size;
        this.initialized = false;
        // Initialize logger - will be used to replace history array
        this.logger = new TrajectoryLogger(parkId);
        this.rng = new RNG();
        this.sandbox_mode = false;
        this.sandbox_steps = -1;
        this.sandbox_action_budget = 0;
        this.seed = null;
        this.value = 0;
        this.info = "";
        this.action_valid = false;
    }

    setSeed(seed) {
        if (!seed) {
            seed = this.rng.randomInt(0, 10000);
        }
        this.seed = seed;
        this.rng = new RNG(seed);
        console.log("Seed set to: ", seed);
        return new CommandResult(true, `Seed=${seed}`);
    }

    setSandboxMode(sandbox_steps) {
        this.sandbox_mode = sandbox_steps > 0;
        this.sandbox_steps = sandbox_steps;
        this.sandbox_action_budget = Math.floor(sandbox_steps * 1.5);
        console.log("Sandbox mode successfully set for %s steps", sandbox_steps, this.sandbox_mode, this.sandbox_steps);
        if (this.logger.trajectoryData.length > 0) {
            const updatedState = this.calculateFullState({includeGuests: false});
            const lastEntry = this.logger.trajectoryData[this.logger.trajectoryData.length - 1];
            if (lastEntry) {
                lastEntry.end_state = updatedState;
            }
        }
        return new CommandResult(true, `Sandbox mode successfully set for ${sandbox_steps} steps`);
    }

    reset({layout, difficulty, starting_money, horizon, return_midday_states = false}) {
        this.layout = layout;
        this.difficulty = difficulty;
        this.startingMoney = starting_money || {"easy": 500, "medium": 500, "hard": 500}[difficulty];
        this.money = this.startingMoney;
        this.value = this.money;
        this.horizon = horizon || config.horizon_by_difficulty[difficulty];
        this.guest_preferences = ["no preferences"];
        this.grid = new Grid(this.size);
        this.guests = [];
        this.rides = [];
        this.shops = [];
        this.staff = []; // Will include janitors and mechanics
        this.curr_guest_count = 0;
        this.revenue = 0; //revenue;
        this.expenses = 0;
        this.salaries_paid = 0;
        this.research = new Research(difficulty);
        this.step = 0; //step
        this.prev_guest_happiness = 0.3;
        this.park_excitement = 0;
        this.park_rating = 20;
        this.num_guests_to_survey = 0;
        this.guest_survey_results = {"list_of_results": [], "age_of_results": 0};
        this.return_midday_states = return_midday_states;
        this.midday_history = [];
        this.action = "reset()";
        this.info = "";
        // Set the provided layout if it exists
        if (layout == 'random') {
            // TODO Currently broken
            this.grid.setupRandomParkLayout(this.difficulty, this.rng);
        } else {
            if (!layout || layout === "undefined") {
                layout = "test"
            }
            try {
                layout = YAML.parse(fs.readFileSync(`./shared/layouts/${layout}.yaml`, 'utf8'));
                this.grid.setupProvidedParkLayout(layout.layout, this.difficulty);
                if (this.difficulty === "hard" && layout.preferences) {
                    this.guest_preferences = layout.preferences[0];
                }
            } catch (error) {
                console.log(error);
                throw new Error("Invalid layout: " + layout);
            }
        } 
        this.entrance = this.grid.entrance
        this.exit = this.grid.exit
        this.initialized = true;

        // Record the cheapest ride
        this.cheapest_building_cost = undefined
        for (const subtype in config.rides){
            for (const subclass in config.rides[subtype]){
                if (this.cheapest_building_cost === undefined || config.rides[subtype][subclass].building_cost < this.cheapest_building_cost){
                    this.cheapest_building_cost = config.rides[subtype][subclass].building_cost
                }
            }
        }
        for (const subtype in config.shops){
            for (const subclass in config.shops[subtype]){
                if (this.cheapest_building_cost === undefined || config.shops[subtype][subclass].building_cost < this.cheapest_building_cost){
                    this.cheapest_building_cost = config.shops[subtype][subclass].building_cost
                }
            }
        }

        // Start logging new episode with initial state
        const initialState = this.calculateFullState();
        this.logger.newEpisode(initialState);

        this.setSeed(this.seed);

        if (this.sandbox_mode) {
            this.sandbox_action_budget--;
            console.log("Sandbox action budget: ", this.sandbox_action_budget);
            if (this.sandbox_action_budget < 0) {
                this.sandbox_mode = false;
                this.sandbox_steps = 0;
                return new CommandResult(false, "You have run out of free sandbox actions. Using a learning day step.");
            }
        }
        return new CommandResult(true, "Park reset successfully");
    }

    setState(state){
        this.difficulty = state.difficulty;
        this.grid = new Grid(this.size);
        this.guests = [];
        this.rides = [];
        this.shops = [];
        this.staff = []; // Will include janitors and mechanics
        this.curr_guest_count = 0;
        this.money = state.state.money;
        this.value = state.state.value;
        this.layout = state.layout;
        this.revenue = state.state.revenue;
        this.expenses = state.state.expenses;
        this.salaries_paid = state.state.total_salary_paid;
        this.step = state.state.step;
        this.horizon = state.state.horizon;
        this.prev_guest_happiness = state.state.prev_guest_happiness;
        this.guest_preferences = state.guest_preferences;
        
        // Set Research object
        this.research = new Research(this.difficulty);
        this.research.current_attraction = state.state.research_current_ride
        this.research.current_color = state.state.research_current_color
        this.research.topic_index = state.state.research_topic_index
        this.research.unresearched_entities = state.state.research_unresearched_entities
        this.research.research_speed = state.state.research_speed
        this.research.research_topics = state.state.research_topics

        for (const ride_type in state.state.available_entities) {
            this.research.researched_entities[ride_type] = state.state.available_entities[ride_type]
        }

        this.num_guests_to_survey = 0;
        this.guest_survey_results = state.guest_survey_results;
 
        // Write objects in grid
        // Set Entrance and Exit
        this.entrance = EntranceTile.fromEntrance(state.entrance)
        this.exit = ExitTile.fromExit(state.exit)
        this.grid.unsafePlaceElement(this.entrance.x, this.entrance.y, this.entrance)
        this.grid.unsafePlaceElement(this.exit.x, this.exit.y, this.exit)
        this.grid.entrance = this.entrance 
        this.grid.exit = this.exit

        // Set Terrain
        for (let terrain of state.terrain) {
            let obj = undefined
            if (terrain.type == "path") {
                obj = PathTile.fromPath(terrain);
            } else {
                obj = new WaterTile(terrain.x, terrain.y)
            }
            this.grid.unsafePlaceElement(terrain.x, terrain.y, obj);
        }

        // Create rides and add to the grid
        this.rides = state.rides.map((r) => Ride.fromRide(r, this))
        for(let ride of this.rides){
            this.grid.unsafePlaceElement(ride.x, ride.y, ride)
        }

        this.shops = state.shops.map((s) => Shop.fromShop(s, this))
        for(let shop of this.shops){
            this.grid.unsafePlaceElement(shop.x, shop.y, shop)
        }

        this.rides.sort((a, b) => a.x !== b.x ? a.x - b.x : a.y - b.y);
        this.shops.sort((a, b) => a.x !== b.x ? a.x - b.x : a.y - b.y);

        const janitors = state.staff.filter(staff => staff.subtype === "janitor").sort((a, b) => a.x - b.x || a.y - b.y || b.amount_cleaned - a.amount_cleaned).map(employee => Janitor.fromEmployee(employee, this.grid, this.step));
        const mechanics = state.staff.filter(staff => staff.subtype === "mechanic").sort((a, b) => a.x - b.x || a.y - b.y || b.repair_steps_performed - a.repair_steps_performed).map(employee => Mechanic.fromEmployee(employee, this.grid, this.step));
        const specialists = state.staff.filter(staff => staff.subtype === "specialist").sort((a, b) => a.x - b.x || a.y - b.y || b.success_metric - a.success_metric).map(employee => {
            if (employee.subclass === "yellow") {
                return Clown.fromEmployee(employee, this.grid, this.step);
            } else if (employee.subclass === "blue") {
                return Stocker.fromEmployee(employee, this.grid, this.step);
            } else if (employee.subclass === "green") {
                return ParkCrier.fromEmployee(employee, this.grid, this.step);
            } else if (employee.subclass === "red") {
                return Vendor.fromEmployee(employee, this.grid, this.step);
            }
        });

        this.staff = [...janitors, ...mechanics, ...specialists];

        this.park_rating = state.state.park_rating;
        this.park_excitement = state.state.park_excitement;
        // recompute routing table
        this.grid.computeRoutingTable(state.difficulty);
        this.initialized = true;

        // Record the cheapest ride
        this.cheapest_building_cost = undefined
        for (const subtype in config.rides){
            for (const subclass in config.rides[subtype]){
                if (this.cheapest_building_cost === undefined || config.rides[subtype][subclass].building_cost < this.cheapest_building_cost){
                    this.cheapest_building_cost = config.rides[subtype][subclass].building_cost
                }
            } 
        }
        for (const subtype in config.shops){
            for (const subclass in config.shops[subtype]){
                if (this.cheapest_building_cost === undefined || config.shops[subtype][subclass].building_cost < this.cheapest_building_cost){
                    this.cheapest_building_cost = config.shops[subtype][subclass].building_cost
                }
            }
        }
        this.action = "setState()";
    }

    // ACTIONS
    addRide(x, y, subtype, subclass, ticket_price) {
        this.action = `place(x=${x}, y=${y}, type="ride", subtype="${subtype}", subclass="${subclass}", price=${ticket_price})`;
        this.expenses = 0;
        this.revenue = 0;
        this.info = "";
        this.action_valid = false;
        let result = Ride.checkParameters(subtype, subclass, ticket_price, this.research.researched_entities[subtype]);
        if (!result.success) {
            this.info = result.message;
            return result;
        }
        if (!this.grid.tileIsInBounds(x, y)) {
            const error_message = "Invalid placement for ride. (" + x + ", " + y + ") must each be within park bounds, i.e., >= 0 and <" + this.size + ".";
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
        if (!this.grid.tileIsAdjacentToPath(this.grid.getTile(x, y))) {
            const error_message = "Invalid placement for ride. Must be adjacent to a path tile.";
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
        if (this.money < config.rides[subtype][subclass].building_cost) {
            const error_message = "Insufficient funds to add ride. Required: " + config.rides[subtype][subclass].building_cost + ", Available: " + this.money;
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
        const ride = new Ride(x, y, subtype, subclass, ticket_price, this);
        result = this.grid.placeElement(x, y, ride)
        if (result.success) {
            // Insert ride at the correct position to maintain sorted order
            let insertIndex = 0;
            for (let i = 0; i < this.rides.length; i++) {
                if (ride.x < this.rides[i].x || 
                    (ride.x === this.rides[i].x && ride.y < this.rides[i].y)) {
                    insertIndex = i;
                    break;
                }
                insertIndex = i + 1;
            }
            this.rides.splice(insertIndex, 0, ride);
            
            this.money -= config.rides[subtype][subclass].building_cost;
            this.expenses += config.rides[subtype][subclass].building_cost;
            this.action_valid = true;
            return new CommandResult(true, ride.format());
        }
        const error_message = "Failed to add ride to " + x + "," + y + ". " + result.message;
        this.info = error_message;
        return new CommandResult(false, error_message);
    }

    addShop(x, y, subtype, subclass, price, order_quantity) {
        this.action = `place(x=${x}, y=${y}, type="shop", subtype="${subtype}", subclass="${subclass}", price=${price}, order_quantity=${order_quantity})`;
        this.expenses = 0;
        this.revenue = 0;
        this.info = "";
        this.action_valid = false;
        let result = Shop.checkParameters(subtype, subclass, price, order_quantity, this.research.researched_entities[subtype]);
        if (!result.success) {
            this.info = result.message;
            return result;
        }
        if (!this.grid.tileIsInBounds(x, y)) {
            const error_message = "Invalid placement for attraction. (" + x + ", " + y + ") must each be within park bounds, i.e., >= 0 and <" + this.size + ".";
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
        if (!this.grid.tileIsAdjacentToPath(this.grid.getTile(x, y))) {
            const error_message = "Invalid placement for shop. Must be adjacent to a path tile.";
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
        if (this.money < config.shops[subtype][subclass].building_cost) {
            const error_message = "Insufficient funds to add shop. Required: " + config.shops[subtype][subclass].building_cost + ", Available: " + this.money;
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
        const shop = new Shop(x, y, subtype, subclass, price, order_quantity);
        result = this.grid.placeElement(x, y, shop)
        if (result.success) {
            // Insert shop at the correct position to maintain sorted order
            let insertIndex = 0;
            for (let i = 0; i < this.shops.length; i++) {
                if (shop.x < this.shops[i].x || 
                    (shop.x === this.shops[i].x && shop.y < this.shops[i].y)) {
                    insertIndex = i;
                    break;
                }
                insertIndex = i + 1;
            }
            this.shops.splice(insertIndex, 0, shop);
            
            this.money -= config.shops[subtype][subclass].building_cost;
            this.expenses += config.shops[subtype][subclass].building_cost;
            this.action_valid = true;
            return new CommandResult(true, shop.format());
        }
        const error_message = "Failed to add shop to " + x + "," + y + ". " + result.message;
        this.info = error_message;
        return new CommandResult(false, error_message);
    }

    moveAttraction(type, subtype, subclass, x, y, new_x, new_y) {
        this.action = `move(x=${x}, y=${y}, type="${type}", subtype="${subtype}", subclass="${subclass}", new_x=${new_x}, new_y=${new_y})`;
        this.expenses = 0;
        this.revenue = 0;
        this.info = "";
        this.action_valid = false;
        if (!this.grid.tileIsInBounds(x, y)) {
            const error_message = "Invalid x, y coordinates. (" + x + ", " + y + ") must each be within park bounds, i.e., >= 0 and <" + this.size + ".";
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
        let attraction = this.grid.getTile(x, y);
        if (attraction.type != type) {
            const error_message = `The provided type (${type}) does not match the type occupying the tile (${attraction.type})`;
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
        if (!this.grid.tileIsInBounds(new_x, new_y)) {
            const error_message = "Invalid placement for attraction. (" + new_x + ", " + new_y + ") must each be within park bounds, i.e., >= 0 and <" + this.size + ".";
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
        if (this.grid.tileIsAdjacentToPath(this.grid.getTile(new_x, new_y))) {
            const result = this.grid.placeElement(new_x, new_y, attraction)
            if (result.success) {
                this.grid.clearTile(x, y)
                attraction.x = new_x
                attraction.y = new_y
                attraction.id = `${attraction.type}-(${new_x},${new_y})`

                if (attraction.type == "ride") {
                    this.rides.sort((a, b) => a.x !== b.x ? a.x - b.x : a.y - b.y);
                } else {
                    this.shops.sort((a, b) => a.x !== b.x ? a.x - b.x : a.y - b.y);
                }

                // Let staff repick their target
                for (let staff of this.staff) {
                    if (attraction.id === staff.curr_target?.id) {
                        staff.curr_target = null;
                    }
                }
                
                this.action_valid = true;
                return new CommandResult(true, attraction.format());
            } else {
                const error_message = "Failed to move attraction to " + new_x + "," + new_y + ". " + result.message;
                this.info = error_message;
                return new CommandResult(false, error_message);
            }
        } else {
            const error_message = "Invalid placement for attraction. Must be adjacent to a path tile.";
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
    }

    modifyAttraction(type, subtype, subclass, x, y, price, order_quantity) {
        this.action = `modify(x=${x}, y=${y}, type="${type}", price=${price}, order_quantity=${order_quantity})`;
        this.expenses = 0;
        this.revenue = 0;
        this.info = "";
        this.action_valid = false;
        if (!this.grid.tileIsInBounds(x, y)) {
            const error_message = "Invalid x, y coordinates. (" + x + ", " + y + ") must each be within park bounds, i.e., >= 0 and <" + this.size + ".";
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
        let attraction = this.grid.getTile(x, y);
        if (attraction.type != type) {
            const error_message = `The provided type (${type}) does not match the type occupying the tile (${attraction.type})`;
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
        if (attraction.type == "shop" && order_quantity === null) {
            const error_message = "order_quantity attribute is null for a shop modify command.";
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
        let result = null;
        if (attraction.type == "ride") {
            result = Ride.checkPrice(attraction.subtype, attraction.subclass, price)
            attraction.price = price;

        } else {
            result = Shop.checkPriceAndQuantity(attraction.subtype, attraction.subclass, price, order_quantity)
            attraction.price = price;
            attraction.order_quantity = order_quantity
        }
        if (!result.success) {
            const error_message = "Failed to modify attraction. " + result.message;
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
        this.action_valid = true;
        return new CommandResult(true, attraction.format());
    }

    sellAttraction(type, subtype, subclass, x, y) {
        this.action = `remove(x=${x}, y=${y}, type="${type}", subtype="${subtype}", subclass="${subclass}")`;
        this.expenses = 0;
        this.revenue = 0;
        this.info = "";
        this.action_valid = false;
        if (!this.grid.tileIsInBounds(x, y)) {
            const error_message = "Invalid x, y coordinates. (" + x + ", " + y + ") must each be within park bounds, i.e., >= 0 and <" + this.size + ".";
            this.info = error_message;
            return new CommandResult(false, error_message);
        }
        const attraction = this.grid.getTile(x, y);

        if (attraction.type != type) {
            const error_message = `The provided type (${type}) does not match the type occupying the tile (${attraction.type})`;
            this.info = error_message;
            return new CommandResult(false, error_message);
        }

        this.grid.clearTile(attraction.x, attraction.y)
        const sell_price = Math.floor(config[attraction.type+"s"][attraction.subtype][attraction.subclass].building_cost * config.sell_percentage)
        this.money += sell_price
        this.revenue += sell_price;
        this.shops = this.shops.filter((s) => s.x !== attraction.x || s.y !== attraction.y)
        this.rides = this.rides.filter((r) => r.x !== attraction.x || r.y !== attraction.y)

        // Update staff to make sure it wasnt their target
        for (let staff of this.staff) {
            if (attraction.id === staff.curr_target?.id) {
                staff.curr_target = null;
            }
        }
        this.action_valid = true;
        return new CommandResult(true, `Sold ${attraction.subtype} at ${attraction.x},${attraction.y} for ${sell_price}`);
    }


    // TODO Implement new action space and fix routes
    // TODO standardize error messages
    hireStaff(x, y, subtype, subclass) {
        this.action = `place(x=${x}, y=${y}, type="staff", subtype="${subtype}", subclass="${subclass}" )`;
        this.expenses = 0;
        this.revenue = 0;
        this.action_valid = false;
        this.info = "";
        if (!this.grid.tileIsInBounds(x, y)) {
            const message = "Invalid location to place staff. (" + x + ", " + y + ") must each be within park bounds, i.e., >= 0 and <" + this.size + ".";
            this.info = message;
            return new CommandResult(false, message);
        }
        if(!["janitor", "mechanic", "specialist"].includes(subtype)){
            const message = "Invalid staff type: " + subtype + ". Must be janitor or mechanic."
            this.info = message;
            return new CommandResult(false, message);
        }
        if(!["yellow", "blue", "green", "red"].includes(subclass)){
            const message = "Invalid staff subclass: " + subclass + ". Must be yellow, blue, green, or red."
            this.info = message;
            return new CommandResult(false, message);
        }
        if (!this.research.researched_entities[subtype].includes(subclass)) {
            return new CommandResult(false, "Staff has not been researched yet: " + subclass + ". Researched subclasses: " + this.research.researched_entities[subtype].join(", "));
        }
        if (['empty', 'water'].includes(this.grid.getTile(x, y).type)) {
            const message = "Invalid location for staff. Must be on a path or in an attraction."
            this.info = message;
            return new CommandResult(false, message);
        }
        let employee = null;
        if(subtype == "janitor"){
            employee = new Janitor(x, y, subclass, this.grid, this.step);
        } else if(subtype == "mechanic"){
            employee = new Mechanic(x, y, subclass, this.grid, this.step);
        } else { // Specialist
            if (subclass == "yellow") {
                employee = new Clown(x, y, subclass, this.grid, this.step);
            } else if (subclass == "blue") {
                employee = new Stocker(x, y, subclass, this.grid, this.step);
            } else if (subclass == "green") {
                employee = new ParkCrier(x, y, subclass, this.grid, this.step);
            } else if (subclass == "red") {
                employee = new Vendor(x, y, subclass, this.grid, this.step);
            } else {
                const message = "Invalid staff subclass: " + subclass + ". Must be yellow, blue, green, or red."
                this.info = message
                return new CommandResult(false, message);
            }
        }
        this.staff.push(employee);
        this.action_valid = true;
        return new CommandResult(true, employee.format());
    }

    fireStaff(subtype, subclass, x, y){
        this.action = `remove(x=${x}, y=${y}, type="staff", subtype="${subtype}", subclass="${subclass}")`;
        this.expenses = 0;
        this.revenue = 0;
        this.action_valid = false;
        this.info = "";
        if (!this.grid.tileIsInBounds(x, y)) {
            const message = "Invalid x, y coordinates for fire staff. (" + x + ", " + y + ") must each be within park bounds, i.e., >= 0 and <" + this.size + ".";
            this.info = message;
            return new CommandResult(false, message);
        }
        
        const employees_to_fire = this.staff.filter((employee) => (employee.subtype == subtype && employee.subclass == subclass && employee.x == x && employee.y == y))

        let employee_to_fire = null;
        for (let employee of employees_to_fire) {
            if (subtype == "janitor") {
                if (employee_to_fire == null || employee.amount_cleaned < employee_to_fire.amount_cleaned) {
                    employee_to_fire = employee;
                }
            } else if (subtype == "mechanic") {
                if (employee_to_fire == null || employee.repair_steps_performed < employee_to_fire.repair_steps_performed) {
                    employee_to_fire = employee;
                }
            } else if (subtype == "specialist") {
                if (employee_to_fire == null || employee.success_metric < employee_to_fire.success_metric) {
                    employee_to_fire = employee;
                }
            }
        }
        if (employee_to_fire == null) {
            const message = `No ${subtype} found at ${x},${y}`
            this.info = message;
            return new CommandResult(false, message);
        }
        
        // Remove the employee from the staff list
        this.staff = this.staff.filter((employee) => employee.id !== employee_to_fire.id)
        this.action_valid = true;
        return new CommandResult(true, employee_to_fire.format());
    }

    moveStaff(subtype, subclass, x, y, new_x, new_y) {
        this.action = `move(x=${x}, y=${y}, type="staff", subtype="${subtype}", subclass="${subclass}", new_x=${new_x}, new_y=${new_y})`;
        this.expenses = 0;
        this.revenue = 0;
        this.action_valid = false;
        this.info = "";
        if (!this.grid.tileIsInBounds(x, y)) {
            const message = "Invalid x, y coordinates for current location. (" + x + ", " + y + ") must each be within park bounds, i.e., >= 0 and <" + this.size + ".";
            this.info = message;
            return new CommandResult(false, message);
        }
        if (!this.grid.tileIsInBounds(new_x, new_y)) {
            const message = "Invalid x, y coordinates for new location. (" + new_x + ", " + new_y + ") must each be within park bounds, i.e., >= 0 and <" + this.size + ".";
            this.info = message;
            return new CommandResult(false, message);
        }
        const staff_to_move = this.staff.find((staff) => (staff.subtype == subtype && staff.subclass == subclass && staff.x == x && staff.y == y))
        if (staff_to_move) {
            if (['empty', 'water'].includes(this.grid.getTile(new_x, new_y).type)) {
                const message = "Invalid location for staff. Must be on a path or in an attraction.";
                this.info = message;
                return new CommandResult(false, message);
            }

            staff_to_move.x = new_x;
            staff_to_move.y = new_y;
            this.action_valid = true;
            return new CommandResult(true, staff_to_move.format());
        } else {
            const message = `No ${subtype} found at ${x},${y}. Existing ${subtype}s locations: ${this.staff.filter(employee => employee.subtype == subtype).map(employee => employee.x + "," + employee.y).join(", ")}`
            this.info = ""
            return new CommandResult(false, message);
        }
    }

    setNumGuestsToSurvey(numGuests) {
        this.action = `survey_guests(num_guests=${numGuests})`;
        this.expenses = 0;
        this.revenue = 0;
        this.action_valid = false;
        this.info = ""
        if (numGuests > config.max_guests_to_survey) {
            const message = "Number of guests to survey must be less than or equal to " + config.max_guests_to_survey;
            this.info = message;
            return new CommandResult(false, message);
        }
        if (this.money < config.per_guest_survey_cost * numGuests) {
            const message = "Insufficient funds to survey guests. Required: " + config.per_guest_survey_cost * numGuests + ", Available: " + this.money;
            this.info = message;
            return new CommandResult(false, message);
        }
        this.money -= config.per_guest_survey_cost * numGuests;
        this.expenses += config.per_guest_survey_cost * numGuests;
        this.num_guests_to_survey = numGuests;
        this.action_valid = true;
        return new CommandResult(true, "Number of guests to survey set successfully");
    }

    setResearch(research_speed, research_topics) {
        this.action = `set_research(research_speed="${research_speed}", research_topics=${JSON.stringify(research_topics)})`;
        this.expenses = 0;
        this.revenue = 0;
        this.action_valid = false;
        this.info = ""
        if (this.difficulty == "easy") {
            const message = "Research cannot be set in easy mode, all research is unlocked from the beginning";
            this.info = message;
            return new CommandResult(false, message);
        }
        const result = Research.checkParameters(research_speed, research_topics);
        if (result.success) {
            this.research.set_research(research_speed, research_topics);
            this.action_valid = true;
            return new CommandResult(true, "Research speed and ride types to research set successfully");
        } else {
            const message = "Failed to set research. " + result.message;
            this.info = message;
            return new CommandResult(false, message);
        }
    }

    maxResearch() {
        if (!this.sandbox_mode) {
            return new CommandResult(false, "Max research can only be called in sandbox mode");
        }
        this.research.research_speed = "none";
        this.research.research_topics = Research.entity_order;
        this.research.researched_entities = {};
        this.research.unresearched_entities = {};
        this.research.fast_days_since_last_new_entity = 0;
        this.research.medium_days_since_last_new_entity = 0;
        this.research.slow_days_since_last_new_entity = 0;
        this.research.new_entity_available = true;
        for (let entity of Research.entity_order) {
            this.research.researched_entities[entity] = [];
            this.research.unresearched_entities[entity] = {order: [], progress: {}};

            for (let color of Research.subclasses) {
                this.research.researched_entities[entity].push(color);
            }
        }
        
        if (this.sandbox_mode) {
            this.sandbox_action_budget--;
            if (this.sandbox_action_budget < 0) {
                this.sandbox_steps--;
                if (this.sandbox_steps < 0) {
                    this.sandbox_mode = false;
                }
            }
        }
        // Update the last entry in logger with the new state
        const updatedState = this.calculateFullState({includeGuests: false});
        const lastEntry = this.logger.trajectoryData[this.logger.trajectoryData.length - 1];
        if (lastEntry) {
            lastEntry.end_state = updatedState;
        }
        return !this.sandbox_mode ? new CommandResult(false, "You have run out of free sandbox actions. Using a learning day step.") : new CommandResult(true, "Max research called successfully");
    }

    addPathTile(x, y) {
        this.action = `add_path_tile(x=${x}, y=${y})`;
        this.expenses = 0;
        this.revenue = 0;
        this.action_valid = false;
        this.info = ""
        if (this.difficulty != "hard") {
            const message = "Path tiles can only be modified in hard mode";
            this.info = message;
            return new CommandResult(false, message);
        }
        if (this.money < config.path_addition_cost) {
            const message = "Insufficient funds to add path tile. Required: " + config.path_addition_cost + ", Available: " + this.money;
            this.info = message;
            return new CommandResult(false, message);
        }
        const result = this.grid.placeElement(x, y, new PathTile(x, y));
        if (result.success) {
            // TODO See if there's a trick to avoid recomputing the whole routing table 
            this.grid.computeRoutingTable(this.difficulty);
            this.money -= config.path_addition_cost;
            this.expenses += config.path_addition_cost;
            this.action_valid = true;
            return new CommandResult(true, "Path tile placed successfully");
        } else {
            const message = "Failed to add path tile. " + result.message;
            this.info = message;
            return new CommandResult(false, message);
        }
    }

    removePathTile(x, y) {
        this.action = `remove_path_tile(x=${x}, y=${y})`;
        this.expenses = 0;
        this.revenue = 0;
        this.action_valid = false;
        this.info = ""
        if (this.difficulty != "hard") {
            const message = "Path tiles can only be modified in hard mode";
            this.info = message;
            return new CommandResult(false, message);
        }
        if (this.money < config.path_removal_cost) {
            const message = "Insufficient funds to remove path tile. Required: " + config.path_removal_cost + ", Available: " + this.money;
            this.info = message;
            return new CommandResult(false, message);
        }
        if (this.grid.getTile(x, y).type !== "path") {
            const message = "Selected tile does not contain a path";
            this.info = message;
            return new CommandResult(false, message);
        }
        if (this.grid.cannotRemovePath(x, y)){
            const message = "Removing this path would prevent guests from reaching the exit";
            this.info = message;
            return new CommandResult(false, message);
        }

        const result = this.grid.clearTile(x, y);
        if (result.success) {
            // TODO See if there's a trick to avoid recomputing the whole routing table 
            this.grid.computeRoutingTable(this.difficulty);
            this.money -= config.path_removal_cost;
            this.expenses += config.path_removal_cost;
            this.action_valid = true;
            return new CommandResult(true, "Path tile removed successfully");
        } else {
            const message = "Failed to remove path tile. " + result.message;
            this.info = message;
            return new CommandResult(false, message);
        }
    }

    addWaterTile(x, y) {
        this.action = `add_water_tile(x=${x}, y=${y})`;
        this.expenses = 0;
        this.revenue = 0;
        this.action_valid = false;
        this.info = ""
        if (this.difficulty != "hard") {
            const message = "Water tiles can only be modified in hard mode";
            this.info = message;
            return new CommandResult(false, message);
        }
        if (this.money < config.water_addition_cost) {
            const message = "Insufficient funds to add water tile. Required: " + config.water_addition_cost + ", Available: " + this.money;
            this.info = message;
            return new CommandResult(false, message);
        }
        const new_water_tile = new WaterTile(x, y);
        const result = this.grid.placeElement(x, y, new_water_tile);
        if (result.success) {
            // Check surrounding rides. If they are now adjacent to water, increase their excitement
            for (let ride of this.grid.getAdjacentRides(new_water_tile)) {
                ride.excitement++;
                ride.num_adjacent_water_tiles++;
            }
            this.money -= config.water_addition_cost;
            this.expenses += config.water_addition_cost;
            this.action_valid = true;
            return new CommandResult(true, "Water tile placed successfully");
        } else {
            const message = "Failed to add water tile. " + result.message;
            this.info = message;
            return new CommandResult(false, message);
        }
    }

    removeWaterTile(x, y) {
        this.action = `remove_water_tile(x=${x}, y=${y})`;
        this.expenses = 0;
        this.revenue = 0;
        this.action_valid = false;
        this.info = ""
        if (this.difficulty != "hard") {
            const message = "Water tiles can only be modified in hard mode";
            this.info = message;
            return new CommandResult(false, message);
        }
        if (this.money < config.water_removal_cost) {
            const message = "Insufficient funds to remove water tile. Required: " + config.water_removal_cost + ", Available: " + this.money;
            this.info = message;
            return new CommandResult(false, message);
        }
        const tile = this.grid.getTile(x, y);
        if (tile.type !== "water") {
            const message = "Selected tile does not contain water";
            this.info = message;
            return new CommandResult(false, message);
        }
        const result = this.grid.clearTile(x, y);
        if (result.success) {
            // Check surrounding rides. If they are now not adjacent to water, reset their excitement to the default value
            for (let ride of this.grid.getAdjacentRides(tile)) {
                ride.excitement--;
                ride.num_adjacent_water_tiles--;
            }
            this.money -= config.water_removal_cost;
            this.expenses += config.water_removal_cost;
            this.action_valid = true;
            return new CommandResult(true, "Water tile removed successfully");
        } else {
            const message = "Failed to remove water tile. " + result.message;
            this.info = message;
            return new CommandResult(false, message);
        }
    }
    

    noop() {
        this.action = `wait()`;
        this.expenses = 0;
        this.revenue = 0;
        this.action_valid = true;
        this.info = ""
        return new CommandResult(true, "Noop called successfully")
    }

    undoDay() {
        if (!this.sandbox_mode) {
            return new CommandResult(false, "Undo day can only be called in sandbox mode");
        }
        const history = this.logger.getHistory();
        if (history.length <= 1) {
            return new CommandResult(false, "Already at earliest day");
        }
        this.logger.popLastEntry();
        const previousState = this.logger.getLastState();
        this.setState(previousState);
        
        this.sandbox_action_budget--;
        if (this.sandbox_action_budget < 0) {
            this.sandbox_steps--;
            if (this.sandbox_steps < 0) {
                this.sandbox_mode = false;
            }
        }
        // Update the last entry in logger with the new state
        const updatedState = this.calculateFullState({includeGuests: false});
        const lastEntry = this.logger.trajectoryData[this.logger.trajectoryData.length - 1];
        if (lastEntry) {
            lastEntry.end_state = updatedState;
        }
        return !this.sandbox_mode ? new CommandResult(false, "You have run out of free sandbox actions. Using a learning day step.") : new CommandResult(true, "Undo day called successfully");
    }

    maxMoney() {
        if (!this.sandbox_mode) {
            return new CommandResult(false, "Max money can only be called in sandbox mode");
        }
        this.money = 99999999;
        this.sandbox_action_budget--;
        if (this.sandbox_action_budget < 0) {
            this.sandbox_steps--;
            if (this.sandbox_steps < 0) {
                this.sandbox_mode = false;
            }
        }
        // Update the last entry in logger with the new state
        const updatedState = this.calculateFullState({includeGuests: false});
        const lastEntry = this.logger.trajectoryData[this.logger.trajectoryData.length - 1];
        if (lastEntry) {
            lastEntry.end_state = updatedState;
        }
        return !this.sandbox_mode ? new CommandResult(false, "You have run out of free sandbox actions. Using a learning day step.") : new CommandResult(true, "Max money called successfully");
    }

    // DAILY OPERATIONS
    stockShops() {
        let shop_stock_cost = 0;
        const max_budget_per_shop = this.money / this.shops.length

        for (let shop of this.shops) {
            shop_stock_cost += shop.stockShop(this, max_budget_per_shop);
        }
    }

    addGuest() {
        const guest = new Guest(this);
        this.curr_guest_count++;
        this.guests.push(guest);
    }

    updateGuests() {
        
        for (let guest of this.guests) {
            if(!guest.exited){
                guest.act();
                guest.updateNeeds();
                guest.litter();
            }
        }
    }

    operateRides() {
        for (let ride of this.rides) {
            ride.operate(this);
        }
    }

    runStaffTasks(day_tick) {
        for (let person of this.staff) {
            if (person.subtype === "janitor") {
                person.clean(this);
            } else if (person.subtype === "mechanic") {
                person.repair(this);
            } else if (person.subtype === "specialist") {
                if (person.subclass === "yellow") {
                    person.entertain(this);
                } else if (person.subclass === "blue") {
                    person.stock(this, day_tick);
                } else if (person.subclass === "green") {
                    person.inform(this);
                } else if (person.subclass === "red") {
                    person.sell(this);
                }
            }
        }
    }
    
    payStaff() {
        this.salaries_paid = 0
        
        for (let employee of this.staff){
            let salary = config.staff[employee.subtype][employee.subclass].salary;
            if (this.money < salary){
                this.fireStaff(employee.subtype, employee.subclass, employee.x, employee.y)
            } else{
                this.money -= salary;
                this.salaries_paid += salary;
                this.expenses += salary;
            }
        }
    }

    surveyGuests() {
        const day_ended_guest_must_leave_id = guest_enums.exit_reason_description_to_id["Day ended"];
        const guests = this.guests.filter(guest => guest.reason_for_exit_id != day_ended_guest_must_leave_id);
        let sampledGuests = [];
        if (guests.length <= this.num_guests_to_survey) {
            sampledGuests = guests;
        } else {
            // Floyd's algorithm for sampling without replacement
            for (let i = guests.length - this.num_guests_to_survey; i < guests.length; i++) {
                const j = Math.floor(this.rng.random() * (i + 1));
                if (j < guests.length - this.num_guests_to_survey) {
                    sampledGuests.push(guests[j]);
                } else {
                    sampledGuests.push(guests[i]);
                }
            }
        }
        let guest_survey_results = []
        for (const guest of sampledGuests) {
            guest_survey_results.push(guest.surveyGuest())
        }
        this.guest_survey_results = {"list_of_results": guest_survey_results, "age_of_results": 0};
        this.num_guests_to_survey = 0;
    }

    update(day_tick) {
        this.updateGuests();
        this.operateRides();
        this.runStaffTasks(day_tick);
    }

    functionally_over() {
        // Return true iff the game is in an unrecoverable state
        let all_rides_broken = this.rides.every(function(element, index){
            return element.out_of_service;
        })

        if (!all_rides_broken){
            return false;
        }

        // Cheapest ride or shop to build
        let min_cost_to_recover = this.cheapest_building_cost
        // Cheapest ride to repair
        for (const ride of this.rides){
            min_cost_to_recover = Math.min(min_cost_to_recover, config.rides[ride.subtype][ride.subclass].building_cost, config.ride_repair_cost_percentage + config.staff.mechanic.yellow.salary)
        }

        // Absolutely no sources of income
        if (all_rides_broken && this.shops.length == 0 && this.money < min_cost_to_recover){
            return true;
        }
        return false; 

        /*
        // How much could be made by selling all shops
        let shop_sale_price = this.shops.reduce( function(a, b){
            return a + config.sell_percentage*config.shops[b.subtype][b.subclass].building_cost;
        }, 0);

        // How much could be made by selling all rides
        let ride_sale_price = this.rides.reduce( function(a, b){
            return a + config.sell_percentage*config.rides[b.subtype][b.subclass].building_cost;
        }, 0);

        // Problem: No way to easily determine how much money can be made by shops, even if all rides are broken.
        */
        
    }

    proceed({visUpdateFn, parkId, io}) {
        // console.time("day_timer");
        // Reset all daily data
        this.guests = []
        this.curr_guest_count = 0;
        const midday_states = []

        // Pre-day operations
        this.park_rating = this.calculateParkRating();
        this.stockShops();
        for (let ride of this.rides) {
            ride.startOfDay();
        }
        for (let staff of this.staff) {
            staff.success_metric_value = 0;
            staff.operating_cost = 0;
        }
        this.research.perform_research(this);

        if (visUpdateFn!=undefined) { visUpdateFn({io, park: this, parkId: parkId, state_type: "day_start", tick: 0}) }

        // Run day 
        this.total_capacity = this.rides.reduce((a, b) => a + b.capacity, 0);
        let max_guests = Math.floor(this.total_capacity * 2.2);
        const guests_per_tick = Math.floor(this.total_capacity / 100) + 1;
        let ticks_between_guests = 5;
        if (this.total_capacity >= 10) {
            ticks_between_guests--;
        }
        if (this.total_capacity >= 24) {
            ticks_between_guests--;
        }
        if (this.total_capacity >= 42) {
            ticks_between_guests--;
        }
        if (this.total_capacity >= 66) {
            ticks_between_guests--;
        }

        this.asset_value = this.getAssetValue();

        // try {
        for(let i = 0; i < config.ticks_per_day; i++){
            // TODO: update 
            if (this.curr_guest_count < max_guests &&
                i % ticks_between_guests == 0 &&
                this.rng.random() < (this.park_rating / 100)) {
                for(let j = 0; j < guests_per_tick; j++){
                    this.addGuest();
                }
            }
            this.update(i);

            let midday_state = null;
            if (this.return_midday_states || (visUpdateFn!=undefined && i % config.vis_update_rate == 0)) {
                midday_state = this.calculateMiddayState();
            }
            if (this.return_midday_states) {
                midday_states.push(midday_state);
            }
            if (visUpdateFn!=undefined && i % config.vis_update_rate == 0) { visUpdateFn({io, park: this, parkId: parkId, state_type: "mid_day", midday_state: midday_state, tick: i}) }
        }

        let allGuestsExited = false
        while(!allGuestsExited){
            allGuestsExited = true
            for(let guest of this.guests){
                allGuestsExited = allGuestsExited & guest.exit()
            }
            if (visUpdateFn!=undefined) { visUpdateFn({io, park: this, parkId: parkId, state_type: "exit_time", tick: config.ticks_per_day}) }
        }

        // Post-day operations
        this.payStaff()
        this.step = this.step + 1
        const done = this.step >= this.horizon;
        if (this.sandbox_mode) {
            this.sandbox_steps--;
            if (this.sandbox_steps < 0) {
                this.sandbox_mode = false;
            }
        }

        for (let guest of this.guests) {
            guest.endOfDay();
        }
        if (this.num_guests_to_survey > 0) {
            this.surveyGuests();
        } else {
            this.guest_survey_results.age_of_results++;
        }

        if (this.guests.length > 0) {
            this.prev_guest_happiness = this.guests.map(guest => guest.happiness).reduce((a, b) => a + b, 0) / this.guests.length;
        } 

        const janitors = this.staff.filter(staff => staff.subtype === "janitor").sort((a, b) => a.x - b.x || a.y - b.y || b.amount_cleaned - a.amount_cleaned);
        const mechanics = this.staff.filter(staff => staff.subtype === "mechanic").sort((a, b) => a.x - b.x || a.y - b.y || b.repair_steps_performed - a.repair_steps_performed);
        const specialists = this.staff.filter(staff => staff.subtype === "specialist").sort((a, b) => a.x - b.x || a.y - b.y || b.success_metric - a.success_metric);

        this.staff = [...janitors, ...mechanics, ...specialists];

        if (this.return_midday_states) {
            this.midday_history.push(midday_states);
            this.logger.log_midday_states(midday_states);
        }
        const new_value = this.asset_value + this.money;
        const reward = new_value - this.value;
        this.value = new_value;
        const full_state = this.calculateFullState();

        // Log the step - action will be set externally when called from routes
        // For now, log with a placeholder action (will be updated when integrated with action tracking)
        this.logger.log(this.step, this.action_valid, this.action, full_state, reward, this.info);

        if (visUpdateFn!=undefined) { visUpdateFn({io, park: this, parkId: parkId, state_type: "day_end", full_state: full_state, tick: 0}) }

        // console.timeEnd("day_timer");
        return {'reward': reward, 'terminated': done, 'truncated': this.functionally_over()};
    }

    getAssetValue(){
        let asset_value = 0;
        for (let ride of this.rides){
            asset_value += config.rides[ride.subtype][ride.subclass].building_cost * config.sell_percentage;
        }
        for (let shop of this.shops){
            asset_value += config.shops[shop.subtype][shop.subclass].building_cost * config.sell_percentage;
        }
        asset_value += this.research.get_research_value();
        return asset_value;
    }

    calculateParkRating(){
        /*
        Park rating (out of 100) =
            + 20 default rating
            + up to 50 from guest happiness (max 50)
            + up to 50 from ride excitement (max 50)
            - up to 20 from ride intensity (max 20)
            - up to 20 from ride uptime (max 20)
            - up to 20 from cleanliness (max 20)
        */
        // TODO make weights configurable

        // Default rating
        let default_rating = 25;

        // Guest happiness
        let guest_happiness_boost = this.prev_guest_happiness * 30;


        // Ride excitement
        this.park_excitement = 0;
        let unique_ride_counts = {
            carousel: { yellow: 0, blue: 0, green: 0, red: 0 },
            ferris_wheel: { yellow: 0, blue: 0, green: 0, red: 0 },
            roller_coaster: { yellow: 0, blue: 0, green: 0, red: 0 }
        };

        let avg_ride_intensity = 0;
        let uptime_penalty = 0;
        let water_excitement_boost = 0;

        for (let ride of this.rides) {
            let excitement = ride.excitement;
            excitement -= ride.num_adjacent_water_tiles;
            water_excitement_boost += ride.num_adjacent_water_tiles;
            this.park_excitement += excitement / (2 ** unique_ride_counts[ride.subtype][ride.subclass]);
            unique_ride_counts[ride.subtype][ride.subclass]++;

            avg_ride_intensity += ride.intensity;

            const ride_uptime = ride.uptime / config.ticks_per_day
            if (ride_uptime < 0.25) {
                uptime_penalty += 4;
            } else if (ride_uptime < 0.5) {
                uptime_penalty += 2;
            } else if (ride_uptime < 0.75) {
                uptime_penalty += 1;
            } else if (ride_uptime < 0.9) {
                uptime_penalty += 0.1;
            }
        }

        for (let shop of this.shops) {
            const shop_uptime = shop.services_attempted > 0 ? Math.round((shop.guests_served / shop.services_attempted) * 100, 2) / 100 : 1.0
            if (shop_uptime < 0.25) {
                uptime_penalty += 4;
            } else if (shop_uptime < 0.5) {
                uptime_penalty += 2;
            } else if (shop_uptime < 0.75) {
                uptime_penalty += 1;
            } else if (shop_uptime < 0.9) {
                uptime_penalty += 0.1;
            }
        }
        this.park_excitement += Math.min(8, water_excitement_boost * 0.2);
        this.park_excitement = Math.min(60, this.park_excitement * 0.8);

        if (this.rides.length == 0) {
            avg_ride_intensity = 1;
        } else {
            avg_ride_intensity = avg_ride_intensity / this.rides.length
        }

        const ride_intensity_penalty = Math.abs(5 - avg_ride_intensity) * 5;
        const ride_uptime_penalty = Math.min(25, uptime_penalty);

        // Cleanliness penalty
        let all_tiles = this.grid.getAllTiles()
        let cleanliness_penalty = 0
        for (let tile of all_tiles) {
            if (tile.cleanliness < 0.2) {
                cleanliness_penalty += 8
            } else if (tile.cleanliness < 0.4) {
                cleanliness_penalty += 4
            } else if (tile.cleanliness < 0.6) {
                cleanliness_penalty += 2
            } else if (tile.cleanliness < 0.8) {
                cleanliness_penalty += 1
            }
        }
        cleanliness_penalty = Math.min(25, cleanliness_penalty)

        // console.log("+DEFAULT RATING", default_rating)
        // console.log("+GUEST HAPPINESS BOOST", guest_happiness_boost)
        // console.log("+PARK EXCITEMENT", this.park_excitement)
        // console.log("-CLEANLINESS PENALTY", cleanliness_penalty)
        // console.log("-RIDE UPTIME PENALTY", ride_uptime_penalty)
        // console.log("-RIDE INTENSITY PENALTY", ride_intensity_penalty)

        let park_rating = default_rating
                        + guest_happiness_boost 
                        + this.park_excitement
                        - cleanliness_penalty 
                        - ride_uptime_penalty 
                        - ride_intensity_penalty;

        park_rating = Math.min(100, park_rating)
        park_rating = Math.max(5, park_rating)
        
        return park_rating;
    }

    // STATE GETTERS
    getState() {
        let research = this.research.format();
        return {
            seed: this.seed,
            step: this.step,
            sandbox_mode: this.sandbox_mode,
            sandbox_steps: this.sandbox_steps,
            horizon: this.horizon,
            money: this.money,
            value: this.value,
            revenue: this.revenue,
            expenses: this.expenses,
            park_excitement: this.park_excitement,
            park_rating: this.park_rating, 
            prev_guest_happiness: this.prev_guest_happiness,
            total_salary_paid: this.salaries_paid,
            research_speed: research.research_speed,
            research_topics: JSON.parse(JSON.stringify(research.research_topics)),
            research_operating_cost: research.operating_cost,
            available_entities: JSON.parse(JSON.stringify(research.available_entities)),
            // TODO: Maybe refactor.
            research_current_entity: research.current_entity,
            research_current_color: research.current_color,
            research_topic_index: research.topic_index,
            research_unresearched_entities: JSON.parse(JSON.stringify(research.unresearched_entities)),
            new_entity_available: research.new_entity_available,
            fast_days_since_last_new_entity: research.fast_days_since_last_new_entity,
            medium_days_since_last_new_entity: research.medium_days_since_last_new_entity,
            slow_days_since_last_new_entity: research.slow_days_since_last_new_entity,
        };
    }

    computeGuestStats() {
        const guestStats = {
            total_guests: 0,
            avg_money_spent: 0.0,
            avg_steps_taken: 0.0,
            avg_rides_visited: 0.0,
            avg_food_shops_visited: 0.0,
            avg_drink_shops_visited: 0.0,
            avg_specialty_shops_visited: 0.0
        };

        if (this.guests.length === 0) {
            return guestStats;
        }

        const day_ended_guest_must_leave_id = guest_enums.exit_reason_description_to_id["Day ended"];
        let full_day_guests = 0;

        for (const guest of this.guests) {
            guestStats.total_guests += 1;
            if (guest.reason_for_exit_id == day_ended_guest_must_leave_id) {
                continue;
            }
            full_day_guests++;
            guestStats.avg_money_spent += guest.money_spent;
            guestStats.avg_steps_taken += guest.steps_at_exit || 0;
            guestStats.avg_rides_visited += guest.rides_visited || 0;
            guestStats.avg_food_shops_visited += guest.food_shops_visited || 0;
            guestStats.avg_drink_shops_visited += guest.drink_shops_visited || 0;
            guestStats.avg_specialty_shops_visited += guest.specialty_shops_visited || 0;
        }

        // Calculate averages
        if (full_day_guests > 0) {
            guestStats.avg_money_spent = Math.round((guestStats.avg_money_spent / full_day_guests) * 100) / 100;
            guestStats.avg_steps_taken = Math.round((guestStats.avg_steps_taken / full_day_guests) * 100) / 100;
            guestStats.avg_rides_visited = Math.round((guestStats.avg_rides_visited / full_day_guests) * 100) / 100;
            guestStats.avg_food_shops_visited = Math.round((guestStats.avg_food_shops_visited / full_day_guests) * 100) / 100;
            guestStats.avg_drink_shops_visited = Math.round((guestStats.avg_drink_shops_visited / full_day_guests) * 100) / 100;
            guestStats.avg_specialty_shops_visited = Math.round((guestStats.avg_specialty_shops_visited / full_day_guests) * 100) / 100;
        }

        return guestStats;
    }

    getFullState({ includeMiddayStates = false, force_recalculate = false }) {
        if (force_recalculate) {
            const recalculatedState = this.calculateFullState();
            // Update the last entry in logger with the recalculated state
            const lastEntry = this.logger.trajectoryData[this.logger.trajectoryData.length - 1];
            if (lastEntry) {
                lastEntry.end_state = recalculatedState;
            }
        }
        const full_state = this.logger.getLastState() || this.calculateFullState();
        if (includeMiddayStates) {
            if (force_recalculate) {
                this.midday_history[this.midday_history.length - 1]
            }
            full_state.midday_states = this.midday_history[this.midday_history.length - 1]
        }
        return full_state;
    }


    calculateFullState() {
        const full_state = {
            difficulty: this.difficulty,
            layout: this.layout,
            state: this.getState(),
            guest_preferences: this.guest_preferences,
            staff: this.staff.map(staff => staff.format()),
            rides: this.rides.map(ride => ride.format()),
            shops: this.shops.map(shop => shop.format()),
            terrain: this.grid.getAllTerrainTiles().map(path => path.format()),
            entrance: this.entrance.format(),
            exit: this.exit.format(),
            guestStats: this.computeGuestStats(),
            guest_survey_results: JSON.parse(JSON.stringify(this.guest_survey_results)),
        }  
        return full_state;
    }

    calculateMiddayState() {
        const tile_dirtiness = this.grid.getAllTiles().filter(tile => tile.cleanliness < 1.0).map(tile => ({x: tile.x, y: tile.y, cleanliness: tile.cleanliness}))
        const midday_state = {
            step: this.step,
            value: this.asset_value + this.money,
            money: this.money,
            profit: this.revenue - this.expenses,
            park_rating: this.park_rating,
            capacity: this.total_capacity,
            total_guests: this.guests.length,
            revenue: this.revenue,
            expenses: this.expenses,
            guests: this.guests.filter(guest => !guest.exited).map(guest => guest.format()),
            staff: this.staff.map(staff => staff.midday_format()),
            rides: this.rides.map(ride => ride.midday_format()),
            shops: this.shops.map(shop => shop.midday_format()),
            tile_dirtiness: tile_dirtiness
        }
        return midday_state;
    }
}

export default Park;