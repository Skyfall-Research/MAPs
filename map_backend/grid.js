import { CommandResult, member } from "./utils.js"
import { EntranceTile, ExitTile, PathTile, WaterTile, EmptyTile } from "./tiles/tile.js"
import config from "./config.js"


const global_routing_table_cache = new Map();
const global_distance_table_cache = new Map();
var global_cache_queue = [];

const global_articulation_path_cache = new Map();
var global_articulation_path_cache_queue = [];

const moves = [
    {dx: 0, dy: 1},
    {dx: 1, dy: 0},
    {dx: 0, dy: -1},
    {dx: -1, dy: 0},
];

function invertMove(move) {
    return {dx: -move.dx, dy: -move.dy};
}

class Grid {
    constructor(size = 20) {
        this.size = size;
        this.tiles = Array.from({ length: size }, (_, rowIndex) =>
            Array.from({ length: size }, (_, colIndex) => new EmptyTile(rowIndex, colIndex))
        );
        
        // Set up range properties from config
        this.min_node_distance_range = config.min_node_distance_range;
        this.node_densification_range = config.node_densification_range;
        this.vertical_pathing_prob_range = config.vertical_pathing_prob_range;

        this.all_tiles_cache = null
        this.cleanable_tiles_cache = null
    }

    resetState(grid){
        for(let x= 0; x < this.size; x++){
            for(let y = 0; y < this.size; y++){
                this.tiles[x][y] = new EmptyTile(x, y)
                this.tiles[x][y].cleanliness = parseFloat(grid[x][y].cleanliness)
            }
        }
        this.all_tiles_cache = null
        this.cleanable_tiles_cache = null
    }
    
    // Getters
    getTile(x, y) {
        return this.tiles[x][y];
    }

    getAllTiles() {
        if (this.all_tiles_cache === null){
            this.all_tiles_cache = this.tiles.flat();
        }
        return this.all_tiles_cache;  // NOTE! Mutation risk! Be careful!
    }

    getCleanableTiles() {
        if (this.cleanable_tiles_cache === null){
            this.cleanable_tiles_cache = this.getAllTiles().filter(tile => tile.type != "water" && tile.type != "empty")
        }
        return this.cleanable_tiles_cache;
    }

    getAllPathTiles() {
        return this.getAllTiles().filter(tile => tile.type === "path");
    }

    getAllEntrancePathAndExitTile() {
        return this.getAllTiles().filter(tile => tile.type === "path" || tile.type === "exit" || tile.type === "entrance");
    }

    getAllTerrainTiles() {
        return this.getAllTiles().filter(tile => tile.type === "path" || tile.type === "water");
    }

    getAllDestinationTiles() {
        return this.getAllTiles().filter(tile => tile.is_destination);
    }

    getAllEmptyTiles() {
        return this.getAllTiles().filter(tile => tile.type === "empty");
    }
    

    tileIsInBounds(x, y) {
        return x >= 0 && x < this.size && y >= 0 && y < this.size;
    }

    // Helper functions
    tileIsAdjacentToPath(tile) {
        // Check all 4 adjacent tiles (up, down, left, right)
        const adjacentPositions = [
            { x: tile.x - 1, y: tile.y }, // up
            { x: tile.x + 1, y: tile.y }, // down
            { x: tile.x, y: tile.y - 1 }, // left
            { x: tile.x, y: tile.y + 1 }  // right
        ];
        
        for (const pos of adjacentPositions) {
            // Check bounds
            if (this.tileIsInBounds(pos.x, pos.y)) {
                if (this.getTile(pos.x, pos.y).type === "path") {return true;}
            }
        }
        return false;
    }

    numTilesAdjacentToWater(tile) {
        const adjacentPositions = [
            { x: tile.x - 1, y: tile.y }, // up
            { x: tile.x + 1, y: tile.y }, // down
            { x: tile.x, y: tile.y - 1 }, // left
            { x: tile.x, y: tile.y + 1 }  // right
        ];
        let count = 0;
        for (const pos of adjacentPositions) {
            if (this.tileIsInBounds(pos.x, pos.y)) {
                if (this.getTile(pos.x, pos.y).type === "water") {count++;}
            }
        }
        return count;
    }

