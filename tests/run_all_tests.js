#!/usr/bin/env node

import { runAllTests as runClickHandlerTests } from './test_click_handler.js'
import { runAllTests as runMiniAmusementParkTests } from './test_mini_amusement_park.js'
import { runAllTests as runGameStateListenerTests } from './test_game_state_listener.js'

async function runAllTests() {
  console.log('🧪 Running All JavaScript Tests\n')
  
  try {
    console.log('='.repeat(50))
    console.log('Testing ClickHandler...')
    console.log('='.repeat(50))
    await runClickHandlerTests()
    
    console.log('\n' + '='.repeat(50))
    console.log('Testing MiniAmusementPark...')
    console.log('='.repeat(50))
    await runMiniAmusementParkTests()
    
    console.log('\n' + '='.repeat(50))
    console.log('Testing GameStateListener...')
    console.log('='.repeat(50))
    await runGameStateListenerTests()
    
    console.log('\n🎉 All test suites completed successfully!')
    
  } catch (error) {
    console.error('❌ Test suite failed:', error.message)
    console.error(error.stack)
    process.exit(1)
  }
}

// Run all tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runAllTests()
}

export { runAllTests }
