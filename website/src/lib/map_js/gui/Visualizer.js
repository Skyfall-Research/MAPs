// Import dependencies
import { Coords } from './AssetManager.js';
// Import configuration
import { loadConfig } from '../config.js'

// Game state enum
export const GameState = {
    MODE_SELECTION_SCREEN: "MODE_SELECTION_SCREEN",
    DIFFICULTY_SELECTION_SCREEN: "DIFFICULTY_SELECTION_SCREEN",
    SCENARIO_SELECTION_SCREEN: "SCENARIO_SELECTION_SCREEN",
    WAITING_FOR_INPUT: "WAITING_FOR_INPUT",
    RUNNING_SIMULATION: "RUNNING_SIMULATION",
    END_SCREEN: "END_SCREEN",
    TERMINATE_GAME: "TERMINATE_GAME"
};

export class Visualizer {
    static guestSurveyColumns = [
        ["Guest", "guest", 100],
        ["Happiness", "happiness_at_exit", 100],
        ["Hunger", "hunger_at_exit", 100],
        ["Thirst", "thirst_at_exit", 100],
        ["Energy", "remaining_energy", 100],
        ["Money", "remaining_money", 100],
        ["% of money spent", "percent_of_money_spent", 200],
        ["Reason for exit", "reason_for_exit", 275],
        ["Preference", "preference", 275]
    ];

    static colorChoices = ["yellow", "blue", "green", "red"];

    constructor(assetManager, scaleFactor = 1.0, phaserScene = null, config = {}, mode = "few-shot") {
        // Canvas setup (replacing pygame)
        this.scaleFactor = scaleFactor;
        this.baseDims = [1900, 1000];
        this.dims = [
            Math.floor(this.baseDims[0] * scaleFactor),
            Math.floor(this.baseDims[1] * scaleFactor)
        ];
        
        // Phaser scene reference
        this.scene = phaserScene;
        
        // Animation and timing
        this.updateDelay = 2.0; // frames between updates
        this.animateDay = true;
        this.finalScore = 0;

        // Initialize assets and coordinates
        this.coords = new Coords(this.baseDims, scaleFactor);
        this.assetManager = assetManager;
        
        // Load config data synchronously
        this.config = config;
        this.mode = mode;

        this.tileSize = Math.floor(50 * scaleFactor);
        this.gridSize = Math.floor(1000 * scaleFactor);

        // Result message
        this.showResultMessage = false;
        this.showNewNotification = false;
        this.previouslyAvailableEntities = null;
        
        // Hiring
        this.pendingHireJob = null; // null, "janitor", or "mechanic"
        
        // Place shop
        this.placeShopPriceInputActive = false;
        this.placeShopTopPriceInputText = "";
        this.placingShopType = null; // "food", "drink", or "specialty"

        // Guest info window
        this.guestSurveyResultsIsOpen = false;
        this.guestSurveyStartIndex = 0;
        this.surveyResults = [];

        // Terraform window
        this.terraformAction = "";

        // Game states
        this.gameMode = GameState.MODE_SELECTION_SCREEN;

        // Sandbox mode properties
        this.sandboxMode = false;
        this.sandboxSteps = 0;

        // Tutorial step
        this.tutorialStep = -1;

        // Background image reference
        this.backgroundImage = null;

        // Input states for top panel
        this.topPanelSelectionType = null;
        this.topPanelStaffType = "janitors";
        this.staffEntryIndex = 0;
        this.staffListIndex = 0;
        this.listPage = 0;
        this.listEntryChoice = 0;
        this.selectedTileStaffList = [];
        this.selectedTile = null;
        this.selectedTileType = null;
        this.highlightRect = null; // Store reference to current highlight rectangle
        
        // Input states for bottom panel
        this.bottomPanelActionType = "ride";
        this.choiceOrder = {
            ride: ["carousel", "ferris_wheel", "roller_coaster"],
            shop: ["drink", "food", "specialty"],
            staff: ["janitor", "mechanic", "specialist"]
        };
        this.subtypeSelectionIdx = {
            ride: 0,
            shop: 0,
            staff: 0
        };
        this.subtypeSelection = {
            ride: this.choiceOrder.ride[0],
            shop: this.choiceOrder.shop[0],
            staff: this.choiceOrder.staff[0]
        };
        this.colorSelection = {};
        for (const entityType of Object.keys(this.choiceOrder)) {
            for (const entity of this.choiceOrder[entityType]) {
                this.colorSelection[entity] = "yellow";
            }
        }

        this.choices_start_x = 0;
        this.scaled_selection_width = 300 * this.scaleFactor;
        
        this.textInputs = {
            "ticket_price": Object.fromEntries(
                Visualizer.colorChoices.flatMap(color => 
                    this.choiceOrder.ride.map(ride => 
                        [`${ride}_${color}`, { active: false, value: "" }]
                    )
                )
            ),
            "item_price": Object.fromEntries(
                Visualizer.colorChoices.flatMap(color => 
                    this.choiceOrder.shop.map(shop => 
                        [`${shop}_${color}`, { active: false, value: "" }]
                    )
                )
            ),
            "order_quantity": Object.fromEntries(
                Visualizer.colorChoices.flatMap(color => 
                    this.choiceOrder.shop.map(shop => 
                        [`${shop}_${color}`, { active: false, value: "" }]
                    )
                )
            ),
            "modify_price": { "modify": { active: false, value: "" } },
            "modify_order_quantity": { "modify": { active: false, value: "" } },
            "survey_guests": { "survey_guests": { active: false, value: "" } }
        };

        // Research window
        this.currentAvailableColors = {
            carousel: ["yellow"],
            ferris_wheel: ["yellow"],
            roller_coaster: ["yellow"],
            drink: ["yellow"],
            food: ["yellow"],
            specialty: ["yellow"],
            janitor: ["yellow"],
            mechanic: ["yellow"],
            specialist: ["yellow"]
        };
        
        this.researchOpen = false;
        this.resAttractionSelections = ["carousel", "ferris_wheel", "roller_coaster", "drink", "food", "specialty", "janitor", "mechanic", "specialist"];
        this.resSpeedChoice = "none";

        // Selection screen
        this.selectionScreenOpen = false;
        this.difficultyChoices = ["easy", "medium"];
        this.modeChoices = ["Tutorial", "Sandbox", "Play Game"];
        this.difficultyChoice = 0;
        this.layoutChoice = 0;
        this.modeChoice = 0;
        this.okButtonPos = null;

        // Surfaces
        this.selectionScreenSurface = null;
        this.idScreenSurface = null;
        this.endScreenSurface = null;
        this.startScreenSurface = null;
        this.surveyGuestsSurface = null;
        this.topPanelSurface = null;
        this.bottomPanelSurface = null;
        this.stateInfoSurface = null;
        this.dayProgressSurface = null;
        this.resultMessageSurface = null;

        this.startTime = Date.now();
    }

    reset() {
        this.subtypeSelectionIdx = {
            ride: 0,
            shop: 0,
            staff: 0
        };
        if (this.tutorialStep == 0) {
            this.subtypeSelectionIdx['ride'] = 1;
        }
        this.subtypeSelection = {
            ride: this.choiceOrder.ride[0],
            shop: this.choiceOrder.shop[0],
            staff: this.choiceOrder.staff[0]
        };
        this.colorSelection = {
            carousel: "yellow",
            ferris_wheel: "yellow", 
            roller_coaster: "yellow",
            drink: "yellow",
            food: "yellow",
            specialty: "yellow",
            janitor: "yellow",
            mechanic: "yellow",
            specialist: "yellow"
        };

        // Research window
        this.currentAvailableColors = {
            carousel: ["yellow"],
            ferris_wheel: ["yellow"],
            roller_coaster: ["yellow"],
            drink: ["yellow"],
            food: ["yellow"],
            specialty: ["yellow"],
            janitor: ["yellow"],
            mechanic: ["yellow"],
            specialist: ["yellow"]
        };
    }

    scaleCoord(coord) {
        return [coord[0] * this.scaleFactor, coord[1] * this.scaleFactor];
    }

    getCenteredCoords(surface) {
        return [Math.floor((this.dims[0] - surface.get_width()) / 2), Math.floor((this.dims[1] - surface.get_height()) / 2)];
    }

    drawModeSelectionScreen() {
        // Draw start button
        const startButton = this.assetManager.createScaledImage(
            this.coords.startButton[0], 
            this.coords.startButton[1], 
            'start_button', 4
        );
        
        const full_x = this.scaled_selection_width * this.modeChoices.length + this.coords.choices_x_spacing * (this.modeChoices.length - 1);
        this.choices_start_x = (this.dims[0] - full_x) / 2;


        // Draw difficulty choices
        for (let i = 0; i < this.modeChoices.length; i++) {
            const mode = this.modeChoices[i];
            const modeText = mode.charAt(0).toUpperCase() + mode.slice(1);
            
            // Draw choice box
            const choiceBox = this.assetManager.createScaledImage(
                this.choices_start_x + i * (this.scaled_selection_width + this.coords.choices_x_spacing), 
                this.coords.choices_y, 
                'box', 4
            );
            
            // Draw difficulty text
            this.addText(
                this.choices_start_x + i * (this.scaled_selection_width + this.coords.choices_x_spacing) + (30 * this.scaleFactor), 
                this.coords.choices_y + (25 * this.scaleFactor), 
                modeText, 
                this.assetManager.getFontStyle('largeFixedWidth', '#000000')
            );

            const choiceTextbox = this.assetManager.createScaledImage(
                this.choices_start_x + i * (this.scaled_selection_width + this.coords.choices_x_spacing), 
                this.coords.choices_textbox_y, 
                'textbox', 4
            );

            let j = 0;
            for (let text of this.assetManager.modeTextboxText[mode].split("\n")) {
                const choiceTextboxText = this.addText(
                    this.choices_start_x + i * (this.scaled_selection_width + this.coords.choices_x_spacing) + (10 * this.scaleFactor), 
                    this.coords.choices_textbox_y + j * 30 * this.scaleFactor + 10, 
                    text, 
                    this.assetManager.getFontStyle('mediumFixedWidth', '#000000')
                );
                j++;
            }
            // Draw selection indicator if this is the selected difficulty
            if (i === this.modeChoice) {
                const selection = this.assetManager.createScaledImage(
                    this.choices_start_x + i * (this.scaled_selection_width + this.coords.choices_x_spacing), 
                    this.coords.choices_y, 
                    'selection', 4
                );
            }
        }
    }