    getAdjacentRides(tile) {
        const adjacentPositions = [
            { x: tile.x - 1, y: tile.y }, // up
            { x: tile.x + 1, y: tile.y }, // down
            { x: tile.x, y: tile.y - 1 }, // left
            { x: tile.x, y: tile.y + 1 }  // right
        ];
        return adjacentPositions.filter(pos => this.tileIsInBounds(pos.x, pos.y)).map(pos => this.getTile(pos.x, pos.y)).filter(tile => tile.type === "ride");
    }

    // Manipulate grid tiles
    clearTile(x,y){
        this.tiles[x][y] = new EmptyTile(x, y)
        this.all_tiles_cache = null
        this.cleanable_tiles_cache = null
        return new CommandResult(true, "Tile cleared successfully")
    }

    /**
     * Places an element (ride, shop, staff, etc.) at the given coordinates
     * if the tile is empty.
     * @param {number} x
     * @param {number} y
     * @param {object} element - The element to place (should include a type property)
     * @returns {boolean} True if placement succeeded.
     */
    placeElement(x, y, element) {
        this.all_tiles_cache = null
        this.cleanable_tiles_cache = null
        if(!this.tileIsInBounds(x, y)){
            return new CommandResult(false, "Coordinates out of bounds")
        }
        if (this.tiles[x][y].type != "empty") {
            const tile_occupant = this.tiles[x][y].type == "water" ? "water" : `a ${this.tiles[x][y].type}`
            return new CommandResult(false, `Tile already contains ${tile_occupant}.`)
        }
        this.tiles[x][y] = element;
        return new CommandResult(true, "Element placed successfully")
    }

    /**
     * Places an element (ride, shop, staff, etc.) at the given coordinates
     * regardless of whether the tile is empty.
     * @param {number} x
     * @param {number} y
     * @param {object} element - The element to place (should include a type property)
     * @returns {boolean} True if placement succeeded.
     */
    unsafePlaceElement(x, y, element) {
        this.all_tiles_cache = null
        this.cleanable_tiles_cache = null
        if (!this.tileIsInBounds(x, y)){
            return new CommandResult(false, "Coordinates out of bounds")
        }
        this.tiles[x][y] = element;
        return new CommandResult(true, "Element placed successfully")
    }

    addEntrance(x, y) {
        this.all_tiles_cache = null
        this.cleanable_tiles_cache = null
        this.entrance = new EntranceTile(x, y);
        this.unsafePlaceElement(x, y, this.entrance);
    }

    addExit(x, y) {
        this.all_tiles_cache = null
        this.cleanable_tiles_cache = null
        this.exit = new ExitTile(x, y);
        this.unsafePlaceElement(x, y, this.exit);
    }

    static randomNode(oldNodes, minDist, i, rng){
        let x = rng.randomInt(0, this.size - 1);
        let y = rng.randomInt(0, this.size - 1);
        if (i == 1){
            x = 0;
        } else if (i == 0){
            x = this.size - 1;
        }

        let remaining_attempts = 5 * this.size * this.size 

        // Randomly sample positions until the selected position is far away enough
        while(Math.min.apply(Math, oldNodes.map((pos) => Math.abs(pos[0] - x) + Math.abs(pos[1] - y))) < minDist){
            // Give up if we can't solve in a large number of attempts
            if (remaining_attempts === 0){
                return undefined;
            }
            x = rng.randomInt(0, this.size - 1);
            y = rng.randomInt(0, this.size - 1);
            if (i == 1){
                x = 0;
            } else if (i == 0){
                x = this.size - 1;
            }

            remaining_attempts = remaining_attempts - 1;
        }

        return [x, y];
    }

