class Person {
    constructor(x, y, type, grid) {
        this.x = x;
        this.y = y;
        this.type = type;
        this.prev_target = null;
        this.curr_target = null;
        this.grid = grid;
    }

    format() {
        return {
            x: this.x,
            y: this.y,
            type: this.type,
        }
    }

    moveToward(target_x, target_y) {

        // Stay in place if not going anywhere (e.g., mechanic
        // cannot affort to repair ride)
        if (target_x === this.x && target_y === this.y){
            return;
        }

        // If someone has ended up at a location that isn't in the routing
        // table (e.g., off path, off store, etc...)
        // then they are stuck in that spot.
        if(this.grid.routing_table[this.x] !== undefined && this.grid.routing_table[this.x][this.y] !== undefined){
            const move = this.grid.routing_table[this.x][this.y][target_x][target_y];
            if (move === undefined) {
                throw new Error("Undefined move in routing table\nFrom: " + this.x +","+this.y + "\nTo: " + target_x +","+target_y + "\nBy: id " + JSON.stringify(this.id))
            }
            if (this.x + move.dx === 12 && this.y + move.dy === 10) {
                //console.log("MOVE FROM: ", this.x, this.y)
                //console.log("MOVE TO: ", target_x, target_y)
            } else if (this.x + move.dx === 10 && this.y + move.dy === 12) {
                //console.log("MOVE FROM: ", this.x, this.y)
                //console.log("MOVE TO: ", target_x, target_y)
            }
            this.x += move.dx;
            this.y += move.dy;
        } else {
            throw new Error("Start location not in routing table\nFrom: " + this.x +","+this.y + "\nTo: " + target_x +","+target_y + "\nBy: id " + JSON.stringify(this.id))
        }
    }


    selectNewTarget(target_options, rng, target_weights = null, distance_weight_scale = 1) {
        // sets new target and returns true if successful
        // returns false if no target can be selected
        // targets will automaticaly be weighted by distance
        // Optionally, if provided, target_weights will be multiplied by the distance weight to get the final weight
        // The higher the final target weight, the more likely the target is to be selected
        let target_probs = [];
        // default to uniform weights
        if (target_weights === null) {
            target_weights = Array(target_options.length).fill(1);
        }

        if (this.caffeinated_steps > 0) {
            distance_weight_scale = distance_weight_scale * 0.5;
        }
        distance_weight_scale = Math.max(0.5, Math.min(2, distance_weight_scale));

        // calculate final weights from target_weights and distance
        for (let i = 0; i < target_options.length; i++) {
            let target = target_options[i];
            let distance = 1;
            if (this.x != target.x || this.y != target.y) {
                if (target.type == "exit" && this.type == "guest") {
                    distance = 4; // exit is always a constant number of steps away for guests
                }
                else {
                    distance = Math.max(this.grid.distance_table[this.x][this.y][target.x][target.y], 2);
                }
            }
            const w = target_weights[i] / Math.pow(distance, distance_weight_scale);
            target_probs.push(w);
        }
        // if all weights are 0, return false
        if (target_probs.reduce((a, b) => a + b, 0) === 0) {
            this.curr_target = null;
            return false;
        }
        // Normalize probabilities
        const sum = target_probs.reduce((a, b) => a + b, 0);
        target_probs = target_probs.map(p => p / sum);

        // select new target
        this.curr_target = rng.weightedRandomChoice(target_options, target_probs);
        // if (this.id == "0") {
        //     console.log("--------------------------------")
        //     console.log("target_probs", target_options.map(t => t.id), target_probs);
        //     console.log("hunger, thirst, happiness, energy", Math.round(this.hunger * 100, 2), Math.round(this.thirst * 100, 2), Math.round(this.happiness * 100, 2), this.energy);
        //     console.log("curr (x, y): ", this.x, this.y, ". Target selected: ", this.curr_target.id, this.curr_target.subtype);
        // }
        return true;
    }
}

export { Person };