    drawDifficultySelectionScreen() {
        // Draw start button
        const startButton = this.assetManager.createScaledImage(
            this.coords.startButton[0], 
            this.coords.startButton[1], 
            'start_button', 4
        );
        
        const full_x = this.scaled_selection_width * this.difficultyChoices.length + this.coords.choices_x_spacing * (this.difficultyChoices.length - 1);
        this.choices_start_x = (this.dims[0] - full_x) / 2;


        // Draw difficulty choices
        for (let i = 0; i < this.difficultyChoices.length; i++) {
            const difficulty = this.difficultyChoices[i];
            const difficultyText = difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
            
            // Draw choice box
            const choiceBox = this.assetManager.createScaledImage(
                this.choices_start_x + i * (this.scaled_selection_width + this.coords.choices_x_spacing), 
                this.coords.choices_y, 
                'box', 4
            );
            
            // Draw difficulty text
            this.addText(
                this.choices_start_x + i * (this.scaled_selection_width + this.coords.choices_x_spacing) + (30 * this.scaleFactor), 
                this.coords.choices_y + (25 * this.scaleFactor), 
                difficultyText, 
                this.assetManager.getFontStyle('largeFixedWidth', '#000000')
            );

            const choiceTextbox = this.assetManager.createScaledImage(
                this.choices_start_x + i * (this.scaled_selection_width + this.coords.choices_x_spacing), 
                this.coords.choices_textbox_y, 
                'textbox', 4
            );

            let j = 0;
            for (let text of this.assetManager.difficultyTextboxText[difficulty].split("\n")) {
                const choiceTextboxText = this.addText(
                    this.choices_start_x + i * (this.scaled_selection_width + this.coords.choices_x_spacing) + (10 * this.scaleFactor), 
                    this.coords.choices_textbox_y + j * 30 * this.scaleFactor + 10, 
                    text, 
                    this.assetManager.getFontStyle('mediumFixedWidth', '#000000')
                );
                j++;
            }
            // Draw selection indicator if this is the selected difficulty
            if (i === this.difficultyChoice) {
                const selection = this.assetManager.createScaledImage(
                    this.choices_start_x + i * (this.scaled_selection_width + this.coords.choices_x_spacing), 
                    this.coords.choices_y, 
                    'selection', 4
                );
            }
        }
    }

    drawLayoutSelectionScreen() {
        // Set layout choices based on sandbox mode
        if (this.sandboxMode) {
            this.layoutChoices = this.config['train_layouts'];
        } else {
            this.layoutChoices = this.config['test_layouts'];
        }
        
        // Draw start button
        const startButton = this.assetManager.createScaledImage(
            this.coords.startButton[0], 
            this.coords.startButton[1], 
            'start_button', 4
        );

        const full_x = this.scaled_selection_width * this.layoutChoices.length + this.coords.choices_x_spacing * (this.layoutChoices.length - 1);
        this.choices_start_x = (this.dims[0] - full_x) / 2;
        
        // Draw layout choices
        for (let i = 0; i < this.layoutChoices.length; i++) {
            const layout = this.layoutChoices[i];
            const layoutText = layout.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
            
            // Draw choice box
            const choiceBox = this.assetManager.createScaledImage(
                this.choices_start_x + i * (this.scaled_selection_width + this.coords.choices_x_spacing),
                this.coords.choices_y, 
                'box', 4
            );
            
            // Draw layout text
            this.addText(
                this.choices_start_x + i * (this.scaled_selection_width + this.coords.choices_x_spacing) + (30 * this.scaleFactor), 
                this.coords.choices_y + (25 * this.scaleFactor), 
                layoutText, 
                this.assetManager.getFontStyle('largeFixedWidth', '#000000')
            );
            
            // Draw selection indicator if this is the selected layout
            if (i === this.layoutChoice) {
                const selection = this.assetManager.createScaledImage(
                    this.choices_start_x + i * (this.scaled_selection_width + this.coords.choices_x_spacing), 
                    this.coords.choices_y, 
                    'selection', 4
                );
            }

            const layoutImage = this.assetManager.createScaledImage(
                this.choices_start_x + i * (this.scaled_selection_width + this.coords.choices_x_spacing), 
                this.coords.choices_textbox_y, 
                `layout_image_${layout}`, 4
            );
        }
    }

    drawTutorialOverlay() {
        if (this.tutorialStep >= 0) {
            let currTutorialStep = null;
            if (this.tutorialStep >= 100) {
                const errorIdx = this.coords.tutorialSteps.length - 2 + (this.tutorialStep - 100)
                currTutorialStep = this.coords.tutorialSteps[errorIdx];
            } else {
                currTutorialStep = this.coords.tutorialSteps[this.tutorialStep];
            }
            const mascot = this.assetManager.createScaledImage(
                this.coords.mascot[0], 
                this.coords.mascot[1], 
                'mascot', 8
            );

            let yOffset = 0;    
            for (let line of currTutorialStep.text.split("\n")) {
                this.addText(
                    this.coords.textbox[0], 
                    this.coords.textbox[1] + yOffset, 
                    line, 
                    this.assetManager.getFontStyle('mediumFixedWidth', '#000000'),
                    12
                );
                yOffset += 40 * this.scaleFactor;
            }

            if (currTutorialStep.include_arrow) {
                const arrow = this.assetManager.createScaledImage(
                    currTutorialStep.highlight_pos[0] + this.coords.arrowOffset[0], 
                    currTutorialStep.highlight_pos[1] + this.coords.arrowOffset[1], 
                    'arrow', 15
                );
            }

            if (currTutorialStep.include_ok_button) {
                this.okButtonPos = [
                    currTutorialStep.highlight_pos[0] + this.coords.okButtonOffset[0], 
                    currTutorialStep.highlight_pos[1] + this.coords.okButtonOffset[1]
                ];
                const okButton = this.assetManager.createScaledImage(
                    this.okButtonPos[0], 
                    this.okButtonPos[1], 
                    'ok_button', 15
                );
            }  else {
                this.okButtonPos = null;
            }

        }
    }

    drawEndScreen() {
        if (this.endScreenSurface === null) {
            // Create final score panel background
            const finalScorePanel = this.assetManager.createScaledImage(
                this.coords.finalScorePanel[0], 
                this.coords.finalScorePanel[1], 
                'final_score_panel', 8
            );
            
            // Create final score text
            const finalScoreText = this.addText(
                this.coords.finalScorePanel[0] + this.coords.finalScoreTextOffset[0],
                this.coords.finalScorePanel[1] + this.coords.finalScoreTextOffset[1] + 10 * this.scaleFactor,
                `Final Score:${this.finalScore.toLocaleString().padStart(11)}`,
                this.assetManager.getFontStyle('largeFixedWidth', '#000000')
            );

            finalScoreText.setDepth(9);

            console.log(`Final Score:${this.finalScore.toLocaleString().padStart(11)}`);

            // Non-sandbox mode: show centered done button
            const doneButton = this.assetManager.createScaledImage(
                this.coords.centerMainButton[0],
                this.coords.centerMainButton[1],
                'done_button_big', 8
            );

            // Mark as created
            this.endScreenSurface = true;
        }
    }

    drawUpdatingDay() {
        const updatingDay = this.assetManager.createScaledImage(this.coords.updatingDay[0], this.coords.updatingDay[1], 'updating_day', 10);
    }

    drawNewNotification(notification, yOffset) {
        if (this.showNewNotification && notification) {
            // Calculate alert textbox coordinates with y offset
            const alertTextboxCoords = [
                this.coords.alertTextbox[0],
                this.coords.alertTextbox[1] + (yOffset * this.scaleFactor)
            ];
            
            // Create notification textbox background
            const notificationTextbox = this.assetManager.createScaledImage(
                alertTextboxCoords[0],
                alertTextboxCoords[1],
                'notification_textbox', 12
            );
            
            // Add close button
            const closeButton = this.assetManager.createScaledImage(
                alertTextboxCoords[0] + (-4 * this.scaleFactor),
                alertTextboxCoords[1] + (-4 * this.scaleFactor),
                'close_button', 12
            );
            
            // Determine font style based on notification length
            let fontStyle;
            let displayText = notification;
            
            if (notification.length >= 100) {
                fontStyle = this.assetManager.getFontStyle('vsmallFixedWidth', '#000000');
                displayText = notification.substring(0, 97) + "...";
            } else if (notification.length >= 90) {
                fontStyle = this.assetManager.getFontStyle('vsmallFixedWidth', '#000000');
            } else if (notification.length >= 75) {
                fontStyle = this.assetManager.getFontStyle('smallFixedWidth', '#000000');
            } else {
                fontStyle = this.assetManager.getFontStyle('mediumFixedWidth', '#000000');
            }
            
            // Calculate alert message coordinates with y offset
            const alertMessageCoords = [
                this.coords.alertMessage[0],
                this.coords.alertMessage[1] + (yOffset * this.scaleFactor)
            ];
            
            // Add notification text
            const resultText = this.addText(
                alertMessageCoords[0],
                alertMessageCoords[1],
                displayText,
                fontStyle,
                12
            );
        }
    }

    drawErrorMessage(msg, yOffset) {
        if (this.showResultMessage && msg) {
            // Calculate alert textbox coordinates with y offset
            const alertTextboxCoords = [
                this.coords.alertTextbox[0],
                this.coords.alertTextbox[1] + (yOffset * this.scaleFactor)
            ];
            
            // Create error textbox background
            const errorTextbox = this.assetManager.createScaledImage(
                alertTextboxCoords[0],
                alertTextboxCoords[1],
                'error_textbox', 12
            );
            
            // Add close button
            const closeButton = this.assetManager.createScaledImage(
                alertTextboxCoords[0] + (-4 * this.scaleFactor),
                alertTextboxCoords[1] + (-4 * this.scaleFactor),
                'close_button', 12
            );
            
            // Determine font style based on message length
            let fontStyle;
            let displayText = msg;
            
            if (msg.length >= 100) {
                fontStyle = this.assetManager.getFontStyle('vsmallFixedWidth', '#000000');
                displayText = msg.substring(0, 97) + "...";
            } else if (msg.length >= 90) {
                fontStyle = this.assetManager.getFontStyle('vsmallFixedWidth', '#000000');
            } else if (msg.length >= 75) {
                fontStyle = this.assetManager.getFontStyle('smallFixedWidth', '#000000');
            } else {
                fontStyle = this.assetManager.getFontStyle('mediumFixedWidth', '#000000');
            }
            
            // Calculate alert message coordinates with y offset
            const alertMessageCoords = [
                this.coords.alertMessage[0],
                this.coords.alertMessage[1] + (yOffset * this.scaleFactor)
            ];
            
            // Add error message text
            const errorText = this.addText(
                alertMessageCoords[0],
                alertMessageCoords[1],
                displayText,
                fontStyle,
                12
            );
        }
    }

