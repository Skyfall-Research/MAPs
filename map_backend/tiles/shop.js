import { Tile } from "./tile.js";
import config from "../config.js";
import { CommandResult } from "../utils.js"

class Shop extends Tile {
    /**
     * @param {number} x - Grid X coordinate
     * @param {number} y - Grid Y coordinate
     * @param {string} subtype - "food", "drink", or "specialty"
     * @param {number} subclass - "yellow", "blue", "green", or "red"
     * @param {number} price - Price for an item
     */
    constructor(x, y, subtype, subclass, price, order_quantity) {
        super(x, y, 'shop');

        this.price = price;
        this.subtype = subtype;
        this.subclass = subclass;
        this.item_cost = config.shops[subtype][subclass].item_cost;
        this.revenue_generated = 0;
        this.guests_served = 0;
        this.services_attempted = 0;
        this.operating_cost = 0;
        // Inventory management
        this.number_of_restocks = 0;
        this.order_quantity = order_quantity; // Maximum possible inventory
        this.inventory = 0; // Current inventory
    }

    /**
     * Create a new object from a json dictionary passed in
     */
    static fromShop(shop){
        const new_shop = new Shop(shop.x, shop.y, shop.subtype, shop.subclass, shop.price)
        if(shop.id !== undefined){
            new_shop.id = shop.id
        }
        new_shop.setState(shop)
        return new_shop
    }

    setState(state){
        this.x = state.x 
        this.y = state.y 
        this.cleanliness = state.cleanliness
        this.price = state.item_price
        this.revenue_generated = state.revenue_generated;
        this.guests_served = state.guests_served;
        this.out_of_service = state.out_of_service;
        this.number_of_restocks = state.number_of_restocks;
        this.order_quantity = state.order_quantity;
        this.inventory = state.inventory;
        this.uptime = state.uptime;
        this.operating_cost = state.operating_cost;
        this.services_attempted = state.services_attempted;
        this.item_cost = config.shops[this.subtype][this.subclass].item_cost;
    }

    static checkParameters(subtype, subclass, price, order_quantity, available_shops) {
        if(!config.shops.hasOwnProperty(subtype)) {
            return new CommandResult(false, "Invalid shop type: " + subtype + ". Valid types: " + Object.keys(config.shops).sort().join(", "));
        }
        if(!config.shops[subtype].hasOwnProperty(subclass)) {
            return new CommandResult(false, "Invalid shop subclass: " + subclass + ". Valid subclasses: " + Object.keys(config.shops[subtype]).sort().join(", "));
        }
        if (!available_shops.includes(subclass)) {
            return new CommandResult(false, "Shop has not been researched yet: " + subclass + ". Researched subclasses: " + available_shops.join(", "));
        }
        return Shop.checkPriceAndQuantity(subtype, subclass, price, order_quantity)
    }

    static checkPriceAndQuantity(subtype, subclass, price, order_quantity) {
        if(price && !Number.isInteger(price)) {
            return new CommandResult(false, "Item price must be an integer. Received: " + price);
        }
        if (price < 0) {
            return new CommandResult(false, "Item price cannot be negative: " + price);
        }
        if((price > config.shops[subtype][subclass].max_item_price)) {
            return new CommandResult(false, "Invalid item price: " + price + ". Max item price: " + config.shops[subtype][subclass].max_item_price);
        }
        if(order_quantity && !Number.isInteger(order_quantity)) {
            return new CommandResult(false, "Inventory order_quantity must be an integer. Received: " + order_quantity);
        }
        if (order_quantity < 0) {
            return new CommandResult(false, "Inventory order_quantity cannot be negative: " + order_quantity);
        }
        return new CommandResult(true, "Valid shop parameters");
    }

    stockShop(park, max_budget) {
        this.revenue_generated = 0;
        this.guests_served = 0;
        this.operating_cost = 0;
        this.number_of_restocks = 0;
        this.uptime = 0.0;
        this.services_attempted = 0;
        const total_cost = this.item_cost * this.order_quantity;

        // Make a full purchase if possible for all shops to do so.
        // If it is too much, then divide evenly among all shops.
        if (total_cost <= max_budget || this.item_cost === 0) {
            this.inventory = this.order_quantity // Full inventory
        } else { 
            this.inventory = Math.min(Math.floor(max_budget/this.item_cost), this.order_quantity)
        }

        // Out of service if no inventory
        this.out_of_service = this.inventory <= 0;
        this.operating_cost = this.inventory * this.item_cost;

        park.expenses += this.operating_cost;
        park.money -= this.operating_cost;
    }