    pathRedundant(x, y){
        let positions = [
            {x: -1, y:-1},
            {x: 0, y:-1},
            {x: 1, y:-1},
            {x: 1, y:0},
            {x: 1, y:1},
            {x: 0, y:1},
            {x: -1, y:1},
            {x: -1, y:0},
        ]

        let occupied = []

        for(const pos of positions){
            // If offset position valid
            if (this.tileIsInBounds(x+pos.x, y+pos.y) &&
                ['path', 'entrance', 'exit'].includes(this.getTile(x+pos.x, y+pos.y).type)){
                occupied.push(1);
            } else {
                occupied.push(0);
            }
        }
        // If this path is surrounded by path then it is redundant
        let neighbours = occupied.reduce((acc, elem) => acc + elem, 0);
        if (neighbours === 8){
            return true;
        // If path has a single neighbouring path, it is never redundant
        } else if (neighbours < 2){
            return false;
        }
        // Otherwise, rotate the surrounding path to put the gap first.
        // It is redundant if there is no other gap
        while (occupied[0] !== 0){
            occupied.push(occupied.shift());
        }

        let first_found = false;
        let end_first_found = false;
        for (let i = 1; i < 8; i++){
            if (occupied[i] === 1 && !first_found){
                first_found = true;
            } else if (occupied[i] === 0 && first_found){
                end_first_found = true;
            } else if (occupied[i] == 1 & end_first_found){
                return false; // Not redundant, there is a gap
            }
        }
        return true; // Redundant, you can path around this path section
    }

    setupRandomParkLayout(difficulty, rng) {
        this.all_tiles_cache = null
        this.cleanable_tiles_cache = null

        // Randomly sample hyperparameters
        let numNodes = rng.randomInt(config.path_nodes_range[0], config.path_nodes_range[1]);
        let minDist = rng.randomInt(this.min_node_distance_range[0], this.min_node_distance_range[1]);
        let density = rng.randomFloat(this.node_densification_range[0], this.node_densification_range[1]);
        let vertProb = rng.randomFloat(this.vertical_pathing_prob_range[0], this.vertical_pathing_prob_range[1]);

        // Generate a number of nodes
        let nodes = [];

        // Generate additional random nodes
        for(let i = 0; i < numNodes; i++){
            // First two generated will be entrance & exit nodes
            let new_node = Grid.randomNode(nodes, minDist, i, rng);

            // If we couldn't get a new node, then the config
            // may be bad. Try resampling the generation parameters.
            if (new_node === undefined){
                return this.setupRandomParkLayout(difficulty, rng); 
            }

            nodes.push(new_node);
        }
        
        // Select edges s.t. the resulting nodes list becomes a tree
        // Reorder nodes to prevent a bias of entrance & exit having higher degree
        let nodes_copy = rng.getRandomSubarray(nodes, nodes.length)
        let edges = [] // (smaller idx, larger idx)
        for(let i = 1; i < numNodes; i++){
            // Connect each node to a random node from the connected set
            edges.push([nodes_copy[rng.randomInt(0, i-1)], nodes_copy[i]]);
        }

        // Randomly sample from the remaining edges
        let remaining_edges = []
        for(let i = 0; i < numNodes - 1; i++){
            for(let j = i + 1; j < numNodes; j++){
                let new_edge = [nodes[i], nodes[j]];
                if(!member(edges, new_edge)){
                    remaining_edges.push(new_edge);
                }
            }
        }
        edges.concat(rng.getRandomSubarray(remaining_edges, Math.round(density * remaining_edges.length)));

        // Create node tiles
        for(let i=2; i < numNodes; i++){
            this.placeElement(nodes[i][0], nodes[i][1], new PathTile(nodes[i][0], nodes[i][1]));
        }

        // Place path between nodes
        for(let i=0; i<edges.length; i++){
            let curr_x = edges[i][0][0]; // current position (has a path)
            let curr_y = edges[i][0][1];
            
            let tar_x = edges[i][1][0];
            let tar_y = edges[i][1][1];

            while(curr_x !== tar_x || curr_y !== tar_y){
                // Chose whether to go vertical or horizontal
                let offset = undefined;
                if (curr_x === tar_x){
                    offset = curr_y < tar_y ? [0, 1] : [0, -1];
                } else if (curr_y === tar_y) {
                    offset = curr_x < tar_x ? [1, 0] : [-1, 0];
                } else {
                    if (rng.random() < vertProb){
                        offset = curr_x < tar_x ? [1, 0] : [-1, 0];
                    } else{
                        offset = curr_y < tar_y ? [0, 1] : [0, -1];
                    }
                }

                curr_x = curr_x + offset[0];
                curr_y = curr_y + offset[1];

                // Place tile; may fail if there's already path there, that's fine
                this.placeElement(curr_x, curr_y, new PathTile(curr_x, curr_y));
            }
        }

        // Set Entrance & Exit; will overwrite 2 path tiles from earlier.
        this.addEntrance(nodes[0][0], nodes[0][1]);
        this.addExit(nodes[1][0], nodes[1][1]);

        // This works but tends to produce some "waffle iron" patterns
        // where several paths intersect. To deal with this, do a second pass and erase
        // redundant adjacent paths.
        let horizontal_tracking = rng.random() < 0.5;
        for(let x_idx = 0; x_idx < this.size; x_idx++){
            for (let y_idx = 0; y_idx < this.size; y_idx++){
                let x = undefined;
                let y = undefined;
                if (horizontal_tracking){
                    x = x_idx;
                    y = y_idx;
                } else {
                    x = y_idx;
                    y = x_idx;
                }

                if (this.getTile(x,y).type === "path" && this.pathRedundant(x, y)){
                    this.unsafePlaceElement(x, y, new EmptyTile(x, y))
                }
            }
        }

        /*
        console.log("EDGES")
        console.log(edges)
        console.log("NODES")
        console.log(nodes)
        */

        // Setup routing table for pathing now that paths are done.
        this.computeRoutingTable(difficulty);
    }

