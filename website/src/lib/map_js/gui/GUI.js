import { Scene } from 'phaser';
import { Visualizer, GameState } from './Visualizer.js';
import { AssetManager } from './AssetManager.js';
import { ClickHandler } from './ClickHandler.js';
import { createMiniAmusementPark } from '../MiniAmusementPark.js';
import { GameStateListener, Queue } from './GameStateListener.js';
import './styles/fonts.css';
import { formatFullState, formatMidDayState, formatGuestsState, getDefaultBackendHostPort } from '../helpers.js';

class GUI extends Scene {
    constructor() {
        super({ key: 'GUI' });
        
        // JS components
        this.gameState = null;
        
        // State Queue
        this.buffer = new Queue();

        // Initialize components
        this.visualizer = null;
        this.assetManager = null;
        this.clickHandler = null;
        this.gameStateListener = null;
        this.mode = 'few-shot'; // "few-shot", "few-shot+docs", "unlimited"
        this.map = null; // <-- create & reset this

        // Game state
        this.currentState = {};
        this.rawStartState = {};
        
        // Game state flags
        this.errorMsgs = [];
        this.running = true;
        this.updateCounter = 0;
        this.unchangedCount = 0;
        this.speedMultiplier = 1;
        this.deferredPositionUpdate = null;
        this.waitingForLastFullState = false;
        this.gameIsDone = false;
        this.newNotification = null;

        // Intermediary flags
        this.dayEnd = false;
        this.researchOngoing = false;
        
        // Game metrics
        this.previouslyAvailableEntities = {};

        // Game initialization flags
        this.gameInitialized = false;

        // Cleanup tracking
        this.cleanupCalled = false;
    }

    preload() {
        this.assetManager = new AssetManager(this, 0.7);
        this.assetManager.preload();
    }

    init(data) {
        // Initialize game parameters from data if provided
        // FIXME: Update to accomodate for more scenarios
        if (data) {
            this.difficulty = data.difficulty || 'medium';
            this.startingMoney = data.startingMoney || 500;
            this.scaleFactor = data.scaleFactor || 1;
            this.mode = data.mode || 'few-shot';
            this.gameState = data.gameState || null;
            this.evalLayout = data.evalLayout || "zig_zag";
        } else {
            this.difficulty = 'medium';
            this.startingMoney = 500;
            this.scaleFactor = 1;
            this.mode = 'few-shot';
            this.gameState = null;
            this.evalLayout = "zig_zag";
        }
    }

    async create() {
        this.visualizer = await Visualizer.create(this.assetManager, this.scaleFactor, this, this.mode);
        await this.visualizer.coords.waitForLoad();
        this.clickHandler = new ClickHandler(this.visualizer, this);

        // Create MiniAmusementPark instance
        const { host, port } = getDefaultBackendHostPort();
        this.map = await createMiniAmusementPark({
            host: host,
            port: port,
            difficulty: this.difficulty,
            visualizer: this.visualizer,
            returnRawInInfo: true,
            renderPark: false
        });

        // Set up GameStateListener with reconnection callbacks
        const reconnectionCallbacks = {
            onDisconnect: (reason) => {
                console.log('[GUI] Socket disconnected:', reason);
                this.errorMsgs.push('Connection lost. Reconnecting...');
                this.visualizer.showResultMessage = true;
            },
            onReconnect: async () => {
                console.log('[GUI] Socket reconnected, recovering game state');

                // Clear the reconnecting message first
                this.errorMsgs = [];

                // Attempt to recover game state
                await this.recoverGameState();
            },
            onReconnectAttempt: (attemptNumber) => {
                console.log('[GUI] Reconnection attempt:', attemptNumber);
                // Update error message to show attempt count
                this.errorMsgs = [`Connection lost. Reconnecting... (attempt ${attemptNumber}/25)`];
                this.visualizer.showResultMessage = true;
            },
            onReconnectError: (error) => {
                console.error('[GUI] Reconnection error:', error);
            },
            onReconnectFailed: () => {
                console.error('[GUI] Reconnection failed after maximum attempts');
                this.errorMsgs = ['Unable to reconnect. Please refresh your browser.'];
                this.visualizer.showResultMessage = true;
            }
        };

        this.gameStateListener = new GameStateListener(
            this.buffer,
            this.map.parkId,
            this.visualizer.animateDay,
            reconnectionCallbacks
        );

        // Set up cleanup handlers for page unload (similar to Python's __exit__)
        this.setupCleanupHandlers();

        this.setupInputHandlers();
        await this.startGame();
        this.gameInitialized = true;
        if (this.visualizer) {
            this.visualizer.gameMode = GameState.MODE_SELECTION_SCREEN;
        }

        const sandboxSteps = this.mode === "unlimited" ? 9999 : (this.visualizer.config?.sandbox_mode_steps || 100);
        const [sandboxObs, sandboxInfo] = await this.map.sandboxAction(`set_sandbox_mode(sandbox_steps=${sandboxSteps})`);

        // Update sandbox mode after setting it
        if (sandboxInfo?.raw_state?.state) {
            this.visualizer.sandboxMode = sandboxInfo.raw_state.state.sandbox_mode ?? false;
            this.visualizer.sandboxSteps = sandboxInfo.raw_state.state.sandbox_steps ?? sandboxSteps;
        }
    }

