import axios from 'axios'

/**
 * Enhanced error logger for production debugging
 * @param {string} context - Where the error occurred (e.g., "putEndpoint", "processAction")
 * @param {Error} error - The error object
 * @param {Object} metadata - Additional context (e.g., endpoint, parkId, action)
 */
function logError(context, error, metadata = {}) {
  const isProduction = window.location.hostname !== 'localhost' &&
                       window.location.hostname !== '127.0.0.1';

  const errorInfo = {
    timestamp: new Date().toISOString(),
    environment: isProduction ? 'production' : 'development',
    context,
    error: {
      message: error.message,
      name: error.name,
      stack: error.stack,
      // Axios-specific error details
      status: error.response?.status,
      statusText: error.response?.statusText,
      code: error.code,
      config: error.config ? {
        url: error.config.url,
        method: error.config.method,
        timeout: error.config.timeout
      } : undefined
    },
    metadata,
    // Browser/client info
    userAgent: navigator.userAgent,
    url: window.location.href
  };

  // Always log to console
  console.error(`[${errorInfo.timestamp}] Error in ${context}:`, errorInfo);

  // In production, you could send to an error tracking service
  if (isProduction) {
    // TODO: Send to error tracking service (e.g., Sentry, LogRocket, etc.)
    // Example: Sentry.captureException(error, { extra: errorInfo });
  }

  return errorInfo;
}

/**
 * Retry a function with exponential backoff
 * @param {Function} fn - The async function to retry
 * @param {number} maxRetries - Maximum number of retry attempts (default: 2)
 * @param {number} baseDelay - Base delay in ms for exponential backoff (default: 1000)
 * @returns {Promise} The result of the function or throws the last error
 */