    drawPlaybackPanel() {
        // Create playback panel background
        const playbackPanel = this.assetManager.createScaledImage(this.coords.playbackPanel[0], this.coords.playbackPanel[1], 'playback_panel', 4);
        
        // Draw up and down buttons
        const upButton = this.assetManager.createScaledImage(this.coords.playbackIncrease[0], this.coords.playbackIncrease[1], 'up_button', 4);
        const downButton = this.assetManager.createScaledImage(this.coords.playbackDecrease[0], this.coords.playbackDecrease[1], 'down_button', 4);

        const pbRate = 16 / this.updateDelay;
        let displayRate = pbRate >= 1 ? Math.floor(pbRate) : pbRate;
        
        // Draw playback rate text
        this.addText(
            this.coords.playbackText[0], 
            this.coords.playbackText[1], 
            `${displayRate}x`, 
            this.assetManager.getFontStyle('mediumFixedWidth', '#000000')
        );

        // Animate day button
        if (this.animateDay) {
            const animateDayActive = this.assetManager.createScaledImage(this.coords.animateDay[0], this.coords.animateDay[1], 'animate_day_active', 4);
        } else {
            const animateDayInactive = this.assetManager.createScaledImage(this.coords.animateDay[0], this.coords.animateDay[1], 'animate_day_inactive', 4);
        }
    }

