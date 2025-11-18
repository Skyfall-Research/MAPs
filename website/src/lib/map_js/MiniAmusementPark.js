
// Import configuration
import { getActionParams, getActionParamTypes, getDefaultSettings } from './config.js'
import { getActionNameAndArgs, isSuperset, getEndpoint, postEndpoint, putEndpoint, deleteEndpoint, deleteParkEndpoint, ParkResponse, getDefaultBackendHostPort} from './helpers.js'

// Sandbox action constants
const SANDBOX_ACTION_NAMES = [
  'undo_day',
  'max_money', 
  'max_research',
  'set_sandbox_mode',
  'reset',
  'change_settings'
]

const SANDBOX_ACTION_PARAMS = {
  'undo_day': new Set(['parkId']),
  'max_money': new Set(['parkId']),
  'max_research': new Set(['parkId']),
  'set_sandbox_mode': new Set(['parkId', 'sandbox_steps']),
  'reset': new Set(['parkId']),
  'change_settings': new Set(['parkId', 'difficulty', 'layout'])
}


export class MiniAmusementPark {
  constructor(options = {}) {
    // Get default host/port from environment variables if not provided
    const defaultBackend = getDefaultBackendHostPort();
    const {
      host = defaultBackend.host,
      port = defaultBackend.port,
      parkId = null,
      observationType = 'pydantic', // 'pydantic', 'gym', 'raw', 'test'
      expName = 'exp',
      renderPark = false,
      visualizer = null,
      dataLevel = 'HIGH',
      observabilityMode = 'NORMAL',
      returnRawInInfo = false,
      returnDetailedGuestInfo = false,
      difficulty = null,
      layout = null,
      startingMoney = null,
      horizon = null,
      noopOnInvalidAction = true,
      seed = null
    } = options

    // Basic properties
    this.host = host
    this.port = port
    this.prevMoney = null
    this.settings = {}
    this.gameSize = 20

    // Observation and action spaces
    this.observationType = observationType
    this.dataLevel = dataLevel
    this.observabilityMode = observabilityMode
    this.returnRawInInfo = returnRawInInfo
    this.returnDetailedGuestInfo = returnDetailedGuestInfo
    this.noopOnInvalidAction = noopOnInvalidAction

    // Logging
    this.expName = expName
    this.visualizer = visualizer

    // Not used for now
    this.renderPark = renderPark

    // State management
    this.resetState = null

    // Settings
    this.difficulty = null
    this.layout = null
    this.startingMoney = null
    this.horizon = null
    this.guestPreferences = null

    // Initialize park ID
    this.parkId = parkId

    // Seed management
    this.seed = seed

    // Update settings (order matches Python: layout, difficulty, startingMoney, horizon)
    this.updateSettings(layout, difficulty, startingMoney, horizon)
  }

  async initializeParkId() {
    try {
      const result = await getEndpoint('park/get_new_park_id', {}, this.host, this.port)
      if (result.error) {
        throw new Error(`Failed to initialize park ID: ${result.message}`)
      }
      this.parkId = result.data.parkId
    } catch (error) {
      console.error("Error initializing park ID:", error.message);
      throw error;
    }
  }

  updateSettings(layout = null, difficulty = null, startingMoney = null, horizon = null) {
    // Parameter order matches Python version: layout, difficulty, startingMoney, horizon
    this.layout = layout || this.layout
    this.difficulty = difficulty || this.difficulty || 'easy'
    this.startingMoney = startingMoney || this.startingMoney
    this.horizon = horizon || this.horizon
  }

  async shutdown() {
    // Clean up resources (similar to Python's __exit__ method)
    // First delete park data from backend, then clean up client resources
    try {
      await this.deletePark();
    } catch (error) {
      console.error('Failed to delete park during shutdown:', error);
    }
    // No session to close in JS (fetch/axios handles connections automatically)
  }

  setParkId(parkId) {
    // TODO close / clear previous park id
    this.parkId = parkId
  }

  async setSeed(seed) {
    seed = seed || this.seed
    const result = await postEndpoint('park/seed', { parkId: this.parkId, seed: seed }, this.host, this.port)
    if (result.error) {
      console.error("ERROR: ", result.message)
    } 
  }