async function retryWithBackoff(fn, maxRetries = 2, baseDelay = 1000) {
  let lastError;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry on client errors (4xx) - these won't succeed on retry
      if (error.response && error.response.status >= 400 && error.response.status < 500) {
        throw error;
      }

      // Don't retry if we've exhausted all attempts
      if (attempt === maxRetries) {
        break;
      }

      // Calculate delay with exponential backoff: baseDelay * 2^attempt
      const delay = baseDelay * Math.pow(2, attempt);
      console.log(`Request failed (attempt ${attempt + 1}/${maxRetries + 1}), retrying in ${delay}ms...`);

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

/**
 * Get default backend host and port from environment variables
 */
function getDefaultBackendHostPort() {
  // Detect environment based on hostname - if localhost, use localhost:3000, otherwise use empty (relative paths)
  const isLocal = window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1';
  const backendHost = isLocal ? 'localhost' : '';
  const backendPort = isLocal ? '3000' : '';
  return { host: backendHost, port: backendPort };
}

function createUrl(endpoint, host = null, port = null) {
  // Use environment variables if host/port not provided
  if (!host || !port) {
    const defaults = getDefaultBackendHostPort();
    host = host || defaults.host;
    port = port || defaults.port;
  }
  //console.log(`Creating URL for endpoint: ${endpoint}, host: ${host}, port: ${port}`)
  // If host is empty or null, use relative path (same origin via ALB)
  if (!host || host === '') {
    return `/v1/${endpoint}`
  }
  return `http://${host}:${port}/v1/${endpoint}`
}

export class ParkResponse {
  constructor(statusCode, message, data, error = false) {
    this.status_code = statusCode
    this.message = message
    this.data = data
    this.error = error
  }
}

export function handleResponse(response) {
  if (response.status == 404) {
    throw new Error(`Endpoint not found: ${response.config?.url}\n full response: ${response}`)
  }
  if (![200, 400, 500].includes(response.status)) {
    // console.log(response)
    //console.log(`Unexpected response: ${JSON.stringify(response.data)}`)
    const data = response.data
    const message = `Unexpected status code: ${response.status}`
    return new ParkResponse(response.status, message, data, true)
  }
  return new ParkResponse(response.status, response.data?.message || 'Success', response.data.data, response.status != 200)
}

export async function getEndpoint(endpoint, params = {}, host = null, port = null) {
  return retryWithBackoff(async () => {
    try {
      const response = await axios.get(createUrl(endpoint, host, port), {
        params,
        timeout: 10000 // 10 second timeout
      })
      return handleResponse(response)
    } catch (error) {
      logError('getEndpoint', error, { endpoint, params, host, port });
      if (error.status == 400) {
        return handleResponse(error.response);
      } else if (error.code === 'ECONNREFUSED') {
        throw new Error(`Cannot connect to server at ${host}:${port}. Is the backend server running?`);
      } else if (error.code === 'ETIMEDOUT') {
        throw new Error(`Request timed out for ${endpoint}. Server may be unresponsive.`);
      } else {
        throw new Error(`HTTP request failed: ${error.message}`);
      }
    }
  });
}
export async function postEndpoint(endpoint, data = {}, host = null, port = null) {
  return retryWithBackoff(async () => {
    try {
      const response = await axios.post(createUrl(endpoint, host, port), data, {
        timeout: 15000 // 15 second timeout for POST requests (they can take longer)
      })
      return handleResponse(response)
    } catch (error) {
      logError('postEndpoint', error, { endpoint, data: { ...data, parkId: data.parkId }, host, port });
      if (error.status == 400) {
        return handleResponse(error.response);
      } else if (error.code === 'ECONNREFUSED') {
        throw new Error(`Cannot connect to server at ${host}:${port}. Is the backend server running?`);
      } else if (error.code === 'ETIMEDOUT') {
        throw new Error(`Request timed out for ${endpoint}. Server may be unresponsive.`);
      } else {
        throw new Error(`HTTP request failed: ${error.message}`);
      }
    }
  });
}

export async function putEndpoint(endpoint, data = {}, host = null, port = null) {
  if (!('x' in data) || !('y' in data)) {
    return {
      status_code: 400,
      message: "Modification actions require 'x' and 'y' as keyword arguments",
      data: {},
      error: true
    };
  }

  const x = data.x;
  const y = data.y;

  const { x: _, y: __, ...requestData } = data;

  return retryWithBackoff(async () => {
    try {
      const response = await axios.put(createUrl(`${endpoint}/${x}/${y}`, host, port), requestData, {
        timeout: 15000 // 15 second timeout
      });
      return handleResponse(response);
    } catch (error) {
      logError('putEndpoint', error, { endpoint, x, y, data: { ...requestData, parkId: data.parkId }, host, port });
      if (error.response && error.response.status === 400) {
        return handleResponse(error.response);
      } else if (error.code === 'ECONNREFUSED') {
        throw new Error(`Cannot connect to server at ${host}:${port}. Is the backend server running?`);
      } else if (error.code === 'ETIMEDOUT') {
        throw new Error(`Request timed out for ${endpoint}. Server may be unresponsive.`);
      } else {
        throw new Error(`HTTP request failed: ${error.message}`);
      }
    }
  });
}

export async function deleteEndpoint(endpoint, data = {}, host = null, port = null) {
  if (!('x' in data) || !('y' in data)) {
    return {
      status_code: 400,
      message: "Deletion actions require 'x' and 'y' as keyword arguments",
      data: {},
      error: true
    };
  }

  const x = data.x;
  const y = data.y;

  const { x: _, y: __, ...requestData } = data;

  const url = createUrl(`${endpoint}/${x}/${y}`, host, port);

  return retryWithBackoff(async () => {
    try {
      let response;
      if (Object.keys(requestData).length > 0) {
        response = await axios.delete(url, {
          data: requestData,
          headers: {
            'Content-Type': 'application/json'
          },
          timeout: 15000 // 15 second timeout
        });
      } else {
        response = await axios.delete(url, {
          timeout: 15000 // 15 second timeout
        });
      }
      return handleResponse(response);
    } catch (error) {
      logError('deleteEndpoint', error, { endpoint, x, y, data: { ...requestData, parkId: data.parkId }, host, port });
      if (error.response && error.response.status === 400) {
        return handleResponse(error.response);
      } else if (error.code === 'ECONNREFUSED') {
        throw new Error(`Cannot connect to server at ${host}:${port}. Is the backend server running?`);
      } else if (error.code === 'ETIMEDOUT') {
        throw new Error(`Request timed out for ${endpoint}. Server may be unresponsive.`);
      } else {
        throw new Error(`HTTP request failed: ${error.message}`);
      }
    }
  });
}

export async function deleteParkEndpoint(parkId, host = null, port = null) {
  return retryWithBackoff(async () => {
    try {
      const response = await axios.delete(createUrl(`park/delete_park/${parkId}`, host, port), {
        timeout: 15000 // 15 second timeout
      });
      return handleResponse(response);
    } catch (error) {
      logError('deleteParkEndpoint', error, { parkId, host, port });
      if (error.response && error.response.status === 400) {
        return handleResponse(error.response);
      } else if (error.code === 'ECONNREFUSED') {
        throw new Error(`Cannot connect to server at ${host}:${port}. Is the backend server running?`);
      } else if (error.code === 'ETIMEDOUT') {
        throw new Error(`Request timed out for delete park. Server may be unresponsive.`);
      } else {
        throw new Error(`HTTP request failed: ${error.message}`);
      }
    }
  });
}

export function getActionNameAndArgs(action) {
  // Parse action string like "place_ride(x=1, y=2, subtype='roller_coaster')"
  const match = action.match(/^(\w+)\((.*)\)$/)
  if (!match) {
    throw new Error('Invalid action format')
  }

  const actionName = match[1]
  const argsString = match[2]
  
  if (!argsString) {
    return [actionName, {}]
  }

  const args = {}
  
  // Simple parsing for arrays of strings - just track bracket depth
  let current = ''
  let bracketDepth = 0
  
  for (let i = 0; i < argsString.length; i++) {
    const char = argsString[i]
    
    if (char === '[') bracketDepth++
    else if (char === ']') bracketDepth--
    
    // Only split on comma if we're not inside brackets
    if (char === ',' && bracketDepth === 0) {
      const [key, value] = current.split('=').map(s => s.trim())
      if (key && value !== undefined) {
        args[key] = parseValue(value)
      }
      current = ''
    } else {
      current += char
    }
  }
  
  // Handle the last argument
  if (current.trim()) {
    const [key, value] = current.split('=').map(s => s.trim())
    if (key && value !== undefined) {
      args[key] = parseValue(value)
    }
  }

  return [actionName, args]
}

export function parseValue(value) {
  // Handle arrays of strings
  if (value.startsWith('[') && value.endsWith(']')) {
    const arrayContent = value.slice(1, -1).trim()
    if (!arrayContent) {
      return []
    }
    
    // Simple split by comma and remove quotes from each string
    return arrayContent.split(',').map(item => {
      const trimmed = item.trim()
      // Remove quotes from strings
      if ((trimmed.startsWith("'") && trimmed.endsWith("'")) || 
          (trimmed.startsWith('"') && trimmed.endsWith('"'))) {
        return trimmed.slice(1, -1)
      }
      return trimmed
    })
  }
  
  // Remove quotes from strings
  if (value.startsWith("'") && value.endsWith("'")) {
    return value.slice(1, -1)
  }
  if (value.startsWith('"') && value.endsWith('"')) {
    return value.slice(1, -1)
  }
  
  // Parse numbers
  if (!isNaN(value)) {
    return Number(value)
  }
  
  // Parse booleans
  if (value === 'true') return true
  if (value === 'false') return false
  
  return value
}

export function isSuperset(setA, setB) {
  for (const elem of setB) {
    if (!setA.has(elem)) {
      return false
    }
  }
  return true
}


export function formatGuestsState(currState, newGuestsInfo) {
  // Mark all existing guests as not updated
  for (const id in currState.guests) {
      currState.guests[id].has_been_updated = false;
  }

  // Update guests with new information
  for (const guest of newGuestsInfo) {
      const id = guest.id;
      const x = guest.x;
      const y = guest.y;
      
      // Get previous position from current state if exists, otherwise use current position
      const prevPos = currState.guests[id]?.curr_pos || [x, y];
      const guestSubclass = currState.guests[id]?.subclass || Math.ceil(Math.random() * 6);
      
      currState.guests[id] = {
          prev_pos: prevPos,
          curr_pos: [x, y],
          has_been_updated: true,
          subclass: guestSubclass
      };
      currState.guests[id].has_been_updated = true;
  }

  // Remove guests that haven't been updated
  const updatedGuests = {};
  for (const [id, guest] of Object.entries(currState.guests)) {
      if (guest.has_been_updated) {
          updatedGuests[id] = guest;
      }
  }
  currState.guests = updatedGuests;
}

function formatStaffState(currState, newState) {
  // Initialize staff tracking objects
  currState.janitors = {};
  currState.mechanics = {};
  currState.specialists = {};

  currState.total_janitors = [0, 0, 0, 0];
  currState.total_mechanics = [0, 0, 0, 0];
  currState.total_specialists = [0, 0, 0, 0];
  currState.total_operating_cost = 0;
  const idx = {'yellow': 0, 'blue': 1, 'green': 2, 'red': 3}
  

  // Process each employee in the staff list
  for (const employee of newState.staff_list || []) {
    const pluralSubtype = employee.subtype + "s";
    const id = employee.id;
    const x = employee.x;
    const y = employee.y;

    currState.total_operating_cost += employee.operating_cost;
    
    // Get previous position from current state if exists, otherwise use current position
    let prevPos;
    if (id in currState[pluralSubtype]) {
      prevPos = [currState.staff[id].x, currState.staff[id].y];
    } else {
      prevPos = [x, y];
    }
    
    // Create staff object with prev_pos
    currState.staff[id] = {
      prev_pos: prevPos,
      ...employee,
    };
    
    // Use string key for position tracking since arrays don't work as object keys
    const posKey = `${x},${y}`;
    if (!(posKey in currState[pluralSubtype])) {
      currState[pluralSubtype][posKey] = [];
    }
    currState[pluralSubtype][posKey].push(id);
    currState[`total_${pluralSubtype}`][idx[employee.subclass]] += 1;
  }
}

export function formatMidDayState(currState, newMidDayInfo) {
  currState.tick = newMidDayInfo.tick;
  currState.step = newMidDayInfo.step;
  currState.value = newMidDayInfo.value;
  currState.money = newMidDayInfo.money;
  currState.profit = newMidDayInfo.profit;
  currState.park_rating = newMidDayInfo.park_rating;
  currState.capacity = newMidDayInfo.capacity;
  currState.total_guests = newMidDayInfo.total_guests;
  currState.revenue = newMidDayInfo.revenue;
  currState.expenses = newMidDayInfo.expenses;
  currState.avg_money_spent = newMidDayInfo.revenue / newMidDayInfo.total_guests;
  console.log("total_guests: ", newMidDayInfo.total_guests, "revenue: ", newMidDayInfo.revenue, "avg_money_spent: ", currState.avg_money_spent);
  formatGuestsState(currState, newMidDayInfo.guests);
  formatStaffState(currState, newMidDayInfo.staff);
  
  currState.oos_attractions = [];
  currState.tile_dirtiness = [];

  for (const ride of newMidDayInfo.rides) {
      const x = ride.x;
      const y = ride.y;
      Object.assign(currState.rides[[x, y]], ride);
      if (ride.out_of_service) {
        currState.oos_attractions.push([x, y]);
      }
  }

  for (const shop of newMidDayInfo.shops) {
      const x = shop.x;
      const y = shop.y;
      Object.assign(currState.shops[[x, y]], shop);
      if (shop.out_of_service) {
        currState.oos_attractions.push([x, y]);
      }
  }
  
  for (const tile of newMidDayInfo.tile_dirtiness) {
      const x = tile.x;
      const y = tile.y;
      const cleanliness = tile.cleanliness;
      currState.tile_dirtiness.push([x, y, cleanliness]);
  }
}

export function formatFullState(newFullState) {
  const currState = {
      rides: {},
      shops: {},
      staff: {},
      guests: {},
      guest_survey_results: newFullState.guest_survey_results,
      entrance: newFullState.entrance,
      exit: newFullState.exit,
      paths: {},
      waters: {},
      oos_attractions: [],
      tile_dirtiness: [],
      tick: newFullState.tick,
      step: newFullState.state.step,
      horizon: newFullState.state.horizon,
      money: newFullState.state.money,
      value: newFullState.state.value,
      revenue: newFullState.state.revenue,
      expenses: newFullState.state.expenses,
      profit: newFullState.state.revenue - newFullState.state.expenses,
      park_rating: newFullState.state.park_rating,
      // Research info
      available_entities: newFullState.state.available_entities,
      new_entity_available: newFullState.state.new_entity_available,
      research_speed: newFullState.state.research_speed,
      research_topics: newFullState.state.research_topics,
      research_operating_cost: newFullState.state.research_operating_cost,
      fast_days_since_last_new_entity: newFullState.state.fast_days_since_last_new_entity,
      medium_days_since_last_new_entity: newFullState.state.medium_days_since_last_new_entity,
      slow_days_since_last_new_entity: newFullState.state.slow_days_since_last_new_entity,
      // Staff info
      total_salary_paid: newFullState.state.total_salary_paid,
      // Guest info
      total_guests: newFullState.guestStats.total_guests,
      avg_money_spent: newFullState.guestStats.avg_money_spent,
      avg_happiness: newFullState.guestStats.avg_happiness,
      avg_time_in_park: newFullState.guestStats.avg_steps_taken,
      avg_attractions_visited: (newFullState.guestStats.avg_rides_visited + 
                              newFullState.guestStats.avg_food_shops_visited + 
                              newFullState.guestStats.avg_drink_shops_visited + 
                              newFullState.guestStats.avg_specialty_shops_visited)
  };

  // Park info
  currState.min_cleanliness = 1.0;
  // Ride info
  currState.total_capacity = 0;
  currState.park_excitement = newFullState.state.park_excitement;
  currState.avg_intensity = [];
  currState.ride_min_uptime = 1.0;
  currState.rides_total_operating_cost = 0;
  currState.rides_total_revenue_generated = 0;

  for (const ride of newFullState.rides) {
      const x = ride.x;
      const y = ride.y;
      currState.rides[[x, y]] = ride;
      
      if (ride.out_of_service) {
          currState.oos_attractions.push([x, y]);
      }
      if (ride.cleanliness < 1.0) {
          currState.min_cleanliness = Math.min(currState.min_cleanliness, ride.cleanliness);
          currState.tile_dirtiness.push([x, y, ride.cleanliness]);
      }
      currState.total_capacity += ride.capacity;
      currState.avg_intensity.push(ride.intensity);
      currState.ride_min_uptime = Math.min(currState.ride_min_uptime, ride.uptime);
      currState.rides_total_operating_cost += ride.operating_cost;
      currState.rides_total_revenue_generated += ride.revenue_generated;
  }

  if (currState.avg_intensity.length > 0) {
      currState.avg_intensity = currState.avg_intensity.reduce((a, b) => a + b, 0) / currState.avg_intensity.length;
  }

  // Shop info
  currState.shops_total_revenue_generated = 0;
  currState.shops_total_operating_cost = 0;
  currState.shops_min_uptime = 1.0;
  for (const shop of newFullState.shops) {
      const x = shop.x;
      const y = shop.y;
      currState.shops[[x, y]] = shop;
      
      if (shop.cleanliness < 1.0) {
          currState.min_cleanliness = Math.min(currState.min_cleanliness, shop.cleanliness);
          currState.tile_dirtiness.push([x, y, shop.cleanliness]);
      }

      if (shop.out_of_service) {
        currState.oos_attractions.push([x, y]);
      }
      currState.shops_total_revenue_generated += shop.revenue_generated;
      currState.shops_total_operating_cost += shop.operating_cost;
      currState.shops_min_uptime = Math.min(currState.shops_min_uptime, shop.uptime);
  }

  for (const terrain of newFullState.terrain) {
      const x = terrain.x;
      const y = terrain.y;
      if (terrain.type == "path") {
          currState.paths[[x, y]] = terrain;
          currState.min_cleanliness = Math.min(currState.min_cleanliness, terrain.cleanliness);
          currState.tile_dirtiness.push([x, y, terrain.cleanliness]);
      } else {
          currState.waters[[x, y]] = terrain;
      }
  }
  
  formatStaffState(currState, newFullState.staff);
  return currState;
}

// Export utility functions for use in other modules
export { getDefaultBackendHostPort };