    drawStateInfo(state) {
        // Create main stat panel background
        const mainStatPanel = this.assetManager.createScaledImage(this.coords.mainStatPanel[0], this.coords.mainStatPanel[1], 'main_stat_panel', 4);
        // if (!state) return;
        const profit = state.profit || 0;
        const money = state.money || 0;

        const info = {
            "day": ["Day: ", `  ${(state.step || 0).toString().padStart(3)} / ${(state.horizon || 50).toString().padStart(3)}`],
            "value": ["Value: ", `$${(state.value || 0).toLocaleString().padStart(10)}`],
            "money": ["Money: ", `$${money.toLocaleString().padStart(10)}`],
            "profit": ["Profit: ", `$${profit.toLocaleString().padStart(10)}`],
            "revenue": ["Revenue: ", `$${(state.revenue || 0).toLocaleString().padStart(9)}`],
            "expenses": ["Expenses: ", `$${(state.expenses || 0).toLocaleString().padStart(9)}`],
            "rating": `${(state.park_rating || 0).toFixed(2).padStart(4)}`,
            "total_capacity": `${(state.total_capacity || 0).toString().padStart(4)}`,
            "guest_count": `${(state.total_guests || 0).toString().padStart(5)}`,
            "avg_money_spent": `${(state.avg_money_spent || 0).toFixed(1).padStart(5)}`
        };

        let fontStyle14 = this.assetManager.getFontStyle('mediumFixedWidth', '#000000');
        let fontStyle12 = this.assetManager.getFontStyle('smallFixedWidth', '#000000');
        // Day label and value
        this.addText(
            this.coords.mainStatPanel[0] + (25 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (32 * this.scaleFactor),
            info["day"][0],
            fontStyle14
        );
        
        this.addText(
            this.coords.mainStatPanel[0] + (115 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (32 * this.scaleFactor),
            info["day"][1],
            fontStyle14
        );
        
        // Value label and value
        this.addText(
            this.coords.mainStatPanel[0] + (25 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (74 * this.scaleFactor),
            info["value"][0],
            fontStyle14
        );
        
        this.addText(
            this.coords.mainStatPanel[0] + (115 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (74 * this.scaleFactor),
            info["value"][1],
            fontStyle14
        );

        // Money label and value
        this.addText(
            this.coords.mainStatPanel[0] + (25 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (116 * this.scaleFactor),
            info["money"][0],
            fontStyle14
        );
        
        this.addText(
            this.coords.mainStatPanel[0] + (115 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (116 * this.scaleFactor),
            info["money"][1],
            fontStyle14
        );

        // Profit label and value (red if negative)
        this.addText(
            this.coords.mainStatPanel[0] + (25 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (158 * this.scaleFactor),
            info["profit"][0],
            fontStyle14
        );
        
        this.addText(
            this.coords.mainStatPanel[0] + (115 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (158 * this.scaleFactor),
            info["profit"][1],
            fontStyle14
        );

        // Revenue label and value
        this.addText(
            this.coords.mainStatPanel[0] + (23 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (196 * this.scaleFactor),
            info["revenue"][0],
            fontStyle12
        );
        
        this.addText(
            this.coords.mainStatPanel[0] + (31 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (210 * this.scaleFactor),
            info["revenue"][1],
            fontStyle12
        );

        // Expenses label and value
        this.addText(
            this.coords.mainStatPanel[0] + (150 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (196 * this.scaleFactor),
            info["expenses"][0],
            fontStyle12
        );
        
        this.addText(
            this.coords.mainStatPanel[0] + (158 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (210 * this.scaleFactor),
            info["expenses"][1],
            fontStyle12
        );

        // Rating
        this.addText(
            this.coords.mainStatPanel[0] + (64 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (280 * this.scaleFactor),
            info["rating"],
            fontStyle14
        );

        // Total capacity
        this.addText(
            this.coords.mainStatPanel[0] + (218 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (280 * this.scaleFactor),
            info["total_capacity"],
            fontStyle14
        );

        // Guest count
        this.addText(
            this.coords.mainStatPanel[0] + (64 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (335 * this.scaleFactor),
            info["guest_count"],
            fontStyle14
        );

        // Average money spent
        this.addText(
            this.coords.mainStatPanel[0] + (207 * this.scaleFactor),
            this.coords.mainStatPanel[1] + (335 * this.scaleFactor),
            info["avg_money_spent"],
            fontStyle14
        );
    }

    drawAggregateInfo(state) {
        // Create aggregate stat panel background
        //console.warn("state: ", state);
        const aggregateStatPanel = this.assetManager.createScaledImage(this.coords.aggregateStatPanel[0], this.coords.aggregateStatPanel[1], 'aggregate_stat_panel', 4);
        
        const park = { 'Min Cleanliness': state.min_cleanliness, 'Avg. Time in Park': state.avg_time_in_park };
        const shopsKeys = { 
            'Revenue Generated': state.shops_total_revenue_generated || 0, 
            'Operating Cost': state.shops_total_operating_cost || 0, 
            'Min Uptime': state.shops_min_uptime || 0 
        };
        const ridesKeys = { 
            'Revenue Generated': state.rides_total_revenue_generated || 0, 
            'Operating Cost': state.rides_total_operating_cost || 0, 
            'Park Excitement': state.park_excitement || 0, 
            'Avg Intensity': state.avg_intensity || 0, 
            "Total Capacity": state.total_capacity || 0, 
            'Min Uptime': state.ride_min_uptime || 0 
        };
        const staffKeys = { 
            'Salary Paid': state.total_salary_paid || 0, 
            'Operating Cost': state.total_operating_cost || 0, 
            '# Janitors': state.total_janitors || 0, 
            '# Mechanics': state.total_mechanics || 0, 
            '# Specialists': state.total_specialists || 0 
        };
        const researchKeys = { 
            'Operating Cost': state.research_operating_cost || 0, 
            'Fast': state.fast_days_since_last_new_entity || 0, 
            'Med.': state.medium_days_since_last_new_entity || 0, 
            'Slow': state.slow_days_since_last_new_entity || 0 
        };
        
        const xPos = this.coords.aggregateStatPanel[0] + (15 * this.scaleFactor);
        let yPos = this.coords.aggregateStatPanel[1] + (22 * this.scaleFactor);
        const valueXPos = xPos + (140 * this.scaleFactor);
        
        const drawCategory = (header, valuesDict, startY) => {
            // Draw header - red
            this.addText(
                xPos, 
                startY, 
                header, 
                this.assetManager.getFontStyle('smallFixedWidth', '#ff0000')
            );
            
            let y = startY + (20 * this.scaleFactor);

            // Draw key-value pairs
            let index = 0;
            for (const [key, value] of Object.entries(valuesDict)) {
                // Add subtitle for Research section when processing "Fast" key
                if (header === "Research" && key === "Fast") {
                    this.addText(
                        xPos, 
                        y, 
                        "Days Since Discovery", 
                        this.assetManager.getFontStyle('smallFixedWidth', '#000000')
                    );
                    y += (20 * this.scaleFactor);
                }
                let formattedValue;
                if (Array.isArray(value)) {
                    formattedValue = value.map(v => v.toString().padStart(2)).join(",");
                } else {
                    formattedValue = typeof value === 'number' && Number.isInteger(value) 
                        ? value.toString().padStart(11) 
                        : value.toFixed(2).padStart(11);
                }
                
                const keyText = this.addText(
                    xPos, 
                    y, 
                    `${key}: `, 
                    this.assetManager.getFontStyle('smallFixedWidth', '#000000')
                );
                
                const valueText = this.addText(
                    valueXPos, 
                    y, 
                    formattedValue, 
                    this.assetManager.getFontStyle('smallFixedWidth', '#000000')
                );
                
                if (header === "Research" && ["Fast", "Med.", "Slow"].includes(key)) {
                    const resXPos = xPos + (85 * (index - 1) * this.scaleFactor);
                    keyText.setPosition(resXPos, y + (5 * this.scaleFactor));
                    valueText.setPosition(resXPos - (30 * this.scaleFactor), y + (5 * this.scaleFactor));
                } else {
                    y += (20 * this.scaleFactor);
                }
                index++;
            }
            return y;
        };
        yPos = drawCategory("Park", park, yPos);
        yPos = drawCategory(`Shops (${state.shops ? Object.keys(state.shops).length : 0})`, shopsKeys, yPos);
        yPos = drawCategory(`Rides (${state.rides ? Object.keys(state.rides).length : 0})`, ridesKeys, yPos);
        yPos = drawCategory("Staff", staffKeys, yPos);
        yPos = drawCategory("Research", researchKeys, yPos);
    }

    drawGuestSurveyResults(currentState) {
        // Create survey guests panel background
        const surveyGuestsPanel = this.assetManager.createScaledImage(
            this.coords.guestSurveyResultsPanel[0], 
            this.coords.guestSurveyResultsPanel[1], 
            'guest_survey_results_panel', 10
        );
        
        // Add close button
        const closeButton = this.assetManager.createScaledImage(
            this.coords.guestSurveyResultsPanel[0] + (47 * this.scaleFactor), 
            this.coords.guestSurveyResultsPanel[1] + (9 * this.scaleFactor), 
            'close_button', 10
        );

        this.surveyResults = currentState.guest_survey_results?.list_of_results || [];
        
        // Get column headers from keys of the first dictionary
        if (this.surveyResults.length === 0) {
            return;
        }
        
        const totalRows = Math.min(this.surveyResults.length + 1, 13); // +1 for header row
        const totalCols = Visualizer.guestSurveyColumns.length;
        const rowHeight = 25 * this.scaleFactor;
        const startX = this.coords.guestSurveyResultsPanel[0];
        const startY = this.coords.guestSurveyResultsPanel[1];

        const ageOfResults = currentState.guest_survey_results?.age_of_results || 0;
        const ageOfResultsText = this.addText(
            startX + (110 * this.scaleFactor), 
            startY + (5 * this.scaleFactor), 
            `Age of Results: ${ageOfResults}`, 
            this.assetManager.getFontStyle('smallFixedWidth', '#000000')
        );
        ageOfResultsText.setDepth(10);

        // Draw cell backgrounds & text
        for (let rowIdx = 0; rowIdx < totalRows; rowIdx++) {
            let colX = startX + (10 * this.scaleFactor);
            
            for (let colIdx = 0; colIdx < totalCols; colIdx++) {
                const [columnName, columnKey, columnWidth] = Visualizer.guestSurveyColumns[colIdx];
                const colWidth = columnWidth * this.scaleFactor;
                
                const cellX = colX;
                colX += colWidth;
                const cellY = startY + rowIdx * rowHeight + (34 * this.scaleFactor);
                
                // Draw cell background
                if (rowIdx === 0) { // Header row
                    const headerRect = this.scene.add.graphics();
                    headerRect.fillStyle(0x969696); // RGB(150,150,150)
                    headerRect.fillRect(cellX, cellY, colWidth, rowHeight);
                    headerRect.setDepth(10);
                    this.assetManager.uiObjects.push(headerRect);
                } else if (colIdx === 0) { // First column
                    const firstColRect = this.scene.add.graphics();
                    firstColRect.fillStyle(0x969696); // RGB(150,150,150)
                    firstColRect.fillRect(cellX, cellY, colWidth, rowHeight);
                    firstColRect.setDepth(10);
                    this.assetManager.uiObjects.push(firstColRect);
                }
                
                // Draw cell border
                const borderRect = this.scene.add.graphics();
                borderRect.lineStyle(1, 0x000000); // Black border
                borderRect.strokeRect(cellX, cellY, colWidth, rowHeight);
                borderRect.setDepth(10);
                this.assetManager.uiObjects.push(borderRect);
                // Cell text
                let textContent;
                if (rowIdx === 0) {
                    // Header
                    textContent = columnName;
                } else {
                    if (colIdx === 0) {
                        // Guest #
                        textContent = (rowIdx + this.guestSurveyStartIndex).toString();
                    } else {
                        // Guest data
                        let key = columnKey;
                        if (["reason_for_exit", "preference"].includes(columnKey)) {
                            key = columnKey + "_id";
                        }
                        let val = this.surveyResults[rowIdx + this.guestSurveyStartIndex - 1][key];
                        if (key == "reason_for_exit_id") {
                            val = this.assetManager.getExitReasonDescription(val);
                        }
                        else if (key == "preference_id") {
                            val = this.assetManager.getPreferenceDescription(val);
                        }
                        else {
                            val = val.toFixed(2);
                        }
                        textContent = val.toString();

                    }
                }
                
                // Center text in the cell
                const cellText = this.addText(
                    cellX + colWidth / 2, 
                    cellY + rowHeight / 2, 
                    textContent, 
                    this.assetManager.getFontStyle('smallFixedWidth', '#000000')
                );
                cellText.setOrigin(0.5, 0.5).setDepth(10); // Center the text
            }
        }

        // Draw pagination buttons if there are more results than can be displayed
        if (this.surveyResults.length - this.guestSurveyStartIndex > 12) {
            const downButton = this.assetManager.createScaledImage(
                this.coords.guestSurveyDownButton[0], 
                this.coords.guestSurveyDownButton[1], 
                'down_button', 10
            );
        }
        
        if (this.guestSurveyStartIndex > 0) {
            const upButton = this.assetManager.createScaledImage(
                this.coords.guestSurveyUpButton[0], 
                this.coords.guestSurveyUpButton[1], 
                'up_button', 10
            );
        }
    }

    drawGameTicks(frameCounter) {
        // Create day progress panel background
        const day_progress_panel = this.assetManager.createScaledImage(this.coords.dayProgressPanel[0], this.coords.dayProgressPanel[1], 'day_progress_panel', 4);
        
        const maxValue = 502;
        const barX = this.coords.dayProgressPanel[0] + (123 * this.scaleFactor);
        const barY = this.coords.dayProgressPanel[1] + (9 * this.scaleFactor);
        const barHeight = this.scaleFactor * 25;
        const barMaxWidth = this.scaleFactor * 447;
        
        const n = Math.min(maxValue, frameCounter + 1);
        const progressRatio = n / maxValue;
        const fillWidth = Math.floor(barMaxWidth * progressRatio);
        
        // Draw progress bar background (dark gray)
        const backgroundRect = this.scene.add.graphics();
        backgroundRect.fillStyle(0x323232); // (50, 50, 50) in hex
        backgroundRect.fillRect(barX, barY, barMaxWidth, barHeight);
        backgroundRect.setDepth(5);
        this.assetManager.uiObjects.push(backgroundRect);
        
        // Draw progress bar fill (green)
        const fillRect = this.scene.add.graphics();
        fillRect.fillStyle(0x8EBE85); // (142, 190, 133) in hex
        fillRect.fillRect(barX, barY, fillWidth, barHeight);
        fillRect.setDepth(6);
        this.assetManager.uiObjects.push(fillRect);
    }

    drawTopPanel(state) {
        // Background panels
        const topPanel = this.assetManager.createScaledImage(this.coords.topPanel[0], this.coords.topPanel[1], 'top_panel', 4);
        const staffListPanel = this.assetManager.createScaledImage(this.coords.staffListPanel[0], this.coords.staffListPanel[1], 'staff_list_panel', 4);
        const selectedTilePanel = this.assetManager.createScaledImage(this.coords.selectedTilePanel[0], this.coords.selectedTilePanel[1], 'selected_tile_panel', 4);
        
        // Moving button
        if (this.gameMode === GameState.WAITING_FOR_INPUT && this.topPanelSelectionType === "attraction" || this.topPanelSelectionType === "staff") {
            if (this.waitingForMove) {
                this.assetManager.createScaledImage(this.coords.moveButton[0], this.coords.moveButton[1], 'moving_button', 4);
            } else {
                this.assetManager.createScaledImage(this.coords.moveButton[0], this.coords.moveButton[1], 'move_button', 4);
            }
        }

        // Staff list
        // If the tile we selected can contain people, get the staff on that tile
        this.selectedTileStaffList = [];
        if (["ride", "shop", "path", "entrance", "exit"].includes(this.selectedTileType)) {
            const staffOnTile = state[this.topPanelStaffType]?.[`${this.selectedTile.x},${this.selectedTile.y}`] || [];
            this.selectedTileStaffList = staffOnTile.map(id => state.staff[id]);
        }

        this.assetManager.createScaledImage(this.coords.topPanelStaffType[this.topPanelStaffType][0], this.coords.topPanelStaffType[this.topPanelStaffType][1], 'staff_type_selection', 4);
        if (this.topPanelSelectionType === "staff") {
            this.assetManager.createScaledImage(this.coords.topPanelStaffEntry[this.staffEntryIndex][0], this.coords.topPanelStaffEntry[this.staffEntryIndex][1], 'staff_entry_selection', 4);
            if (this.gameMode === GameState.WAITING_FOR_INPUT) {
                this.assetManager.createScaledImage(this.coords.fireButton[0], this.coords.fireButton[1], 'fire_button', 4);
            }
        }

        const pageEntities = this.selectedTileStaffList.slice(this.listPage, this.listPage + 3);
        const startCoord = this.addCoords(this.coords.staffListPanel, this.scaleCoord([20, 60]));
        
        for (let i = 0; i < pageEntities.length; i++) {
            const entity = pageEntities[i];
            const currentStartCoord = this.addCoords(startCoord, this.scaleCoord([0, i * 51]));
            
            // Render type text
            this.addText(
                currentStartCoord[0], 
                currentStartCoord[1] + (5 * this.scaleFactor), 
                `${entity.subclass.charAt(0).toUpperCase() + entity.subclass.slice(1)} ${entity.subtype.charAt(0).toUpperCase() + entity.subtype.slice(1)}`, 
                this.assetManager.getFontStyle('mediumFixedWidth', '#000000')
            );
            
            // Format success metric value
            const successMetricValue = entity.success_metric === "amount_cleaned" 
                ? `${entity.success_metric_value.toFixed(2).padStart(4)}` 
                : `${Math.floor(entity.success_metric_value).toString().padStart(4)}`;

            // Create success metric text
            const successMetricText = `${entity.success_metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: ${successMetricValue}`;
            this.addText(
                currentStartCoord[0], 
                currentStartCoord[1] + (28 * this.scaleFactor), 
                successMetricText, 
                this.assetManager.getFontStyle('smallFixedWidth', '#000000')
            );
            
            // Render salary text
            this.addText(
                currentStartCoord[0] + (300 * this.scaleFactor), 
                currentStartCoord[1] + (5 * this.scaleFactor), 
                `Salary: ${entity.salary}`, 
                this.assetManager.getFontStyle('smallFixedWidth', '#000000')
            );
            
            // Render operating cost text
            this.addText(
                currentStartCoord[0] + (300 * this.scaleFactor), 
                currentStartCoord[1] + (28 * this.scaleFactor), 
                `Operating Cost: ${entity.operating_cost}`, 
                this.assetManager.getFontStyle('smallFixedWidth', '#000000')
            );
        }

        // Show up/down buttons
        // FIXME: Only show when necessary
        if (this.listPage >= 1) {
            this.assetManager.createScaledImage(this.coords.staffListUpButton[0], this.coords.staffListUpButton[1], 'up_button', 4);
        }
        if (this.listPage + 3 < this.selectedTileStaffList.length) {
            this.assetManager.createScaledImage(this.coords.staffListDownButton[0], this.coords.staffListDownButton[1], 'down_button', 4);
        }

        // Attraction list
        let tileAttributes = [];
        if (this.selectedTileType === "ride") {
            if (this.newTileSelected) {
                this.textInputs.modify_price.modify.value = this.selectedTile.ticket_price.toString();
                this.newTileSelected = false;
            }

            this.addText(
                this.coords.selectedTilePanel[0] + 25, 
                this.coords.selectedTilePanel[1] + 3, 
                `${this.selectedTile.subclass.charAt(0).toUpperCase() + this.selectedTile.subclass.slice(1)} ${this.selectedTile.subtype.charAt(0).toUpperCase() + this.selectedTile.subtype.slice(1).replace(/_/g, ' ')}`, 
                this.assetManager.getFontStyle('mediumFixedWidth', '#000000')
            );

            tileAttributes = [
                ["Cleanliness", this.selectedTile.cleanliness],
                ["Uptime", this.selectedTile.uptime],
                ["Out Of Service", this.selectedTile.out_of_service],
                ["Capacity", this.selectedTile.capacity],
                ["Intensity", this.selectedTile.intensity],
                ["Excitement", this.selectedTile.excitement],
                ["Revenue", this.selectedTile.revenue_generated],
                ["Costs", this.selectedTile.operating_cost],
                ["# Guests", this.selectedTile.guests_entertained],
                ["Times Op.", this.selectedTile.times_operated],
                ["Cost/Op.", this.selectedTile.operating_cost],
                ["Guests/Op.", this.selectedTile.avg_guests_per_operation],
                ["Wait Time", this.selectedTile.avg_wait_time],
                ["Breakdown %", (this.selectedTile.breakdown_rate * 100).toFixed(2)]
            ];

        } else if (this.selectedTileType === "shop") {
            if (this.newTileSelected) {
                this.textInputs.modify_price.modify.value = this.selectedTile.item_price.toString();
                this.textInputs.modify_order_quantity.modify.value = this.selectedTile.order_quantity.toString();
                this.newTileSelected = false;
            }
            
            this.addText(
                this.coords.selectedTilePanel[0] + 25, 
                this.coords.selectedTilePanel[1] + 3, 
                `${this.selectedTile.subclass.charAt(0).toUpperCase() + this.selectedTile.subclass.slice(1)} ${this.selectedTile.subtype.charAt(0).toUpperCase() + this.selectedTile.subtype.slice(1).replace(/_/g, ' ')} Shop`, 
                this.assetManager.getFontStyle('mediumFixedWidth', '#000000')
            );
            
            tileAttributes = [
                ["Cleanliness", this.selectedTile.cleanliness],
                ["Uptime", this.selectedTile.uptime],
                ["Out Of Service", this.selectedTile.out_of_service],
                ["Item Cost", this.selectedTile.item_cost],
                ["Item Price", this.selectedTile.item_price],
                ["Order Qty.", this.selectedTile.order_quantity],
                ["Inventory", this.selectedTile.inventory],
                ["Revenue", this.selectedTile.revenue_generated],
                ["Costs", this.selectedTile.operating_cost],
                ["", ""], // Empty row for spacing
                ["# Guests", this.selectedTile.guests_served],
                ["# Restocks", this.selectedTile.number_of_restocks]
            ];

        } else if (this.selectedTileType === "path") {
            this.addText(
                this.coords.selectedTilePanel[0] + 25, 
                this.coords.selectedTilePanel[1] + 3, 
                "Path", 
                this.assetManager.getFontStyle('mediumFixedWidth', '#696969')
            );
            
            tileAttributes = [
                ["Cleanliness", this.selectedTile.cleanliness]
            ];

        } else if (this.selectedTileType === "water") {
            this.addText(
                this.coords.selectedTilePanel[0] + 25, 
                this.coords.selectedTilePanel[1] + 3, 
                "Water", 
                this.assetManager.getFontStyle('mediumFixedWidth', '#0000FF')
            );
            
            tileAttributes = [];
        }

        // Price change text box
        if (["ride", "shop", "path", "water"].includes(this.selectedTileType)) {
            this.assetManager.createScaledImage(this.coords.selectedTilePanel[0], this.coords.selectedTilePanel[1], 'selected_tile_selection', 4);

            for (let i = 0; i < tileAttributes.length; i++) {
                let [attribute, value] = tileAttributes[i];
                let textColor = "#000000"; // Black
                
                if (attribute === "Out Of Service") {
                    if (!value) {
                        continue;
                    } else {
                        textColor = "#FF0000"; // Red
                        value = "";
                    }
                } else if ((attribute === "Cleanliness" || attribute === "Uptime") && value < 0.5) {
                    textColor = "#FF0000"; // Red
                }

                const row = Math.floor(i / 3);
                const col = i % 3;
                const x = this.coords.selectedTilePanel[0] + 10 + 133 * col;
                const y = this.coords.selectedTilePanel[1] + 30 + 16 * row;
                
                this.addText(
                    x, 
                    y, 
                    attribute.padEnd(10), 
                    this.assetManager.getFontStyle('smallFixedWidth', textColor)
                );

                if (value === "") {
                    continue;
                }
                
                const valueText = typeof value === 'number' && !Number.isInteger(value) ? value.toFixed(2).padStart(4) : value.toString().padStart(4);
                this.addText(
                    x + 88, 
                    y, 
                    valueText, 
                    this.assetManager.getFontStyle('smallFixedWidth', textColor)
                );
            }

            if (this.gameMode === GameState.WAITING_FOR_INPUT && this.topPanelSelectionType === "attraction") {
                const changeableAttributes = this.selectedTileType === "ride" ? ["modify_price"] : ["modify_price", "modify_order_quantity"];

                for (let i = 0; i < changeableAttributes.length; i++) {
                    const param = changeableAttributes[i];
                    this.assetManager.createScaledImage(this.coords.changeAttributesBox[i][0], this.coords.changeAttributesBox[i][1], 'attributes_box', 4);
                    
                    const assetKey = this.textInputs[param]["modify"].active ? 'input_box_selected' : 'input_box';
                    const inputBox = this.assetManager.createScaledImage(
                        this.coords.changeAttributesBox[i][0] + (100 * this.scaleFactor), 
                        this.coords.changeAttributesBox[i][1] + (3 * this.scaleFactor), 
                        assetKey, 4
                    );
                    
                    const value = this.textInputs[param]["modify"].value;
                    let paramText = param.replace("modify_", "").replace(/_/g, " ");
                    paramText = paramText.replace("order quantity", "ord.qty.");
                    // FIXME: paramText instead of param here??
                    if (param === "item_price") {
                        paramText = "price";
                    }
                    
                    this.addText(
                        this.coords.changeAttributesBox[i][0] + (10 * this.scaleFactor), 
                        this.coords.changeAttributesBox[i][1] + (12 * this.scaleFactor), 
                        `${paramText + ':'}`.padEnd(11) + value.toString().padStart(4), 
                        this.assetManager.getFontStyle('smallFixedWidth', '#000000')
                    );

                    if (param === "item_price") {
                        const configParams = this.config[this.selectedTile.type][this.selectedTile.subtype][this.selectedTile.subclass];
                        this.addText(
                            this.coords.changeAttributesBox[i][0] + (10 * this.scaleFactor), 
                            this.coords.changeAttributesBox[i][1] + (12 * this.scaleFactor), 
                            `max: ${configParams.max_item_price}`, 
                            this.assetManager.getFontStyle('vsmallFixedWidth', '#696969')
                        );
                    }
                }
                
                this.assetManager.createScaledImage(this.coords.modifyButton[0], this.coords.modifyButton[1], 'modify_button', 4);
                this.assetManager.createScaledImage(this.coords.sellButton[0], this.coords.sellButton[1], 'sell_button', 4);
            }
        }
    }

    drawBottomPanel(state) {
        // Main action type tabs
        for (const buttonType of Object.values(this.assetManager.actionTypeTabs)) {
            const coords = this.coords.actionTypeTabs[buttonType];
            const buttonTypeKey = `${buttonType}_tab`;
            const actionButton = this.assetManager.createScaledImage(coords[0], coords[1], buttonTypeKey, 4);
        }

        // Panel background
        const panelBackground = this.assetManager.createScaledImage(this.coords.bottomPanel[0], this.coords.bottomPanel[1], 'bottom_panel', 3);
        const actionTabSelection = this.assetManager.createScaledImage(
            this.coords.actionTypeTabs[this.bottomPanelActionType][0] - (6 * this.scaleFactor), 
            this.coords.actionTypeTabs[this.bottomPanelActionType][1] - (6 * this.scaleFactor), 
            'action_tab_selection', 4
        );

        let costText = "";
        if (["ride", "shop", "staff"].includes(this.bottomPanelActionType)) {
            this.subtypeSelection[this.bottomPanelActionType] = 
                this.choiceOrder[this.bottomPanelActionType][this.subtypeSelectionIdx[this.bottomPanelActionType]];
            const entitySubtype = this.subtypeSelection[this.bottomPanelActionType];

            this.currentAvailableColors[entitySubtype] = state["available_entities"][entitySubtype];
            const colorSelectionBorder = this.assetManager.createScaledImage(
                this.coords.colorSelection[this.colorSelection[entitySubtype]][0] - 4 * this.scaleFactor,
                this.coords.colorSelection[this.colorSelection[entitySubtype]][1] - 4 * this.scaleFactor,
                'color_selection_border', 4);
            
            for (const color of Visualizer.colorChoices) {
                if (this.currentAvailableColors[entitySubtype].includes(color)) {
                    const colorButton = this.assetManager.createScaledImage(
                        this.coords.colorSelection[color][0],
                        this.coords.colorSelection[color][1],
                        `${color}_button`, 4
                    );
                }
            }

            for (let i = 0; i < 3; i++) {
                const baseBox = this.assetManager.createScaledImage(this.coords.subtypesChoices[i][0], this.coords.subtypesChoices[i][1], 'base_box', 4);
                const entityKey = this.choiceOrder[this.bottomPanelActionType][i];
                const colorKey = this.colorSelection[entityKey];
                
                // Get dimensions for centering calculation
                const boxWidth = baseBox.displayWidth;
                const boxHeight = baseBox.displayHeight;
                
                // Create entity image to get its dimensions
                const tempEntityImage = this.assetManager.createScaledImage(0, 0, `entity_${entityKey}_${colorKey}`, 4);
                const entityWidth = tempEntityImage.displayWidth;
                const entityHeight = tempEntityImage.displayHeight;
                
                // Calculate centering offsets
                const centeringX = (boxWidth - entityWidth) / 2;
                const centeringY = (boxHeight - entityHeight) / 2;
                
                // Position the entity image with proper centering
                const entityImage = this.assetManager.createScaledImage(
                    this.coords.subtypesChoices[i][0] + centeringX,
                    this.coords.subtypesChoices[i][1] + centeringY,
                    `entity_${entityKey}_${colorKey}`, 4
                );
                
                // Clean up the temporary image
                tempEntityImage.destroy();
            }
            
            const baseSelection = this.assetManager.createScaledImage(
                this.coords.subtypesChoices[this.subtypeSelectionIdx[this.bottomPanelActionType]][0],
                this.coords.subtypesChoices[this.subtypeSelectionIdx[this.bottomPanelActionType]][1],
                'base_selection', 4
            );

            if (this.bottomPanelActionType === "staff") {
                const staffParams = this.config["staff"][entitySubtype][this.colorSelection[entitySubtype]];
                const salary = staffParams['salary'] >= 1000 ? `${staffParams['salary']/1000}K` : staffParams['salary'].toString();
                costText = `$${salary.padStart(3)}/day`;
                const bigDescriptionBox = this.assetManager.createScaledImage(this.coords.bigDescriptionBox[0], this.coords.bigDescriptionBox[1], 'big_description_box', 5);
                
                const notes = staffParams["notes"].split(".");
                this.addText(
                    this.coords.bigDescriptionBox[0] + 20 * this.scaleFactor,
                    this.coords.bigDescriptionBox[1] + 20 * this.scaleFactor,
                    notes[0].trim() + ".",
                    this.assetManager.getFontStyle('smallFixedWidth', '#000000')
                );
                
                if (notes.length > 1 && notes[1] !== "") {
                    this.addText(
                        this.coords.bigDescriptionBox[0] + 20 * this.scaleFactor,
                        this.coords.bigDescriptionBox[1] + 50 * this.scaleFactor,
                        notes[1].trim() + ".",
                        this.assetManager.getFontStyle('smallFixedWidth', '#000000')
                    );
                }
            }
    
            else if (this.bottomPanelActionType === "ride") {
                const rideParams = this.config["rides"][entitySubtype][this.colorSelection[entitySubtype]];
                for (let i = 0; i < 6; i++) {
                    const param = ["excitement", "intensity", "capacity", "cost_per_operation", "breakdown_rate", "ticket_price"][i];
                    const attributesBox = this.assetManager.createScaledImage(this.coords.attributesBox[i][0], this.coords.attributesBox[i][1], 'attributes_box', 4);
                    
                    let value = rideParams[param];
                    if (value === -1) {
                        const selectedRide = `${entitySubtype}_${this.colorSelection[entitySubtype]}`;
                        const assetKey = this.textInputs[param][selectedRide]["active"] ? 'input_box_selected' : 'input_box';
                        const assetImage = this.assetManager.createScaledImage(
                            this.coords.attributesBox[i][0] + 100 * this.scaleFactor,
                            this.coords.attributesBox[i][1] + 5 * this.scaleFactor,
                            assetKey, 5
                        );
                        value = this.textInputs[param][selectedRide]["value"];
                    }
    
                    let paramText = param;
                    if (param === "cost_per_operation") {
                        paramText = "cost / op.";
                    } else if (param === "breakdown_rate") {
                        paramText = "break %";
                        value = (value * 100).toFixed(1);
                    } else if (param === "ticket_price") {
                        paramText = "price";
                    } else {
                        paramText = param.replace("_", " ");
                    }
                    const buildingCost = rideParams['building_cost'] >= 1000 ? `${rideParams['building_cost']/1000}K` : rideParams['building_cost'].toString();
                    costText = `$${buildingCost.padStart(3)}`;
                    
                    this.addText(
                        this.coords.attributesBox[i][0] + 10 * this.scaleFactor,
                        this.coords.attributesBox[i][1] + 16 * this.scaleFactor,
                        `${paramText.padEnd(11)}${value.toString().padStart(4)}`,
                        this.assetManager.getFontStyle('smallFixedWidth', '#000000')
                    );
                    
                    if (param === "ticket_price") {
                        this.addText(
                            this.coords.attributesBox[i][0] + 15 * this.scaleFactor,
                            this.coords.attributesBox[i][1] + 27 * this.scaleFactor,
                            `max: ${rideParams['max_ticket_price']}`,
                            this.assetManager.getFontStyle('vsmallFixedWidth', '#666666')
                        );
                    }
                }
            }
    
            else if (this.bottomPanelActionType === "shop") {
                const shopParams = this.config["shops"][entitySubtype][this.colorSelection[entitySubtype]];
                let selectedShop = '';
                for (let i = 0; i < 3; i++) {
                    const param = ["item_cost", "item_price", "order_quantity"][i];
                    const attributesBox = this.assetManager.createScaledImage(this.coords.attributesBox[i][0], this.coords.attributesBox[i][1], 'attributes_box', 4);

                    let value = shopParams[param];
                    if (value === -1) {
                        selectedShop = `${entitySubtype}_${this.colorSelection[entitySubtype]}`;
                        const assetKey = this.textInputs[param][selectedShop]["active"] ? 'input_box_selected' : 'input_box';
                        const inputBox = this.assetManager.createScaledImage(
                            this.coords.attributesBox[i][0] + 100 * this.scaleFactor,
                            this.coords.attributesBox[i][1] + 5 * this.scaleFactor,
                            assetKey, 4
                        );
                        value = this.textInputs[param][selectedShop]["value"];
                    }
    
                    let paramText = param.replace("_", " ");
                    if (param === "item_price") {
                        paramText = "price";
                    }
                    else if (param === "order_quantity") {
                        paramText = "ord.qty.";
                    }
                    
                    this.addText(
                        this.coords.attributesBox[i][0] + 10 * this.scaleFactor,
                        this.coords.attributesBox[i][1] + 16 * this.scaleFactor,
                        `${paramText.padEnd(11)}${value.toString().padStart(4)}`,
                        this.assetManager.getFontStyle('smallFixedWidth', '#000000')
                    );
                    
                    if (param === "item_price") {
                        this.addText(
                            this.coords.attributesBox[i][0] + 15 * this.scaleFactor,
                            this.coords.attributesBox[i][1] + 27 * this.scaleFactor,
                            `max: ${shopParams['max_item_price']}`,
                            this.assetManager.getFontStyle('vsmallFixedWidth', '#666666')
                        );
                    }
                }
    
                const descriptionBox = this.assetManager.createScaledImage(this.coords.descriptionBox[0], this.coords.descriptionBox[1], 'description_box', 4);
                this.addText(
                    this.coords.descriptionBox[0] + 20,
                    this.coords.descriptionBox[1] + 10,
                    shopParams["notes"],
                    this.assetManager.getFontStyle('smallFixedWidth', '#000000')
                );
    
                const buildingCost = shopParams['building_cost'] >= 1000 ? `${shopParams['building_cost']/1000}K` : shopParams['building_cost'].toString();
                try {
                    const dailyCost = shopParams["item_cost"] * parseInt(this.textInputs["order_quantity"][selectedShop]["value"]);
                    if (isNaN(dailyCost)) {
                        throw new Error("dailyCost is NaN");
                    }
                    const dailyCostStr = dailyCost >= 1000 ? `${(dailyCost/1000).toFixed(1)}K` : dailyCost.toString();
                    costText = `$${buildingCost.padStart(3)}+$${dailyCostStr.padStart(3)}/day`;
                } catch {
                    costText = `$${buildingCost.padStart(3)}`;
                }
            }
        }

        // Display for selected list option
        if (this.bottomPanelActionType === "research") {
            const setResearchButton = this.assetManager.createScaledImage(this.coords.setResearchButton[0], this.coords.setResearchButton[1], 'set_research_button', 4);
            
            const speedCost = this.config['research']['speed_cost'][this.resSpeedChoice] >= 1000 ? `${this.config['research']['speed_cost'][this.resSpeedChoice]/1000}K` : this.config['research']['speed_cost'][this.resSpeedChoice].toString();
            this.addText(
                this.coords.setResearchButton[0] + -10 * this.scaleFactor,
                this.coords.setResearchButton[1] + 45 * this.scaleFactor,
                `$${speedCost.padStart(3)}/day`,
                this.assetManager.getFontStyle('mediumFixedWidth', '#000000')
            );

            this.addText(
                this.coords.bottomPanel[0] + 50 * this.scaleFactor,
                this.coords.bottomPanel[1] + 25 * this.scaleFactor,
                "Topics:",
                this.assetManager.getFontStyle('medium', '#000000')
            );
            this.addText(
                this.coords.bottomPanel[0] + 400 * this.scaleFactor,
                this.coords.bottomPanel[1] + 25 * this.scaleFactor,
                "Speed:",
                this.assetManager.getFontStyle('medium', '#000000')
            );

            for (const [entity, assetKey] of Object.entries(this.assetManager.researchEntityChoices)) {
                const resBox = this.assetManager.createScaledImage(this.coords.resEntities[entity][0], this.coords.resEntities[entity][1], 'res_box', 4);

                // Get dimensions for centering calculation
                const boxWidth = resBox.displayWidth;
                const boxHeight = resBox.displayHeight;
                
                // Create entity image to get its dimensions
                const tempEntityImage = this.assetManager.createScaledImage(0, 0, assetKey, 4);
                const entityWidth = tempEntityImage.displayWidth;
                const entityHeight = tempEntityImage.displayHeight;
                
                // Calculate centering offsets
                const centeringX = (boxWidth - entityWidth) / 2;
                const centeringY = (boxHeight - entityHeight) / 2;
                
                // Position the entity image with proper centering
                const entityImage = this.assetManager.createScaledImage(
                    this.coords.resEntities[entity][0] + centeringX,
                    this.coords.resEntities[entity][1] + centeringY,
                    assetKey, 4
                );
                
                // Clean up the temporary image
                tempEntityImage.destroy();

                // entityImage.setTint(0x808080); // Make grayscale
                if (this.resAttractionSelections.includes(entity)) {
                    const resSelection = this.assetManager.createScaledImage(this.coords.resEntities[entity][0], this.coords.resEntities[entity][1], 'res_selection', 4);
                }
            }

            // Draw speed selection boxes and text
            for (const speed of ["none", "slow", "medium", "fast"]) {
                const resSpeedBox = this.assetManager.createScaledImage(this.coords.resSpeedChoices[speed][0], this.coords.resSpeedChoices[speed][1], 'res_speed_box', 4);
                // Draw text label for each speed
                const speedText = this.addText(
                    this.coords.resSpeedChoices[speed][0] + 30 * this.scaleFactor,
                    this.coords.resSpeedChoices[speed][1] + 15 * this.scaleFactor,
                    speed.charAt(0).toUpperCase() + speed.slice(1),
                    this.assetManager.getFontStyle('largeFixedWidth', '#000000')
                );
            }

            // Draw selection border on the currently selected speed
            const resSpeedSelection = this.assetManager.createScaledImage(this.coords.resSpeedChoices[this.resSpeedChoice][0], this.coords.resSpeedChoices[this.resSpeedChoice][1], 'res_speed_selection', 4);
        }

        else if (this.bottomPanelActionType === "survey_guests") {
            const bigDescriptionBox = this.assetManager.createScaledImage(this.coords.bigDescriptionBox[0], this.coords.bigDescriptionBox[1], 'big_description_box', 4);
            const numGuestsInputBoxKey = this.textInputs["survey_guests"]["survey_guests"]["active"] ? 'input_box_selected' : 'input_box';
            const numGuestsInputBoxImage = this.assetManager.createScaledImage(this.coords.bigDescriptionBox[0] + 450 * this.scaleFactor, this.coords.bigDescriptionBox[1] + 30 * this.scaleFactor, numGuestsInputBoxKey, 5);
            this.addText(
                this.coords.bigDescriptionBox[0] + 478 * this.scaleFactor,
                this.coords.bigDescriptionBox[1] + 40 * this.scaleFactor,
                this.textInputs["survey_guests"]["survey_guests"]["value"].padStart(2),
                this.assetManager.getFontStyle('smallFixedWidth', '#000000')
            );
            this.addText(
                this.coords.bigDescriptionBox[0] + 25 * this.scaleFactor,
                this.coords.bigDescriptionBox[1] + 26 * this.scaleFactor,
                "number of guests to survey:",
                this.assetManager.getFontStyle('medium', '#000000')
            );
            this.addText(
                this.coords.bigDescriptionBox[0] + 40 * this.scaleFactor,
                this.coords.bigDescriptionBox[1] + 55 * this.scaleFactor,
                `max guests: ${this.config['max_guests_to_survey']}`,
                this.assetManager.getFontStyle('smallFixedWidth', '#666666')
            );
            const surveyGuestsButton = this.assetManager.createScaledImage(this.coords.surveyGuestsButton[0], this.coords.surveyGuestsButton[1], 'survey_guests_button', 4);
            
            if (this.textInputs["survey_guests"]["survey_guests"]["value"] !== "") {
                const surveyCost = this.config['per_guest_survey_cost'] * parseInt(this.textInputs['survey_guests']['survey_guests']['value']) >= 1000 ? `${this.config['per_guest_survey_cost'] * parseInt(this.textInputs['survey_guests']['survey_guests']['value'])/1000}K` : this.config['per_guest_survey_cost'] * parseInt(this.textInputs['survey_guests']['survey_guests']['value']).toString();
                this.addText(
                    this.coords.surveyGuestsButton[0] + -10 * this.scaleFactor,
                    this.coords.surveyGuestsButton[1] + 45 * this.scaleFactor,
                    `$${surveyCost}`.padStart(3),
                    this.assetManager.getFontStyle('mediumFixedWidth', '#000000')
                );
            }

            if (state["guest_survey_results"]["list_of_results"].length > 0) {
                const showResultsButtonActive = this.assetManager.createScaledImage(this.coords.showResultsButton[0], this.coords.showResultsButton[1], 'show_results_button_active', 4);
            } else {
                const showResultsButtonInactive = this.assetManager.createScaledImage(this.coords.showResultsButton[0], this.coords.showResultsButton[1], 'show_results_button_inactive', 4);
            }
        }

        else if (this.bottomPanelActionType === "terraform") {
            this.addText(
                this.coords.terraformButtons["add"]["path"][0],
                this.coords.terraformButtons["add"]["path"][1] + 128 * this.scaleFactor,
                `$${this.config['path_addition_cost'] >= 1000 ? `${this.config['path_addition_cost']/1000}K` : this.config['path_addition_cost'].toString()}`,
                this.assetManager.getFontStyle('mediumFixedWidth', '#000000')
            );
            this.addText(
                this.coords.terraformButtons["remove"]["path"][0],
                this.coords.terraformButtons["remove"]["path"][1] + 128 * this.scaleFactor,
                `$${this.config['path_removal_cost'] >= 1000 ? `${this.config['path_removal_cost']/1000}K` : this.config['path_removal_cost'].toString()}`,
                this.assetManager.getFontStyle('mediumFixedWidth', '#000000')
            );
            this.addText(
                this.coords.terraformButtons["add"]["water"][0],
                this.coords.terraformButtons["add"]["water"][1] + 128 * this.scaleFactor,
                `$${this.config['water_addition_cost'] >= 1000 ? `${this.config['water_addition_cost']/1000}K` : this.config['water_addition_cost'].toString()}`,
                this.assetManager.getFontStyle('mediumFixedWidth', '#000000')
            );
            this.addText(
                this.coords.terraformButtons["remove"]["water"][0],
                this.coords.terraformButtons["remove"]["water"][1] + 128 * this.scaleFactor,
                `$${this.config['water_removal_cost'] >= 1000 ? `${this.config['water_removal_cost']/1000}K` : this.config['water_removal_cost'].toString()}`,
                this.assetManager.getFontStyle('smallFixedWidth', '#000000')
            );
            
            for (const terraformAction of ["add", "remove"]) {
                for (const terraformType of ["path", "water"]) {
                    if (this.terraformAction === `${terraformAction}_${terraformType}`) {
                        const actionIng = terraformAction === "remove" ? "removing" : `${terraformAction}ing`;

                        const terraformButton = this.assetManager.createScaledImage(
                            this.coords.terraformButtons[terraformAction][terraformType][0],
                            this.coords.terraformButtons[terraformAction][terraformType][1],
                            `${actionIng}_${terraformType}`,
                            4
                        );
                    } else {
                        const terraformButton = this.assetManager.createScaledImage(
                            this.coords.terraformButtons[terraformAction][terraformType][0],
                            this.coords.terraformButtons[terraformAction][terraformType][1],
                            `${terraformAction}_${terraformType}`,
                            4
                        );
                    }
                }
            }
        }

        if (["ride", "shop", "staff"].includes(this.bottomPanelActionType)) {
            if (this.waitingForGridClick) {
                this.assetManager.createScaledImage(this.coords.placeButton[0], this.coords.placeButton[1], 'placing_button', 4);
            } else {
                this.assetManager.createScaledImage(this.coords.placeButton[0], this.coords.placeButton[1], 'place_button', 4);
            }
            this.addText(
                this.coords.placeButton[0] + -10 * this.scaleFactor,
                this.coords.placeButton[1] + 45 * this.scaleFactor,
                costText,
                this.assetManager.getFontStyle('mediumFixedWidth', '#000000')
            );
        }

        else if (this.bottomPanelActionType === "wait") {
            this.assetManager.createScaledImage(this.coords.waitButton[0], this.coords.waitButton[1], 'wait_button', 4);

            if (this.sandboxMode) {
                // Sandbox actions text - dynamically centered
                const sandboxActionsText = this.addText(
                    0, // temporary x position
                    this.coords.bottomPanel[1] + this.coords.sandboxActionsYOffset - 10 * this.scaleFactor,
                    "Sandbox Actions",
                    this.assetManager.getFontStyle('smallFixedWidth', '#000000')
                );
                // Center the text based on its width
                const xOffset = this.coords.bottomPanel[0] + (panelBackground.displayWidth - sandboxActionsText.width) / 2;
                sandboxActionsText.setX(xOffset);
                sandboxActionsText.setDepth(9);

                // Sandbox action buttons
                this.assetManager.createScaledImage(this.coords.undoDayButton[0], this.coords.undoDayButton[1], 'undo_day_button', 4);
                this.assetManager.createScaledImage(this.coords.maxResearchButton[0], this.coords.maxResearchButton[1], 'max_research_button', 4);
                this.assetManager.createScaledImage(this.coords.maxMoneyButton[0], this.coords.maxMoneyButton[1], 'max_money_button', 4);
                this.assetManager.createScaledImage(this.coords.resetButton[0], this.coords.resetButton[1], 'reset_button', 4);
                this.assetManager.createScaledImage(this.coords.switchLayoutsButton[0], this.coords.switchLayoutsButton[1], 'switch_layouts_button', 4);
                this.assetManager.createScaledImage(this.coords.doneButton[0], this.coords.doneButton[1], 'done_button', 4);

                // Remaining days text - dynamically centered
                const budgetTextStr = `Remaining Days To Learn From: ${this.sandboxSteps}`;
                const budgetText = this.addText(
                    0, // temporary x position
                    this.coords.bottomPanel[1] + this.coords.remainingDaysToLearnFromYOffset,
                    budgetTextStr,
                    this.assetManager.getFontStyle('smallFixedWidth', '#000000')
                );
                // Center the text based on its width
                const budgetPanelX = this.coords.bottomPanel[0] + (panelBackground.displayWidth - budgetText.width) / 2;
                budgetText.setX(budgetPanelX);//budgetXOffset);
                budgetText.setDepth(9);
            }
        }
    }

    static async create(assetManager, scaleFactor = 1.0, phaserScene = null, mode = "few-shot") {
        const config = await loadConfig();
        return new Visualizer(assetManager, scaleFactor, phaserScene, config, mode);
    }

    addCoords(coord1, coord2) {
        return [coord1[0] + coord2[0], coord1[1] + coord2[1]];
    }

    isPathNeighbor(x, y, state) {
        const hasPosition = (collection, pos) => {
            if (!collection) return false;
            for (const item of Object.values(collection)) {
                if (item.x === pos[0] && item.y === pos[1]) {
                    return true;
                }
            }
            return false;
        };

        return (
            hasPosition(state.paths, [x, y]) ||
            hasPosition(state.rides, [x, y]) ||
            hasPosition(state.shops, [x, y]) ||
            (state.entrance && state.entrance.x === x && state.entrance.y === y) ||
            (state.exit && state.exit.x === x && state.exit.y === y)
        );
    }

    isWaterNeighbor(x, y, state) {
        // Helper function to check if a position exists in different data structures
        const hasPosition = (collection, pos) => {
            if (!collection) return false;
            if (collection instanceof Set || collection instanceof Map) {
                return collection.has(pos);
            }
            if (Array.isArray(collection)) {
                return collection.some(item => 
                    Array.isArray(item) && item[0] === pos[0] && item[1] === pos[1]
                );
            }
            // Handle object with string keys (e.g., "x,y")
            if (typeof collection === 'object') {
                const key = `${pos[0]},${pos[1]}`;
                if (key in collection) {
                    return true;
                }
                // Also check by iterating values (for backward compatibility)
                for (const item of Object.values(collection)) {
                    if (item && item.x === pos[0] && item.y === pos[1]) {
                        return true;
                    }
                }
            }
            return false;
        };

        return hasPosition(state.waters, [x, y]);
    }

    getTerrainAsset(pos, state, tileType) {
        const adjMap = [];
        const entrance = [state.entrance.x, state.entrance.y];
        const exit = [state.exit.x, state.exit.y];
        let neighborDiff = [[-1, 0],[0, 1], [1, 0], [0, -1]]; // up, right, down, left
        // [[0, -1],[1, 0], [0, 1], [-1, 0]];
        
        if (tileType === "water") {
            neighborDiff = neighborDiff.concat([[1, -1], [-1, -1], [-1, 1], [1, 1]]);
            // top right, top left, bottom left, bottom right
        }
        
        for (const [dx, dy] of neighborDiff) {
            const newX = pos.x + dx;
            const newY = pos.y + dy;
            
            if (tileType === "path") {
                adjMap.push(this.isPathNeighbor(newX, newY, state));
            } else if (tileType === "water") {
                adjMap.push(this.isWaterNeighbor(newX, newY, state));
            }
        }

        let assetList = tileType === "path" ? this.assetManager.paths : this.assetManager.water;

        if (adjMap[0] && adjMap[1] && adjMap[2] && adjMap[3]) {
            let asset = assetList[0];
            if (tileType === "water") {
                if (adjMap[4] && adjMap[5] && adjMap[6] && adjMap[7]) {
                    asset = asset[15];
                } else if (adjMap[4] && adjMap[5] && adjMap[6]) {
                    asset = asset[14];
                } else if (adjMap[5] && adjMap[6] && adjMap[7]) {
                    asset = asset[13];
                } else if (adjMap[6] && adjMap[7] && adjMap[4]) {
                    asset = asset[12];
                } else if (adjMap[7] && adjMap[4] && adjMap[5]) {
                    asset = asset[11];
                } else if (adjMap[4] && adjMap[6]) {
                    asset = asset[10];
                } else if (adjMap[5] && adjMap[7]) {
                    asset = asset[9];
                } else if (adjMap[4] && adjMap[5]) {
                    asset = asset[8];
                } else if (adjMap[5] && adjMap[6]) {
                    asset = asset[7];
                } else if (adjMap[6] && adjMap[7]) {
                    asset = asset[6];
                } else if (adjMap[7] && adjMap[4]) {
                    asset = asset[5];
                } else if (adjMap[4]) {
                    asset = asset[4];
                } else if (adjMap[5]) {
                    asset = asset[3];
                } else if (adjMap[6]) {
                    asset = asset[2];
                } else if (adjMap[7]) {
                    asset = asset[1];
                } else {
                    asset = asset[0];
                }
            }
            return asset;
        } else if (adjMap[0] && adjMap[2] && adjMap[3]) {
            let asset = assetList[1];
            if (tileType === "water") {
                if (adjMap[4] && adjMap[5]) {
                    asset = asset[3];
                } else if (adjMap[4]) {
                    asset = asset[2];
                } else if (adjMap[5]) {
                    asset = asset[1];
                } else {
                    asset = asset[0];
                }
            }
            return asset;
        } else if (adjMap[0] && adjMap[1] && adjMap[3]) {
            let asset = assetList[2];
            if (tileType === "water") {
                if (adjMap[5] && adjMap[6]) {
                    asset = asset[3];
                } else if (adjMap[5]) {
                    asset = asset[2];
                } else if (adjMap[6]) {
                    asset = asset[1];
                } else {
                    asset = asset[0];
                }
            }
            return asset; // path3_image
        } else if (adjMap[0] && adjMap[1] && adjMap[2]) {
            let asset = assetList[3];
            if (tileType === "water") {
                if (adjMap[6] && adjMap[7]) {
                    asset = asset[3];
                } else if (adjMap[6]) {
                    asset = asset[2];
                } else if (adjMap[7]) {
                    asset = asset[1];
                } else {
                    asset = asset[0];
                }
            }
            return asset;
        } else if (adjMap[1] && adjMap[2] && adjMap[3]) {
            let asset = assetList[4];
            if (tileType === "water") {
                if (adjMap[7] && adjMap[4]) {
                    asset = asset[3];
                } else if (adjMap[7]) {
                    asset = asset[2];
                } else if (adjMap[4]) {
                    asset = asset[1];
                } else {
                    asset = asset[0];
                }
            }
            return asset;
        } else if (adjMap[0] && adjMap[3]) {
            let asset = assetList[5];
            if (tileType === "water") {
                if (adjMap[5]) {
                    asset = asset[1];
                } else {
                    asset = asset[0];
                }
            }
            return asset;
        } else if (adjMap[0] && adjMap[1]) {
            let asset = assetList[6];
            if (tileType === "water") {
                if (adjMap[6]) {
                    asset = asset[1];
                } else {
                    asset = asset[0];
                }
            }
            return asset;
        } else if (adjMap[1] && adjMap[2]) {
            let asset = assetList[7];
            if (tileType === "water") {
                if (adjMap[7]) {
                    asset = asset[1];
                } else {
                    asset = asset[0];
                }
            }
            return asset;
        } else if (adjMap[2] && adjMap[3]) {
            let asset = assetList[8];
            if (tileType === "water") {
                if (adjMap[4]) {
                    asset = asset[1];
                } else {
                    asset = asset[0];
                }
            }
            return asset; // path9_image
        } else if (adjMap[1] && adjMap[3]) {
            return assetList[9]; // path10_image
        } else if (adjMap[0] && adjMap[2]) {
            return assetList[10]; // path11_image
        } else if (adjMap[0]) {
            return assetList[12]; // path13_image
        } else if (adjMap[1]) {
            return assetList[13]; // path14_image
        } else if (adjMap[2]) {
            return assetList[11]; // path12_image
        } else if (adjMap[3]) {
            return assetList[14]; // path16_image
        } else {
            return assetList[15];
        }
    }

    drawSelectedTile() {
        if (this.selectedTile) {
            const [x, y] = this.gridPosToPixelPos([this.selectedTile.x, this.selectedTile.y]);
            this.highlightRect = this.scene.add.graphics();
            this.highlightRect.lineStyle(2, 0xff0000);
            this.highlightRect.strokeRect(x, y, this.tileSize, this.tileSize);
            this.highlightRect.setDepth(3);
            this.assetManager.uiObjects.push(this.highlightRect);
        }
    }

    gridPosToPixelPos(pos) {
        // Flip x and y because we are using switched axes
        return [pos[1] * this.tileSize, pos[0] * this.tileSize];
    }

    drawPerson(personType, prevPos, currPos, subtype = null, subclass = null, xOffset = 0, yOffset = 0) {
        const [x0, y0] = prevPos;
        const [x1, y1] = currPos;

        const isStationary = (x0 === x1) && (y0 === y1);
        const [pixelX, pixelY] = this.gridPosToPixelPos([x1, y1]);
        const finalPixelX = pixelX + (xOffset * this.scaleFactor);
        const finalPixelY = pixelY + (yOffset * this.scaleFactor);

        let personImage;
        if (personType === "guest") {
            personImage = this.assetManager.createScaledImage(finalPixelX, finalPixelY, `guest${subclass}`, 10);
        } else if (personType === "staff") {
            personImage = this.assetManager.createScaledImage(finalPixelX, finalPixelY, `staff_${subtype}_${subclass}`, 10);
        }
    }

    drawPeople(state) {
        const guestCounts = {};
        
        // Draw guests
        for (const [id, guest] of Object.entries(state.guests || {})) {
            const prevPos = guest.prev_pos;
            const currPos = guest.curr_pos;
            const currCount = guestCounts[currPos] || 0;
            const xOffset = (currCount % 10) * 4;
            const yOffset = Math.floor(currCount / 10) * 2;
            this.drawPerson("guest", prevPos, currPos, null, guest.subclass, xOffset, yOffset);
            guestCounts[currPos] = currCount + 1;
        }
        
        // Draw staff
        const staffCounts = {};
        for (const [id, staff] of Object.entries(state.staff || {})) {
            const prevPos = staff.prev_pos;
            const currPos = [staff.x, staff.y];
            const subtype = staff.subtype;
            const subclass = staff.subclass;
            const currCount = staffCounts[currPos] || 0;
            const xOffset = (currCount % 7) * 5;
            const yOffset = Math.floor(currCount / 6) * 4;
            this.drawPerson("staff", prevPos, currPos, subtype, subclass, xOffset, yOffset + 27);
            staffCounts[currPos] = currCount + 1;
        }
    }

    drawTileState(state) {
        // Draw out of service attractions
        for (const [x, y] of state.oos_attractions || []) {
            const pixelPos = this.gridPosToPixelPos([x, y]);
            const oosImage = this.assetManager.createScaledImage(pixelPos[0], pixelPos[1], 'out_of_service', 3);
        }
        
        // Draw tile dirtiness
        for (const [x, y, cleanliness] of state.tile_dirtiness || []) {
            const pixelPos = this.gridPosToPixelPos([x, y]);
            for (let i = 0; i < 4; i++) {
                if (cleanliness < (0.8 - 0.2 * i)) {
                    const dirtImage = this.assetManager.createScaledImage(
                        pixelPos[0] - 5, 
                        pixelPos[1] + 15,
                        `cleanliness${i + 1}`, 3
                    );
                }
            }
        }
    }

    drawGameGrid(state) {
        // Create grid surface (equivalent to pygame.Surface)
        const gridSize = this.gridSize;
        const tileSize = this.tileSize;

        // Draw grid lines
        for (let x = 0; x < gridSize; x += tileSize) {
            for (let y = 0; y < gridSize; y += tileSize) {
                // Draw grid rectangle (equivalent to pygame.draw.rect)
                const graphics = this.scene.add.graphics();
                graphics.lineStyle(1, 0x006400); // darkgreen color
                graphics.strokeRect(x, y, tileSize, tileSize);
                graphics.setDepth(0);
                this.assetManager.uiObjects.push(graphics);
            }
        }

        // Draw entrance and exit
        const entrancePos = this.gridPosToPixelPos([state.entrance.x, state.entrance.y]);
        const exitPos = this.gridPosToPixelPos([state.exit.x, state.exit.y]);
        const entranceImage = this.assetManager.createScaledImage(entrancePos[0], entrancePos[1], 'entrance', 1);
        const exitImage = this.assetManager.createScaledImage(exitPos[0], exitPos[1], 'exit', 1);

        // Draw paths
        if (state.paths) {
            for (const path of Object.values(state.paths)) {
                const tileAsset = this.getTerrainAsset(path, state, "path");
                const pathPos = this.gridPosToPixelPos([path.x, path.y]);
                const pathImage = this.assetManager.createScaledImage(pathPos[0], pathPos[1], tileAsset, 1);
            };
        }
        // Draw waters
        if (state.waters) {
            for (const water of Object.values(state.waters)) {
                const waterAsset = this.getTerrainAsset(water, state, "water");
                const waterPos = this.gridPosToPixelPos([water.x, water.y]);
                const waterImage = this.assetManager.createScaledImage(waterPos[0], waterPos[1], waterAsset, 1);
            }
        }

        // Draw rides
        if (state.rides) {
            for (const [key, ride] of Object.entries(state.rides)) {
                const { x, y, subtype, subclass } = ride;
                const pixelPos = this.gridPosToPixelPos([x, y]);
                
                // Get offsets for different ride types
                const offsets = {
                    "carousel": [0, -7],
                    "ferris_wheel": [-5, -12],
                    "roller_coaster": [-1, -7]
                };
                
                const [xOffset, yOffset] = offsets[subtype] || [0, 0];
                const rideKey = `ride_${subtype}_${subclass}`;
                const rideImage = this.assetManager.createScaledImage(pixelPos[0] + xOffset, pixelPos[1] + yOffset, rideKey, 2);
            }
        }

        // Draw shops
        if (state.shops) {
            for (const [key, shop] of Object.entries(state.shops)) {
                const { x, y, subtype, subclass } = shop;
                const pixelPos = this.gridPosToPixelPos([x, y]);
                
                // Get offsets for different shop types
                const offsets = {
                    "drink": [0, -4],
                    "food": [0, -3],
                    "specialty": [0, -5]
                };
                
                const [xOffset, yOffset] = offsets[subtype] || [0, 0];
                const shopKey = `shop_${subtype}_${subclass}`;
                const shopImage = this.assetManager.createScaledImage(pixelPos[0] + xOffset, pixelPos[1] + yOffset, shopKey, 2);
            }
        }
    }

    renderBackground() {
        // Only create background once to match Python's pattern but be efficient for Phaser
        if (!this.backgroundImage) {
            this.backgroundImage = this.scene.add.image(0, 0, 'background');
            this.backgroundImage.setOrigin(0, 0); // Phaser default is 0.5, 0.5
            this.backgroundImage.setScale(this.scaleFactor);
            this.backgroundImage.setDepth(-1000);
        }
        // Ensure background is visible (matches Python's every-frame render pattern)
        if (this.backgroundImage) {
            this.backgroundImage.setVisible(true);
        }
    }

    renderGrid(state) {
        this.drawGameGrid(state);
        this.drawPeople(state);
        this.drawTileState(state);
        this.drawSelectedTile();
    }
    
    // Helper to create and track text objects
    addText(x, y, text, style, depth = 5) {
        const textObj = this.scene.add.text(Math.round(x), Math.round(y), text, style)
          .setDepth(depth)
          .setResolution(Math.max(1, Math.floor(window.devicePixelRatio || 1))); // <<—
        this.assetManager.uiObjects.push(textObj);
        return textObj;
      }
}