    /**
     * Serves a guest: deducts money, increases park revenue,
     * and applies an effect based on the shop type.
     * @param {object} guest - The guest interacting with the shop.
     * @param {object} park - The park instance for revenue updates.
     */
    serve(guest, park) {
        if (this.out_of_service) {return};

        guest.money -= this.price;
        guest.money_spent += this.price;
        guest.recordVisit(this);
        park.money += this.price;
        park.revenue += this.price;
        this.revenue_generated += this.price;
        this.guests_served += 1;
        this.services_attempted += 1;
        this.inventory -= 1;

        if (this.inventory <= 0){
            this.out_of_service = true;
        }
        
        // Apply shop-specific effects:
        if (this.subtype === "food") {
            // Yellow and blue food only have standard hunger reduction
            const hunger_reduction = config.shops[this.subtype][this.subclass].hunger_reduction
            guest.hunger = Math.max(0.0, guest.hunger - hunger_reduction);
            // Green food additionally increases thirst
            if (this.subclass === "green") {
                guest.thirst = Math.max(0, guest.thirst - config.shops[this.subtype][this.subclass].thirst_reduction)
            }
            // Red food additionally increases happiness
            if (this.subclass === "red") {
                guest.happiness = Math.min(1, guest.happiness + config.shops[this.subtype][this.subclass].happiness_boost)
            }
        } else if (this.subtype === "drink") {
            const thirst_reduction = config.shops[this.subtype][this.subclass].thirst_reduction
            guest.thirst = Math.max(0, guest.thirst - thirst_reduction);
            // Green drink additionally increases happiness
            if (this.subclass === "green") {
                guest.happiness = Math.min(1, guest.happiness + config.shops[this.subtype][this.subclass].happiness_boost)
            }
            // Red drink additionally increases energy and walking speed (through caffeinated_steps)
            if (this.subclass === "red") {
                guest.energy = guest.energy + config.shops[this.subtype][this.subclass].energy_boost
                let caffeinated_steps = config.shops[this.subtype][this.subclass].caffeinated_steps / 2 ** guest.num_times_caffeinated;
                guest.caffeinated_steps = caffeinated_steps;
                guest.num_times_caffeinated += 1
            }
        } else if (this.subtype === "specialty") {
            // Yellow specialty is a souvenir shop with a higher happiness boost that exponentially decays with each new souvenir
            if (this.subclass === "yellow") {
                guest.happiness = Math.min(1, guest.happiness + config.shops[this.subtype][this.subclass].happiness_boost * 2 ** (-guest.souvenir_count))
                guest.souvenir_count+=1
            }
            // Blue specialty is an info booth that gives guests information about the park
            // Guests with preference will now only visit attractions that match their preference
            else if (this.subclass === "blue") {
                guest.has_park_info = true;
            }
            // Green specialty is an ATM that allows guests to withdraw money from their account
            else if (this.subclass === "green") {
                let atm_withdrawal = config.shops[this.subtype][this.subclass].money_withdrawal
                atm_withdrawal = Math.max(config.shops[this.subtype][this.subclass].min_withdrawal, Math.round(atm_withdrawal / (2 ** guest.atm_withdrawals)))
                guest.money += atm_withdrawal
                guest.atm_withdrawals += 1
            }
            // Red specialty is a billboard that increases guest thirst and hunger and resets visit count for shops
            // If guests have less than 10 money, target them toward an atm
            else if (this.subclass === "red") {
                guest.thirst = Math.min(config.soft_target_threshold, guest.thirst + config.shops[this.subtype][this.subclass].thirst_boost)
                guest.hunger = Math.min(config.soft_target_threshold, guest.hunger + config.shops[this.subtype][this.subclass].hunger_boost)
                guest.happiness = Math.min(1.0, guest.happiness + config.shops[this.subtype][this.subclass].happiness_boost)
                for (let subclass_subtype in guest.visits) {
                    if (["food", "drink", "specialty"].includes(subclass_subtype.split('-')[0])) {
                        guest.visits[subclass_subtype] = 0;
                    }
                }
                if (guest.money < config.shops[this.subtype][this.subclass].money_threshold) {
                    // find the closest atm
                    const atm = park.shops.filter(shop => shop.subtype === "specialty" && shop.subclass === "green");
                    if (atm.length > 0) {
                        guest.selectNewTarget(atm, park.rng);
                        guest.next_target = null;
                    }
                }
            }
        }
    }

    format() {
        return {
            ...super.format(),
            subtype: this.subtype,
            subclass: this.subclass,
            operating_cost: this.operating_cost,
            revenue_generated: this.revenue_generated,
            out_of_service: this.out_of_service,
            guests_served: this.guests_served,
            number_of_restocks: this.number_of_restocks,
            order_quantity: this.order_quantity,
            inventory: this.inventory,
            item_price: this.price,
            item_cost: this.item_cost,
            uptime: this.services_attempted > 0 ? Math.round((this.guests_served / this.services_attempted) * 100, 2) / 100 : 1.0,
            services_attempted: this.services_attempted,
        }
    }

    midday_format() {
        return {
            ...super.format(),
            operating_cost: this.operating_cost,
            revenue_generated: this.revenue_generated,
            out_of_service: this.out_of_service,
            guests_served: this.guests_served,
            number_of_restocks: this.number_of_restocks,
            inventory: this.inventory,
            uptime: this.services_attempted > 0 ? Math.round((this.guests_served / this.services_attempted) * 100, 2) / 100 : 1.0,
        }
    }
}

export default Shop;