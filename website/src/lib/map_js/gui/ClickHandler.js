import { GameState } from './Visualizer.js';

export class ClickHandler {
    constructor(visualizer, scene) {
        this.visualizer = visualizer;
        this.scene = scene;

        this.visualizer.waitingForGridClick = false;
        this.visualizer.waitingForMove = false;
    }

    handleTutorialScreenButtons(pos) {
        if (this.visualizer.okButtonPos && this.isPointInRect(pos, this.visualizer.okButtonPos, this.getActualAssetSize('ok_button'))) {
            this.visualizer.tutorialStep += 1;
            return true;
        }
        return false;
    }

//#region Handle Action Buttons
    handleActionButtons(pos) {
        let action = null;
        let sandboxAction = null;
        
        // Handle grid clicks
        if (pos[0] < this.visualizer.gridSize) {
            if (this.visualizer.waitingForMove) {
                action = this.formatMoveAction(pos);
            }
            if (this.visualizer.waitingForGridClick) {
                if (this.visualizer.bottomPanelActionType === "terraform") {
                    action = this.formatTerraformAction(pos);
                } else {
                    action = this.formatPlaceAction(pos);
                }
            }
        }
        
        this.visualizer.waitingForMove = false;
        this.visualizer.waitingForGridClick = false;
        this.visualizer.terraformAction = "";

        const topResult = this.handleTopPanelActionButtons(pos);
        action = topResult.action || action;
        const bpResult = this.handleBottomPanelActionButtons(pos);
        action = bpResult.action || action;
        sandboxAction = bpResult.sandboxAction || sandboxAction;
        const selectionResult = this.handleSelectionScreenButtons(pos);
        sandboxAction = selectionResult.sandboxAction || sandboxAction;

        return { action, sandboxAction };
    }

    handleTopPanelActionButtons(pos) {
        let action = null;
        
        // Attraction actions
        if (this.visualizer.topPanelSelectionType === "attraction") {
            // Change price (modify button)
            if (this.isPointInRect(pos, this.visualizer.coords.modifyButton, this.getActualAssetSize('modify_button'))) {
                if (this.visualizer.selectedTile) {
                    action = this.formatModifyAction() || action;
                }
            }
            // Sell
            if (this.isPointInRect(pos, this.visualizer.coords.sellButton, this.getActualAssetSize('sell_button'))) {
                if (this.visualizer.selectedTile) {
                    this.visualizer.entityToRemove = this.visualizer.selectedTile;
                    this.visualizer.entityToRemoveType = this.visualizer.selectedTileType;
                    action = this.formatRemoveAction() || action;
                }
            }
        }

        // Staff actions (fire staff)
        if (this.visualizer.topPanelSelectionType === "staff") {
            if (this.isPointInRect(pos, this.visualizer.coords.fireButton, this.getActualAssetSize('fire_button'))) {
                if (this.visualizer.selectedTileStaffList.length > this.visualizer.staffEntryIndex) {
                    this.visualizer.entityToRemove = this.visualizer.selectedTileStaffList[this.visualizer.staffEntryIndex];
                    this.visualizer.entityToRemoveType = "staff";
                    action = this.formatRemoveAction() || action;
                }
            }
        }

        // Move attraction or staff
        if (this.isPointInRect(pos, this.visualizer.coords.moveButton, this.getActualAssetSize('move_button'))) {
            if (this.visualizer.topPanelSelectionType === "attraction" && this.visualizer.selectedTile) {
                this.visualizer.entityToMove = this.visualizer.selectedTile;
                this.visualizer.entityToMoveType = this.visualizer.selectedTileType;
                this.visualizer.waitingForMove = true;
            } else if (this.visualizer.staffEntryIndex < this.visualizer.selectedTileStaffList.length) {
                this.visualizer.entityToMove = this.visualizer.selectedTileStaffList[this.visualizer.staffEntryIndex];
                this.visualizer.entityToMoveType = "staff";
                this.visualizer.waitingForMove = true;
            }
        }
           
        return { action, sandboxAction: null };
    }

