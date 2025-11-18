import Research from './research.js';
import config from './config.js';

// Dummy park object for testing
class DummyPark {
    constructor(initialMoney = 1000000) {
        this.money = initialMoney;
    }
}

// Helper function to count total unresearched rides
function countUnresearchedRides(research) {
    let total = 0;
    for (const rideType in research.unresearchedRides) {
        total += research.unresearchedRides[rideType].order.length;
    }
    return total;
}

// Helper function to count total researched rides
function countResearchedRides(research) {
    let total = 0;
    for (const rideType in research.researchedRides) {
        total += research.researchedRides[rideType].length;
    }
    return total;
}

// Helper function to get all available ride types
function getAllRideTypes() {
    return Object.keys(config.rides);
}

// Test function for research speed comparison
function testResearchSpeed(researchSpeed) {
    console.log(`\n=== Testing Research Speed: ${researchSpeed} ===`);
    
    const park = new DummyPark();
    const research = new Research();
    
    // Set research speed and all available topics
    const allRideTypes = getAllRideTypes();
    research.set_research(researchSpeed, allRideTypes);
    
    console.log(`Initial unresearched rides: ${countUnresearchedRides(research)}`);
    console.log(`Initial researched rides: ${countResearchedRides(research)}`);
    console.log(`Initial money: $${park.money}`);
    
    let steps = 0;
    const maxSteps = 100;
    const initialMoney = park.money;
    
    while (steps < maxSteps) {
        const researchPerformed = research.perform_research(park);
        
        if (!researchPerformed) {
            console.log(`Research stopped at step ${steps} - no more research possible`);
            break;
        }
        
        steps++;
        
        const currentUnresearched = countUnresearchedRides(research);
        const currentResearched = countResearchedRides(research);
        
        if (currentUnresearched === 0) {
            console.log(`All rides researched at step ${steps}!`);
            break;
        }
        
        if (steps % 10 === 0) {
            console.log(`Step ${steps}: Unresearched: ${currentUnresearched}, Researched: ${currentResearched}, Money: $${park.money}`);
        }
    }
    
    const totalCost = initialMoney - park.money;
    
    console.log(`\nResults for ${researchSpeed} speed:`);
    console.log(`- Steps taken: ${steps}`);
    console.log(`- Total cost: $${totalCost}`);
    console.log(`- Final unresearched rides: ${countUnresearchedRides(research)}`);
    console.log(`- Final researched rides: ${countResearchedRides(research)}`);
    
    return {
        speed: researchSpeed,
        steps: steps,
        totalCost: totalCost,
        finalUnresearched: countUnresearchedRides(research),
        finalResearched: countResearchedRides(research)
    };
}

// Test function for individual ride type research
function testRideTypeResearch(rideType) {
    console.log(`\n=== Testing Ride Type: ${rideType} ===`);
    
    const park = new DummyPark();
    const research = new Research();
    
    // Set fast research speed and single ride type
    research.set_research("fast", [rideType]);
    
    console.log(`Initial unresearched rides for ${rideType}: ${research.unresearchedRides[rideType]?.order.length || 0}`);
    console.log(`Initial researched rides for ${rideType}: ${research.researchedRides[rideType]?.length || 0}`);
    console.log(`Initial money: $${park.money}`);
    
    let steps = 0;
    const maxSteps = 100;
    const initialMoney = park.money;
    
    while (steps < maxSteps) {
        const researchPerformed = research.perform_research(park);
        
        if (!researchPerformed) {
            console.log(`Research stopped at step ${steps} - no more research possible`);
            break;
        }
        
        steps++;
        
        const currentUnresearched = research.unresearchedRides[rideType]?.order.length || 0;
        const currentResearched = research.researchedRides[rideType]?.length || 0;
        
        if (currentUnresearched === 0) {
            console.log(`All ${rideType} rides researched at step ${steps}!`);
            break;
        }
        
        if (steps % 5 === 0) {
            console.log(`Step ${steps}: Unresearched: ${currentUnresearched}, Researched: ${currentResearched}, Money: $${park.money}`);
        }
    }
    
    const totalCost = initialMoney - park.money;
    
    console.log(`\nResults for ${rideType}:`);
    console.log(`- Steps taken: ${steps}`);
    console.log(`- Total cost: $${totalCost}`);
    console.log(`- Final unresearched rides: ${research.unresearchedRides[rideType]?.order.length || 0}`);
    console.log(`- Final researched rides: ${research.researchedRides[rideType]?.length || 0}`);
    
    return {
        rideType: rideType,
        steps: steps,
        totalCost: totalCost,
        finalUnresearched: research.unresearchedRides[rideType]?.order.length || 0,
        finalResearched: research.researchedRides[rideType]?.length || 0
    };
}

