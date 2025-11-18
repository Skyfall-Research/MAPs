import { v4 as uuidv4 } from 'uuid';


class Tile {
    constructor(x, y, type) {
        if (new.target === Tile) {
            throw new TypeError("Cannot construct Tile instances directly");
        }
        this.id = `${type}-(${x},${y})`; 
        this.x = x;
        this.y = y;
        this.type = type;
        this.is_walkable = ['path', 'entrance', 'exit'].includes(type);
        this.is_destination = ['exit', 'ride', 'shop'].includes(type);
        this.cleanliness = 1.0; // Cleanliness level from 0 to 1
    }

    format() {
        return {
            // id: this.id,
            x: this.x,
            y: this.y,
            type: this.type,
            cleanliness: Math.round(this.cleanliness * 100) / 100
        }
    }
}

class EntranceTile extends Tile {
    constructor(x, y) {
        super(x, y, "entrance");
    }

    static fromEntrance(entrance){
        const new_entrance = new EntranceTile(entrance.x, entrance.y)
        new_entrance.cleanliness = entrance.cleanliness
        return new_entrance
    }
}

class ExitTile extends Tile {
    constructor(x, y) {
        super(x, y, "exit");
    }

    static fromExit(exit){
        const new_exit = new ExitTile(exit.x, exit.y)
        new_exit.cleanliness = exit.cleanliness
        return new_exit
    }
}

class PathTile extends Tile {
    constructor(x, y) {
        super(x, y, "path");
    }
    /**
     * Create a new object from a json dictionary passed in
     */
    static fromPath(path){
        const new_path = new PathTile(path.x, path.y)
        new_path.cleanliness = path.cleanliness
        return new_path
    }
}

class WaterTile extends Tile {
    constructor(x, y) {
        super(x, y, "water");
    }
}

class EmptyTile extends Tile {
    constructor(x, y) {
        // Empty tile ids don't matter, not exposed. Can have race conditions.
        super(x, y, "empty");
    }
}


export { Tile, EntranceTile, ExitTile, PathTile, EmptyTile, WaterTile };