    async startGame() {
        const { host, port } = getDefaultBackendHostPort();
        const socketServer = (!host || host === '')
            ? window.location.origin  // Use same origin when host is empty (production via ALB)
            : `http://${host}:${port}`;  // Use explicit URL for local development

        await this.gameStateListener.startSocketioListener(socketServer);

        // Clear buffer
        this.buffer.clear();

        // Initialize game metrics
        this.score = 0;
        this.turnTimes = [];
        this.prevTime = Date.now();
        
        // Reset the game
        let obs = {}, info = {};
        if (Object.keys(this.rawStartState).length > 0) {
            console.log("Setting game with raw start state: ", this.rawStartState);
            [obs, info] = await this.map.set(this.rawStartState);
            if (obs.staff && info.raw_state) {
                obs.staff.staff_list = info.raw_state.staff;
            }
        } else {
            [obs, info] = await this.map.reset();
        }

        // Initialize sandbox mode (may be undefined on first reset, will be set after set_sandbox_mode)
        this.visualizer.sandboxMode = info?.raw_state?.state?.sandbox_mode ?? false;
        this.visualizer.sandboxSteps = info?.raw_state?.state?.sandbox_steps ?? -1;

        this.researchOngoing = false;
        this.previouslyAvailableEntities = obs?.state?.available_entities || {};
        this.visualizer.renderBackground();
        this.updateAndDrawGrid({ full_state: obs });

    }

    async recoverGameState() {
        try {
            console.log('[GUI] Recovering game state after reconnection');

            // Fetch current park state from backend
            const rawState = await this.map.getRawState();

            // Clear buffer to prevent stale updates
            this.buffer.clear();

            // Update display with recovered state
            this.updateAndDrawGrid({ full_state: rawState });

            // Reset to WAITING_FOR_INPUT state (stop any running simulation)
            this.visualizer.gameMode = GameState.WAITING_FOR_INPUT;

            // Show success notification
            this.newNotification = 'Connection restored!';
            this.visualizer.showNewNotification = true;

            // Clear any error messages
            this.errorMsgs = [];

            console.log('[GUI] Game state recovered successfully');
        } catch (error) {
            console.error('[GUI] Failed to recover game state:', error);

            // Check if the error is due to park not existing (backend restart)
            const errorMessage = error.message || '';
            if (errorMessage.includes('Invalid parkId') ||
                errorMessage.includes('Park has not yet been initialized') ||
                errorMessage.includes('Park not found')) {
                // Backend was restarted and park data was lost
                this.errorMsgs = ['Server restarted - park data lost. Please refresh your browser.'];
            } else {
                // Other error
                this.errorMsgs = ['Failed to recover game state. Please refresh your browser.'];
            }

            this.visualizer.showResultMessage = true;
        }
    }