    setupProvidedParkLayout(layout, difficulty) {
        this.all_tiles_cache = null
        this.cleanable_tiles_cache = null
        let exit_added = false;
        let entrance_added = false;
        for (let x = 0; x < this.size; x++) {
            for (let y = 0; y < this.size; y++) {
                if (layout[x][y] == 1) {
                    if (entrance_added){
                        throw new Error("Invalid provided layout: Entrance already added");
                    }
                    this.addEntrance(x, y);
                    entrance_added = true;
                } else if (layout[x][y] == 2) {
                    if (exit_added){
                        throw new Error("Invalid provided layout: Exit already added");
                    }
                    this.addExit(x, y);
                    exit_added = true;
                } else if (layout[x][y] == 3) {
                    this.placeElement(x, y, new PathTile(x, y));
                } else if (layout[x][y] == 4) {
                    // if (difficulty == "easy"){
                    //    // Pass. Water is not added in easy mode.
                    // } else {
                    this.placeElement(x, y, new WaterTile(x, y));
                    // }
                }
            }
        }
        this.computeRoutingTable(difficulty);
    }

    isEntrancePathOrExitTile(x, y) {
        if (!this.tileIsInBounds(x, y)) {
            return false;
        }
        let tile = this.getTile(x, y);
        return tile.type === "path" || tile.type === "exit" || tile.type === "entrance";
    }

    isWalkableTile(x, y) {
        if (!this.tileIsInBounds(x, y)) {
            return false;
        }
        return this.getTile(x, y).is_walkable;
    }
    
    isDestinationTile(x, y) {
        if (!this.tileIsInBounds(x, y)) {
            return false;
        }
        return this.getTile(x, y).is_destination;
    }
    
    getDestinationNeighbors(x, y) {
        return moves
            .map(({dx, dy}) => ({x: x + dx, y: y + dy}))
            .filter(neighbor => this.tileIsInBounds(neighbor.x, neighbor.y) && this.getTile(neighbor.x, neighbor.y).is_destination);
    }
    
    #articulationPathDFS(node, depth, visited, parent_node){
        // Record that we have visited this node, and its depth.
        // From what we have explored thusfar, the shallowest reachable
        // node is itself.
        if (visited[node.x] === undefined){
            visited[node.x] = {};
        }

        visited[node.x][node.y] = {'depth': depth, 'shallowest_reachable': depth}