  async set(state = null) {
    if (!state) {
      throw new Error('State is required for set operation')
    }

    const stateCopy = { ...state }
    // Reduce payload sent to server; guests aren't set so clearing this is fine
    stateCopy.guests = []

    const params = { parkId: this.parkId, state: stateCopy }
    const result = await postEndpoint('park/set', params, this.host, this.port)
    
    const info = {}
    if (result.error) {
      info.error = {
        message: result.message,
        type: 'set_error'
      }
      throw new Error(`Error setting park: ${result.message}`)
    }

    this.prevMoney = stateCopy.state.money

    let obs
    if (this.observationType !== 'raw') {
      const [observation] = await this.getObservationAndRawState()
      obs = observation
      if (this.returnRawInInfo) {
        info.raw_state = stateCopy
      }
    } else {
      obs = stateCopy
    }

    return [obs, info]
  }

  async getRawState() {
    const params = {
      parkId: this.parkId,
      fullState: true,
      includeGuests: this.returnDetailedGuestInfo
    }
    
    const result = await getEndpoint('park/', params, this.host, this.port)
    if (result.error) {
      throw new Error(`Server encountered error while observing: ${result.message}`)
    }
    
    return result.data
  }

  async getObservationAndRawState() {
    const params = {
      parkId: this.parkId,
      fullState: true,
      includeGuests: this.returnDetailedGuestInfo
    }
    
    const result = await getEndpoint('park/', params, this.host, this.port)
    if (result.error) {
      throw new Error(`Server encountered error while observing: ${result.message}`)
    }

    // FIXME: Differentiate based on observation type
    let obs = result.data
    return [obs, result.data]
  }

  async observe() {
    const [obs] = await this.getObservationAndRawState()
    return obs
  }

  async step(action) {
    const info = {}

    let actionResult = null
    if (action !== null) {
      actionResult = await this.act(action)
    }

    if (actionResult.error) {
      const reward = 0
      info.error = {
        message: actionResult.message,
        type: 'invalid_action'
      }
    }

    let truncated = false, terminated = false
    let reward = 0
    if (!actionResult.error || this.noopOnInvalidAction) {
      // Run park for a day
      const data = { parkId: this.parkId }
      
      const proceedResult = await postEndpoint('park/proceed', data, this.host, this.port)
      
      // Check if park encountered an error
      if (proceedResult.error) {
        info.error = {
          message: proceedResult.message,
          type: 'proceed_error'
        }
      } else {
        // Action OK & no park server error, advance number of steps
        reward = proceedResult.data.reward
        terminated = proceedResult.data.terminated
        truncated = proceedResult.data.truncated
      }
    }

    // Get observation and raw state
    const [obs, rawState] = await this.getObservationAndRawState()

    if (this.returnRawInInfo) {
      info.raw_state = rawState
    }

    return [obs.state, reward, terminated, truncated, info]
  }

  async reset(hardReset = false) {
    const info = {}
    
    // If this has been randomly reset before, then restore stored start state
    if (this.layout === null && this.resetState !== null && !hardReset) {
      const [, setInfo] = await this.set(this.resetState)
      if (setInfo.error) {
        info.error = {
          message: setInfo.message,
          type: 'reset_error'
        }
      }
    } else {
      // Otherwise, proceed with server-side reset
      const resetArgs = {
        parkId: this.parkId,
        layout: this.layout !== null ? this.layout : "",
        difficulty: this.difficulty,
        starting_money: this.startingMoney,
        horizon: this.horizon
      }
      const result = await postEndpoint('park/reset', resetArgs, this.host, this.port)
      
      if (result.error) {
        info.error = {
          message: result.message,
          type: 'reset_error'
        }
        console.error(`Error resetting park: ${result.message}`)
      }
    }

    const [obs, rawState] = await this.getObservationAndRawState()

    if (this.layout === null) {
      this.resetState = rawState
    }

    this.prevMoney = rawState.state.money
    
    if (this.returnRawInInfo) {
      info.raw_state = rawState.state
    }

    if (this.renderPark) {
      this.visualizer.drawGameGrid(rawState)
    }

    return [obs, info]
  }

