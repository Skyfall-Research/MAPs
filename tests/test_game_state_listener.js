import { Queue, GameStateListener, createGameStateListener } from '../map_js/gui/GameStateListener.js'

async function testQueue() {
  const queue = new Queue()
  
  // Test initial state
  console.assert(queue !== null, 'Queue created')
  console.assert(queue.size() === 0, '❌ Queue should be empty')
  console.assert(queue.is_empty(), '❌ Queue should be empty')

  queue.enqueue({ test: 'data1' })
  queue.enqueue({ test: 'data2' })
  queue.enqueue({ test: 'data3' })
  
  console.assert(queue.size() === 3, '❌ Queue size != 3')
  console.assert(queue.is_empty() === false, '❌ Queue should not be empty')
  
  // Test peek
  const peeked = queue.peek()
  console.assert(peeked.test === 'data1', '❌ Peeked item should be { test: "data1" }')
  
  // Test dequeue
  const item1 = queue.dequeue()
  const item2 = queue.dequeue()
  
  console.assert(item1.test === 'data1', '❌ Item 1 should be { test: "data1" }')
  console.assert(item2.test === 'data2', '❌ Item 2 should be { test: "data2" }')
  console.assert(queue.size() === 1, '❌ Queue size != 1')

  queue.clear()
  console.assert(queue.is_empty(), '❌ Queue should be empty')
  console.assert(queue.size() === 0, '❌ Queue size != 0')

  try {
    queue.dequeue()
  } catch (error) {
    // error cought
  }
  
  return queue
}

async function testGameStateListenerInit() {
  const buffer = new Queue()
  const listener = new GameStateListener(buffer, "abcd1234")
  
  console.assert(listener !== null, '❌ GameStateListener should be created')
  console.assert(listener.accept_midday_updates === false, '❌ Accept midday updates should be false')
  console.assert(listener.getNumUpdates() === 0, '❌ Number of updates should be 0')
  console.assert(!listener.isConnected(), '❌ Is connected should be null')
  
  listener.setAcceptMiddayUpdates(true)
  console.assert(listener.accept_midday_updates === true, '❌ Accept midday updates should be true')
  
  return listener
}

async function testFactoryFunction() {
  const listener = createGameStateListener("abcd1234")

  console.assert(listener !== null, '❌ Factory function created listener failed')
  console.assert(listener.buffer.constructor.name === 'Queue', '❌ Buffer type should be Queue')
  console.assert(listener.buffer.is_empty(), '❌ Buffer should be empty')
  
  return listener
}

async function testGameUpdateHandling() {
  const listener = createGameStateListener("abcd1234")
  listener.setAcceptMiddayUpdates(true)
  
  // Mock game update data
  const mockFullStateData = {
    state_type: 'full_state',
    data: {
      state: { step: 1, guests: 10, revenue: 100, parkId: "abcd1234" },
      grid: [[{ type: 'path' }, { type: 'empty' }]],
      guests: [{ id: 1, x: 5, y: 5 }],
      staff: [
        { id: 1, type: 'janitor', x: 1, y: 1 },
        { id: 2, type: 'mechanic', x: 2, y: 2 }
      ],
      rides: [],
      shops: [],
      auditLog: []
    }
  }
  
  const mockMidDayData = {
    state_type: 'mid_day',
    data: {
      state: { parkId: "abcd1234" },
      guests: [{ id: 1, x: 6, y: 6 }],
      staff: {
        janitors: [{ id: 1, x: 1, y: 1 }],
        mechanics: [{ id: 2, x: 2, y: 2 }]
      }
    }
  }
  
  // Test full state handling
  listener.handleGameUpdate(mockFullStateData)
  console.assert(listener.buffer.size() === 1, '❌ Buffer size != 1')
  
  // Test midday update handling
  listener.handleGameUpdate(mockMidDayData)
  console.assert(listener.buffer.size() === 2, '❌ Buffer size != 2')
  console.assert(listener.getNumUpdates() === 1, '❌ Number of updates != 1')
  
  // Test dequeue
  const update1 = listener.buffer.dequeue()
  const update2 = listener.buffer.dequeue()
  
  console.assert(Object.keys(update1).length === 1, '❌ Update 1 keys != 1')
  console.assert(Object.keys(update1)[0] === 'full_state', '❌ Update 1 key != full_state')
  console.assert(Object.keys(update2).length === 1, '❌ Update 2 keys != 1')
  console.assert(Object.keys(update2)[0] === 'mid_day', '❌ Update 2 key != mid_day')
  console.assert(listener.buffer.size() === 0, '❌ Buffer size != 0')
  
  return listener
}

async function testErrorHandling() {
  const listener = createGameStateListener("abcd1234")
  
  // Test invalid game update data
  const invalidData = {
    state_type: 'invalid_type',
    data: null
  }
  
  // This should not throw an error
  listener.handleGameUpdate(invalidData)
  
  // Test empty buffer peek
  const peeked = listener.buffer.peek()
  console.assert(Object.keys(peeked).length === 0, '❌ Empty buffer peek should return empty object')
  
  return listener
}

async function runAllTests() {
  try {
    console.log('GameStateListener JavaScript Tests')

    await testQueue()
    await testGameStateListenerInit()
    await testFactoryFunction()
    await testGameUpdateHandling()
    await testErrorHandling()

    console.log('🎉 All tests completed successfully!')

  } catch (error) {
    console.error('❌ Test failed:', error.message)
    console.error(error.stack)
  }
}

async function testRealConnection() {
  console.log('Note: This requires a running Node.js backend server')
  console.log('Starting connection test...')
  
  const listener = createGameStateListener("abcd1234")
  
  try {
    await listener.startSocketioListener("http://localhost:3000")
    console.log('✅ Successfully connected to server!')
    
    // Wait a bit for potential updates
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    console.log('Buffer size:', listener.buffer.size())
    console.log('Number of updates:', listener.getNumUpdates())
    
    listener.disconnect()
    console.log('✅ Disconnected from server')
    
  } catch (error) {
    console.log('❌ Server connection failed (expected if server not running):', error.message)
  }
}

// Export for use in other modules
export {
  testQueue,
  testGameStateListenerInit,
  testFactoryFunction,
  testGameUpdateHandling,
  testErrorHandling,
  runAllTests,
  testRealConnection
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runAllTests()
}
