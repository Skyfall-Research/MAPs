import { MiniAmusementPark, createMiniAmusementPark } from '../map_js/MiniAmusementPark.js'

async function testInitialization() {
  const map = new MiniAmusementPark({
    host: 'localhost',
    port: '3000',
    difficulty: 'easy',
    observationType: 'pydantic',
    agentName: 'test_agent',
    expName: 'test_experiment'
  })
  
  console.assert(map.difficulty === 'easy', '❌ Difficulty should be easy')
  console.assert(map.startingMoney === 500, '❌ Starting money should be 500')
  console.assert(map.horizon === 50, '❌ Horizon should be 50')
  console.assert(JSON.stringify(map.guestPreferences) === JSON.stringify(['no preferences']), '❌ Guest preferences should be no preferences')
  
  return map
}

async function testSettingsUpdate(map) {
  // Update settings
  map.updateSettings('hard', null, 1000, 300, [['thrill_seeker'], ['family_friendly']])
  
  console.assert(map.difficulty === 'hard', '❌ Difficulty should be hard')
  console.assert(map.startingMoney === 1000, '❌ Starting money should be 1000')
  console.assert(map.horizon === 300, '❌ Horizon should be 300')
  const actual = JSON.stringify(map.guestPreferences)
  const expected = JSON.stringify([['thrill_seeker'], ['family_friendly']])
  console.assert(actual === expected, '❌ Guest preferences should be thrill_seeker and family_friendly')
}

async function testScenarioLoading(map) {
  const scenarioData = {
    difficulty: 'medium',
    layout: [
      [0, 0, 1, 1, 0],
      [0, 1, 2, 1, 0],
      [1, 1, 1, 1, 1],
      [0, 1, 1, 1, 0],
      [0, 0, 1, 0, 0]
    ],
    starting_money: 750,
    horizon: 150,
    preferences: [
      ['thrill_seeker', 'adventure_lover'],
      ['family_friendly', 'child_safe']
    ]
  }
  
  map.loadScenario(scenarioData, 0)
  
  console.assert(map.difficulty === 'medium', '❌ Difficulty should be medium')
  console.assert(map.startingMoney === 750, '❌ Starting money should be 750')
  console.assert(map.horizon === 150, '❌ Horizon should be 150')
  console.assert(JSON.stringify(map.guestPreferences) === JSON.stringify(['thrill_seeker', 'adventure_lover']), '❌ Guest preferences should be thrill_seeker,adventure_lover')
}

async function testActionParsing(map) {
  // Wait for config to load
  await new Promise(resolve => setTimeout(resolve, 100));
  
  const testActions = [
    "place(x=5, y=5, type='ride', subtype='roller_coaster', subclass='red', price=10, quantity=0)",
    "place(x=3, y=3, type='shop', subtype='food', subclass='blue', price=5, quantity=100)",
    "place(x=1, y=1, type='staff', subtype='janitor', subclass='yellow', price=0, quantity=0)",
    "move(type='ride', subtype='roller_coaster', subclass='red', x=5, y=5, new_x=6, new_y=6)",
    "modify(type='ride', x=5, y=5, price=15, quantity=0)",
    "remove(type='shop', subtype='drink', subclass='red', x=5, y=5)",
    "remove(type='staff', subtype='janitor', subclass='yellow', x=1, y=1)",
    "survey_guests(num_guests=5)",
    "set_research(research_speed='medium', research_topics=['roller_coaster', 'food'])",
    "add_path(x=2, y=2)",
    "remove_path(x=2, y=2)",
    "add_water(x=4, y=4)",
    "remove_water(x=4, y=4)",
    "wait()"
  ]
  
  for (const action of testActions) {
    const result = map.parseAction(action)
    console.assert(!result.error, '❌ Action parsing should not error')
  }
}