  parseAction(action) {
    try {
      const [actionName, actionArgs] = getActionNameAndArgs(action)
      actionArgs.parkId = this.parkId

      // Validate action type
      const actionParams = getActionParams()
      if (!actionParams[actionName]) {
        return new ParkResponse(400, `Invalid action type: ${actionName} must be in ${Object.keys(actionParams)}`, {}, true)
      }

      // Set default values for specific action types (translated from Python)
      if (actionName === "place" && "type" in actionArgs && actionArgs.type === "staff") {
        actionArgs.price = actionArgs.price || 1;
        actionArgs.order_quantity = actionArgs.order_quantity || -1;
      }
      if ((actionName === "place" || actionName === "modify") && "type" in actionArgs && actionArgs.type === "ride") {
        actionArgs.order_quantity = actionArgs.order_quantity || -1;
      }

      // Validate presence of arguments
      const actionParamsSet = new Set(Object.keys(actionArgs))
      const requiredParams = actionParams[actionName]

      if (!isSuperset(actionParamsSet, requiredParams)) {
        const missing = [...requiredParams].filter(param => !actionParamsSet.has(param))
        return new ParkResponse(400, `Invalid action: ${action} is missing the arguments ${missing}`, {}, true)
      }

      if (!isSuperset(requiredParams, actionParamsSet)) {
        const excess = [...actionParamsSet].filter(param => !requiredParams.has(param))
        return new ParkResponse(400, `Invalid action: ${action} has excess arguments ${excess}`, {}, true)
      }

      // Validate argument types
      const actionParamTypes = getActionParamTypes()
      for (const paramName of actionParamsSet) {
        if (paramName === 'parkId') continue
        
        const expectedType = actionParamTypes[paramName]
        const paramValue = actionArgs[paramName]
        
        if (expectedType) {
          let expectedTypeName = expectedType.name.toLowerCase()
          let actualTypeName = typeof paramValue
          
          // Handle array type checking specially
          if (expectedTypeName === 'array') {
            if (!Array.isArray(paramValue)) {
              return new ParkResponse(400, `Invalid action: ${action} has argument ${paramName} of type ${actualTypeName} but expected type array`, {}, true)
            }
          } else if (actualTypeName !== expectedTypeName) {
            return new ParkResponse(400, `Invalid action: ${action} has argument ${paramName} of type ${actualTypeName} but expected type ${expectedTypeName}`, {}, true)
          }
        }
      }

      return new ParkResponse(200, `Action ${action} is valid`, [actionName, actionArgs], false)
    } catch (error) {
      return new ParkResponse(400, `Error parsing action: ${error.message}`, {}, true)
    }
  }

  static isSandboxAction(action) {
    try {
      const [actionName] = getActionNameAndArgs(action)
      return SANDBOX_ACTION_NAMES.includes(actionName)
    } catch {
      return false
    }
  }

  parseSandboxAction(action) {
    try {
      const [actionName, actionArgs] = getActionNameAndArgs(action)
      actionArgs.parkId = this.parkId

      // Validate action type
      if (!SANDBOX_ACTION_NAMES.includes(actionName)) {
        return new ParkResponse(400, `Invalid sandbox action type: ${actionName} must be in ${SANDBOX_ACTION_NAMES}`, {}, true)
      }

      // Add in optional arguments in case they are not provided
      if (actionName === "change_settings") {
        actionArgs.difficulty = actionArgs.difficulty || null
        actionArgs.layout = actionArgs.layout || null
      }

      // Validate presence of arguments
      const actionParams = new Set(Object.keys(actionArgs))
      const requiredParams = SANDBOX_ACTION_PARAMS[actionName]

      if (!isSuperset(actionParams, requiredParams)) {
        const missing = [...requiredParams].filter(param => !actionParams.has(param))
        return new ParkResponse(400, `Invalid sandbox action: ${action} is missing the arguments ${missing}`, {}, true)
      }

      if (!isSuperset(requiredParams, actionParams)) {
        const excess = [...actionParams].filter(param => !requiredParams.has(param))
        return new ParkResponse(400, `Invalid sandbox action: ${action} has excess arguments ${excess}`, {}, true)
      }

      return new ParkResponse(200, `Sandbox action ${action} is valid`, [actionName, actionArgs], false)
    } catch (error) {
      return new ParkResponse(400, `Error parsing sandbox action: ${error.message}`, {}, true)
    }
  }

