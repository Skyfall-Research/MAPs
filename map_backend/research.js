import config from "./config.js"
import { CommandResult } from "./utils.js"

class Research {

    static subclasses = ["yellow", "blue", "green", "red"]

    static research_speed_progress = config.research.speed_progress;
    static research_speed_cost = config.research.speed_cost;
    static research_points_required = config.research.points_required;

    static entity_order = Object.keys(config.rides).concat(Object.keys(config.shops)).concat(Object.keys(config.staff));
    static priority_ordering = Research.entity_order.reduce((acc, entity, index) => {
        acc[entity] = index + 1;
        return acc;
    }, {});

    static checkParameters(research_speed, research_topics) {
        if (!["none", "slow", "medium", "fast"].includes(research_speed)) {
            return new CommandResult(false, "Invalid research speed: " + research_speed + ". Must be none, slow, medium, or fast.");
        }
        if (!Array.isArray(research_topics)) {
            return new CommandResult(false, "Ride types to research must be an array.");
        }
        for (const entity_type of research_topics) {
            if (!Research.entity_order.includes(entity_type)) {
                return new CommandResult(false, "Invalid entity type: " + entity_type + ". Must be one of: " + Research.entity_order.join(", "));
            }
        }
        return new CommandResult(true, "Research speed and entity types to research set successfully");
    }

    constructor(difficulty) {
        this.research_speed = "none"; // Default speed.
        this.research_topics = Research.entity_order;
        this.operating_cost = 0;
        this.researched_entities = {};
        this.unresearched_entities = {};
        this.total_research_progress_made = 0;
        // determined by the order of the entities in the config.yaml
        this.topic_index = -1;
        for (let entity of Research.entity_order) {
            this.researched_entities[entity] = [];
            this.unresearched_entities[entity] = {order: [], progress: {}};
            
            for (let color of Research.subclasses) {
                if (color == "yellow" || difficulty == "easy") { // Yellow is the starting entity. In easy mode, we start with all entities.
                    this.researched_entities[entity].push(color);
                } else { // All other entities are unresearched at the start.
                    this.unresearched_entities[entity].order.push(color);
                    this.unresearched_entities[entity].progress[color] = Research.research_points_required[color];
                }
            }
        }
        this.current_entity = undefined;
        this.current_color = undefined;
        this.fast_days_since_last_new_entity = 0;
        this.medium_days_since_last_new_entity = 0;
        this.slow_days_since_last_new_entity = 0;
        this.new_entity_available = false;
    }

    /**
     * Set the research speed and available research topics.
     * @param {number} research_speed - How fast research progresses (one of "none", "slow", "medium", "fast").
     * @param {object} entity_types_to_research - list of entity types to research
     */
    set_research(research_speed, research_topics) {
        this.research_speed = research_speed;
        this.research_topics = research_topics.sort((a, b) => Research.priority_ordering[a] - Research.priority_ordering[b]);
    }

    select_next_research_topic() {
        // loop through the entity order until we find a entity that is in the research topics
        for (let i = 0; i < Research.entity_order.length; i++) {
            this.topic_index = (this.topic_index + 1) % Research.entity_order.length;
            const entity = Research.entity_order[this.topic_index];

            // If the entity is in the research topics and there are unresearched entities of this kind, select the first unresearched entity
            if (this.research_topics.includes(entity) && this.unresearched_entities[entity].order.length > 0) {
                this.current_entity = entity;
                this.current_color = this.unresearched_entities[entity].order[0];
                return true;
            }
        }
        this.research_speed = "none";
        this.current_entity = undefined;
        this.current_color = undefined;
        return false;
    }

    perform_research(park) {
        this.new_entity_available = false;
        this.operating_cost = 0;

        // Returns true if research is performed, false if no research is performed
        if (this.research_speed == "none") {
            return false;
        }

        // if we are not currently researching this kind of entity, or there is no unresearched entities of this kind,
        if (this.current_entity == undefined || !this.research_topics.includes(this.current_entity)) {
            // Find the next entity to research, if there is no next entity, return false
            if (!this.select_next_research_topic()) {
                return false;
            }
        }

        // If we don't have enough money to research, set research speed to none and return false
        if (park.money < Research.research_speed_cost[this.research_speed]) {
            this.research_speed = "none";
            return false;
        }

        park.money -= Research.research_speed_cost[this.research_speed];
        park.expenses += Research.research_speed_cost[this.research_speed];
        this.operating_cost += Research.research_speed_cost[this.research_speed];
        let progress = Research.research_speed_progress[this.research_speed];

        if (this.research_speed == "fast") {
            this.fast_days_since_last_new_entity++;
        } else if (this.research_speed == "medium") {
            this.medium_days_since_last_new_entity++;
        } else if (this.research_speed == "slow") {
            this.slow_days_since_last_new_entity++;
        }

        // console.log("UNRESEARCHED", this.unresearched_entities);
        // console.log("RESEARCHED", this.researched_entities);
        // console.log("PROGRESS", progress);
        // console.log("CURRENT RIDE", this.current_entity, "- CURRENT COLOR", this.current_color);
        // console.log("--------------------------------");

        // If the progress is greater than the amount of research points required for the current entity,
        // complete the entity, select the next entity to research and continue progress there
        while (progress >= this.unresearched_entities[this.current_entity].progress[this.current_color]) {
            progress -= this.unresearched_entities[this.current_entity].progress[this.current_color];
            this.unresearched_entities[this.current_entity].progress[this.current_color] = 0;
            this.researched_entities[this.current_entity].push(this.current_color);
            this.unresearched_entities[this.current_entity].order.shift();
            this.new_entity_available = true;
            this.total_research_progress_made += this.unresearched_entities[this.current_entity].progress[this.current_color];
            this.fast_days_since_last_new_entity = 0;
            this.medium_days_since_last_new_entity = 0;
            this.slow_days_since_last_new_entity = 0;

            // Find the next entity to research, if there is no next entity, return true
            if (!this.select_next_research_topic()) {
                return true;
            }
        } 
        // Use remaining progress toward the next entity
        this.unresearched_entities[this.current_entity].progress[this.current_color] -= progress;
        this.total_research_progress_made += progress;
        return true;
    }

    get_research_value() {
        return this.total_research_progress_made * config.research_value_per_point;
    }

    format() {
        return {
            research_speed: this.research_speed,
            research_topics: this.research_topics,
            operating_cost: this.operating_cost,
            available_entities: this.researched_entities,
            current_entity: this.current_entity,
            current_color: this.current_color,
            topic_index: this.topic_index,
            unresearched_entities: this.unresearched_entities,
            fast_days_since_last_new_entity: this.fast_days_since_last_new_entity,
            medium_days_since_last_new_entity: this.medium_days_since_last_new_entity,
            slow_days_since_last_new_entity: this.slow_days_since_last_new_entity,
            new_entity_available: this.new_entity_available,
        }
    }
}

export default Research;


