import { io } from 'socket.io-client'

/**
 * Queue class equivalent to Python deque-based queue
 */
export class Queue {
  constructor() {
    this._items = []
  }

  enqueue(item) {
    this._items.push(item)
  }

  dequeue() {
    if (this.is_empty()) {
      throw new Error("dequeue from an empty queue")
    }
    return this._items.shift()
  }

  peek() {
    if (this.is_empty()) {
      return {}
    }
    return this._items[0]
  }

  is_empty() {
    return this._items.length === 0
  }

  size() {
    return this._items.length
  }

  clear() {
    this._items = []
  }

  toString() {
    return `Queue(${JSON.stringify(this._items)})`
  }
}

/**
 * GameStateListener class - JavaScript equivalent of Python GameStateListener
 */
export class GameStateListener {
  constructor(buffer, parkId, accept_midday_updates = false, callbacks = {}) {
    this.sio = null
    this.accept_midday_updates = accept_midday_updates

    // Step and buffer management
    this.buffer = buffer
    this.num_updates = 0
    this.parkId = parkId

    // Callbacks for GUI notifications
    this.onDisconnect = callbacks.onDisconnect || (() => {})
    this.onReconnect = callbacks.onReconnect || (() => {})
    this.onReconnectAttempt = callbacks.onReconnectAttempt || (() => {})
    this.onReconnectError = callbacks.onReconnectError || (() => {})
    this.onReconnectFailed = callbacks.onReconnectFailed || (() => {})

    // Track if we were previously connected (for reconnection detection)
    this.wasConnected = false
  }

  startSocketioListener(server = null) {
    // Use environment variable if server not provided
    if (!server) {
      // Detect environment based on hostname
      // If localhost, use localhost:3000, otherwise use relative path (empty string)
      const isLocal = typeof window !== 'undefined' &&
                     (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
      server = isLocal ? 'http://localhost:3000' : '';
    }
    return new Promise((resolve, reject) => {
      try {
        // Development-only test mode: Use shorter timeouts to trigger disconnections faster
        const isDevelopment = server.includes('localhost') || server.includes('127.0.0.1');
        const testMode = false; // DEBUG: Set to true to test reconnection with aggressive 5s/3s timeouts

        this.sio = io(server, {
          transports: ['websocket', 'polling'],
          reconnection: true,
          reconnectionAttempts: 25,  // ~5 minutes with backoff
          reconnectionDelay: 1000,   // Start at 1 second
          reconnectionDelayMax: 10000,  // Max 10 seconds between attempts
          timeout: 10000,  // 10 second connection timeout (increased from default 20s)
          // In test mode, use very short intervals to trigger disconnection quickly
          pingInterval: (isDevelopment && testMode) ? 5000 : 60000,  // 5s (test) or 60s (prod)
          pingTimeout: (isDevelopment && testMode) ? 3000 : 30000    // 3s (test) or 30s (prod)
        })

        // Connection event handlers
        this.sio.on('connect', () => {
          console.log('[SocketIO] Connected to server')

          // If this is a reconnection (not initial connection), handle state recovery
          if (this.wasConnected) {
            console.log('[SocketIO] Reconnected after disconnection')
            this.onReconnect()
          }

          this.wasConnected = true
          resolve()
        })

        this.sio.on('disconnect', (reason) => {
          console.warn('[SocketIO] Disconnected:', reason)
          this.onDisconnect(reason)

          // If server initiated disconnect, manually reconnect
          if (reason === 'io server disconnect') {
            this.sio.connect()
          }
        })

        this.sio.on('connect_error', (error) => {
          // Only reject on initial connection error
          // After that, reconnection errors are handled separately
          if (!this.wasConnected) {
            reject(error)
          }
        })

        // Reconnection event handlers
        this.sio.on('reconnect_attempt', (attemptNumber) => {
          console.log(`[SocketIO] Reconnection attempt ${attemptNumber}`)
          this.onReconnectAttempt(attemptNumber)
        })

        this.sio.on('reconnect_error', (error) => {
          console.error('[SocketIO] Reconnection error:', error)
          this.onReconnectError(error)
        })

        this.sio.on('reconnect_failed', () => {
          console.error('[SocketIO] Reconnection failed after maximum attempts')
          this.onReconnectFailed()
        })

        // Add timeout
        setTimeout(() => {
          if (!this.sio.connected) {
            reject(new Error("Connection timeout"));
          }
        }, 5000);

        // Game event handlers
        this.sio.on('action', (data) => {
          console.log("[SocketIO] Action received:", data)
        })

        this.sio.on('game_update', (data) => {
          this.handleGameUpdate(data)
        })

      } catch (error) {
        console.error("[SocketIO] Failed to initialize:", error)
        reject(error)
      }
    })
  }

  handleGameUpdate(data) {
    const stateType = data.state_type;
    if (data.data.state.parkId !== this.parkId) {
      // console.log("Park ID mismatch:", data.data.state.parkId, "!=", this.parkId)
      return;
    }
    if (['full_state', 'day_start', 'day_end'].includes(stateType)) {
      const staffList = data.data.staff
      data.data.staff = {'staff_list': staffList}
      this.buffer.enqueue({ [stateType]: data.data })
      
    } else if (stateType === 'mid_day' && this.accept_midday_updates) {
      this.num_updates += 1
      data.data.staff = {'staff_list': data.data.staff}
      this.buffer.enqueue({ 'mid_day': data.data })
      
    } else if (stateType === 'exit_time' && this.accept_midday_updates) {
      this.buffer.enqueue({ 'exit_time': data.data })
    }
  }

  setAcceptMiddayUpdates(accept) {
    this.accept_midday_updates = accept
  }

  getNumUpdates() {
    return this.num_updates
  }

  disconnect() {
    if (this.sio) {
      this.sio.disconnect()
      this.sio = null
    }
  }

  isConnected() {
    return this.sio && this.sio.connected
  }

  emitAction(action) {
    if (this.sio && this.sio.connected) {
      this.sio.emit('action', action)
    } else {
      console.log("[SocketIO] Not connected to server, cannot emit action")
    }
  }
}

export function createGameStateListener(parkId) {
  const buffer = new Queue()
  return new GameStateListener(buffer, parkId)
}

// Export for use in other modules
export default {
  Queue,
  GameStateListener,
  createGameStateListener
}