    setupInputHandlers() {
        // Set up click event handler
        this.input.on('pointerdown', (pointer) => {
            this.handleInputEvents(pointer);
        });

        // DEBUG: Add keyboard shortcut to test reconnection (Ctrl+Shift+D/R)
        // Only enabled in development (localhost)
        const isDevelopment = typeof window !== 'undefined' &&
                              (window.location.hostname === 'localhost' ||
                               window.location.hostname === '127.0.0.1');

        if (isDevelopment) {
            console.log('[DEBUG] Reconnection test shortcuts enabled: Ctrl+Shift+D (disconnect), Ctrl+Shift+R (reconnect)');
            window.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.shiftKey && e.key === 'D') {
                    console.log('[DEBUG] Manually disconnecting socket for testing');
                    if (this.gameStateListener && this.gameStateListener.sio) {
                        this.gameStateListener.sio.disconnect();
                        console.log('[DEBUG] Socket disconnected. Wait a few seconds, then press Ctrl+Shift+R to reconnect');
                    }
                }
                if (e.ctrlKey && e.shiftKey && e.key === 'R') {
                    console.log('[DEBUG] Manually reconnecting socket');
                    if (this.gameStateListener && this.gameStateListener.sio) {
                        this.gameStateListener.sio.connect();
                    }
                }
            });
        }
        
        // Set up keyboard input handler
        this.input.keyboard.on('keydown', (event) => {
            this.handleKeyboardInput(event);
        });
    }

    update() {
        // Only run update logic if game is properly initialized
        if (!this.running || !this.visualizer || !this.map || !this.map.parkId || !this.gameInitialized) {
            return;
        }
        this.updateGameState();
        this.render();
    }

    updateGameState() {
        if (this.visualizer.gameMode === GameState.RUNNING_SIMULATION) {
            if (!this.buffer.is_empty()) {
                this.updateCounter += this.speedMultiplier;
                if (this.updateCounter >= this.visualizer.updateDelay) {
                    this.updateCounter = 0;
                    let nextUpdate = this.buffer.dequeue();

                    while (!this.visualizer.animateDay && ["mid_day", "exit_time"].includes(Object.keys(nextUpdate)[0])) {
                        if (this.buffer.is_empty()) {
                            return;
                        }
                        nextUpdate = this.buffer.dequeue();
                    }
                    this.updateAndDrawGrid(nextUpdate);
                }
            } else if (this.dayEnd) {
                this.dayEnd = false;
                if (!this.buffer.is_empty()) {
                    this.buffer.clear();
                }

                if (!this.gameIsDone) {
                    this.prevTime = Date.now();
                    this.visualizer.gameMode = GameState.WAITING_FOR_INPUT;
                } else {
                    console.log("Game is done, score:", this.score);
                    this.visualizer.finalScore = this.score;
                    this.visualizer.gameMode = GameState.END_SCREEN;

                    // Show leaderboard submission popup if score qualifies for top 25
                    if (!this.visualizer.sandboxMode) {
                        const thresholdKey = `${this.evalLayout}_${this.difficulty}`;
                        const threshold = this.gameState.thresholdsState.getThresholds()[thresholdKey];

                        // Show popup if threshold is null (< 25 scores) OR score >= threshold
                        const shouldShowPopup = threshold === null || threshold === undefined || this.score >= threshold;

                        console.log(`Threshold check: layout=${this.evalLayout}, difficulty=${this.difficulty}, threshold=${threshold}, score=${this.score}, shouldShow=${shouldShowPopup}`);

                        if (shouldShowPopup) {
                            this.gameState.leaderboardSubmissionState.setShowPopup(true);
                            this.gameState.leaderboardSubmissionState.setFinalScore(this.score);
                            this.gameState.leaderboardSubmissionState.setParkId(this.map.parkId);
                            this.gameState.leaderboardSubmissionState.setDifficulty(this.difficulty);
                            this.gameState.leaderboardSubmissionState.setLayout(this.evalLayout);
                        }
                    }
                }
            }
        }
    }

    updateAndDrawGrid(nextUpdate) {
        if ("day_start" in nextUpdate) {
            this.dayEnd = false;
            nextUpdate = { 'full_state': nextUpdate.day_start };
        }

        if ("day_end" in nextUpdate) {
            this.dayEnd = true;
            if (this.waitingForLastFullState) {
                this.gameIsDone = true;
            }
            nextUpdate = { 'full_state': nextUpdate.day_end };
            console.log("Tutorial step: ", this.visualizer.tutorialStep);
            if (nextUpdate.full_state.rides.length > 0 && (this.visualizer.tutorialStep < 14 || this.visualizer.tutorialStep >= 100)) {
                this.visualizer.tutorialStep = 14;
                if (nextUpdate.full_state.shops.length > 0 && (this.visualizer.tutorialStep < 26 || this.visualizer.tutorialStep >= 100)) {
                    this.visualizer.tutorialStep = 26;
                    if (nextUpdate.full_state.staff.staff_list.length > 0 && (this.visualizer.tutorialStep < 28 || this.visualizer.tutorialStep >= 100)) {
                        this.visualizer.tutorialStep = 28;
                    }
                }
            }
        }

        if ("full_state" in nextUpdate) {
            this.gameState.loadingState.setState(false);
            this.currentState = formatFullState(nextUpdate.full_state);
            this.visualizer.drawGameGrid(this.currentState);
            this.visualizer.drawPeople(this.currentState);
            this.visualizer.drawTileState(this.currentState);
            
            if (this.visualizer.selectedTile !== null) {
                this.clickHandler.handleGridSelection(
                    this.visualizer.selectedTile.x, 
                    this.visualizer.selectedTile.y, 
                    this.currentState
                );
            }
            
            // Set research selections to the current state
            this.visualizer.resAttractionSelections = this.currentState.research_topics || [];
            this.visualizer.resSpeedChoice = this.currentState.research_speed || "none";
        }

        if ("mid_day" in nextUpdate) {
            formatMidDayState(this.currentState, nextUpdate.mid_day);
            this.visualizer.drawPeople(this.currentState);
            this.visualizer.drawTileState(this.currentState);
        }

        if ("exit_time" in nextUpdate) {
            formatGuestsState(this.currentState, nextUpdate.exit_time.guests);
            this.visualizer.drawPeople(this.currentState);
        }
    }

    render() {
        // Ensure background is rendered before any screen drawing (matches Python pattern)
        this.visualizer.renderBackground();

        if (this.visualizer.gameMode === GameState.MODE_SELECTION_SCREEN) {
            this.assetManager.clearUIObjects();
            this.visualizer.drawModeSelectionScreen();
        } else if (this.visualizer.gameMode === GameState.DIFFICULTY_SELECTION_SCREEN) {
            this.assetManager.clearUIObjects();
            this.visualizer.drawDifficultySelectionScreen();
        } else if (this.visualizer.gameMode === GameState.LAYOUT_SELECTION_SCREEN) {
            this.assetManager.clearUIObjects();
            this.visualizer.drawLayoutSelectionScreen();
        } else if (this.visualizer.gameMode === GameState.END_SCREEN) {
            if (this.visualizer.endScreenSurface === null) {
                this.assetManager.clearUIObjects();
                this.visualizer.drawEndScreen();
            }
        } else if (this.visualizer.gameMode === GameState.WAITING_FOR_INPUT) {
            this.assetManager.clearUIObjects();
            this.visualizer.drawGameTicks(this.currentState.tick);
            this.visualizer.drawPlaybackPanel();
            this.visualizer.renderGrid(this.currentState);
            
            let yOffset = 0;
            if (this.errorMsgs && this.errorMsgs.length > 0) {
                for (const errorMsg of this.errorMsgs) {
                    this.visualizer.drawErrorMessage(errorMsg, yOffset);
                    yOffset += 75;
                }
            }
            if (this.newNotification) {
                this.visualizer.drawNewNotification(this.newNotification, yOffset);
            }
            
            this.visualizer.drawTopPanel(this.currentState);
            this.visualizer.drawBottomPanel(this.currentState);
            this.visualizer.drawStateInfo(this.currentState);
            this.visualizer.drawAggregateInfo(this.currentState);
            
            if (this.visualizer.guestSurveyResultsIsOpen) {
                this.visualizer.drawGuestSurveyResults(this.currentState);
            }
            if (this.visualizer.tutorialStep >= 0 && this.visualizer.in_tutorial_mode) {
                this.visualizer.drawTutorialOverlay();
            }
        } else if (this.visualizer.gameMode === GameState.RUNNING_SIMULATION) {
            this.assetManager.clearUIObjects();
            if (this.visualizer.animateDay) {
                this.gameStateListener.setAcceptMiddayUpdates(true);
                this.visualizer.drawTopPanel(this.currentState);
                this.visualizer.drawBottomPanel(this.currentState);
                this.visualizer.drawGameTicks(this.currentState.tick);
                this.visualizer.drawStateInfo(this.currentState);
                this.visualizer.drawPlaybackPanel();
                this.visualizer.renderGrid(this.currentState);
                
                let yOffset = 0;
                if (this.errorMsgs && this.errorMsgs.length > 0) {
                    for (const errorMsg of this.errorMsgs) {
                        this.visualizer.drawErrorMessage(errorMsg, yOffset);
                        yOffset += 75;
                    }
                }
                if (this.visualizer.tutorialStep >= 0 && this.visualizer.in_tutorial_mode) {
                    this.visualizer.drawTutorialOverlay();
                }
            } else {
                this.gameStateListener.setAcceptMiddayUpdates(false);
                this.visualizer.updateDelay = 1;
                this.visualizer.drawUpdatingDay();
            }
        } else if (this.visualizer.gameMode === GameState.TERMINATE_GAME) {
            this.running = false;
        } else {
            console.error("Invalid game mode:", this.visualizer.gameMode);
        }
    }

    handleInputEvents(pointer) {
        let action = null;
        let sandboxAction = null;
        
        if (this.visualizer.gameMode === GameState.MODE_SELECTION_SCREEN || 
                   this.visualizer.gameMode === GameState.DIFFICULTY_SELECTION_SCREEN ||
                   this.visualizer.gameMode === GameState.LAYOUT_SELECTION_SCREEN) {
            const result = this.clickHandler.handleSelectionScreenButtons([pointer.x, pointer.y]);
            sandboxAction = result.sandboxAction ?? sandboxAction;
        } else if (this.visualizer.gameMode === GameState.END_SCREEN) {
            const result = this.clickHandler.handleEndScreenButtons([pointer.x, pointer.y]);
            action = result.action;
            sandboxAction = result.sandboxAction;
        } else if (this.visualizer.gameMode === GameState.WAITING_FOR_INPUT || 
                   this.visualizer.gameMode === GameState.RUNNING_SIMULATION) {
            // Skip input if animate_day is false and we're in RUNNING_SIMULATION
            if (!this.visualizer.animateDay && this.visualizer.gameMode === GameState.RUNNING_SIMULATION) {
                return;
            } else if (this.visualizer.gameMode === GameState.WAITING_FOR_INPUT) {
                const result = this.clickHandler.handleActionButtons([pointer.x, pointer.y]);
                action = result.action;
                sandboxAction = result.sandboxAction;
            }
            if (this.visualizer.tutorialStep >= 0 && this.visualizer.in_tutorial_mode) {
                const result = this.clickHandler.handleTutorialScreenButtons([pointer.x, pointer.y]);
                if (result) {
                    return;
                }
            }
            this.handleSelectionEvents(pointer);
        }

        if (action !== null) {
            this.processAction(action);
        }
        
        if (sandboxAction !== null) {
            this.processSandboxAction(sandboxAction);
        }
    }

    handleSelectionEvents(pointer) {
        this.handleTextBoxSelection([pointer.x, pointer.y]);
        this.clickHandler.handleSelectionButtons([pointer.x, pointer.y], this.currentState);
    }

    handleKeyboardInput(event) {
        for (const key1 in this.visualizer.textInputs) {
            for (const key2 in this.visualizer.textInputs[key1]) {
                if (this.visualizer.textInputs[key1][key2].active) {
                    if (event.key === 'Backspace') {
                        this.visualizer.textInputs[key1][key2].value = 
                            this.visualizer.textInputs[key1][key2].value.slice(0, -1);
                    } else if (/\d/.test(event.key)) {
                        if (this.visualizer.textInputs[key1][key2].value.length < 4) {
                            this.visualizer.textInputs[key1][key2].value += event.key;
                            if (key1 === "ticket_price") {
                                this.visualizer.tutorialStep = 9;
                            } else if (key1 === "item_price") {
                                this.visualizer.tutorialStep = 24;
                            } else if (key1 === "order_quantity") {
                                this.visualizer.tutorialStep = 25;
                            }
                        }
                    } else if (event.key === 'Tab') {
                        // Tab to the next text box that is available
                        event.preventDefault();
                        const switches = [["modify_price", "modify_order_quantity"], ["item_price", "order_quantity"]];
                        for (const switchPair of switches) {
                            if (key1 === switchPair[0] && this.visualizer.textInputs[switchPair[0]][key2].active) {
                                this.visualizer.textInputs[switchPair[0]][key2].active = false;
                                this.visualizer.textInputs[switchPair[1]][key2].active = true;
                                this.visualizer.textInputs[switchPair[1]][key2].value = "";
                                return;
                            } else if (key1 === switchPair[1] && this.visualizer.textInputs[switchPair[1]][key2].active) {
                                this.visualizer.textInputs[switchPair[1]][key2].active = false;
                                this.visualizer.textInputs[switchPair[0]][key2].active = true;
                                this.visualizer.textInputs[switchPair[0]][key2].value = "";
                                return;
                            }
                        }
                    }
                }
            }
        }
    }

    handleTextBoxSelection(pos) {
        // Define text box rectangles and their corresponding active flags
        const textBoxes = [
            ['modify_price', this.visualizer.coords.changeAttributesBox[0], this.visualizer.assetManager.createScaledImage(0, 0, 'attributes_box')],
            ['modify_order_quantity', this.visualizer.coords.changeAttributesBox[1], this.visualizer.assetManager.createScaledImage(0, 0, 'attributes_box')],
            ['survey_guests', this.visualizer.coords.bigDescriptionBox, this.visualizer.assetManager.createScaledImage(0, 0, 'big_description_box')],
            ['item_price', this.visualizer.coords.attributesBox[1], this.visualizer.assetManager.createScaledImage(0, 0, 'attributes_box')],
            ['order_quantity', this.visualizer.coords.attributesBox[2], this.visualizer.assetManager.createScaledImage(0, 0, 'attributes_box')],
            ['ticket_price', this.visualizer.coords.attributesBox[5], this.visualizer.assetManager.createScaledImage(0, 0, 'attributes_box')],
        ];

        for (const [key1, coord, asset] of textBoxes) {
            let boxType = null, key2;
            if (["modify_price", "modify_order_quantity"].includes(key1)) {
                key2 = "modify";
            } else if (key1 === "survey_guests") {
                boxType = "survey_guests";
                key2 = "survey_guests";
            } else {
                boxType = key1 === "ticket_price" ? "ride" : "shop";
                const entitySubtype = this.visualizer.subtypeSelection[boxType];
                key2 = `${entitySubtype}_${this.visualizer.colorSelection[entitySubtype]}`;
            }

            // Check if click is within text box bounds using Pygame's Rect.collidepoint logic
            const rect = { x: coord[0], y: coord[1], width: asset.displayWidth, height: asset.displayHeight };
            const isWithinBounds = pos[0] >= rect.x && pos[0] <= rect.x + rect.width &&
                                 pos[1] >= rect.y && pos[1] <= rect.y + rect.height;

            if (isWithinBounds &&
                ((this.visualizer.selectedTileType === "ride" && key2 === "modify") ||
                 (this.visualizer.selectedTileType === "shop" && key2 === "modify") ||
                 (this.visualizer.bottomPanelActionType === boxType))) {
                    this.visualizer.textInputs[key1][key2].active = true;
                    this.visualizer.textInputs[key1][key2].value = "";
            } else {
                // Can only change the price of the current entry
                this.visualizer.textInputs[key1][key2].active = false;
            }
        }
    }

    async processAction(action) {
        this.errorMsgs = [];
        this.visualizer.showResultMessage = true;
        this.newNotification = null;

        if (action.includes("Error")) {
            this.errorMsgs.push(action);
            return;
        }

        // if no errors or noop on invalid action, run day
        this.visualizer.gameMode = GameState.RUNNING_SIMULATION;

        this.turnTimes.push(Date.now() - this.prevTime);
        console.log("Calling map.step with action:", action);

        let result, obs, reward, done, truncated, info;
        try {
            result = await this.map.step(action);
            [obs, reward, done, truncated, info] = result;
        } catch (error) {
            console.error("Error in map.step:", error);
            this.errorMsgs.push(`Action failed: ${error.message}`);
            // Reset game state to allow user to continue
            this.visualizer.gameMode = GameState.WAITING_FOR_INPUT;
            this.visualizer.showResultMessage = true;
            return;
        }

        if (done || truncated) {
            this.waitingForLastFullState = true;
        }

        if (!obs) {
            console.error("No obs returned from map.step:", result);
            this.errorMsgs.push("No observation returned from server");
            return;
        }


        // Check for sandbox mode changes
        if (info?.raw_state?.state) {
            if (!info.raw_state.state.sandbox_mode && this.visualizer.sandboxMode) {
                this.visualizer.gameMode = GameState.END_SCREEN;
            }
            if (info.raw_state.state.sandbox_mode && !this.visualizer.sandboxMode) {
                this.visualizer.gameMode = GameState.END_SCREEN;
            }
        }

        this.score = obs.value;
        
        if (info?.error?.message) {
            this.errorMsgs.push(info.error.message);
            this.visualizer.tutorialStep = 100; // Error tutorial
            console.log("?????? Tutorial step: ", this.visualizer.tutorialStep);
            if (this.visualizer.in_tutorial_mode) {
                this.visualizer.animateDay = true;
            }
        } else {
            if (info.raw_state.state.step == 1) {
                this.visualizer.tutorialStep = 11;
            } 
        }

        // Update sandbox mode and research speed from info
        if (info?.raw_state?.state) {
            this.visualizer.sandboxMode = info.raw_state.state.sandbox_mode && this.visualizer.sandboxMode;
            this.visualizer.sandboxSteps = this.visualizer.sandboxMode ? (info.raw_state.state.sandbox_steps || -1) : -1;
            // Update research speed from state
            if (info.raw_state.state.research_speed !== undefined) {
                this.visualizer.resSpeedChoice = info.raw_state.state.research_speed;
            }
        }

        const obsDump = obs;
        if (obsDump.new_entity_available) {
            for (const attraction in obsDump.available_entities || {}) {
                for (const color of obsDump.available_entities[attraction] || []) {
                    if (!this.previouslyAvailableEntities[attraction]?.includes(color)) {
                        const colorTitle = color.charAt(0).toUpperCase() + color.slice(1);
                        const attractionTitle = attraction.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        this.newNotification = `Research Complete: ${colorTitle} ${attractionTitle}!`;
                        this.previouslyAvailableEntities[attraction].push(color);
                        this.visualizer.showNewNotification = true;
                    }
                }
            }
        }

        // research banner no funds logic
        if (action.includes("set_research")) {
            if (action.includes("none")) {
                this.researchOngoing = false;
            } else {
                this.researchOngoing = true;
            }
        }

        if (this.researchOngoing && info?.raw_state?.state?.research_speed === "none") {
            this.errorMsgs.push("Research has stopped.");
            this.researchOngoing = false;
        }
    }

    async processSandboxAction(sandboxAction) {
        let sandboxActions = sandboxAction;
        if (!Array.isArray(sandboxActions)) {
            sandboxActions = [sandboxActions];
        }

        for (const action of sandboxActions) {
            this.visualizer.showResultMessage = true;
            console.log("Sandbox action: ", action);

            if (action.startsWith("reset") || action.startsWith("change_settings")) {
                this.researchOngoing = false;
                this.buffer.clear();
                this.assetManager.clearUIObjects();
                this.score = 0;
                this.waitingForLastFullState = false;
                this.gameIsDone = false;
                this.dayEnd = false;
                this.visualizer.reset();
                // Note: seed handling would need to be implemented if needed
            }
            
            let result, obs, info;
            try {
                result = await this.map.sandboxAction(action);
                [obs, info] = result;
            } catch (error) {
                console.error("Error in map.sandboxAction:", error);
                this.errorMsgs.push(`Sandbox action failed: ${error.message}`);
                this.visualizer.showResultMessage = true;
                continue; // Skip to next action
            }

            if (info?.error) {
                this.errorMsgs.push(info.error.message);
            }

            // if (action.startsWith("reset") || action.startsWith("change_settings")) {
            //     this.currentState = formatFullState(info.raw_state);
            //     this.updateAndDrawGrid({ full_state: this.currentState });
            // }
            
            if (action === "max_research()") {
                this.newNotification = "Research Complete: Everything!";
                this.visualizer.showNewNotification = true;
            }

            // Check for sandbox mode changes
            if (info?.raw_state?.state) {
                if (!info.raw_state.state.sandbox_mode && this.visualizer.sandboxMode) {
                    this.visualizer.gameMode = GameState.END_SCREEN;
                }
                if (info.raw_state.state.sandbox_mode && !this.visualizer.sandboxMode) {
                    this.visualizer.gameMode = GameState.END_SCREEN;
                }
            }

            // Update game state
            if (obs) {
                const obsDump = obs;
                if (obsDump.staff?.staff_list !== undefined) {
                    obsDump.staff.staff_list = info.raw_state?.staff || [];
                }
                this.updateAndDrawGrid({ full_state: obs });
                this.previouslyAvailableEntities = obsDump.state.available_entities || {};
            }

            // Update sandbox mode and research speed from info
            if (info?.raw_state?.state) {
                this.visualizer.sandboxMode = info.raw_state.state.sandbox_mode && this.visualizer.sandboxMode;
                this.visualizer.sandboxSteps = this.visualizer.sandboxMode ? (info.raw_state.state.sandbox_steps || -1) : -1;
                // Update research speed from state
                if (info.raw_state.state.research_speed !== undefined) {
                    this.visualizer.resSpeedChoice = info.raw_state.state.research_speed;
                }
            }
        }
    }

    setupCleanupHandlers() {
        // Set up event listeners to clean up park data when user leaves
        // This is similar to Python's __exit__ context manager pattern

        // beforeunload: fires when the page is about to be unloaded (refresh/close/navigate away)
        window.addEventListener('beforeunload', () => {
            this.cleanupParkData();
        });

        // pagehide: more reliable on mobile and some browsers
        window.addEventListener('pagehide', () => {
            this.cleanupParkData();
        });

        // visibilitychange: detects when tab becomes hidden (backup)
        // document.addEventListener('visibilitychange', () => {
        //     if (document.visibilityState === 'hidden') {
        //         this.cleanupParkData();
        //     }
        // });
    }

    cleanupParkData() {
        // Clean up park data from backend to prevent server congestion
        // Uses keepalive flag to ensure request completes even during page unload

        // Prevent duplicate cleanup calls (multiple events can fire)
        if (this.cleanupCalled || !this.map || !this.map.parkId) {
            return;
        }
        this.cleanupCalled = true;

        const url = `http://${this.map.host}:${this.map.port}/v1/park/delete_park/${this.map.parkId}`;

        try {
            // Use fetch with keepalive flag for reliable delivery during page unload
            // keepalive allows the request to outlive the page
            fetch(url, {
                method: 'DELETE',
                keepalive: true, // This ensures the request continues even if the page unloads
            }).catch(error => {
                // Errors are expected during unload, but log them anyway
                console.error('Cleanup request error (may be expected during unload):', error);
            });

            console.log(`Park ${this.map.parkId} cleanup request sent with keepalive`);
        } catch (error) {
            console.error('Failed to send cleanup request:', error);

            // Fallback: try synchronous XMLHttpRequest as last resort
            try {
                const xhr = new XMLHttpRequest();
                xhr.open('DELETE', url, false); // false = synchronous
                xhr.send();
                console.log(`Park ${this.map.parkId} cleanup via synchronous XHR`);
            } catch (xhrError) {
                console.error('Synchronous XHR fallback also failed:', xhrError);
            }
        }
    }

    shutdown() {
        // Clean up resources
        if (this.gameStateListener) {
            this.gameStateListener.disconnect();
        }

        // Clean up park data from backend
        if (this.map && this.map.parkId) {
            // Call deletePark asynchronously (for programmatic shutdown)
            this.map.deletePark().catch(err => {
                console.error('Failed to delete park during shutdown:', err);
            });
        }

        this.running = false;
    }
}

// Export the scene class so it can be imported elsewhere
export { GUI };