    handleBottomPanelActionButtons(pos) {
        let action = null;
        let sandboxAction = null;

        // Place ride/shop/staff
        if (["ride", "shop", "staff"].includes(this.visualizer.bottomPanelActionType)) {
            if (this.isPointInRect(pos, this.visualizer.coords.placeButton, this.getActualAssetSize('place_button')) &&
                this.visualizer.gameMode === GameState.WAITING_FOR_INPUT) {
                this.visualizer.waitingForGridClick = true;
                if (this.visualizer.tutorialStep == 9) {
                    this.visualizer.tutorialStep++;
                }
            }
        }
        // Research
        else if (this.visualizer.bottomPanelActionType === "research") {
            if (this.isPointInRect(pos, this.visualizer.coords.setResearchButton, this.getActualAssetSize('set_research_button'))) {
                action = this.formatResearchAction() || action;
            }
        }
        // Survey guests
        else if (this.visualizer.bottomPanelActionType === "survey_guests") {
            if (this.isPointInRect(pos, this.visualizer.coords.surveyGuestsButton, this.getActualAssetSize('survey_guests_button'))) {
                action = this.formatSurveyGuestAction() || action;
            }
        }
        // Terraform
        else if (this.visualizer.bottomPanelActionType === "terraform") {
            for (const terraformType of ["path", "water"]) {
                for (const terraformAction of ["add", "remove"]) {
                    if (this.isPointInRect(pos, this.visualizer.coords.terraformButtons[terraformAction][terraformType], this.getActualAssetSize(`${terraformAction}_${terraformType}`))) {
                        this.visualizer.waitingForGridClick = true;
                        this.visualizer.terraformAction = `${terraformAction}_${terraformType}`;
                    }
                }
            }
        }
        // Wait/Sandbox
        else if (this.visualizer.bottomPanelActionType === "wait") {
            if (this.isPointInRect(pos, this.visualizer.coords.waitButton, this.getActualAssetSize('wait_button'))) {
                action = this.formatWaitAction() || action;
                return { action, sandboxAction };
            }

            if (this.visualizer.sandboxMode) {
                if (this.isPointInRect(pos, this.visualizer.coords.undoDayButton, this.getActualAssetSize('undo_day_button'))) {
                    sandboxAction = this.formatUndoDayAction() || sandboxAction;
                } else if (this.isPointInRect(pos, this.visualizer.coords.maxResearchButton, this.getActualAssetSize('max_research_button'))) {
                    sandboxAction = this.formatMaxResearchAction() || sandboxAction;
                } else if (this.isPointInRect(pos, this.visualizer.coords.maxMoneyButton, this.getActualAssetSize('max_money_button'))) {
                    sandboxAction = this.formatMaxMoneyAction() || sandboxAction;
                } else if (this.isPointInRect(pos, this.visualizer.coords.resetButton, this.getActualAssetSize('reset_button'))) {
                    sandboxAction = this.formatResetAction() || sandboxAction;
                } else if (this.isPointInRect(pos, this.visualizer.coords.switchLayoutsButton, this.getActualAssetSize('switch_layouts_button'))) {
                    this.visualizer.gameMode = GameState.LAYOUT_SELECTION_SCREEN;
                } else if (this.isPointInRect(pos, this.visualizer.coords.doneButton, this.getActualAssetSize('done_button'))) {
                    this.visualizer.sandboxMode = false;
                    this.visualizer.gameMode = GameState.MODE_SELECTION_SCREEN;
                }
            }
        }

        return { action, sandboxAction };
    }
//#endregion Handle Action Buttons

//#region Handle Selection Buttons
    handleTopPanelSelectionButtons(pos) {
        // Identify entry type
        if (this.isPointInRect(pos, this.visualizer.coords.selectedTilePanel, this.getActualAssetSize('selected_tile_selection'))) {
            this.visualizer.topPanelSelectionType = "attraction";
        }
        
        // Staff list panel button
        if (this.isPointInRect(pos, this.visualizer.coords.staffListPanel, this.getActualAssetSize('staff_list_panel'))) {
            this.visualizer.topPanelSelectionType = "staff";
            // If entry type is staff, identify subtype
            for (const staffType of ["janitors", "mechanics", "specialists"]) {
                if (this.isPointInRect(pos, this.visualizer.coords.topPanelStaffType[staffType], this.getActualAssetSize('staff_type_selection'))) {
                    this.visualizer.topPanelStaffType = staffType;
                }
            }

            // If entry type is staff, get the index of the selected staff
            if (this.visualizer.coords.topPanelStaffEntry) {
                for (let i = 0; i < this.visualizer.coords.topPanelStaffEntry.length; i++) {
                    const coord = this.visualizer.coords.topPanelStaffEntry[i];
                    if (this.isPointInRect(pos, coord, this.getActualAssetSize('staff_entry_selection'))) {
                        this.visualizer.staffEntryIndex = i;
                    }
                }
            }
        }
        // Attention: this may create this button click even when up down buttons are not visible
        if (this.isPointInRect(pos, this.visualizer.coords.staffListUpButton, this.getActualAssetSize('up_button'))) {
            this.visualizer.listPage -= 1;
        }

        if (this.isPointInRect(pos, this.visualizer.coords.staffListDownButton, this.getActualAssetSize('down_button'))) {
            this.visualizer.listPage += 1;
        }
    }

