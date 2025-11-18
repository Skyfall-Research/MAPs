# WebSocket Reconnection Testing Guide

## Quick Test Scenarios

### ✅ Test 1: Manual Disconnect/Reconnect (30 seconds)
**Goal:** Verify automatic reconnection works

1. Start game and get to WAITING_FOR_INPUT state
2. Press **Ctrl+Shift+D** to disconnect
3. Observe:
   - ✓ Error message appears: "Connection lost. Reconnecting..."
   - ✓ Reconnection attempts shown: "Reconnecting... (attempt 1/25)"
4. Wait 5-10 seconds
5. Press **Ctrl+Shift+R** to force reconnect
6. Observe:
   - ✓ "Connection restored!" notification appears
   - ✓ Game state is correctly displayed
   - ✓ Game is in WAITING_FOR_INPUT mode
   - ✓ No data loss

**Pass criteria:** All checkmarks verified

---

### ✅ Test 2: Disconnect During Simulation (60 seconds)
**Goal:** Verify state recovery when simulation is running

1. Start game and begin a day simulation (RUNNING_SIMULATION)
2. While animation is playing, press **Ctrl+Shift+D**
3. Observe:
   - ✓ Error message appears
   - ✓ Animation may pause/freeze
4. Wait for automatic reconnection (~5-10 seconds)
5. Observe after reconnection:
   - ✓ Game state is fetched from backend
   - ✓ Game mode changes to WAITING_FOR_INPUT
   - ✓ Display shows current state (not stale animation)
   - ✓ Buffer is cleared (no duplicate animations)

**Pass criteria:** Game recovers to correct state, no duplicate animations

---

### ✅ Test 3: Browser Offline Mode (45 seconds)
**Goal:** Verify behavior with network loss

1. Start game and get to WAITING_FOR_INPUT
2. Open DevTools → Network tab
3. Set Throttling to "Offline"
4. Observe:
   - ✓ Error message appears within 3-5 seconds
   - ✓ Reconnection attempts start
5. Wait 10 seconds (should see multiple attempts)
6. Set Throttling back to "No throttling"
7. Observe:
   - ✓ Reconnection succeeds
   - ✓ State is recovered
   - ✓ "Connection restored!" appears

**Pass criteria:** Handles offline → online transition gracefully

---

### ✅ Test 4: Backend Server Restart (60 seconds)
**Goal:** Verify recovery from server restart

1. Start game
2. In terminal, restart backend:
   ```bash
   # Find process
   lsof -i :3000

   # Kill it
   kill -9 <PID>

   # Restart immediately
   cd map_backend && npm start
   ```
3. Observe:
   - ✓ Error message appears when backend goes down
   - ✓ Reconnection attempts shown
   - ✓ Successfully reconnects when backend is back
   - ✓ State is recovered

**Pass criteria:** Survives backend restart without manual intervention

---

### ✅ Test 5: Maximum Reconnection Attempts (2 minutes)
**Goal:** Verify manual reconnect button appears after failures

1. Start game
2. Press **Ctrl+Shift+D** to disconnect
3. **Keep backend stopped** or stay in Offline mode
4. Wait for all 25 reconnection attempts (~2 minutes with backoff)
5. Observe:
   - ✓ Attempt counter increases: "Reconnecting... (attempt X/25)"
   - ✓ After attempt 25: "Unable to reconnect. Click here to try again."
   - ✓ `showReconnectButton` flag is true
6. Click anywhere on the error message
7. Observe:
   - ✓ New reconnection attempt starts
   - ✓ Error message updates to "Reconnecting..."

**Pass criteria:** Provides manual retry without page refresh

---

### ✅ Test 6: Rapid Disconnect/Reconnect (30 seconds)
**Goal:** Verify stability under rapid connection changes

1. Start game
2. Rapidly alternate:
   - Press **Ctrl+Shift+D** (disconnect)
   - Wait 2 seconds
   - Press **Ctrl+Shift+R** (reconnect)
   - Wait 2 seconds
   - Repeat 5 times
3. Observe:
   - ✓ No crashes or errors
   - ✓ Connection status updates correctly
   - ✓ State remains consistent
   - ✓ No memory leaks (check DevTools Memory tab)

**Pass criteria:** System remains stable through rapid changes

---

### ✅ Test 7: Long Idle Connection (5 minutes)
**Goal:** Verify ALB idle timeout fix works

**Prerequisites:** Deploy ALB idle_timeout change to production

1. Start game in production environment
2. Leave game idle in WAITING_FOR_INPUT for 6 minutes (longer than 5 min timeout)
3. Don't interact with the game at all
4. After 6 minutes, try to perform an action
5. Observe:
   - ✓ No disconnection occurs
   - ✓ Action processes successfully
   - ✓ Connection remains stable

**Pass criteria:** Connection stays alive through idle period

---

### ✅ Test 8: Production Stress Test (10 minutes)
**Goal:** Verify fix works under real production conditions

1. Deploy to production/staging
2. Play through 10-20 in-game days
3. Monitor browser console for:
   - ✓ No unexpected disconnections
   - ✓ Ping/pong messages every 60 seconds (if verbose logging enabled)
   - ✓ No "WebSocket connection failed" errors
4. If disconnection occurs:
   - ✓ Automatic reconnection works
   - ✓ State recovery is successful
   - ✓ No need to refresh page

**Pass criteria:** Stable connection throughout gameplay session

---

## Console Monitoring

Watch for these log messages:

**Good signs:**
```
[SocketIO] Connected to server
[SocketIO] Reconnected after disconnection
[GUI] Game state recovered successfully
```

**Expected during testing:**
```
[SocketIO] Disconnected: io client disconnect
[SocketIO] Reconnection attempt 1
[GUI] Recovering game state after reconnection
```

**Red flags:**
```
[GUI] Failed to recover game state: <error>
[SocketIO] Failed to initialize: <error>
```

---

## Rollback Plan

If issues are found:

1. **Quick fix:** Set `reconnection: false` in GameStateListener.js:87
2. **Revert ALB timeout:** `terraform apply` with idle_timeout removed
3. **Disable debug keys:** Remove Ctrl+Shift+D/R handlers
4. **Emergency:** Revert all commits

---

## Performance Monitoring

After deploying, monitor:

1. **CloudWatch ALB metrics:**
   - ActiveConnectionCount
   - RejectedConnectionCount
   - TargetResponseTime

2. **Browser console:**
   - Check for reconnection frequency
   - Monitor memory usage over time

3. **Backend logs:**
   - Socket.io connection/disconnection patterns
   - Any 'ping timeout' messages

---

## Known Issues to Watch For

1. **Buffer overflow:** If many updates queue during disconnection
2. **State desync:** If backend state changes significantly during disconnection
3. **Memory leaks:** From repeated reconnection attempts
4. **Race conditions:** Multiple simultaneous reconnection attempts

---

## Success Criteria

✅ All 8 tests pass
✅ No console errors during normal gameplay
✅ Connections stable for 10+ minute sessions
✅ Automatic recovery works 100% of the time
✅ Manual reconnect works when automatic fails
✅ No data loss or park deletion
