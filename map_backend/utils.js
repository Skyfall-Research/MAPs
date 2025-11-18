// Utility function - not related to RNG
function member(array, value) {
    return array.some(item => JSON.stringify(item) === JSON.stringify(value));
}

// Utility class - not related to RNG
class CommandResult {
    constructor(success, message) {
        this.success = success;
        this.message = message;
    }
}

/**
 * Seeded Random Number Generator
 * Uses SFC32 algorithm for deterministic random number generation
 */
class RNG {
    /**
     * Create a new RNG instance
     * @param {string|number} seed - Seed value for deterministic randomness. If not provided, uses Math.random()
     */
    constructor(seed = null) {
        if (seed !== null) {
            console.log("Seeding RNG with seed:", seed);
            this.seeded = true;
            const [a, b, c, d] = this._cyrb128(String(seed));
            this._sfc32State = { a, b, c, d };
            this._normalSpare = null;
        } else {
            this.seeded = false;
        }
    }

    seed(seed) {
        if (seed !== null) {
            this.seeded = true;
            const [a, b, c, d] = this._cyrb128(String(seed));
            this._sfc32State = { a, b, c, d };
            this._normalSpare = null;
        } else {
            this.seeded = false;
        }
    }

    /**
     * Hash a seed string into four 32-bit integers
     * @private
     */
    _cyrb128(str) {
        let h1 = 1779033703, h2 = 3144134277, h3 = 1013904242, h4 = 2773480762;
        for (let i = 0, k; i < str.length; i++) {
            k = str.charCodeAt(i);
            h1 = h2 ^ Math.imul(h1 ^ k, 597399067);
            h2 = h3 ^ Math.imul(h2 ^ k, 2869860233);
            h3 = h4 ^ Math.imul(h3 ^ k, 951274213);
            h4 = h1 ^ Math.imul(h4 ^ k, 2716044179);
        }
        h1 = Math.imul(h3 ^ (h1 >>> 18), 597399067);
        h2 = Math.imul(h4 ^ (h2 >>> 22), 2869860233);
        h3 = Math.imul(h1 ^ (h3 >>> 17), 951274213);
        h4 = Math.imul(h2 ^ (h4 >>> 19), 2716044179);
        return [(h1^h2)>>>0, (h3^h4)>>>0, (h1^h3)>>>0, (h2^h4)>>>0];
    }

    /**
     * SFC32 random number generator
     * @private
     */
    _sfc32() {
        let { a, b, c, d } = this._sfc32State;
        a >>>= 0; b >>>= 0; c >>>= 0; d >>>= 0;
        let t = (a + b) | 0;
        a = b ^ (b >>> 9);
        b = (c + (c << 3)) | 0;
        c = (c << 21 | c >>> 11);
        d = (d + 1) | 0;
        t = (t + d) | 0;
        c = (c + t) | 0;
        this._sfc32State = { a, b, c, d };
        return (t >>> 0) / 4294967296;
    }

    /**
     * Generate a random float between 0 (inclusive) and 1 (exclusive)
     * @returns {number} Random float in [0, 1)
     */
    random() {
        return this.seeded ? this._sfc32() : Math.random();
    }

    /**
     * Generate a random integer between min and max (inclusive)
     * @param {number} min - Minimum value (inclusive)
     * @param {number} max - Maximum value (inclusive)
     * @returns {number} Random integer in [min, max]
     */
    randomInt(min, max) {
        return Math.floor(this.random() * (max - min + 1)) + min;
    }

    /**
     * Generate a random float between min and max
     * @param {number} min - Minimum value (inclusive)
     * @param {number} max - Maximum value (exclusive)
     * @returns {number} Random float in [min, max)
     */
    randomFloat(min, max) {
        return this.random() * (max - min) + min;
    }

    /**
     * Select a random element from an array with weighted probabilities
     * @param {Array} array - Array of elements to choose from
     * @param {Array<number>} weights - Array of weights corresponding to each element
     * @returns {*} Randomly selected element
     */
    weightedRandomChoice(array, weights) {
        const sum = weights.reduce((a, b) => a + b, 0);
        let randomNum = this.random() * sum;
        let cumSum = 0;
        for (let i = 0; i < array.length; i++) {
            cumSum += weights[i];
            if (randomNum < cumSum) {
                return array[i];
            }
        }
        return array[array.length - 1]; // Fallback to last element
    }

    /**
     * Get a random subset from an array (Fisher-Yates shuffle)
     * @param {Array} arr - Source array
     * @param {number} size - Size of subset to return
     * @returns {Array} Random subset of the array
     */
    getRandomSubarray(arr, size) {
        const shuffled = arr.slice(0);
        let i = arr.length;
        let temp, index;
        while (i--) {
            index = Math.floor((i + 1) * this.random());
            temp = shuffled[index];
            shuffled[index] = shuffled[i];
            shuffled[i] = temp;
        }
        return shuffled.slice(0, size);
    }

    /**
     * Generate a random number from a normal distribution N(mean, stdDev)
     * Uses Box-Muller transform
     * @param {number} mean - Mean of the distribution (default: 0)
     * @param {number} stdDev - Standard deviation (default: 1)
     * @returns {number} Random number from normal distribution
     */
    randomNormal(mean = 0, stdDev = 1) {
        if (this._normalSpare !== null) {
            const z = this._normalSpare;
            this._normalSpare = null;
            return z * stdDev + mean;
        }

        let u = 0, v = 0, s = 0;
        while (s === 0) {
            u = this.random() * 2 - 1;
            v = this.random() * 2 - 1;
            s = u * u + v * v;
            if (s >= 1) s = 0;
        }
        const m = Math.sqrt(-2 * Math.log(s) / s);
        this._normalSpare = v * m;
        return (u * m) * stdDev + mean;
    }

    /**
     * Shuffle an array in-place
     * @param {Array} arr - Array to shuffle
     * @returns {Array} The shuffled array (same reference)
     */
    shuffle(arr) {
        let i = arr.length;
        let temp, index;
        while (i--) {
            index = Math.floor((i + 1) * this.random());
            temp = arr[index];
            arr[index] = arr[i];
            arr[i] = temp;
        }
        return arr;
    }

    /**
     * Pick a random element from an array
     * @param {Array} arr - Array to pick from
     * @returns {*} Random element
     */
    choice(arr) {
        return arr[this.randomInt(0, arr.length - 1)];
    }
}


export {
    member,
    CommandResult,
    RNG
};