    handleBottomPanelSelectionButtons(pos) {
        // Picking action tab
        for (const buttonType of this.visualizer.assetManager.actionTypeTabs) {
            if (this.isPointInRect(pos, this.visualizer.coords.actionTypeTabs[buttonType], this.getActualAssetSize(`${buttonType}_tab`))) {
                this.visualizer.bottomPanelActionType = buttonType;
                if ((this.visualizer.tutorialStep == 21 && buttonType === "shop") || 
                    (this.visualizer.tutorialStep == 26 && buttonType === "staff") ||
                    (this.visualizer.tutorialStep == 28 && buttonType === "research") ||
                    (this.visualizer.tutorialStep == 29 && buttonType === "survey_guests") ||
                    (this.visualizer.tutorialStep == 30 && buttonType === "wait")) {
                    this.visualizer.tutorialStep++;
                }
                return;
            }
        }
        
        // Changing options
        if (["ride", "shop", "staff"].includes(this.visualizer.bottomPanelActionType)) {
            for (let i = 0; i < 3; i++) {
                if (this.isPointInRect(pos, this.visualizer.coords.subtypesChoices[i], this.getActualAssetSize('base_box'))) {
                    this.visualizer.subtypeSelectionIdx[this.visualizer.bottomPanelActionType] = i;
                    if (this.visualizer.tutorialStep == 3 && i == 0) {
                        this.visualizer.tutorialStep++;
                    } else if (this.visualizer.tutorialStep == 22) {
                        this.visualizer.tutorialStep++;
                    }
                    return;
                }
            }

            // Changing color for rides or shops or staff
            for (const color of ["yellow", "blue", "green", "red"]) {
                if (this.isPointInRect(pos, this.visualizer.coords.colorSelection[color], this.getActualAssetSize(`${color}_button`)) &&
                    this.visualizer.currentAvailableColors[this.visualizer.subtypeSelection[this.visualizer.bottomPanelActionType]].includes(color)) {
                    this.visualizer.colorSelection[this.visualizer.subtypeSelection[this.visualizer.bottomPanelActionType]] = color;
                    
                    if (this.visualizer.tutorialStep == 5 && color == "green") {
                        this.visualizer.tutorialStep++;
                    } else if (this.visualizer.tutorialStep == 7 && color == "yellow") {
                        this.visualizer.tutorialStep++;
                    }
                    return;
                }
            }
        }
        
        // Picking research direction
        if (this.visualizer.bottomPanelActionType === "research") {
            // Research attraction selection
            for (const choice of ["carousel", "ferris_wheel", "roller_coaster", "drink", "food", "specialty", "janitor", "mechanic", "specialist"]) {
                const coord = this.visualizer.coords.resEntities[choice];
                if (this.isPointInRect(pos, coord, this.getActualAssetSize('res_box'))) {
                    if (!this.visualizer.resAttractionSelections.includes(choice)) {
                        this.visualizer.resAttractionSelections.push(choice);
                    } else {
                        this.visualizer.resAttractionSelections = this.visualizer.resAttractionSelections.filter(item => item !== choice);
                    }
                    break;
                }
            }
                    
            // Research speed selection
            for (const choice of ["none", "slow", "medium", "fast"]) {
                const coord = this.visualizer.coords.resSpeedChoices[choice];
                if (this.isPointInRect(pos, coord, this.getActualAssetSize(`res_speed_${choice}`))) {
                    this.visualizer.resSpeedChoice = choice;
                    break;
                }
            }
        }

        // Survey guests
        if (this.visualizer.bottomPanelActionType === "survey_guests") {
            if (this.isPointInRect(pos, this.visualizer.coords.showResultsButton, this.getActualAssetSize('show_results_button_active'))) {
                this.visualizer.guestSurveyResultsIsOpen = true;
                return;
            }
        }
    }