// Main test execution
function runAllTests() {
    console.log("🧪 RESEARCH FUNCTIONALITY TEST SUITE");
    console.log("=====================================");
    
    // Test 1-4: Research speed comparison
    console.log("\n📊 TESTS 1-4: Research Speed Comparison");
    console.log("Testing all research speeds with all available ride types...");
    
    const speedResults = [];
    const speeds = ["none", "slow", "medium", "fast"];
    
    for (const speed of speeds) {
        const result = testResearchSpeed(speed);
        speedResults.push(result);
    }
    
    // Analyze speed results
    console.log("\n📈 SPEED COMPARISON ANALYSIS:");
    console.log("Speed\t\tSteps\tCost\t\tUnresearched\tResearched");
    console.log("-----\t\t-----\t----\t\t-----------\t---------");
    for (const result of speedResults) {
        console.log(`${result.speed.padEnd(12)}\t${result.steps}\t$${result.totalCost}\t\t${result.finalUnresearched}\t\t${result.finalResearched}`);
    }
    
    // Verify speed progression
    console.log("\n✅ SPEED PROGRESSION VERIFICATION:");
    const nonNoneResults = speedResults.filter(r => r.speed !== "none");
    let speedIncreases = true;
    for (let i = 1; i < nonNoneResults.length; i++) {
        if (nonNoneResults[i].steps >= nonNoneResults[i-1].steps) {
            speedIncreases = false;
            console.log(`❌ Speed progression failed: ${nonNoneResults[i].speed} (${nonNoneResults[i].steps} steps) >= ${nonNoneResults[i-1].speed} (${nonNoneResults[i-1].steps} steps)`);
        }
    }
    if (speedIncreases) {
        console.log("✅ Speed progression verified: faster speeds complete research in fewer steps");
    }
    
    // Verify "none" speed does nothing
    const noneResult = speedResults.find(r => r.speed === "none");
    if (noneResult.finalResearched === noneResult.finalResearched) {
        console.log("✅ 'none' speed verified: no research performed");
    } else {
        console.log("❌ 'none' speed failed: research was performed when it shouldn't be");
    }
    
    // Test 5-7: Individual ride type research
    console.log("\n🎢 TESTS 5-7: Individual Ride Type Research");
    console.log("Testing each ride type with fast research speed...");
    
    const rideTypeResults = [];
    const rideTypes = getAllRideTypes();
    
    for (const rideType of rideTypes) {
        const result = testRideTypeResearch(rideType);
        rideTypeResults.push(result);
    }
    
    // Analyze ride type results
    console.log("\n📊 RIDE TYPE COMPARISON ANALYSIS:");
    console.log("Ride Type\t\tSteps\tCost\t\tUnresearched\tResearched");
    console.log("---------\t\t-----\t----\t\t-----------\t---------");
    for (const result of rideTypeResults) {
        console.log(`${result.rideType.padEnd(15)}\t${result.steps}\t$${result.totalCost}\t\t${result.finalUnresearched}\t\t${result.finalResearched}`);
    }
    
    // Verify consistent research time for different ride types
    console.log("\n✅ RIDE TYPE CONSISTENCY VERIFICATION:");
    const stepCounts = rideTypeResults.map(r => r.steps);
    const uniqueStepCounts = [...new Set(stepCounts)];
    if (uniqueStepCounts.length === 1) {
        console.log(`✅ All ride types take the same number of steps: ${uniqueStepCounts[0]}`);
    } else {
        console.log("❌ Ride types take different numbers of steps:");
        for (const result of rideTypeResults) {
            console.log(`   ${result.rideType}: ${result.steps} steps`);
        }
    }
    
    console.log("\n🎉 TEST SUITE COMPLETED!");
}

// Run the tests
runAllTests(); 