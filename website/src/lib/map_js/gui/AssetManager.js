export class AssetManager {
    constructor(scene, scaleFactor = 1.0) {
        this.scene = scene;
        this.scaleFactor = scaleFactor;
        this.assetPath = '/assets/';

        // Grid assets
        this.shops = ['food', 'drink', 'specialty'];
        this.rides = ['carousel', 'ferris_wheel', 'roller_coaster'];
        this.staff = ['janitor', 'mechanic', 'specialist'];
        this.subclasses = ['yellow', 'blue', 'green', 'red'];
        // Bottom panel assets
        this.actionTypeTabs = ["staff", "ride", "shop", "research", "survey_guests", "terraform", "wait"];
        this.colors = ["red", "blue", "green", "yellow"];
        this.entities = ["food", "drink", "specialty", "carousel", "ferris_wheel", "roller_coaster", "janitor", "mechanic", "specialist"];
        this.speeds = ["none", "slow", "medium", "fast"];
        this.uiObjects = [];
        
        // Guest enums - will be loaded asynchronously
        this.guestEnums = null;
        this.guestEnumsLoaded = false;
    }

    async preload() {
        // Load all asset categories
        this.loadGridAssets();
        this.loadBottomPanelAssets();
        this.loadCeoAgentAssets();
        this.loadTopPanelAssets();
        this.loadStatsPanelAssets();
        this.loadMiscAssets();
        this.loadSelectionScreenAssets();
        await this.loadFonts();
        await this.loadGuestEnums();
        await this.loadTutorialScreenAssets();
        
        console.log('AssetManager: Finished loading assets');
    }

    loadGridAssets() {
        // Background
        this.scene.load.image('background', `${this.assetPath}grid_assets/background.png`);

        // Shops
        this.shops.forEach(type => {
            this.subclasses.forEach(subclass => {
                const key = `shop_${type}_${subclass}`;
                const path = `${this.assetPath}grid_assets/shops/${type}/${subclass}.png`;
                this.scene.load.image(key, path);
            });
        });

        // Rides
        this.rides.forEach(ride => {
            this.subclasses.forEach(subclass => {
                const key = `ride_${ride}_${subclass}`;
                const path = `${this.assetPath}grid_assets/rides/${ride}/${subclass}.png`;
                this.scene.load.image(key, path);
            });
        });

        // Staff
        this.staff.forEach(staff => {
            this.subclasses.forEach(subclass => {
                const key = `staff_${staff}_${subclass}`;
                const path = `${this.assetPath}grid_assets/staff/${staff}/${subclass}.png`;
                this.scene.load.image(key, path);
            });
        });

        // Entrance & Exit
        this.scene.load.image('entrance', `${this.assetPath}grid_assets/entrance.png`);
        this.scene.load.image('exit', `${this.assetPath}grid_assets/exit.png`);

        // Guest frames
        this.guests = [];
        for (let i = 1; i < 7; i++) {
            const key = `guest${i}`;
            const path = `${this.assetPath}grid_assets/guest_assets/guest${i}.png`;
            this.scene.load.image(key, path);
            this.guests.push(key);
        }

        // Out of service
        this.scene.load.image('out_of_service', `${this.assetPath}grid_assets/out_of_service.png`);

        // Paths
        this.paths = [];
        for (let i = 1; i <= 16; i++) {
            const key = `path${i}`;
            const path = `${this.assetPath}grid_assets/path_assets/path${i}.png`;
            this.scene.load.image(key, path);
            this.paths.push(key);
        }

        // Water assets
        this.water = [];
        for (let i = 1; i <= 16; i++) {
            if (i === 1) {
                const water1Frames = [];
                const chars = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p"];
                chars.forEach(char => {
                    const key = `water1${char}`;
                    const path = `${this.assetPath}grid_assets/water_assets/water1${char}.png`;
                    this.scene.load.image(key, path);
                    water1Frames.push(key);
                });
                this.water.push(water1Frames);
            } else if ([2, 3, 4, 5].includes(i)) {
                const waterFrames = [];
                const chars = ["a", "b", "c", "d"];
                chars.forEach(char => {
                    const key = `water${i}${char}`;
                    const path = `${this.assetPath}grid_assets/water_assets/water${i}${char}.png`;
                    this.scene.load.image(key, path);
                    waterFrames.push(key);
                });
                this.water.push(waterFrames);
            } else if ([6, 7, 8, 9].includes(i)) {
                const waterFrames = [];
                const chars = ["a", "b"];
                chars.forEach(char => {
                    const key = `water${i}${char}`;
                    const path = `${this.assetPath}grid_assets/water_assets/water${i}${char}.png`;
                    this.scene.load.image(key, path);
                    waterFrames.push(key);
                });
                this.water.push(waterFrames);
            } else {
                const key = `water${i}`;
                const path = `${this.assetPath}grid_assets/water_assets/water${i}.png`;
                this.scene.load.image(key, path);
                this.water.push(key);
            }
        }

        // Cleanliness
        this.cleanliness = [];
        for (let i = 1; i <= 4; i++) {
            const key = `cleanliness${i}`;
            const path = `${this.assetPath}grid_assets/cleanliness_indicator/cleanliness${i}.png`;
            this.scene.load.image(key, path);
            this.cleanliness.push(key);
        }
    }

    loadCeoAgentAssets() {
        this.scene.load.image('ceo_walk1', `${this.assetPath}ceo_agent_assets/ceo_walk1.png`);
        this.scene.load.image('ceo_walk2', `${this.assetPath}ceo_agent_assets/ceo_walk2.png`);
        this.scene.load.image('ceo_walk3', `${this.assetPath}ceo_agent_assets/ceo_walk3.png`);
        this.scene.load.image('office_panel', `${this.assetPath}ceo_agent_assets/office_panel.png`);
    }

    loadTopPanelAssets() {
        this.scene.load.image('top_panel', `${this.assetPath}top_panel_assets/top_panel.png`);
        this.scene.load.image('top_panel_ai_mode', `${this.assetPath}top_panel_assets/top_panel_ai_mode.png`);
        this.scene.load.image('staff_list_panel', `${this.assetPath}top_panel_assets/staff_list_panel.png`);
        this.scene.load.image('staff_type_selection', `${this.assetPath}top_panel_assets/staff_type_selection.png`);
        this.scene.load.image('staff_entry_selection', `${this.assetPath}top_panel_assets/staff_entry_selection.png`);
        this.scene.load.image('selected_tile_panel', `${this.assetPath}top_panel_assets/selected_tile_panel.png`);
        this.scene.load.image('selected_tile_selection', `${this.assetPath}top_panel_assets/selected_tile_selection.png`);
        this.scene.load.image('move_button', `${this.assetPath}top_panel_assets/move_button.png`);
        this.scene.load.image('moving_button', `${this.assetPath}top_panel_assets/moving_button.png`);
        this.scene.load.image('fire_button', `${this.assetPath}top_panel_assets/fire_button.png`);
        this.scene.load.image('sell_button', `${this.assetPath}top_panel_assets/sell_button.png`);
        this.scene.load.image('modify_button', `${this.assetPath}top_panel_assets/modify_button.png`);
    }

    loadBottomPanelAssets() {
        // Bottom panel assets
        this.scene.load.image('bottom_panel', `${this.assetPath}bottom_panel_assets/bottom_panel.png`);
        
        // Action type tabs
        this.actionTypeTabs.forEach(tab => {
            this.scene.load.image(`${tab}_tab`, `${this.assetPath}bottom_panel_assets/${tab}_tab.png`);
        });
        
        this.scene.load.image('action_tab_selection', `${this.assetPath}bottom_panel_assets/action_tab_selection.png`);
        
        // Buttons
        this.scene.load.image('place_button', `${this.assetPath}bottom_panel_assets/place_button.png`);
        this.scene.load.image('placing_button', `${this.assetPath}bottom_panel_assets/placing_button.png`);
        this.scene.load.image('color_selection_border', `${this.assetPath}bottom_panel_assets/color_options/color_selection_border.png`);
        
        // Colored buttons
        this.colors.forEach(color => {
            this.scene.load.image(`${color}_button`, `${this.assetPath}bottom_panel_assets/color_options/${color}_button.png`);
        });
        
        // Boxes
        this.scene.load.image('attributes_box', `${this.assetPath}bottom_panel_assets/attribute_box.png`);
        this.scene.load.image('description_box', `${this.assetPath}bottom_panel_assets/description_box.png`);
        this.scene.load.image('big_description_box', `${this.assetPath}bottom_panel_assets/big_description_box.png`);
        
        // Entity selection (shops, rides, staff)
        // Store entities that need post-processing
        const entitiesToProcess = [];
        this.entities.forEach(entity => {
            const type = ["food", "drink", "specialty"].includes(entity) ? "shops" : 
                        ["carousel", "ferris_wheel", "roller_coaster"].includes(entity) ? "rides" : "staff";
            
            this.colors.forEach(subclass => {
                const key = `entity_${entity}_${subclass}_unprocessed`;
                this.scene.load.image(key, `${this.assetPath}grid_assets/${type}/${entity}/${subclass}.png`);
                entitiesToProcess.push({ key, type });
            });
        });
        
        // Staff tab assets
        this.scene.load.image('base_box', `${this.assetPath}bottom_panel_assets/base_box.png`);
        this.scene.load.image('base_selection', `${this.assetPath}bottom_panel_assets/base_selection.png`);
        
        // Research panel
        const researchEntities = ["carousel", "ferris_wheel", "roller_coaster", "food", "drink", "specialty", "janitor", "mechanic", "specialist"];
        this.researchEntityChoices = {}
        const researchEntitiesToProcess = [];
        researchEntities.forEach(entity => {
            const key = `research_${entity}_unprocessed`;
            const type = ["food", "drink", "specialty"].includes(entity) ? "shops" : 
                        ["carousel", "ferris_wheel", "roller_coaster"].includes(entity) ? "rides" : "staff";
            this.researchEntityChoices[entity] = `research_${entity}`
            this.scene.load.image(key, `${this.assetPath}grid_assets/${type}/${entity}/yellow.png`);
            researchEntitiesToProcess.push({ key, type });
        });
        
        // Process entities after loading completes
        this.scene.load.once('complete', () => {
            // Process entity selection images
            entitiesToProcess.forEach(({ key, type }) => {
                if (type === "staff") {
                    this.rawScale(key, 4);
                } else {
                    this.rawScale(key, 2);
                }
            });
            
            // Process research entity images
            researchEntitiesToProcess.forEach(({ key, type }) => {
                const scale = (type == "staff") ? 2 : 1;
                this.applyGrayscale(key, scale);
            });
        });
        
        this.scene.load.image('res_box', `${this.assetPath}bottom_panel_assets/research_tab/res_box.png`);
        this.scene.load.image('res_selection', `${this.assetPath}bottom_panel_assets/research_tab/res_selection.png`);
        
        this.scene.load.image('res_speed_box', `${this.assetPath}bottom_panel_assets/research_tab/res_speed_box.png`);
        this.scene.load.image('res_speed_selection', `${this.assetPath}bottom_panel_assets/research_tab/res_speed_selection.png`);
        
        // Research speed choices
        this.speeds.forEach(speed => {
            this.scene.load.image(`res_speed_${speed}`, `${this.assetPath}bottom_panel_assets/research_tab/${speed}.png`);
        });
        
        this.scene.load.image('set_research_button', `${this.assetPath}bottom_panel_assets/research_tab/set_research_button.png`);
        
        // Terraform buttons
        const terraformTypes = ["path", "water"];
        const terraformActions = ["add", "remove"];
        terraformActions.forEach(action => {
            terraformTypes.forEach(type => {
                this.scene.load.image(`${action}_${type}`, `${this.assetPath}bottom_panel_assets/terraform_tab/${action}_${type}.png`);
                // Handle irregular verb "remove" -> "removing"
                const actionIng = action === "remove" ? "removing" : `${action}ing`;
                this.scene.load.image(`${actionIng}_${type}`, `${this.assetPath}bottom_panel_assets/terraform_tab/${actionIng}_${type}.png`);
            });
        });
        
        // Survey guest tab
        this.scene.load.image('guest_survey_results_panel', `${this.assetPath}bottom_panel_assets/survey_guests_tab/guest_survey_results_panel.png`);
        this.scene.load.image('survey_guests_button', `${this.assetPath}bottom_panel_assets/survey_guests_tab/survey_guests_button.png`);
        this.scene.load.image('num_guests_input_box', `${this.assetPath}bottom_panel_assets/survey_guests_tab/num_guests_input_box.png`);
        this.scene.load.image('show_results_button_active', `${this.assetPath}bottom_panel_assets/survey_guests_tab/show_results_button_active.png`);
        this.scene.load.image('show_results_button_inactive', `${this.assetPath}bottom_panel_assets/survey_guests_tab/show_results_button_inactive.png`);
        
       // Wait tab
       this.scene.load.image('wait_button', `${this.assetPath}bottom_panel_assets/wait_tab/wait_button.png`)
       this.scene.load.image('undo_day_button', `${this.assetPath}bottom_panel_assets/wait_tab/undo_day_button.png`)
       this.scene.load.image('max_research_button', `${this.assetPath}bottom_panel_assets/wait_tab/max_research_button.png`)
       this.scene.load.image('max_money_button', `${this.assetPath}bottom_panel_assets/wait_tab/max_money_button.png`)
       this.scene.load.image('reset_button', `${this.assetPath}bottom_panel_assets/wait_tab/reset_button.png`)
       this.scene.load.image('switch_layouts_button', `${this.assetPath}bottom_panel_assets/wait_tab/switch_layouts_button.png`)
    }

    loadStatsPanelAssets() {
        this.scene.load.image('main_stat_panel', `${this.assetPath}stat_assets/main_stat_panel.png`);
        this.scene.load.image('aggregate_stat_panel', `${this.assetPath}stat_assets/aggregate_stat_panel.png`);
    }

    loadMiscAssets() {
        this.scene.load.image('playback_panel', `${this.assetPath}misc_assets/playback_panel.png`);
        this.scene.load.image('animate_day_active', `${this.assetPath}misc_assets/animate_day_active.png`);
        this.scene.load.image('animate_day_inactive', `${this.assetPath}misc_assets/animate_day_inactive.png`);
        this.scene.load.image('day_progress_panel', `${this.assetPath}misc_assets/day_progress_panel.png`);
        this.scene.load.image('updating_day', `${this.assetPath}misc_assets/updating_day.png`);
        this.scene.load.image('up_button', `${this.assetPath}misc_assets/up_button.png`);
        this.scene.load.image('down_button', `${this.assetPath}misc_assets/down_button.png`);
        this.scene.load.image('error_textbox', `${this.assetPath}misc_assets/error_textbox.png`);
        this.scene.load.image('notification_textbox', `${this.assetPath}misc_assets/notification_textbox.png`);
        this.scene.load.image('close_button', `${this.assetPath}misc_assets/close_button.png`);
        this.scene.load.image('final_score_panel', `${this.assetPath}misc_assets/final_score_panel.png`);
        this.scene.load.image('input_box', `${this.assetPath}misc_assets/input_box.png`);
        this.scene.load.image('input_box_selected', `${this.assetPath}misc_assets/input_box_selected.png`);
        this.scene.load.image('reset_button_big', `${this.assetPath}misc_assets/reset_button_big.png`);
        this.scene.load.image('done_button', `${this.assetPath}misc_assets/done_button.png`);
        this.scene.load.image('done_button_big', `${this.assetPath}misc_assets/done_button_big.png`);
    }

    async loadFonts() {
        // Load TTF fonts - equivalent to Python's _load_fonts method
        // Note: Phaser loads fonts via CSS, so we'll define font families here
        // The actual font files should be loaded via CSS @font-face rules
        
        // Define font configurations similar to Python version
        this.fonts = {
            // Pixel font (equivalent to pixel_font.ttf)
            big: {
                family: 'PixelFont',
                size: Math.floor(25 * this.scaleFactor)
            },
            medium: {
                family: 'PixelFont', 
                size: Math.floor(20 * this.scaleFactor)
            },
            small: {
                family: 'PixelFont',
                size: Math.floor(15 * this.scaleFactor)
            },
            
            // SpaceMono font (equivalent to SpaceMono-Regular.ttf)
            vsmallFixedWidth: {
                family: 'SpaceMono',
                size: Math.floor(15 * this.scaleFactor)
            },
            smallFixedWidth: {
                family: 'SpaceMono',
                size: Math.floor(17 * this.scaleFactor)
            },
            mediumFixedWidth: {
                family: 'SpaceMono',
                size: Math.floor(20 * this.scaleFactor)
            },
            largeFixedWidth: {
                family: 'SpaceMono',
                size: Math.floor(25 * this.scaleFactor)
            }
        };
        
        console.log('AssetManager: Font configurations loaded');
    }

    // Helper method to get font configuration
    getFont(fontType) {
        if (!this.fonts || !this.fonts[fontType]) {
            console.warn(`Font type '${fontType}' not found, using default`);
            return {
                family: 'Arial',
                size: 16
            };
        }
        return this.fonts[fontType];
    }

    // Helper method to get font style string for Phaser text objects
    getFontStyle(fontType, color = '#000000', stroke = null, strokeThickness = 0) {
        const font = this.getFont(fontType);
        
        // Add fallback fonts to ensure something displays
        let fontFamily = font.family;
        if (font.family === 'SpaceMono') {
            fontFamily = 'SpaceMono, "Courier New", Courier, monospace';
        } else if (font.family === 'PixelFont') {
            fontFamily = 'PixelFont, "Courier New", Courier, monospace';
        }
        
        const style = {
            fontSize: `${font.size}px`,
            fontFamily: fontFamily,
            fill: color
        };
        
        if (stroke) {
            style['stroke'] = stroke;
            style['strokeThickness'] = strokeThickness;
        }
        
        return style;
    }

    loadSelectionScreenAssets() {
        this.scene.load.image('start_button', `${this.assetPath}selection_screen_assets/start_button.png`);
        this.scene.load.image('box', `${this.assetPath}selection_screen_assets/box.png`);
        this.scene.load.image('selection', `${this.assetPath}selection_screen_assets/selection.png`);
        this.scene.load.image('textbox', `${this.assetPath}selection_screen_assets/textbox.png`);
        this.difficultyTextboxText = {
            "easy": "50 days.\nEverything available\nfrom the start.",
            "medium": "100 days.\nResearch required\nto unlock higher \nentities.",
        }
        this.modeTextboxText = {
            "Tutorial": "Tutorial mode.\nLearn basic mechanics\n& how to play the game.",
            "Sandbox": "Sandbox mode.\nExplore the game and\nexperiment using\ndifferent strategies.",
            "Play Game": "Evaluation mode.\nPlay the game.\nClimb the leaderboard.",
        }
        for (let layout_name of ["diagonal_squares", "ribs", "zig_zag", "the_islands", "the_ladder", "the_line", "the_fork", "two_lakes", "two_paths"]) {
            this.scene.load.image(`layout_image_${layout_name}`, `${this.assetPath}selection_screen_assets/${layout_name}.png`);
        }
    }

    async loadTutorialScreenAssets() {
        this.scene.load.image('arrow', `${this.assetPath}tutorial_assets/red_arrow.png`);
        this.scene.load.image('mascot', `${this.assetPath}tutorial_assets/mascot.png`);
        this.scene.load.image('ok_button', `${this.assetPath}tutorial_assets/ok_button.png`);
    }

    createScaledImage(x, y, key, depth = 0) {
        // Safety check: ensure the texture exists before creating image
        if (!this.scene.textures.exists(key)) {
            console.error(`Asset '${key}' not found in texture cache. Make sure it's loaded before use.`);
            // Return a placeholder or null to prevent crashes
            return null;
        }
        
        const image = this.scene.add.image(x, y, key);
        image.setOrigin(0, 0); // Phaser default is 0.5, 0.5
        image.setScale(this.scaleFactor);
        image.setDepth(depth);
        this.uiObjects.push(image);
        return image;
    }


    /**
     * Load and scale an image with two-stage scaling (mimics Python's load_and_scale)
     * This method processes an already-loaded texture and creates a new scaled version.
     *
     * Phase 1: Apply relScale using non-smoothing (nearest-neighbor) scaling
     * Phase 2: Apply scaleFactor using smoothing (bilinear) scaling
     *
     * @param {string} sourceKey - The key of the already-loaded texture
     * @param {string} targetKey - The key to use for the new scaled texture
     * @param {number} relScale - Relative scale factor (applied first, default 1)
     * @returns {boolean} - True if successful, false otherwise
     */
    rawScale(key, scale = 1) {
        if (!this.scene.textures.exists(key)) {
            console.error(`Source texture '${key}' not found`);
            return false;
        }

        if (scale == 1) {
            return true;
        }

        const texture = this.scene.textures.get(key);
        const source = texture.getSourceImage();
        const newWidth = Math.floor(source.width * scale);
        const newHeight = Math.floor(source.height * scale);

        const newCanvas = document.createElement('canvas');
        newCanvas.width = newWidth;
        newCanvas.height = newHeight;
        const newCtx = newCanvas.getContext('2d');
        
        // Disable image smoothing to avoid antialiasing
        newCtx.imageSmoothingEnabled = false;
        newCtx.drawImage(source, 0, 0, newWidth, newHeight);

        // Add the scaled texture to Phaser's texture manager
        this.scene.textures.addCanvas(key.slice(0, -'_unprocessed'.length), newCanvas);

        return true;
    }

    /**
     * Apply grayscale transformation to a texture (mimics pygame.transform.grayscale)
     * Uses the standard luminosity formula: 0.299*R + 0.587*G + 0.114*B
     * Optionally scales the image if scale > 1
     *
     * @param {string} key - The key of the texture to convert to grayscale
     * @param {number} scale - Scale factor to apply (default 1)
     * @returns {boolean} - True if successful, false otherwise
     */
    applyGrayscale(key, scale = 1) {
        if (!this.scene.textures.exists(key)) {
            console.error(`Source texture '${key}' not found for grayscale conversion`);
            return false;
        }

        const texture = this.scene.textures.get(key);
        const source = texture.getSourceImage();

        // Calculate dimensions based on scale
        const width = scale > 1 ? Math.floor(source.width * scale) : source.width;
        const height = scale > 1 ? Math.floor(source.height * scale) : source.height;

        // Create canvas for grayscale conversion
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        canvas.width = width;
        canvas.height = height;

        // Draw the source image (scaled if needed)
        // Disable image smoothing to avoid antialiasing
        ctx.imageSmoothingEnabled = false;
        if (scale > 1) {
            ctx.drawImage(source, 0, 0, width, height);
        } else {
            ctx.drawImage(source, 0, 0);
        }

        // Get image data for pixel manipulation
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;

        // Apply grayscale transformation using luminosity method
        // Formula: 0.299*R + 0.587*G + 0.114*B (same as pygame)
        for (let i = 0; i < data.length; i += 4) {
            const gray = Math.floor(0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]);
            data[i] = gray;       // R
            data[i + 1] = gray;   // G
            data[i + 2] = gray;   // B
            // data[i + 3] is alpha, leave unchanged
        }

        // Put the grayscale data back
        ctx.putImageData(imageData, 0, 0);

        // Add the grayscale texture to Phaser's texture manager
        // Using the same key to replace in place (similar to rawScale)
        this.scene.textures.addCanvas(key.slice(0, -'_unprocessed'.length), canvas);

        return true;
    }

    async loadGuestEnums() {
        try {
            const response = await fetch('/guest_enums.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.guestEnums = await response.json();
            this.guestEnumsLoaded = true;
            console.log('AssetManager: Guest enums loaded successfully');
        } catch (error) {
            console.error('AssetManager: Failed to load guest enums:', error);
            this.guestEnums = null;
            this.guestEnumsLoaded = false;
        }
    }

    // Wait for guest enums to be loaded
    async waitForGuestEnums() {
        while (!this.guestEnumsLoaded) {
            await new Promise(resolve => setTimeout(resolve, 10));
        }
        return this.guestEnums;
    }

    // Get preference description by ID
    getPreferenceDescription(preferenceId) {
        if (!this.guestEnums || !this.guestEnums.preferences) {
            return `Unknown preference (${preferenceId})`;
        }
        const preference = this.guestEnums.preferences[preferenceId.toString()];
        return preference ? preference.description : `Unknown preference (${preferenceId})`;
    }

    // Get preference ID by description
    getPreferenceId(description) {
        if (!this.guestEnums || !this.guestEnums.preference_description_to_id) {
            return null;
        }
        return this.guestEnums.preference_description_to_id[description] || null;
    }

    // Get exit reason description by ID
    getExitReasonDescription(exitReasonId) {
        if (!this.guestEnums || !this.guestEnums.exit_reasons) {
            return `Unknown exit reason (${exitReasonId})`;
        }
        const exitReason = this.guestEnums.exit_reasons[exitReasonId.toString()];
        return exitReason ? exitReason.description : `Unknown exit reason (${exitReasonId})`;
    }

    // Get exit reason ID by description
    getExitReasonId(description) {
        if (!this.guestEnums || !this.guestEnums.exit_reason_description_to_id) {
            return null;
        }
        return this.guestEnums.exit_reason_description_to_id[description] || null;
    }

    // Get all preference descriptions
    getAllPreferenceDescriptions() {
        if (!this.guestEnums || !this.guestEnums.preferences) {
            return [];
        }
        return Object.values(this.guestEnums.preferences).map(p => p.description);
    }

    // Get all exit reason descriptions
    getAllExitReasonDescriptions() {
        if (!this.guestEnums || !this.guestEnums.exit_reasons) {
            return [];
        }
        return Object.values(this.guestEnums.exit_reasons).map(r => r.description);
    }

    clearUIObjects() {
        this.uiObjects.forEach(obj => {
            if (obj && obj.destroy) {
                obj.destroy();
            }
        });
        this.uiObjects = [];
    }

}