    handleMiscSelectionButtons(pos) {
        // Animation speed
        if (this.isPointInRect(pos, this.visualizer.coords.playbackIncrease, this.getActualAssetSize('up_button'))) {
            if (this.visualizer.updateDelay !== 1) {
                this.visualizer.updateDelay /= 2;
            }
            return;
        }
        
        if (this.isPointInRect(pos, this.visualizer.coords.playbackDecrease, this.getActualAssetSize('down_button'))) {
            if (this.visualizer.updateDelay !== 64) {
                this.visualizer.updateDelay *= 2;
            }
            return;
        }
        
        // Animate day
        if (this.isPointInRect(pos, this.visualizer.coords.animateDay, this.getActualAssetSize('animate_day_active'))) {
            this.visualizer.animateDay = !this.visualizer.animateDay;
            return;
        }

        // Close guest info panel
        if (this.visualizer.guestSurveyResultsIsOpen) {
            const closeButtonPos = [
                this.visualizer.coords.guestSurveyResultsPanel[0] + (47 * this.visualizer.scaleFactor),
                this.visualizer.coords.guestSurveyResultsPanel[1] + (9 * this.visualizer.scaleFactor)
            ];
            if (this.isPointInRect(pos, closeButtonPos, this.getActualAssetSize('close_button'))) {
                this.visualizer.guestSurveyResultsIsOpen = false;
                return;
            }
            
            // Guest survey up button
            if (this.isPointInRect(pos, this.visualizer.coords.guestSurveyUpButton, this.getActualAssetSize('up_button')) &&
                this.visualizer.guestSurveyStartIndex > 0) {
                this.visualizer.guestSurveyStartIndex -= 1;
                return;
            }
            
            // Guest survey down button
            if (this.isPointInRect(pos, this.visualizer.coords.guestSurveyDownButton, this.getActualAssetSize('down_button')) && this.visualizer.surveyResults && Object.keys(this.visualizer.surveyResults).length - this.visualizer.guestSurveyStartIndex > 12) {
                this.visualizer.guestSurveyStartIndex += 1;
                return;
            }
        }

        if (this.visualizer.showResultMessage || this.visualizer.showNewNotification) {
            const closeButtonPos = [
                this.visualizer.coords.alertTextbox[0] + (-4 * this.visualizer.scaleFactor),
                this.visualizer.coords.alertTextbox[1] + (-4 * this.visualizer.scaleFactor)
            ];
            const closeButtonSize = this.getActualAssetSize('close_button');

            if (this.isPointInRect(pos, closeButtonPos, closeButtonSize)) {
                this.visualizer.showResultMessage = false;
                this.visualizer.showNewNotification = false;
            }
        }
    }

    handleGridSelection(x, y, state) {
        const key = `${x},${y}`;
        let newSelectedTile;
        
        if (state.paths && key in state.paths) {
            newSelectedTile = state.paths[key];
            this.visualizer.selectedTileType = "path";
            this.visualizer.topPanelSelectionType = null;
        } else if (state.waters && key in state.waters) {
            newSelectedTile = state.waters[key];
            this.visualizer.selectedTileType = "water";
            this.visualizer.topPanelSelectionType = null;
        } else if (state.shops && state.shops[key]) {
            newSelectedTile = state.shops[key];
            this.visualizer.selectedTileType = "shop";
        } else if (state.rides && state.rides[key]) {
            newSelectedTile = state.rides[key];
            this.visualizer.selectedTileType = "ride";
        } else if (state.entrance && state.entrance[key]) {
            newSelectedTile = state.entrance[key];
            this.visualizer.selectedTileType = "entrance";
        } else if (state.exit && state.exit[key]) {
            newSelectedTile = state.exit[key];
            this.visualizer.selectedTileType = "exit";
        } else {
            newSelectedTile = {x: x, y: y };
            this.visualizer.selectedTileType = null;
            this.visualizer.topPanelSelectionType = null;
        }


        if (JSON.stringify(newSelectedTile) !== JSON.stringify(this.visualizer.selectedTile)) {
            this.visualizer.newTileSelected = true;
            this.visualizer.selectedTile = newSelectedTile;
            if (this.visualizer.selectedTileType === "ride" || this.visualizer.selectedTileType === "shop") {
                this.visualizer.topPanelSelectionType = "attraction";
            }
        }
    }

