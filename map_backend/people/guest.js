import config from "../config.js"
import { Person } from "./person.js"
import fs from 'fs';
import YAML from 'yaml';

// Load guest preferences enum
const guest_enums = YAML.parse(fs.readFileSync('./shared/guest_enums.yaml', 'utf8'));

// Create preference functions mapped by integer ID
const GUEST_PREFERENCES = {
    0: (attraction) => true, // standard - always valid
    1: (() => { // thrill_seeker
        return (attraction, rng) => {
            return ((attraction.type === 'ride' && attraction.intensity > rng.randomInt(3, 7)) || (attraction.type === 'shop'))
        };
    })(),
    2: (() => { // scaredy_cat
        return (attraction, rng) => {
            return ((attraction.type === 'ride' && attraction.intensity < rng.randomInt(3, 7)) || (attraction.type === 'shop'))
        };
    })(),
    3: (() => { // penny_pincher
        return (attraction, rng) => {
            return attraction.price < rng.randomInt(8, 12)
        };
    })(),
    4: (() => { // big_spender
        return (attraction, rng) => {
            return attraction.price > rng.randomInt(8, 12)
        };
    })(),
    5: (attraction) => { // roller_coaster_addict
        return ((attraction.type === 'ride' && attraction.subtype === 'roller_coaster') || (attraction.type === 'shop'))
    },
    6: (attraction) => { // ferris_wheel_junkie
        return ((attraction.type === 'ride' && attraction.subtype === 'ferris_wheel') || (attraction.type === 'shop'))
    },
    7: (attraction) => { // carousel_enthusiast
        return ((attraction.type === 'ride' && attraction.subtype === 'carousel') || (attraction.type === 'shop'))
    },
    8: (attraction) => { // red_colored_rides
        return ((attraction.subclass === 'red'))
    },
    9: (attraction) => { // blue_colored_rides
        return ((attraction.subclass === 'blue'))
    },
    10: (attraction) => { // green_colored_rides
        return ((attraction.subclass === 'green'))
    },
    11: (attraction) => { // yellow_colored_rides
        return ((attraction.subclass === 'yellow'))
    },
    12: (attraction) => { // water_lover
        return ((attraction.type === 'ride' && attraction.num_adjacent_water_tiles > 0) || (attraction.type === 'shop'))
    },
    13: (attraction) => { // dry_lander
        return ((attraction.type === 'ride' && attraction.num_adjacent_water_tiles === 0) || (attraction.type === 'shop'))
    },
};

// Helper functions for enums
const getPreferenceIdByName = (name) => guest_enums.preference_description_to_id[name];
function getExitReasonIdByDescription(description) {
    const id = guest_enums.exit_reason_description_to_id[description];
    if (id === undefined) {
        console.log(`Exit reason description ${description} not found in guest enums`);
        return 0;
    }
    return id;
}

const getExitReasonDescriptionById = (id) => guest_enums.exit_reasons[id].description;

class Guest extends Person {
    constructor(park) {
        // Call super constructor with required parameters
        super(park.entrance.x, park.entrance.y, "guest", park.grid);

        this.id = `${park.guests.length}`;
        
        this.park = park;
        this.starting_money = park.rng.randomNormal(config.guest_initial_money[0], config.guest_initial_money[1]);
        this.money = this.starting_money;
        this.money_spent = 0;
        this.happiness = Math.min(1.0, Math.max(0.0, park.rng.randomNormal(0.9, 0.05)));
        this.hunger = Math.max(0.0, Math.min(1.0, park.rng.randomNormal(0.1, 0.05))) // hunger low is good, high is bad
        this.thirst = Math.max(0.0, Math.min(1.0, park.rng.randomNormal(0.1, 0.05))); // thirst low is good, high is bad
        this.energy = Math.floor(park.rng.randomNormal(config.guest_initial_energy[0], config.guest_initial_energy[1])); 
        this.avg_happiness = [];
        this.avg_hunger = [];
        this.avg_thirst = [];
        this.steps_at_exit = 0;
        this.x = this.park.entrance.x;
        this.y = this.park.entrance.y;
        this.exited = false;
        this.curr_target = null;
        this.prev_target = {id: null, type: null};
        this.next_target = null;
        this.waiting = false;
        this.entrance_tile = this.park.entrance;
        this.exit_tile = this.park.exit;
        this.visits = {};
        this.visits["exit"] = 8;
        this.reason_for_exit_id = getExitReasonIdByDescription("No specific reason for exit"); // Initialize with "none" ID
        this.is_caffeinated = false;
        this.caffeinated_steps = 0;
        this.souvenir_count = 0.0
        this.has_park_info = false;
        this.has_status_info = false;
        this.ride_waiting_for = null;
        // Select a random preference ID from the filtered preferences
        const selected_preference_name = park.guest_preferences[park.rng.randomInt(0, park.guest_preferences.length - 1)];

        this.preference_id = getPreferenceIdByName(selected_preference_name);  
        this.preferences = GUEST_PREFERENCES[this.preference_id];
        
        this.rides_visited = 0;
        this.food_shops_visited = 0;
        this.drink_shops_visited = 0;
        this.specialty_shops_visited = 0;
        this.atm_withdrawals = 0;
        this.num_times_caffeinated = 0;
    }