        for (const move of moves) {
            const neighbor = {x: node.x + move.dx, y: node.y + move.dy};

            // Consider only valid neighbouring paths or the exit
            if (this.isEntrancePathOrExitTile(neighbor.x, neighbor.y)){
                
                // If unvisited, run DFS on this node
                if(visited?.[neighbor.x]?.[neighbor.y] === undefined){
                    this.#articulationPathDFS(neighbor, depth+1, visited, node)
                }

                // Update the low point if the neighbour isn't the parent
                if (neighbor.x !== parent_node.x || neighbor.y !== parent_node.y){
                    visited[node.x][node.y]['shallowest_reachable'] = 
                        Math.min(visited[node.x][node.y]['shallowest_reachable'], 
                                 visited[neighbor.x][neighbor.y]['shallowest_reachable'])
                }
            }
        }
    }

    cannotRemovePath(x, y){
        return this.articulation_paths.filter(path => path.x === x && path.y === y).length !== 0;
    }

    computeArticulationPaths(){
        // Determines what path tiles cannot be deleted without disconnecting the
        // entrance and exit.

        // Need to know the entrance & exit also for the caching of articulation tiles
        let paths = JSON.stringify({"paths": this.getAllEntrancePathAndExitTile().map(path => [path.x, path.y])})
        
        if (global_articulation_path_cache.get(paths) !== undefined){
            this.articulation_paths = global_articulation_path_cache.get(paths);
            return;
        }
    
        // If the cache contains more than 30 states, then kick
        // the oldest. This may run into problems if reset is being
        // repeatedly called with random state generation True.
        if (global_articulation_path_cache_queue.length > 30){
            let key_to_del = global_articulation_path_cache_queue.shift()
            global_articulation_path_cache.delete(key_to_del)
        }

        // Run DFS to get depth & low points of all nodes
        let visited = {};
        this.#articulationPathDFS(this.entrance, 0, visited, this.entrance)

        // Determine articulation paths
        // Assumes routing table has already been computed as it will use the recorded
        // path from the entrance to the exit
        let curr = this.entrance
        this.articulation_paths = []
        while (curr.x !== this.exit.x || curr.y !== this.exit.y){
            let move = this.routing_table[curr.x][curr.y][this.exit.x][this.exit.y]
            let next = {'x': curr.x + move.dx, 'y': curr.y + move.dy}

            // If the next node on the path has no way up to a shallower node
            // this the current node is an articulation point
            if(visited[curr.x][curr.y].depth <= visited[next.x][next.y].shallowest_reachable){
                this.articulation_paths.push({'x': curr.x, 'y': curr.y})
            }

            curr = next 
        }
        
        // Add to cache
        global_articulation_path_cache.set(paths, this.articulation_paths);
        global_articulation_path_cache_queue.push(paths)
    }

    computeRoutingTable(difficulty) {
        let paths = JSON.stringify(this.getAllPathTiles().map(path => [path.x, path.y]))
        
        if (global_routing_table_cache.get(paths) !== undefined){
            this.routing_table = global_routing_table_cache.get(paths);
            this.distance_table = global_distance_table_cache.get(paths);
            if (difficulty == "hard"){
                let articulation_key = JSON.stringify({"paths": this.getAllEntrancePathAndExitTile().map(path => [path.x, path.y])})
                this.articulation_paths = global_articulation_path_cache.get(articulation_key)
            }
            return;
        }
    
        // If the cache contains more than 30 states, then kick
        // the oldest. This may run into problems if reset is being
        // repeatedly called with random state generation True.
        if (global_cache_queue.length > 30){
            let removed_key = global_cache_queue.shift();
            global_routing_table_cache.delete(removed_key)
            global_distance_table_cache.delete(removed_key)
        }
    
        // Create sparse array mapping; [curr_x][curr_y][target_x][target_y] maps to next position object
        this.routing_table = new Array(this.size);
        this.distance_table = new Array(this.size);
        for (let i = 0; i < this.size; i++) {
            this.routing_table[i] = new Array(this.size);
            this.distance_table[i] = new Array(this.size);
            for (let j = 0; j < this.size; j++) {
                this.routing_table[i][j] = new Array(this.size);
                this.distance_table[i][j] = new Array(this.size);
                for (let k = 0; k < this.size; k++) {
                    this.routing_table[i][j][k] = new Array(this.size);
                    this.distance_table[i][j][k] = new Array(this.size);
                }
            }
        }
        // For each possible destination tile, compute how to get the from every possible source tile (i.e. a tile a person can occupy)
        // Start with the exit tile
        let allTiles = [this.exit, ...this.getAllTiles().filter(tile => tile.type !== "exit")]
        for (const dest_tile of allTiles) {
            // Skip tiles that are not walkable, destinations, or adjacent to a path tile
            if (!(dest_tile.is_walkable || dest_tile.is_destination || this.tileIsAdjacentToPath(dest_tile))) {
                continue;
            }

            // Skip tiles that are not the exit and do not have a path back to the exit
            if(dest_tile !== this.exit && this.routing_table[dest_tile.x][dest_tile.y][this.exit.x][this.exit.y] === undefined){
                continue;
            }
    
            const dest = {x: dest_tile.x, y: dest_tile.y};
            // Visited keeps track of the what move to take from a given source tile to move toward the destination tile
            const valid_visited = {};         // visited[node] = {tile, move, distance}
            valid_visited[JSON.stringify(dest)] = {tile: dest, move: {dx: 0, dy: 0}, distance: 0};
            // queue keeps track of the tiles to expand
            const queue = [{node: dest, distance: 0}];
        
            // BFS from the destination node
            while (queue.length > 0) {
                const {node, distance} = queue.shift();
                for (const move of moves) {
                    const neighbor = {x: node.x + move.dx, y: node.y + move.dy};
                    if (this.tileIsInBounds(neighbor.x, neighbor.y)) {
                        const neighborKey = JSON.stringify(neighbor);
    
                        let neighbor_is_walkable = this.isWalkableTile(neighbor.x, neighbor.y);
                        // If the neighbor is walkable, then add it to the queue to expand later
                        if (neighbor_is_walkable) {
                            if (!(neighborKey in valid_visited)) {
                                queue.push({node: neighbor, distance: distance + 1});
                            }
                        }
                        
                        // Entrance-Path-Ride
                        // NOTE: this works because all useable path/destination tiles are inherently adjacent to a path tile
                        if (this.tileIsAdjacentToPath(neighbor) || neighbor_is_walkable) {
                            // Add this connection if:
                            //     1. We haven't visited this neighbor before AND
                            //     2. This isn't the destination tile or the destination is a path or the neighbor is walkable. This prevents walking directly between attractions
                            if (!(neighborKey in valid_visited) && (node.x !== dest_tile.x || node.y !== dest_tile.y || dest_tile.type === 'path' || neighbor_is_walkable)) {
                                valid_visited[neighborKey] = {tile: node, move: invertMove(move), distance: distance + 1};
                            }
                        }
                    }
                }
            }
      
            // Build next step map for all sources toward this destination
            for (const srcKey in valid_visited) {
                const srcData = valid_visited[srcKey];
                if (srcData === null) continue; 
                
                const destKey = JSON.stringify(dest);
    
                let srcObj = JSON.parse(srcKey);
                let destObj = JSON.parse(destKey);
                
                this.routing_table[srcObj.x][srcObj.y][destObj.x][destObj.y] = srcData.move;
                this.distance_table[srcObj.x][srcObj.y][destObj.x][destObj.y] = srcData.distance;
            }
        }

        global_routing_table_cache.set(paths, this.routing_table);
        global_distance_table_cache.set(paths, this.distance_table);
        global_cache_queue.push(paths)

        // In hard mode, also determine the paths that
        // cannot be safely deleted.
        if (difficulty == "hard"){
            this.computeArticulationPaths();
        }
    }

    format() {
        return this.tiles.map((row, rowIndex) => row.map((tile, colIndex) => tile.id));
    }
}

export default Grid;