    handleSelectionButtons(pos, state) {
        // Handle grid clicks
        if (pos[0] < this.visualizer.gridSize) {
            const x = Math.floor(pos[1] / this.visualizer.tileSize);
            const y = Math.floor(pos[0] / this.visualizer.tileSize);
            this.handleGridSelection(x, y, state);
        }
        this.handleTopPanelSelectionButtons(pos);
        this.handleBottomPanelSelectionButtons(pos);
        this.handleMiscSelectionButtons(pos);
    }
//#endregion Handle Selection Buttons

//#region Format Actions
    formatPlaceAction(mousePos) {
        this.visualizer.waitingForGridClick = false;
        const x = Math.floor(mousePos[1] / this.visualizer.tileSize);
        const y = Math.floor(mousePos[0] / this.visualizer.tileSize);
        const entityType = this.visualizer.bottomPanelActionType;
        const entitySubtype = this.visualizer.subtypeSelection[this.visualizer.bottomPanelActionType];
        const entitySubclass = this.visualizer.colorSelection[entitySubtype];

        let extraArgs = "";
        if (this.visualizer.bottomPanelActionType === "ride") {
            if (this.visualizer.textInputs.ticket_price[`${entitySubtype}_${entitySubclass}`].value === '') {
                return "Error: missing price input field";
            }
            extraArgs = `, price=${this.visualizer.textInputs.ticket_price[`${entitySubtype}_${entitySubclass}`].value}`;
        } else if (this.visualizer.bottomPanelActionType === "shop") {
            if (this.visualizer.textInputs.item_price[`${entitySubtype}_${entitySubclass}`].value === '') {
                return "Error: missing price input field";
            }
            if (this.visualizer.textInputs.order_quantity[`${entitySubtype}_${entitySubclass}`].value === '') {
                return "Error: missing order_quantity input field";
            }
            extraArgs = `, price=${this.visualizer.textInputs.item_price[`${entitySubtype}_${entitySubclass}`].value}`;
            extraArgs += `, order_quantity=${this.visualizer.textInputs.order_quantity[`${entitySubtype}_${entitySubclass}`].value}`;
        }

        const action = `place(x=${x}, y=${y}, type="${entityType}", subtype="${entitySubtype}", subclass="${entitySubclass}"${extraArgs})`;
        return action;
    }

    formatMoveAction(mousePos) {
        this.visualizer.waitingForMove = false;
        const x = Math.floor(mousePos[1] / this.visualizer.tileSize);
        const y = Math.floor(mousePos[0] / this.visualizer.tileSize);
        const selectedEntity = this.visualizer.entityToMove;
        const selectedEntityType = this.visualizer.entityToMoveType;
        const action = `move(type="${selectedEntityType}", subtype="${selectedEntity.subtype}", subclass="${selectedEntity.subclass}", x=${selectedEntity.x}, y=${selectedEntity.y}, new_x=${x}, new_y=${y})`;
        return action;
    }

    formatRemoveAction() {
        const selectedEntity = this.visualizer.entityToRemove;
        const selectedEntityType = this.visualizer.entityToRemoveType;
        const action = `remove(type="${selectedEntityType}", subtype="${selectedEntity.subtype}", subclass="${selectedEntity.subclass}", x=${selectedEntity.x}, y=${selectedEntity.y})`;
        return action;
    }

