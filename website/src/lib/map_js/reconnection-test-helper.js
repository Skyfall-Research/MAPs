/**
 * WebSocket Reconnection Test Helper
 *
 * Usage: Paste this entire script into browser console while game is running
 * Then run: startReconnectionTest()
 */

window.reconnectionTestHelper = {
    // Test 1: Simple disconnect and wait for auto-reconnect
    async testAutoReconnect() {
        console.log('🧪 TEST: Auto Reconnect');
        console.log('1. Disconnecting...');

        // Find the game instance (adjust selector if needed)
        const game = window.game || this.findGameInstance();
        if (!game?.scene?.scenes[0]?.gameStateListener?.sio) {
            console.error('❌ Cannot find game socket. Is game running?');
            return;
        }

        const socket = game.scene.scenes[0].gameStateListener.sio;

        socket.disconnect();
        console.log('2. Disconnected. Waiting 10 seconds for auto-reconnect...');

        await this.sleep(10000);

        if (socket.connected) {
            console.log('✅ SUCCESS: Socket auto-reconnected');
        } else {
            console.log('❌ FAIL: Socket did not reconnect');
        }
    },

    // Test 2: Disconnect during simulation
    async testDisconnectDuringSimulation() {
        console.log('🧪 TEST: Disconnect During Simulation');
        console.log('Make sure game is in RUNNING_SIMULATION state!');

        const game = window.game || this.findGameInstance();
        if (!game?.scene?.scenes[0]) {
            console.error('❌ Cannot find game instance');
            return;
        }

        const gui = game.scene.scenes[0];
        console.log('Current game mode:', gui.visualizer?.gameMode);

        console.log('1. Disconnecting socket...');
        gui.gameStateListener.sio.disconnect();

        await this.sleep(5000);

        console.log('2. Reconnecting...');
        gui.gameStateListener.sio.connect();

        await this.sleep(5000);

        console.log('3. Final game mode:', gui.visualizer?.gameMode);
        console.log('Expected: WAITING_FOR_INPUT');
    },

    // Test 3: Stress test - multiple rapid reconnects
    async testRapidReconnects(count = 5) {
        console.log(`🧪 TEST: Rapid Reconnects (${count}x)`);

        const game = window.game || this.findGameInstance();
        const socket = game?.scene?.scenes[0]?.gameStateListener?.sio;

        if (!socket) {
            console.error('❌ Cannot find socket');
            return;
        }

        for (let i = 1; i <= count; i++) {
            console.log(`${i}. Disconnect`);
            socket.disconnect();
            await this.sleep(2000);

            console.log(`${i}. Reconnect`);
            socket.connect();
            await this.sleep(2000);
        }

        console.log('✅ Rapid reconnect test complete');
        console.log('Check console for any errors');
    },

    // Monitor connection state
    monitorConnection(duration = 60000) {
        console.log(`🔍 Monitoring connection for ${duration/1000} seconds...`);

        const game = window.game || this.findGameInstance();
        const socket = game?.scene?.scenes[0]?.gameStateListener?.sio;

        if (!socket) {
            console.error('❌ Cannot find socket');
            return;
        }

        const startTime = Date.now();
        let disconnectCount = 0;
        let reconnectCount = 0;

        const disconnectHandler = (reason) => {
            disconnectCount++;
            console.log(`⚠️  Disconnect ${disconnectCount}: ${reason} at ${new Date().toISOString()}`);
        };

        const connectHandler = () => {
            reconnectCount++;
            console.log(`✅ Connect ${reconnectCount} at ${new Date().toISOString()}`);
        };

        socket.on('disconnect', disconnectHandler);
        socket.on('connect', connectHandler);

        setTimeout(() => {
            socket.off('disconnect', disconnectHandler);
            socket.off('connect', connectHandler);

            console.log('\n📊 MONITORING RESULTS:');
            console.log(`Duration: ${(Date.now() - startTime)/1000}s`);
            console.log(`Disconnects: ${disconnectCount}`);
            console.log(`Reconnects: ${reconnectCount}`);
            console.log(`Final state: ${socket.connected ? '🟢 Connected' : '🔴 Disconnected'}`);
        }, duration);
    },

    // Check reconnection configuration
    checkConfig() {
        console.log('🔧 Checking reconnection configuration...\n');

        const game = window.game || this.findGameInstance();
        const socket = game?.scene?.scenes[0]?.gameStateListener?.sio;

        if (!socket) {
            console.error('❌ Cannot find socket');
            return;
        }

        console.log('Socket.IO Configuration:');
        console.log('Connected:', socket.connected);
        console.log('Reconnection enabled:', socket.io._reconnection);
        console.log('Reconnection attempts:', socket.io._reconnectionAttempts);
        console.log('Reconnection delay:', socket.io._reconnectionDelay);
        console.log('Reconnection delay max:', socket.io._reconnectionDelayMax);
        console.log('\nCallbacks configured:', {
            onDisconnect: !!game.scene.scenes[0].gameStateListener.onDisconnect,
            onReconnect: !!game.scene.scenes[0].gameStateListener.onReconnect,
            onReconnectAttempt: !!game.scene.scenes[0].gameStateListener.onReconnectAttempt,
            onReconnectFailed: !!game.scene.scenes[0].gameStateListener.onReconnectFailed,
        });
    },

    // Helper: Find game instance
    findGameInstance() {
        // Try common locations
        if (window.game) return window.game;

        // Try Phaser global
        if (window.Phaser?.GAMES?.[0]) return window.Phaser.GAMES[0];

        console.error('❌ Cannot find game instance. Try: window.game = <your_game_instance>');
        return null;
    },

    // Helper: Sleep
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    // Run all tests
    async runAllTests() {
        console.log('🚀 Running all reconnection tests...\n');

        await this.testAutoReconnect();
        await this.sleep(5000);

        await this.testRapidReconnects(3);
        await this.sleep(5000);

        console.log('\n✅ All automated tests complete!');
        console.log('Check console output for any failures');
    }
};

// Shortcuts
window.startReconnectionTest = () => window.reconnectionTestHelper.runAllTests();
window.monitorConnection = (seconds = 60) => window.reconnectionTestHelper.monitorConnection(seconds * 1000);
window.checkSocketConfig = () => window.reconnectionTestHelper.checkConfig();

console.log('✅ Reconnection Test Helper loaded!');
console.log('\nAvailable commands:');
console.log('  startReconnectionTest()  - Run all automated tests');
console.log('  monitorConnection(60)    - Monitor connection for 60 seconds');
console.log('  checkSocketConfig()      - View current socket configuration');
console.log('\nIndividual tests:');
console.log('  reconnectionTestHelper.testAutoReconnect()');
console.log('  reconnectionTestHelper.testRapidReconnects(5)');
console.log('  reconnectionTestHelper.testDisconnectDuringSimulation()');