    ///Force exit the park at the end of the day
    exit(){
        if(this.exited){
            return this.exited
        }
        this.waiting = false;
        this.interact();
        if(this.exited){
            return this.exited
        }
        this.reason_for_exit_id = getExitReasonIdByDescription("Day ended");
        this.moveToward(this.exit_tile.x, this.exit_tile.y);
        // this.updateNeeds();
        return this.exited
    }

    recordVisit(tile){
        if (tile.type == "ride") {
            this.rides_visited += 1;
        }
        else if (tile.type == "shop") {
            if (tile.subtype == "food") {
                this.food_shops_visited += 1;
            }
            else if (tile.subtype == "drink") {
                this.drink_shops_visited += 1;
            }
            else if (tile.subtype == "specialty") {
                this.specialty_shops_visited += 1;
            }
        }
    }

    act() {
        this.steps_at_exit += 1;
        this.target_type = "attractions"
        if (this.waiting) {
            if (this.thirst > config.hard_target_threshold || this.hunger > config.hard_target_threshold) {
                // Guest got too hungry/thirsty in line
                this.happiness = Math.max(0, this.happiness - config.happiness_attraction_rejection_penalty);
                this.waiting = false;
                // Remove this guest from the ride's boarded guests
                this.ride_waiting_for.boarded_guests = this.ride_waiting_for.boarded_guests.filter(guest => guest !== this);
                // Remove this guest from the ride's queue
                this.ride_waiting_for.queue = this.ride_waiting_for.queue.filter(guest => guest !== this);
                this.ride_waiting_for = null;
            } else {
                this.ride_waiting_for.total_wait_time += 1;
                this.energy = Math.max(0, this.energy - 0.25);
                return;
            }
        }

        if (this.curr_target == this.exit_tile) {
            // keep moving toward exit
            if (this.x === this.curr_target.x && this.y === this.curr_target.y) {this.interact();}
            else {this.moveToward(this.curr_target.x, this.curr_target.y);}
            return;
        } else if (this.happiness === 0) {
            // If guest is too unhappy, move to exit
            this.curr_target = this.exit_tile;
            this.reason_for_exit_id = getExitReasonIdByDescription("Too unhappy");
        } else if (this.energy <= 0) {
            // If guest is too tired, move to exit
            this.curr_target = this.exit_tile;
            this.reason_for_exit_id = getExitReasonIdByDescription("Ran out of energy");
        } else if (this.money <= 1) {
            // If guest is too broke, move to exit
            this.curr_target = this.exit_tile;
            this.reason_for_exit_id = getExitReasonIdByDescription("Spent all their money");
        } else if(this.thirst >= 1) {
            this.curr_target = this.exit_tile;
            this.reason_for_exit_id = getExitReasonIdByDescription("Too thirsty"); 
        } else if(this.hunger >= 1) {
            this.curr_target = this.exit_tile;
            this.reason_for_exit_id = getExitReasonIdByDescription("Too hungry");
        } else if(this.curr_target === null || 
                 (this.hunger > config.hard_target_threshold && this.hunger > this.thirst && this.curr_target.subtype != 'food') || 
                 (this.thirst > config.hard_target_threshold && this.thirst > this.hunger && this.curr_target.subtype != 'drink')) {
            this.hard_target = false;
            if (this.hunger > config.hard_target_threshold || this.thirst > config.hard_target_threshold) {
                this.hard_target = true;
            } 
            // Otherwise if guest has no target, choose a target
            const food_shops = this.park.shops.filter((item) => (item.subtype == 'food' && item.id != this.prev_target?.id))
            const drink_shops = this.park.shops.filter((item) => (item.subtype == 'drink' && item.id != this.prev_target?.id))
            const rides = this.park.rides.filter((item) => (item.id != this.prev_target?.id))

            let targets = [];

            if(this.thirst > config.soft_target_threshold && this.thirst > this.hunger){
                if (drink_shops.length == 0) {
                    this.reason_for_exit_id = getExitReasonIdByDescription("Too few drink shops");
                    this.curr_target = this.exit_tile;
                    return;
                }
                this.target_type = "drink shops";
                targets = drink_shops;
            }
            else if(this.hunger > config.soft_target_threshold){
                if (food_shops.length == 0) {
                    this.reason_for_exit_id = getExitReasonIdByDescription("Too few food shops");
                    this.curr_target = this.exit_tile;
                    return;
                }
                this.target_type = "food shops";
                targets = food_shops;
            }
            else if(this.happiness < (1 - config.soft_target_threshold)){
                if (rides.length == 0) {
                    this.reason_for_exit_id = getExitReasonIdByDescription("Too few rides");
                    this.curr_target = this.exit_tile;
                    return;
                }
                // targets all specialty shops and rides
                this.target_type = "rides";
                targets = rides;
            }
            else if (this.next_target !== null) {
                targets = [this.next_target];
            }
            else {
                targets = rides.concat(food_shops).concat(drink_shops);
            }

            if (this.has_park_info) {
                targets = targets.filter(target => this.preferences(target) && this.money >= target.price);
            }  
            if (this.has_status_info) {
                targets = targets.filter(target => !target.out_of_service && target.cleanliness > 0.4);
            }

            targets = targets.filter(target => this.grid.routing_table[this.x]?.[this.y]?.[target.x]?.[target.y] !== undefined);


            //find food shop
            let target_weights = []
            for (let target of targets) {
                let weight = 4 / (2**(this.visits[target.subtype + "-" + target.subclass] || 0)); 
                if (target.type == "ride") {
                    weight *= (target.excitement + (target.capacity / 8));
                    if (this.has_status_info) {
                        weight *= (1 / Math.max(1, (target.queue.length + target.boarded_guests.length) / target.capacity));
                    }
                } else if (target.type == "shop") {
                    if (target.subtype == "food") {
                        weight *= 10 * this.hunger;
                    } else if (target.subtype == "drink") {
                        weight *= 10 * this.thirst;
                    }
                }
                if (this.has_status_info) {
                    weight *= target.cleanliness;
                    if (target.out_of_service) {
                        weight *= 0.001; // practically 0 chance of selecting an out of service ride
                    }
                }
                target_weights.push(weight);
            }
            targets.push(this.exit_tile);
            let exit_weight = targets.length - 0.99;
            if (this.has_park_info) {
                exit_weight *= 0.5;
            }
            if (this.has_status_info) {
                exit_weight *= 0.5;
            }
            target_weights.push(exit_weight);
            this.next_target = null;
            // Distance is weighted more heavily when guests are urgently seeking a target
            let distance_weight_scale = this.thirst + this.hunger + (1 - this.happiness);
            if (this.hard_target) {
                distance_weight_scale *= 2;
            }
            this.selectNewTarget(targets, this.park.rng, target_weights, distance_weight_scale);
            // console.log(`Guest ${this.id} (step: ${this.steps_at_exit}) picked target: ${this.curr_target.subtype} (${this.curr_target.x}, ${this.curr_target.y})`)
            if (this.curr_target == this.exit_tile && this.reason_for_exit_id == getExitReasonIdByDescription("No specific reason for exit")) {
                this.reason_for_exit_id = getExitReasonIdByDescription(`Too few unique ${this.target_type}`)
            }
        }

        // guest has reached target
        if(this.x === this.curr_target.x && this.y === this.curr_target.y){
            // console.log(`Guest ${this.id} (step: ${this.steps_at_exit}) is interacting with target: ${this.curr_target.subtype} (${this.curr_target.x}, ${this.curr_target.y})`)
            this.interact();

            if (this.exited){
                return;
            }
    
            this.prev_target = this.curr_target;
            this.curr_target = null;
            this.next_target = null;
        // If guest has not reached target, move toward it
        } else {
            this.energy = Math.max(0, this.energy - 1);
            // if we are on a path and not hard set on a target, take a chance to move to a non-target destination if immediately adjacent to it
            if (this.grid.getTile(this.x, this.y).type == "path" && !this.hard_target) {
                // filter out destination neighbors that are specialty blue shops if the guest already has park info
                const destinationNeighbors = this.grid.getDestinationNeighbors(this.x, this.y).filter(neighbor => 
                    (neighbor.x != this.prev_target?.x || neighbor.y != this.prev_target?.y) && 
                    (neighbor.x != this.curr_target?.x || neighbor.y != this.curr_target?.y) &&
                    !(neighbor.subtype == "specialty" && neighbor.subclass == "blue" && this.has_park_info)
                );
                const rand_num = this.park.rng.random();
                let visit_chance = 0.0;
                for (let neighbor of destinationNeighbors) {
                    visit_chance += neighbor.subtype == "specialty" ? 0.275 : 0.125;
                    if (rand_num <= visit_chance) {
                       this.prev_target = null;
                        this.next_target = this.curr_target;
                        this.curr_target = neighbor;
                        if (this.curr_target === undefined) {
                            console.log("PROBLEM IN ADJACENT NEIGHBOR")
                        }
                        if (this.curr_target == this.exit_tile && this.reason_for_exit_id == getExitReasonIdByDescription("No specific reason for exit")) {
                            this.reason_for_exit_id = getExitReasonIdByDescription("Walked by the exit");
                        }
                        break;
                    }
                }
            }
            this.moveToward(this.curr_target.x, this.curr_target.y);
            // caffeinated guests move twice
            if (this.caffeinated_steps > 0 && this.x !== this.curr_target.x && this.y !== this.curr_target.y) {
                this.energy = Math.max(0, this.energy - 1);
                this.moveToward(this.curr_target.x, this.curr_target.y);
                this.caffeinated_steps -= 1;
            }
        }
       
    }