    formatTerraformAction(mousePos) {
        this.visualizer.waitingForGridClick = false;
        const x = Math.floor(mousePos[1] / this.visualizer.tileSize);
        const y = Math.floor(mousePos[0] / this.visualizer.tileSize);
        const action = `${this.visualizer.terraformAction}(x=${x}, y=${y})`;
        this.visualizer.terraformAction = "";
        return action;
    }

    formatModifyAction() {
        if (this.visualizer.textInputs.modify_price.modify.value === '') {
            return "Error: missing price input field";
        }
        if (this.visualizer.textInputs.modify_order_quantity.modify.value === '' && this.visualizer.selectedTileType === "shop") {
            return "Error: missing order_quantity input field";
        }

        const entityType = this.visualizer.selectedTileType;
        const entityX = this.visualizer.selectedTile.x;
        const entityY = this.visualizer.selectedTile.y;

        const newPrice = parseInt(this.visualizer.textInputs.modify_price.modify.value);
        let extraArgs = "";
        if (entityType === "shop") {
            extraArgs += `, order_quantity=${this.visualizer.textInputs.modify_order_quantity.modify.value}`;
        }
        
        const action = `modify(type="${entityType}", x=${entityX}, y=${entityY}, price=${newPrice}${extraArgs})`;
        return action;
    }

    formatResearchAction() {
        if (!this.visualizer.resAttractionSelections || this.visualizer.resAttractionSelections.length === 0) {
            return "Error: No research direction selected";
        }
        const speed = this.visualizer.resSpeedChoice;
        const attractionList = [...this.visualizer.resAttractionSelections];
        const action = `set_research(research_speed="${speed}", research_topics=${JSON.stringify(attractionList)})`;
        return action;
    }

    formatSurveyGuestAction() {
        if (this.visualizer.textInputs.survey_guests.survey_guests.value === "") {
            return "Error: missing number of guests input";
        }
        const numGuests = parseInt(this.visualizer.textInputs.survey_guests.survey_guests.value);
        return `survey_guests(num_guests=${numGuests})`;
    }

    formatNoopAction() {
        return "wait()";
    }

    formatWaitAction() {
        return "wait()";
    }

    formatUndoDayAction() {
        return "undo_day()";
    }

    formatMaxResearchAction() {
        return "max_research()";
    }

    formatMaxMoneyAction() {
        return "max_money()";
    }

    formatResetAction() {
        return "reset()";
    }

    formatChangeSettingsAction() {
        const difficulty = this.visualizer.difficultyChoices[this.visualizer.difficultyChoice];
        const layout = this.visualizer.layoutChoices[this.visualizer.layoutChoice];
        return `change_settings(difficulty='${difficulty}', layout='${layout}')`;
    }

//#endregion Format Actions

//#region Screen-Specific Button Handlers
    handleEndScreenButtons(pos) {
        if (this.visualizer.gameMode === GameState.END_SCREEN) {
            if (this.isPointInRect(pos, this.visualizer.coords.centerMainButton, this.getActualAssetSize('done_button_big'))) {
                this.visualizer.gameMode = GameState.MODE_SELECTION_SCREEN;
            }
        }
        return { action: null, sandboxAction: null };
    }