async function testInvalidActions(map) {
  // Wait for config to load
  await new Promise(resolve => setTimeout(resolve, 100));
  
  const invalidActions = [
    "invalid_action()",
    "place(x=5)", // Missing required parameters
    "place(x=5, y=5, type='ride', subtype='roller_coaster', extra_param=123)", // Extra parameter
    "place(x='invalid', y=5, type='ride', subtype='roller_coaster')", // Wrong type
    "move()", // Missing all parameters
    "place(type='invalid_type', x=1, y=1)", // Invalid entity type
    "set_research(research_speed='invalid_speed')", // Invalid research speed
  ]
  
  for (const action of invalidActions) {
    const result = map.parseAction(action)
    console.assert(result.error, '❌ Action parsing should error')
  }
}

async function testHttpClient() {
  const map = new MiniAmusementPark({
    host: 'localhost',
    port: '3000'
  })
  
  // Test HTTP client methods (these would fail without a real server)
  console.assert(map.httpClient.baseUrl === 'http://localhost:3000', '❌ HTTP Client base URL should be http://localhost:3000')
}

async function testFactoryFunction() {
  const map = createMiniAmusementPark({
    difficulty: 'hard',
    observationType: 'raw'
  })
  
  console.assert(map.difficulty === 'hard', '❌ Difficulty should be hard')
  console.assert(map.observationType === 'raw', '❌ Observation type should be raw')
}

async function runAllTests() {
  try {
    console.log('MiniAmusementPark JavaScript Tests')
    
    const map = await testInitialization()
    await testSettingsUpdate(map)
    await testScenarioLoading(map)
    await testActionParsing(map)
    await testInvalidActions(map)
    await testHttpClient()
    await testSharedActionSpec()
    await testFactoryFunction()
    
    console.log('🎉 All tests completed successfully!')
    
  } catch (error) {
    console.error('❌ Test failed:', error.message)
    console.error(error.stack)
  }
}

async function testSharedActionSpec() {
  // Test that we can import the shared config
  const { ACTION_PARAMS, ACTION_PARAM_TYPES } = await import('../map_backend/config.js')
  
  console.assert(Object.keys(ACTION_PARAMS).length > 0, '❌ ACTION_PARAMS should not be empty')
  console.assert(Object.keys(ACTION_PARAM_TYPES).length > 0, '❌ ACTION_PARAM_TYPES should not be empty')

  for (const action of Object.keys(ACTION_PARAMS)) {
    if (ACTION_PARAMS[action]) {
      console.assert(ACTION_PARAMS[action].size > 0, '❌ ACTION_PARAMS should not be empty')
    }
  }
}

async function exampleWithRealServer() {
  console.log('\n=== Example: Real Server Usage ===')
  console.log('Note: This requires a running Node.js backend server')
  
  const map = new MiniAmusementPark({
    host: 'localhost',
    port: '3000',
    difficulty: 'easy',
    observationType: 'pydantic'
  })
  
  try {
    // Initialize park ID
    console.log('Initializing park ID...')
    await map.initializeParkId()
    console.log('✅ Park ID initialized:', map.parkId)
    
    // Reset the environment
    console.log('Resetting environment...')
    const [obs, info] = await map.reset()
    console.log('✅ Environment reset:', Object.keys(obs))
    
    // Perform some actions
    console.log('Placing an attraction...')
    const actionResult = await map.act("place_attraction(x=5, y=5, type='ride', subtype='roller_coaster', subclass='red', price=10)")
    console.log('Action result:', actionResult.error ? '❌' : '✅', actionResult.message)
    
    // Step the environment
    console.log('Stepping environment...')
    const [observation, reward, terminated, truncated, stepInfo] = await map.step("wait()")
    console.log('Step completed:', { reward, terminated, truncated })
    
  } catch (error) {
    console.log('❌ Server communication failed (expected if server not running):', error.message)
  }
}

// Export for use in other modules
export {
  testInitialization,
  testSettingsUpdate,
  testScenarioLoading,
  testActionParsing,
  testInvalidActions,
  testHttpClient,
  testSharedActionSpec,
  testFactoryFunction,
  runAllTests,
  exampleWithRealServer
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runAllTests()
}