    updateNeeds() {
        if (this.curr_target == this.exit_tile) {
            return;
        }

        let multiplier = 1;
        if (this.waiting) {
            multiplier = 0.75;
        }

        this.hunger = Math.min(1, this.hunger + config.hunger_build_rate * multiplier);
        if (this.hunger > config.soft_target_threshold) {
            this.happiness = Math.max(0, this.happiness - this.hunger * config.happiness_decay_rate);
        }
        this.thirst = Math.min(1, this.thirst + config.thirst_build_rate * multiplier);
        if (this.thirst > config.soft_target_threshold) {
            this.happiness = Math.max(0, this.happiness - this.thirst * config.happiness_decay_rate);
        }
        // Small base decay rate
        this.happiness = Math.max(0, this.happiness - config.happiness_decay_rate * multiplier / 5);

        // Cleanliness penalty
        const curr_tile_cleanliness = this.grid.getTile(this.x, this.y).cleanliness;

        if (curr_tile_cleanliness < 0.8) {
            this.happiness = Math.max(0, this.happiness - config.happiness_decay_rate_low_cleanliness);
        }
        // Double penalty if cleanliness is below 0.5
        if (curr_tile_cleanliness < 0.6) {
            this.happiness = Math.max(0, this.happiness - config.happiness_decay_rate_low_cleanliness);
        }
        // Triple penalty if cleanliness is below 0.2
        if (curr_tile_cleanliness < 0.4) {
            this.happiness = Math.max(0, this.happiness - config.happiness_decay_rate_low_cleanliness);
        }
        this.avg_happiness.push(this.happiness);
        this.avg_hunger.push(this.hunger);
        this.avg_thirst.push(this.thirst);
    }