    handleSelectionScreenButtons(pos) {
        if (this.visualizer.gameMode === GameState.MODE_SELECTION_SCREEN) {
            for (let i = 0; i < this.visualizer.modeChoices.length; i++) {
                const coord = [this.visualizer.choices_start_x + i * (this.visualizer.scaled_selection_width + this.visualizer.coords.choices_x_spacing), this.visualizer.coords.choices_y];
                if (this.isPointInRect(pos, coord, this.getActualAssetSize('box'))) {
                    this.visualizer.modeChoice = i;
                    return { action: null, sandboxAction: null };
                }
            }
            if (this.isPointInRect(pos, this.visualizer.coords.startButton, this.getActualAssetSize('start_button'))) {
                if (this.visualizer.modeChoice === 0) { // Tutorial
                    this.visualizer.gameMode = GameState.WAITING_FOR_INPUT;
                    this.visualizer.tutorialStep = 0;
                    this.visualizer.in_tutorial_mode = true;
                    this.visualizer.sandboxSteps = 100;
                    this.visualizer.sandboxMode = true;
                    return { action: null, sandboxAction: [
                        "set_sandbox_mode(sandbox_steps=100)",
                        `change_settings(difficulty='easy', layout='tutorial')`
                    ] };
                } else if (this.visualizer.modeChoice === 1) { // Sandbox
                    this.visualizer.gameMode = GameState.DIFFICULTY_SELECTION_SCREEN;
                    this.visualizer.sandboxSteps = 9999;
                    this.visualizer.sandboxMode = true;
                    this.visualizer.in_tutorial_mode = false;
                    this.visualizer.tutorialStep = -1;
                    return { action: null, sandboxAction: "set_sandbox_mode(sandbox_steps=9999)"};
                } else { // Evaluation
                    this.visualizer.gameMode = GameState.DIFFICULTY_SELECTION_SCREEN;
                    this.visualizer.sandboxSteps = -1;
                    this.visualizer.sandboxMode = false;
                    this.visualizer.in_tutorial_mode = false;
                    this.visualizer.tutorialStep = -1;
                    return { action: null, sandboxAction: "set_sandbox_mode(sandbox_steps=-1)"};
                }
            }
        } else if (this.visualizer.gameMode === GameState.DIFFICULTY_SELECTION_SCREEN) {
            for (let i = 0; i < this.visualizer.difficultyChoices.length; i++) {
                const coord = [this.visualizer.choices_start_x + i * (this.visualizer.scaled_selection_width + this.visualizer.coords.choices_x_spacing), this.visualizer.coords.choices_y];
                console.log(coord);
                if (this.isPointInRect(pos, coord, this.getActualAssetSize('box'))) {
                    this.visualizer.difficultyChoice = i;
                    return { action: null, sandboxAction: null };
                }
            }

            if (this.isPointInRect(pos, this.visualizer.coords.startButton, this.getActualAssetSize('start_button'))) {
                this.visualizer.gameMode = GameState.LAYOUT_SELECTION_SCREEN;
                return { action: null, sandboxAction: `change_settings(difficulty='${this.visualizer.difficultyChoices[this.visualizer.difficultyChoice]}')` };
            }
        } else if (this.visualizer.gameMode === GameState.LAYOUT_SELECTION_SCREEN) {
            for (let i = 0; i < this.visualizer.layoutChoices.length; i++) {
                const coord = [this.visualizer.choices_start_x + i * (this.visualizer.scaled_selection_width + this.visualizer.coords.choices_x_spacing), this.visualizer.coords.choices_y];
                if (this.isPointInRect(pos, coord, this.getActualAssetSize('box'))) {
                    this.visualizer.layoutChoice = i;
                    return { action: null, sandboxAction: null };
                }
            }

            if (this.isPointInRect(pos, this.visualizer.coords.startButton, this.getActualAssetSize('start_button'))) {
                this.visualizer.assetManager.clearUIObjects();
                this.visualizer.gameMode = GameState.WAITING_FOR_INPUT;
                return { action: null, sandboxAction: `change_settings(layout='${this.visualizer.layoutChoices[this.visualizer.layoutChoice]}')` };
            }
        }
        return { action: null, sandboxAction: null };
    }

//#region Helper Functions
    getActualAssetSize(assetName) {
        // Get the texture from Phaser's cache (already loaded by AssetManager)
        const texture = this.scene.textures.get(assetName);
        if (!texture) {
            console.error(`Asset ${assetName} not found in texture cache`);
            return null;
        }
        
        // Get the source image dimensions
        const sourceImage = texture.getSourceImage();
        if (!sourceImage) {
            console.error(`Source image not found for ${assetName}`);
            return null;
        }
        
        // Apply the scale factor to get actual scene dimensions
        const scaleFactor = this.visualizer.scaleFactor;
        return [
            sourceImage.width * scaleFactor,
            sourceImage.height * scaleFactor
        ];
    }

    isPointInRect(point, rectPos, rectSize) {
        return point[0] >= rectPos[0] && 
            point[0] <= rectPos[0] + rectSize[0] && 
            point[1] >= rectPos[1] && 
            point[1] <= rectPos[1] + rectSize[1];
    }
//#endregion Helper Functions
}