  async sandboxAction(action) {
    const info = {}
    const actionResult = this.parseSandboxAction(action)
    
    if (actionResult.error) {
      info.error = {
        message: actionResult.message,
        type: 'invalid_sandbox_action'
      }
      console.log("Error parsing sandbox action: ", actionResult.message)
      var actionName = null
      var actionArgs = null
    } else {
      [actionName, actionArgs] = actionResult.data
    }

    if (actionName && ['undo_day', 'max_money', 'max_research', 'set_sandbox_mode'].includes(actionName)) {
      const data = { parkId: this.parkId }
      if (actionName === "set_sandbox_mode") {
        data.sandbox_steps = actionArgs.sandbox_steps
      }
      
      const result = await postEndpoint(`park/${actionName}`, data, this.host, this.port)
      if (result.error) {
        info.error = {
          message: result.message,
          type: `${actionName}_error`
        }
      }
      
      const [obs, rawState] = await this.getObservationAndRawState()
      if (this.returnRawInInfo) {
        info.raw_state = rawState
      }
      return [obs, info]
    } else if (actionName === "reset") {
      return await this.reset(true) // hardReset = true
    } else if (actionName === "change_settings") {
      this.updateSettings(actionArgs.layout, actionArgs.difficulty)
      return await this.reset(true) // hardReset = true
    } else {
      if (!info.error) {
        info.error = {
          message: `Invalid sandbox action: ${actionName}`,
          type: 'invalid_sandbox_action'
        }
      }
      
      const [obs, rawState] = await this.getObservationAndRawState()
      if (this.returnRawInInfo) {
        info.raw_state = rawState
      }
      return [obs, info]
    }
  }

  async act(action) {
    const actionResult = this.parseAction(action)
    if (actionResult.error) {
      return actionResult
    }
    
    const [actionName, actionArgs] = actionResult.data
    const actionNameKeywords = actionName.split('_')

    // Apply action based on type
    if (actionNameKeywords[0] === 'place') {
      const objectToPlace = actionArgs.type
      if (['ride', 'shop', 'staff'].includes(objectToPlace)) {
        return await postEndpoint(objectToPlace, actionArgs, this.host, this.port)
      } else {
        return new ParkResponse(400, `Object to place must be ride, shop, or staff, got ${objectToPlace}`, {}, true)
      }
    }
    
    if (actionNameKeywords[0] === 'move' || actionNameKeywords[0] === 'modify') {
      const objectToModify = actionArgs.type
      if (['ride', 'shop', 'staff'].includes(objectToModify)) {
        return await putEndpoint(objectToModify, actionArgs, this.host, this.port)
      } else {
        return new ParkResponse(400, `Object to move must be ride, shop, or staff, got ${objectToModify}`, {}, true)
      }
    }
    
    if (actionNameKeywords[0] === 'remove' && actionNameKeywords.length === 1) {
      let objectToRemove = actionArgs.type
      if (['ride', 'shop', 'staff'].includes(objectToRemove)) {
        return await deleteEndpoint(objectToRemove, actionArgs, this.host, this.port)
      } else {
        return new ParkResponse(400, `Object to remove must be ride, shop, or staff, got ${objectToRemove}`, {}, true)
      }
    }
    
    // Special actions
    if (actionName === 'survey_guests') {
      return await postEndpoint('park/survey_guests', actionArgs, this.host, this.port)
    }
    
    if (actionName === 'set_research') {
      return await postEndpoint('park/research', actionArgs, this.host, this.port)
    }
    
    if (actionName === 'add_path') {
      return await postEndpoint('park/path', actionArgs, this.host, this.port)
    }
    
    if (actionName === 'remove_path') {
      return await deleteEndpoint('park/path', actionArgs, this.host, this.port)
    }
    
    if (actionName === 'add_water') {
      return await postEndpoint('park/water', actionArgs, this.host, this.port)
    }
    
    if (actionName === 'remove_water') {
      return await deleteEndpoint('park/water', actionArgs, this.host, this.port)
    }
    
    if (actionName === 'wait') {
      return await postEndpoint('park/noop', actionArgs, this.host, this.port)
    }
    
    return new ParkResponse(400, `Invalid action: ${action}`, {}, true)
  }

  async deletePark() {
    // Clear all data related to the current parkId.
    // Deletes the park instance from the backend server.
    const result = await deleteParkEndpoint(this.parkId, this.host, this.port)
    if (result.error) {
      console.error(`ERROR clearing park: ${result.message}`)
    } else {
      console.log(`Successfully cleared park ${this.parkId}`)
    }
    return result.data
  }

  async saveTrajectory(mode = "few-shot", username = "anon", saveLocal = false, saveToCloud = false) {
    const data = {
      parkId: this.parkId,
      mode: mode,
      saveLocal: saveLocal,
      saveToCloud: saveToCloud,
      username: username || "anon"
    }
    const result = await postEndpoint('leaderboard/', data, this.host, this.port)
    if (result.error) {
      console.error("ERROR: ", result.message)
      return result
    } else {
      console.log("Successfully saved trajectory to leaderboard: ", result.message)
    }
    return result.data
  }
}

export async function createMiniAmusementPark(options = {}) {
  const map = new MiniAmusementPark(options)
  await map.initializeParkId()
  await map.setSeed()
  return map
}

export default MiniAmusementPark