    litter() {
        let littering_chance =  (1 - this.happiness) / 2
        littering_chance = Math.max(0.06, littering_chance)
        littering_chance = Math.min(littering_chance, 0.26)
        if (this.curr_target == this.exit_tile) {
            littering_chance *= 0.4;
        }
        if (this.park.rng.random() < littering_chance) {
            let tile = this.grid.getTile(this.x, this.y)
            tile.cleanliness = Math.max(0, tile.cleanliness - config.littering_penalty);
        }
    }

    interact() {
        if (this.exited) {return;}
        const tile = this.grid.getTile(this.x, this.y);
        // if (this.id == "0") {
        //     console.log("interacting with tile: ", tile.id, tile.subtype);
        // }
        // interact with park exit
        if (this.x === this.exit_tile.x && this.y === this.exit_tile.y) {
            // if (this.id == "0") {
            //     console.log("exiting park because: ", getExitReasonDescriptionById(this.reason_for_exit_id));
            // }
            this.exited = true;
            this.park.curr_guest_count--;
            return;
        }
        // if does not match guest preference, apply penalty. Specialty shops are not affected by this.
        if (!this.preferences(tile) && tile.subtype != "specialty") {
            this.happiness = Math.max(0, this.happiness - config.happiness_attraction_rejection_penalty);
            // set visit count to 1000 to avoid visiting again
            this.visits[tile.subtype + "-" + tile.subclass] = 1000;
            return;
        }
        // interact with ride
        else if (tile && tile.type === "ride") {
            // If the ride is out of order, the guest cannot pay, or the ride is too dirty, apply penalty a
            if (tile.out_of_service || this.money < tile.price || this.park.rng.random() > tile.cleanliness) {
                this.happiness = Math.max(0, this.happiness - config.happiness_attraction_rejection_penalty);
                // set visit count to 1000 to avoid visiting again
                this.visits[tile.subtype + "-" + tile.subclass] += 4;
                return;
            }

            tile.queueGuest(this);
            this.visits[tile.subtype + "-" + tile.subclass] = (this.visits[tile.subtype + "-" + tile.subclass] || 0) + 1;
        // interact with shop
        } else if (tile && tile.type === "shop") {
            // If the shop is out of order, the guest cannot pay, or the shop is too dirty, apply penalty 
            if (tile.out_of_service) {
                tile.services_attempted += 1;
                this.happiness = Math.max(0, this.happiness - config.happiness_attraction_rejection_penalty);
                // set visit count higher to avoid visiting again
                this.visits[tile.subtype + "-" + tile.subclass] = Math.max(this.visits[tile.subtype + "-" + tile.subclass] * 2, 2);
                return;
            } else if (this.money < tile.price || this.park.rng.random() > tile.cleanliness) {
                this.happiness = Math.max(0, this.happiness - config.happiness_attraction_rejection_penalty);
                // set visit count higher to avoid visiting again
                this.visits[tile.subtype + "-" + tile.subclass] = Math.max(this.visits[tile.subtype + "-" + tile.subclass] * 2, 2);
                return;
            }
            tile.serve(this, this.park);
            this.visits[tile.subtype + "-" + tile.subclass] = (this.visits[tile.subtype + "-" + tile.subclass] || 0) + 1;
        }
    }