export class Coords {
    constructor(baseDims, scaleFactor = 1.0) {
        this.baseDims = baseDims;
        this.scaleFactor = scaleFactor;
        this.dims = [
            Math.floor(this.baseDims[0] * scaleFactor),
            Math.floor(this.baseDims[1] * scaleFactor)
        ];
        this.coordsData = null;
        this.isLoaded = false;
        this.loadCoordsData();
    }

    async loadCoordsData() {
        // Load coordinate data from JSON file
        const coordsPath = '/coords.json';
        const response = await fetch(coordsPath);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const coordsData = await response.json();
        this.coordsData = coordsData;
        this.defines(coordsData);
        this.isLoaded = true;
    }

    // Method to wait for coordinates to be loaded
    async waitForLoad() {
        while (!this.isLoaded) {
            await new Promise(resolve => setTimeout(resolve, 10));
        }
        return this;
    }

    defines(coordsData) {
        // Load all coordinate values from JSON
        const panels = coordsData["panels"];
        
        // Panel coordinates
        this.dayProgressPanel = this.scale(panels["day_progress_panel"]);
        this.topPanel = this.scale(panels["top_panel"]);
        this.bottomPanel = this.scale(panels["bottom_panel"]);
        this.mainStatPanel = this.scale(panels["main_stat_panel"]);
        this.aggregateStatPanel = this.scale(panels["aggregate_stat_panel"]);

        this.playbackPanel = this.scale(panels["playback_panel"]);
        this.animateDay = this.scale(panels["animate_day"]);
        
        // Calculate updating_day position using loaded offset values
        const offset = panels["updating_day_offset"];
        this.updatingDay = this.scale([(this.baseDims[0] - offset[0]) / 2, (this.baseDims[1] - offset[1]) / 2]);

        // Misc coordinates
        const misc = coordsData["misc_coords"];
        this.playbackIncrease = this.addCoords(this.playbackPanel, this.scale(misc["playback_increase_offset"]));
        this.playbackDecrease = this.addCoords(this.playbackPanel, this.scale(misc["playback_decrease_offset"]));
        this.playbackText = this.addCoords(this.playbackPanel, this.scale(misc["playback_text_offset"]));
        this.alertTextbox = this.scale(misc["alert_textbox"]);
        this.alertMessage = this.addCoords(this.alertTextbox, this.scale(misc["alert_message_offset"]));
        this.leftMainButton = this.scale(misc["left_main_button_offset"]);
        this.rightMainButton = this.scale(misc["right_main_button_offset"]);
        this.centerMainButton = this.scale(misc["center_main_button_offset"]);

        // Top panel element coordinates
        const topPanel = coordsData["top_panel"];
        
        this.modifyButton = this.addCoords(this.topPanel, this.scale(topPanel["modify_button_offset"]));
        this.moveButton = this.addCoords(this.topPanel, this.scale(topPanel["move_button_offset"]));
        this.sellButton = this.addCoords(this.topPanel, this.scale(topPanel["sell_button_offset"]));
        this.fireButton = this.addCoords(this.topPanel, this.scale(topPanel["fire_button_offset"]));
        this.staffListPanel = this.addCoords(this.topPanel, this.scale(topPanel["staff_list_panel_offset"]));
        
        // Staff type coordinates
        const staffTypeOffsets = topPanel["staff_type_offsets"];
        this.topPanelStaffType = {
            "janitors": this.addCoords(this.staffListPanel, this.scale(staffTypeOffsets["janitors"])),
            "mechanics": this.addCoords(this.staffListPanel, this.scale(staffTypeOffsets["mechanics"])),
            "specialists": this.addCoords(this.staffListPanel, this.scale(staffTypeOffsets["specialists"]))
        };
        
        this.staffListUpButton = this.addCoords(this.staffListPanel, this.scale(topPanel["staff_list_up_button_offset"]));
        this.staffListDownButton = this.addCoords(this.staffListPanel, this.scale(topPanel["staff_list_down_button_offset"]));
        
        // Staff entry coordinates
        const staffEntryOffsets = topPanel["staff_entry_offsets"];
        this.topPanelStaffEntry = staffEntryOffsets.map(offset => 
            this.addCoords(this.staffListPanel, this.scale(offset))
        );
        
        this.selectedTilePanel = this.addCoords(this.topPanel, this.scale(topPanel["selected_tile_panel_offset"]));
        
        // Change attributes box
        const changeAttrsOffsets = topPanel["change_attributes_box_offsets"];
        this.changeAttributesBox = changeAttrsOffsets.map(offset => 
            this.addCoords(this.topPanel, this.scale(offset))
        );

        // Bottom panel element coordinates
        const bottomPanel = coordsData["bottom_panel"];
        
        // Action type tabs - load configuration and calculate positions
        const tabConfig = bottomPanel["action_type_tabs"];
        const buttonTypes = tabConfig["button_types"];
        const tabStartX = tabConfig["tab_start_x"];
        const tabSpacing = tabConfig["tab_spacing"];
        const tabY = tabConfig["tab_y"];
        
        this.actionTypeTabs = {};
        for (let i = 0; i < buttonTypes.length; i++) {
            const buttonType = buttonTypes[i];
            const x = tabStartX + i * tabSpacing;
            const y = tabY;
            this.actionTypeTabs[buttonType] = this.addCoords(this.bottomPanel, this.scale([x, y]));
        }

        // Shared coords
        this.placeButton = this.addCoords(this.bottomPanel, this.scale(bottomPanel["place_button_offset"]));
        
        // Color selection - load configuration and calculate positions
        const colorConfig = bottomPanel["color_selection"];
        const colors = colorConfig["colors"];
        const startX = colorConfig["start_x"];
        const spacing = colorConfig["spacing"];
        const y = colorConfig["y"];
        
        this.colorSelection = {};
        for (let i = 0; i < colors.length; i++) {
            const color = colors[i];
            const x = startX + i * spacing;
            this.colorSelection[color] = this.addCoords(this.bottomPanel, this.scale([x, y]));
        }
        
        // Subtypes choices - load configuration and calculate positions
        const subtypesConfig = bottomPanel["subtypes_choices"];
        const startXSubtypes = subtypesConfig["start_x"];
        const spacingSubtypes = subtypesConfig["spacing"];
        const ySubtypes = subtypesConfig["y"];
        const count = subtypesConfig["count"];
        this.subtypesChoices = [];
        for (let i = 0; i < count; i++) {
            const x = startXSubtypes + spacingSubtypes * i;
            this.subtypesChoices.push(this.addCoords(this.bottomPanel, this.scale([x, ySubtypes])));
        }
        
        // Attributes box - load configuration and calculate positions
        const attrsConfig = bottomPanel["attributes_box"];
        const startXAttrs = attrsConfig["start_x"];
        const startYAttrs = attrsConfig["start_y"];
        const colSpacing = attrsConfig["col_spacing"];
        const rowSpacing = attrsConfig["row_spacing"];
        const cols = attrsConfig["cols"];
        const rows = attrsConfig["rows"];
        
        this.attributesBox = [];
        for (let i = 0; i < cols * rows; i++) {
            const row = Math.floor(i / cols);
            const col = i % cols;
            const x = startXAttrs + col * colSpacing;
            const y = startYAttrs + row * rowSpacing;
            this.attributesBox.push(this.addCoords(this.bottomPanel, this.scale([x, y])));
        }
        
        this.descriptionBox = this.addCoords(this.bottomPanel, this.scale(bottomPanel["description_box_offset"]));
        this.bigDescriptionBox = this.addCoords(this.bottomPanel, this.scale(bottomPanel["big_description_box_offset"]));

        // Research tab coords
        const researchTab = coordsData["research_tab"];
        this.setResearchButton = this.addCoords(this.bottomPanel, this.scale(researchTab["set_research_button_offset"]));
        
        // Speed choices - load configuration and calculate positions
        const speedConfig = researchTab["speed_choices"];
        const speeds = speedConfig["speeds"];
        const startXSpeed = speedConfig["start_x"];
        const startYSpeed = speedConfig["start_y"];
        const spacingSpeed = speedConfig["spacing"];
        
        this.resSpeedChoices = {};
        for (let i = 0; i < speeds.length; i++) {
            const speed = speeds[i];
            this.resSpeedChoices[speed] = this.addCoords(this.bottomPanel, this.scale([startXSpeed, startYSpeed + i * spacingSpeed]));
        }

        // Research entities - load configuration and calculate positions
        const entitiesConfig = researchTab["entities"];
        const entityTypes = entitiesConfig["entity_types"];
        const startXEntities = entitiesConfig["start_x"];
        const startYEntities = entitiesConfig["start_y"];
        const colSpacingEntities = entitiesConfig["col_spacing"];
        const rowSpacingEntities = entitiesConfig["row_spacing"];
        const colsEntities = entitiesConfig["cols"];
        
        this.resEntities = {};
        for (let i = 0; i < entityTypes.length; i++) {
            const entity = entityTypes[i];
            const row = Math.floor(i / colsEntities);
            const col = i % colsEntities;
            const x = startXEntities + col * colSpacingEntities;
            const y = startYEntities + row * rowSpacingEntities;
            this.resEntities[entity] = this.addCoords(this.bottomPanel, this.scale([x, y]));
        }

        // Survey guests tab coords
        const surveyTab = coordsData["survey_guests_tab"];
        this.guestSurveyResultsPanel = this.scale(surveyTab["guest_survey_results_panel"]);
        this.numGuestsInputBox = this.addCoords(this.bottomPanel, this.scale(surveyTab["num_guests_input_box_offset"]));
        this.surveyGuestsButton = this.addCoords(this.bottomPanel, this.scale(surveyTab["survey_guests_button_offset"]));
        this.showResultsButton = this.addCoords(this.bottomPanel, this.scale(surveyTab["show_results_button_offset"]));
        this.guestSurveyUpButton = this.addCoords(this.guestSurveyResultsPanel, this.scale(surveyTab["guest_survey_up_button_offset"]));
        this.guestSurveyDownButton = this.addCoords(this.guestSurveyResultsPanel, this.scale(surveyTab["guest_survey_down_button_offset"]));
        
        // Terraform tab coords
        const terraformTab = coordsData["terraform_tab"];
        const buttonsConfig = terraformTab["buttons"];
        
        this.terraformButtons = {
            "add": {
                "path": this.addCoords(this.bottomPanel, this.scale(buttonsConfig["add"]["path_offset"])),
                "water": this.addCoords(this.bottomPanel, this.scale(buttonsConfig["add"]["water_offset"]))
            },
            "remove": {
                "path": this.addCoords(this.bottomPanel, this.scale(buttonsConfig["remove"]["path_offset"])),
                "water": this.addCoords(this.bottomPanel, this.scale(buttonsConfig["remove"]["water_offset"]))
            }
        };

        // Wait/Sandbox tab coords
        const waitTab = coordsData["wait_tab"];
        this.waitButton = this.addCoords(this.bottomPanel, this.scale(waitTab["wait_button_offset"]));
        this.sandboxActionsYOffset = waitTab["sandbox_actions_y_offset"] * this.scaleFactor;
        this.undoDayButton = this.addCoords(this.bottomPanel, this.scale(waitTab["undo_day_button_offset"]));
        this.maxResearchButton = this.addCoords(this.bottomPanel, this.scale(waitTab["max_research_button_offset"]));
        this.maxMoneyButton = this.addCoords(this.bottomPanel, this.scale(waitTab["max_money_button_offset"]));
        this.resetButton = this.addCoords(this.bottomPanel, this.scale(waitTab["reset_button_offset"]));
        this.switchLayoutsButton = this.addCoords(this.bottomPanel, this.scale(waitTab["switch_layouts_button_offset"]));
        this.doneButton = this.addCoords(this.bottomPanel, this.scale(waitTab["done_button_offset"]));
        this.remainingDaysToLearnFromYOffset = waitTab["remaining_days_to_learn_from_y_offset"] * this.scaleFactor;

        // Tutorial screen coords
        const tutorialScreen = coordsData["tutorial_screen"];
        this.tutorialSteps = tutorialScreen["steps"].map(step => {return {
            "text": step["text"],
            "highlight_pos": this.scale(step["highlight_pos"]),
            "include_ok_button": step["include_ok_button"],
            "include_arrow": step["include_arrow"]
        }});
        this.mascot = this.scale(tutorialScreen["mascot"]);
        this.textbox = this.scale(tutorialScreen["textbox"]);
        this.arrowOffset = this.scale(tutorialScreen["arrow_offset"]);
        this.okButtonOffset = this.scale(tutorialScreen["ok_button_offset"]);

        // Selection screen coords
        const selectionScreen = coordsData["selection_screen"];
        this.startButton = this.scale(selectionScreen["start_button_offset"]);

        this.choices_x_spacing = selectionScreen["choices"]["x_spacing"] * this.scaleFactor;
        this.choices_y = selectionScreen["choices"]["y"] * this.scaleFactor;
        this.choices_textbox_y = selectionScreen["choices"]["textbox_y"] * this.scaleFactor;

        // End screen coords
        const endScreen = coordsData["end_screen"];
        this.finalScorePanel = this.scale(endScreen["final_score_panel"]);
        this.finalScore = this.addCoords(this.finalScorePanel, this.scale(endScreen["final_score_offset"]));
        this.finalScoreTextOffset = this.scale(endScreen["final_score_text_offset"]);
    }

    addCoords(coord1, coord2) {
        return [coord1[0] + coord2[0], coord1[1] + coord2[1]];
    }

    scale(coord) {
        return [
            Math.floor(coord[0] * this.scaleFactor),
            Math.floor(coord[1] * this.scaleFactor)
        ];
    }

}