    endOfDay(){
        // // console.log(`money spent: ${this.money_spent}, money: ${this.money}, starting money: ${this.starting_money}`)
        this.avg_happiness = this.avg_happiness.reduce((a, b) => a + b, 0) / this.avg_happiness.length;
        this.avg_hunger = this.avg_hunger.reduce((a, b) => a + b, 0) / this.avg_hunger.length;
        this.avg_thirst = this.avg_thirst.reduce((a, b) => a + b, 0) / this.avg_thirst.length;
        this.x = this.exit_tile.x;
        this.y = this.exit_tile.y;
        this.exited = true;
    }

    surveyGuest() {
        return {
            happiness_at_exit: this.happiness,
            hunger_at_exit: this.hunger,
            thirst_at_exit: this.thirst,
            remaining_energy: this.energy,
            remaining_money: this.money,
            percent_of_money_spent: this.money_spent / this.starting_money,
            reason_for_exit_id: this.reason_for_exit_id,
            preference_id: this.preference_id,
        }
    }

    format() {
        //If the day is not complete get the current levels
        let happiness = this.avg_happiness
        if (Array.isArray(happiness)) {
            happiness = this.happiness;
        }
        let hunger = this.avg_hunger
        if (Array.isArray(hunger)) {
            hunger = this.hunger;
        }
        let thirst = this.avg_thirst
        if (Array.isArray(thirst)) {
            thirst = this.thirst;
        }

        return {
            ...super.format(),
            id: this.id,
            exited: this.exited,
            money_spent: this.money_spent,
            happiness: Math.round(happiness * 100) / 100,
            hunger: Math.round(hunger * 100) / 100,
            thirst: Math.round(thirst * 100) / 100,
            steps_at_exit : this.steps_at_exit,
            rides_visited: this.rides_visited,
            food_shops_visited: this.food_shops_visited,
            drink_shops_visited: this.drink_shops_visited,
            specialty_shops_visited: this.specialty_shops_visited,
            reason_for_exit_id: this.reason_for_exit_id,
        }
    }

    midday_format() {
        return {
            ...super.format(),
            id: this.id,
            exited: this.exited,
        }
    }
}

export default Guest;