import map_py
import numpy as np
import pygame
import json
import os
import importlib.resources

SHARED_DIR = importlib.resources.files(map_py)/".."/"shared"

class Assets:
    def __init__(self, scale_factor):
        self.scale_factor = scale_factor
        self.asset_path = str(SHARED_DIR/"assets") + "/"
        self._load_grid_assets()
        self._load_ceo_agent_assets()
        self._load_top_panel_assets()
        self._load_bottom_panel_assets()
        self._load_stats_panel_assets()
        self._load_misc_assets()
        self._load_fonts()
        self._load_selection_screen_assets()
        self._load_tutorial_screen_assets()

    def load_and_scale(self, path, rel_scale=1):
        image = pygame.image.load(path).convert_alpha()
        if rel_scale != 1:
            image = pygame.transform.scale_by(image, rel_scale)
        size = (int(image.get_width() * self.scale_factor), int(image.get_height() * self.scale_factor))
        return pygame.transform.smoothscale(image, size)
    
    def _load_fonts(self):
        self.big_font = pygame.font.Font(self.asset_path + "text_assets/pixel_font.ttf", int(25 * self.scale_factor))
        self.medium_font = pygame.font.Font(self.asset_path + "text_assets/pixel_font.ttf", int(20 * self.scale_factor))
        self.small_font = pygame.font.Font(self.asset_path + "text_assets/pixel_font.ttf", int(15 * self.scale_factor))
        self.vsmall_fixed_width_font = pygame.font.Font(self.asset_path + "text_assets/SpaceMono-Regular.ttf", int(15 * self.scale_factor))
        self.small_fixed_width_font = pygame.font.Font(self.asset_path + "text_assets/SpaceMono-Regular.ttf", int(17 * self.scale_factor))
        self.medium_fixed_width_font = pygame.font.Font(self.asset_path + "text_assets/SpaceMono-Regular.ttf", int(20 * self.scale_factor))
        self.large_fixed_width_font = pygame.font.Font(self.asset_path + "text_assets/SpaceMono-Regular.ttf", int(25 * self.scale_factor))

    def _load_grid_assets(self):
        self.background = self.load_and_scale(self.asset_path + "grid_assets/background.png").convert()
        self.shops = {
            "food": {subclass: self.load_and_scale(self.asset_path + f"grid_assets/shops/food/{subclass}.png").convert_alpha() for subclass in ["yellow","blue","green","red"]},
            "drink": {subclass: self.load_and_scale(self.asset_path + f"grid_assets/shops/drink/{subclass}.png").convert_alpha() for subclass in ["yellow","blue","green","red"]},
            "specialty": {subclass: self.load_and_scale(self.asset_path + f"grid_assets/shops/specialty/{subclass}.png").convert_alpha() for subclass in ["yellow","blue","green","red"]}
        }
        self.rides = {
            "carousel": {subclass: self.load_and_scale(self.asset_path + f"grid_assets/rides/carousel/{subclass}.png").convert_alpha() for subclass in ["yellow", "blue", "green", "red"]},
            "ferris_wheel": {subclass: self.load_and_scale(self.asset_path + f"grid_assets/rides/ferris_wheel/{subclass}.png").convert_alpha() for subclass in ["yellow", "blue", "green", "red"]},
            "roller_coaster": {subclass: self.load_and_scale(self.asset_path + f"grid_assets/rides/roller_coaster/{subclass}.png").convert_alpha() for subclass in ["yellow", "blue", "green", "red"]}
        }

        self.staff = {
            "janitor": {subclass: self.load_and_scale(self.asset_path + f"grid_assets/staff/janitor/{subclass}.png").convert_alpha() for subclass in ["yellow","blue","green","red"]},
            "mechanic": {subclass: self.load_and_scale(self.asset_path + f"grid_assets/staff/mechanic/{subclass}.png").convert_alpha() for subclass in ["yellow","blue","green","red"]},
            "specialist": {subclass: self.load_and_scale(self.asset_path + f"grid_assets/staff/specialist/{subclass}.png").convert_alpha() for subclass in ["yellow","blue","green","red"]}
        }
        self.entrance = self.load_and_scale(self.asset_path + "grid_assets/entrance.png").convert_alpha()
        self.exit = self.load_and_scale(self.asset_path + "grid_assets/exit.png").convert_alpha()

        self.guests = [self.load_and_scale(self.asset_path + f"grid_assets/guest_assets/guest{i}.png").convert_alpha() for i in range(1,7)]

        self.out_of_service = self.load_and_scale(self.asset_path + "grid_assets/out_of_service.png").convert_alpha()
        self.paths = [self.load_and_scale(self.asset_path + f"grid_assets/path_assets/path{i}.png").convert_alpha() for i in range(1,17)]
        self.water = []
        for i in range(1, 17):
            if i == 1:
                self.water.append([self.load_and_scale(self.asset_path + f"grid_assets/water_assets/water{i}{char}.png").convert_alpha() for char in ["a", "b", "c", "d",
                                                                                                                                                      "e", "f", "g", "h",
                                                                                                                                                      "i", "j", "k", "l",
                                                                                                                                                      "m", "n", "o", "p"]])
            elif i in [2,3,4,5]:
                self.water.append([self.load_and_scale(self.asset_path + f"grid_assets/water_assets/water{i}{char}.png").convert_alpha() for char in ["a", "b", "c", "d"]])
            elif i in [6,7,8,9]:
                self.water.append([self.load_and_scale(self.asset_path + f"grid_assets/water_assets/water{i}{char}.png").convert_alpha() for char in ["a", "b"]])
            else:
                self.water.append(self.load_and_scale(self.asset_path + f"grid_assets/water_assets/water{i}.png").convert_alpha())
        self.cleanliness = {
            level: self.load_and_scale(self.asset_path + f"grid_assets/cleanliness_indicator/cleanliness{level}.png") for level in [1,2,3,4]
        }

    def _load_ceo_agent_assets(self):
        self.ceo_frames = [self.load_and_scale(self.asset_path + f"ceo_agent_assets/ceo_walk{i}.png").convert_alpha() for i in range(1,4)]
        self.office_panel = self.load_and_scale(self.asset_path + "ceo_agent_assets/office_panel.png")

    def _load_top_panel_assets(self):
        # top panel assets
        self.top_panel = self.load_and_scale(self.asset_path + "top_panel_assets/top_panel.png")
        self.top_panel_ai_mode = self.load_and_scale(self.asset_path + "top_panel_assets/top_panel_ai_mode.png")
        self.staff_list_panel = self.load_and_scale(self.asset_path + "top_panel_assets/staff_list_panel.png")
        self.staff_type_selection = self.load_and_scale(self.asset_path + "top_panel_assets/staff_type_selection.png")
        self.staff_entry_selection = self.load_and_scale(self.asset_path + "top_panel_assets/staff_entry_selection.png")
        self.selected_tile_panel = self.load_and_scale(self.asset_path + "top_panel_assets/selected_tile_panel.png")
        self.selected_tile_selection = self.load_and_scale(self.asset_path + "top_panel_assets/selected_tile_selection.png")
        self.move_button = self.load_and_scale(self.asset_path + "top_panel_assets/move_button.png")
        self.moving_button = self.load_and_scale(self.asset_path + "top_panel_assets/moving_button.png")
        self.fire_button = self.load_and_scale(self.asset_path + "top_panel_assets/fire_button.png")
        self.sell_button = self.load_and_scale(self.asset_path + "top_panel_assets/sell_button.png")
        self.modify_button = self.load_and_scale(self.asset_path + "top_panel_assets/modify_button.png")

    def _load_bottom_panel_assets(self):
        # bottom panel assets
        self.bottom_panel = self.load_and_scale(self.asset_path + "bottom_panel_assets/bottom_panel.png")
        self.action_type_tabs = {
            key: self.load_and_scale(self.asset_path + f"bottom_panel_assets/{key}_tab.png") for key in ["staff", "ride", "shop", "research", "survey_guests", "terraform", "wait"]
        }
        self.action_type_tab_border = self.load_and_scale(self.asset_path + "bottom_panel_assets/action_tab_selection.png")

        self.place_button = self.load_and_scale(self.asset_path + "bottom_panel_assets/place_button.png")
        self.placing_button = self.load_and_scale(self.asset_path + "bottom_panel_assets/placing_button.png")
        self.color_selection_border = self.load_and_scale(self.asset_path + "bottom_panel_assets/color_options/color_selection_border.png")
        self.colored_buttons = {color: self.load_and_scale(self.asset_path + f"bottom_panel_assets/color_options/{color}_button.png") for color in ["red", "blue", "green", "yellow"]}

        self.attributes_box = self.load_and_scale(self.asset_path + "bottom_panel_assets/attribute_box.png")
        self.description_box = self.load_and_scale(self.asset_path + "bottom_panel_assets/description_box.png")
        self.big_description_box = self.load_and_scale(self.asset_path + "bottom_panel_assets/big_description_box.png")

        self.entity_selection = {}
        for i, entity in enumerate(["food", "drink", "specialty", "carousel", "ferris_wheel", "roller_coaster", "janitor", "mechanic", "specialist"]):
            multipler = 4 if entity in ["janitor", "mechanic", "specialist"] else 2
            type = "shops" if entity in ["food", "drink", "specialty"] else "rides" if entity in ["carousel", "ferris_wheel", "roller_coaster"] else "staff"
            self.entity_selection[entity] = {subclass: self.load_and_scale(self.asset_path + f"grid_assets/{type}/{entity}/{subclass}.png", rel_scale=multipler).convert_alpha() for subclass in ["yellow","blue","green","red"]}
        
        # Staff tab assets
        self.base_box = self.load_and_scale(self.asset_path + "bottom_panel_assets/base_box.png")
        self.base_selection = self.load_and_scale(self.asset_path + "bottom_panel_assets/base_selection.png")
        
        # research panel
        self.research_entity_choices = {
            **{k: pygame.transform.grayscale(self.load_and_scale(self.asset_path + f"grid_assets/rides/{k}/yellow.png").convert_alpha()) for k in ["carousel", "ferris_wheel", "roller_coaster"]},
            **{k: pygame.transform.grayscale(self.load_and_scale(self.asset_path + f"grid_assets/shops/{k}/yellow.png").convert_alpha()) for k in ["food", "drink", "specialty"]},
            **{k: pygame.transform.grayscale(self.load_and_scale(self.asset_path + f"grid_assets/staff/{k}/yellow.png", rel_scale=2).convert_alpha()) for k in ["janitor", "mechanic", "specialist"]}
        }
        self.res_box = self.load_and_scale(self.asset_path + "bottom_panel_assets/research_tab/res_box.png")
        self.res_selection = self.load_and_scale(self.asset_path + "bottom_panel_assets/research_tab/res_selection.png")

        self.res_speed_box = self.load_and_scale(self.asset_path + "bottom_panel_assets/research_tab/res_speed_box.png")
        self.res_speed_selection = self.load_and_scale(self.asset_path + "bottom_panel_assets/research_tab/res_speed_selection.png")
        self.res_speed_choices = {
            speed: self.load_and_scale(self.asset_path + f"bottom_panel_assets/research_tab/{speed}.png") for speed in ["none", "slow", "medium", "fast"]
        }

        self.set_research_button = self.load_and_scale(self.asset_path + "bottom_panel_assets/research_tab/set_research_button.png")

        self.terraform_buttons = {
            "add": {
                "path": (self.load_and_scale(self.asset_path + "bottom_panel_assets/terraform_tab/add_path.png"),
                         self.load_and_scale(self.asset_path + "bottom_panel_assets/terraform_tab/adding_path.png")),
                "water": (self.load_and_scale(self.asset_path + "bottom_panel_assets/terraform_tab/add_water.png"),
                          self.load_and_scale(self.asset_path + "bottom_panel_assets/terraform_tab/adding_water.png"))
            },
            "remove": {
                "path": (self.load_and_scale(self.asset_path + "bottom_panel_assets/terraform_tab/remove_path.png"),
                         self.load_and_scale(self.asset_path + "bottom_panel_assets/terraform_tab/removing_path.png")),
                "water": (self.load_and_scale(self.asset_path + "bottom_panel_assets/terraform_tab/remove_water.png"),
                          self.load_and_scale(self.asset_path + "bottom_panel_assets/terraform_tab/removing_water.png"))
            }
        }

        # Survey guests tab assets
        self.guest_survey_results_panel = self.load_and_scale(self.asset_path + "bottom_panel_assets/survey_guests_tab/guest_survey_results_panel.png")
        self.survey_guests_button = self.load_and_scale(self.asset_path + "bottom_panel_assets/survey_guests_tab/survey_guests_button.png")
        self.num_guests_input_box = self.load_and_scale(self.asset_path + "bottom_panel_assets/survey_guests_tab/num_guests_input_box.png")
        self.show_results_button_active = self.load_and_scale(self.asset_path + "bottom_panel_assets/survey_guests_tab/show_results_button_active.png")
        self.show_results_button_inactive = self.load_and_scale(self.asset_path + "bottom_panel_assets/survey_guests_tab/show_results_button_inactive.png")

        # Wait/Sandbox tab assets
        self.wait_button = self.load_and_scale(self.asset_path + "bottom_panel_assets/wait_tab/wait_button.png")
        self.undo_day_button = self.load_and_scale(self.asset_path + "bottom_panel_assets/wait_tab/undo_day_button.png")
        self.max_research_button = self.load_and_scale(self.asset_path + "bottom_panel_assets/wait_tab/max_research_button.png")
        self.max_money_button = self.load_and_scale(self.asset_path + "bottom_panel_assets/wait_tab/max_money_button.png")
        self.reset_button = self.load_and_scale(self.asset_path + "bottom_panel_assets/wait_tab/reset_button.png")
        self.switch_layouts_button = self.load_and_scale(self.asset_path + "bottom_panel_assets/wait_tab/switch_layouts_button.png")

    def _load_stats_panel_assets(self):
        self.main_stat_panel = self.load_and_scale(self.asset_path + "stat_assets/main_stat_panel.png")
        self.aggregate_stat_panel = self.load_and_scale(self.asset_path + "stat_assets/aggregate_stat_panel.png")


    def _load_misc_assets(self):
        # misc assets
        self.playback_panel = self.load_and_scale(self.asset_path + "misc_assets/playback_panel.png")
        self.animate_day_active = self.load_and_scale(self.asset_path + "misc_assets/animate_day_active.png")
        self.animate_day_inactive = self.load_and_scale(self.asset_path + "misc_assets/animate_day_inactive.png")
        self.day_progress_panel = self.load_and_scale(self.asset_path + "misc_assets/day_progress_panel.png")
        self.updating_day = self.load_and_scale(self.asset_path + "misc_assets/updating_day.png")
        self.up_button = self.load_and_scale(self.asset_path + "misc_assets/up_button.png")
        self.down_button = self.load_and_scale(self.asset_path + "misc_assets/down_button.png")
        self.error_textbox = self.load_and_scale(self.asset_path + "misc_assets/error_textbox.png")
        self.notification_textbox = self.load_and_scale(self.asset_path + "misc_assets/notification_textbox.png")
        self.close_button = self.load_and_scale(self.asset_path + "misc_assets/close_button.png")
        self.final_score_panel = self.load_and_scale(self.asset_path + "misc_assets/final_score_panel.png")
        self.input_box = self.load_and_scale(self.asset_path + "misc_assets/input_box.png")
        self.input_box_selected = self.load_and_scale(self.asset_path + "misc_assets/input_box_selected.png")
        self.done_button = self.load_and_scale(self.asset_path + "misc_assets/done_button.png")
        self.done_button_big = self.load_and_scale(self.asset_path + "misc_assets/done_button_big.png")
        self.reset_button_big = self.load_and_scale(self.asset_path + "misc_assets/reset_button_big.png")

    def _load_selection_screen_assets(self):
        self.start_button = self.load_and_scale(self.asset_path + "selection_screen_assets/start_button.png")
        self.box = self.load_and_scale(self.asset_path + "selection_screen_assets/box.png")
        self.selection = self.load_and_scale(self.asset_path + "selection_screen_assets/selection.png")
        self.textbox = self.load_and_scale(self.asset_path + "selection_screen_assets/textbox.png")

        # Mode selection text descriptions (matching JS version)
        self.mode_textbox_text = {
            0: "Tutorial mode.\nLearn basic mechanics\n& how to play the game.",
            1: "Sandbox mode.\nExplore the game and\nexperiment using\ndifferent strategies.",
            2: "Evaluation mode.\nPlay the game.\nClimb the leaderboard."
        }

        # Difficulty selection text descriptions (matching JS version)
        self.difficulty_textbox_text = {
            0: "50 days.\nEverything available\nfrom the start.",
            1: "100 days.\nResearch required\nto unlock higher \nentities."
        }

        # Layout preview images
        layout_names = ["diagonal_squares", "ribs", "zig_zag", "the_islands", "the_ladder", "the_line", "the_fork", "two_lakes", "two_paths"]
        self.layout_previews = {}
        for layout in layout_names:
            try:
                self.layout_previews[layout] = self.load_and_scale(
                    self.asset_path + f"selection_screen_assets/{layout}.png"
                )
            except:
                # If layout preview doesn't exist, skip it
                pass

    def _load_tutorial_screen_assets(self):
        self.mascot = self.load_and_scale(self.asset_path + "tutorial_assets/mascot.png")
        self.ok_button = self.load_and_scale(self.asset_path + "tutorial_assets/ok_button.png")
        self.arrow = self.load_and_scale(self.asset_path + "tutorial_assets/red_arrow.png")
        self.tutorial_textbox = self.load_and_scale(self.asset_path + "tutorial_assets/textbox.png")
        self.tile_highlight = self.load_and_scale(self.asset_path + "tutorial_assets/tile_highlight.png")
        self.button_highlight = self.load_and_scale(self.asset_path + "tutorial_assets/button_highlight.png")


class Coords:
    def __init__(self, dims, scale_factor):
        self.dims = dims
        self.scale_factor = scale_factor
        self.coords_data = self._load_coords_from_json()
        self._defines()

    def _load_coords_from_json(self):
        """Load coordinate data from JSON file"""
        coords_path = SHARED_DIR/"coords.json"
        try:
            with open(coords_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Required file {coords_path} not found")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing {coords_path}: {e}")

    def scale(self, coord):
        return (int(coord[0] * self.scale_factor), int(coord[1] * self.scale_factor))
    
    def _defines(self):
        # Load all coordinate values from JSON
        panels = self.coords_data["panels"]
        
        # Panel coordinates
        self.day_progress_panel = self.scale(tuple(panels["day_progress_panel"]))
        self.top_panel = self.scale(tuple(panels["top_panel"]))
        self.bottom_panel = self.scale(tuple(panels["bottom_panel"]))
        self.main_stat_panel = self.scale(tuple(panels["main_stat_panel"]))
        self.aggregate_stat_panel = self.scale(tuple(panels["aggregate_stat_panel"]))

        self.playback_panel = self.scale(tuple(panels["playback_panel"]))
        self.animate_day = self.scale(tuple(panels["animate_day"]))
        
        # Calculate updating_day position using loaded offset values
        offset = panels["updating_day_offset"]
        self.updating_day = self.scale(((self.dims[0] - offset[0]) // 2, (self.dims[1] - offset[1]) // 2))

        # Misc coordinates
        misc = self.coords_data["misc_coords"]
        self.playback_increase = np.add(self.playback_panel, self.scale(tuple(misc["playback_increase_offset"])))
        self.playback_decrease = np.add(self.playback_panel, self.scale(tuple(misc["playback_decrease_offset"])))
        self.playback_text = np.add(self.playback_panel, self.scale(tuple(misc["playback_text_offset"])))
        self.alert_textbox = self.scale(tuple(misc["alert_textbox"]))
        self.alert_message = np.add(self.alert_textbox, self.scale(tuple(misc["alert_message_offset"])))
        self.left_main_button = self.scale(tuple(misc["left_main_button_offset"]))
        self.right_main_button = self.scale(tuple(misc["right_main_button_offset"]))
        self.center_main_button = self.scale(tuple(misc["center_main_button_offset"]))

        # Top panel element coordinates
        top_panel = self.coords_data["top_panel"]
        
        self.modify_button = np.add(self.top_panel, self.scale(tuple(top_panel["modify_button_offset"])))
        self.move_button = np.add(self.top_panel, self.scale(tuple(top_panel["move_button_offset"])))
        self.sell_button = np.add(self.top_panel, self.scale(tuple(top_panel["sell_button_offset"])))
        self.fire_button = np.add(self.top_panel, self.scale(tuple(top_panel["fire_button_offset"])))
        self.staff_list_panel = np.add(self.top_panel, self.scale(tuple(top_panel["staff_list_panel_offset"])))
        
        # Staff type coordinates
        staff_type_offsets = top_panel["staff_type_offsets"]
        self.top_panel_staff_type = {
            "janitors": np.add(self.staff_list_panel, self.scale(tuple(staff_type_offsets["janitors"]))),
            "mechanics": np.add(self.staff_list_panel, self.scale(tuple(staff_type_offsets["mechanics"]))),
            "specialists": np.add(self.staff_list_panel, self.scale(tuple(staff_type_offsets["specialists"])))
        }
        
        self.staff_list_up_button = np.add(self.staff_list_panel, self.scale(tuple(top_panel["staff_list_up_button_offset"])))
        self.staff_list_down_button = np.add(self.staff_list_panel, self.scale(tuple(top_panel["staff_list_down_button_offset"])))
        
        # Staff entry coordinates
        staff_entry_offsets = top_panel["staff_entry_offsets"]
        self.top_panel_staff_entry = [np.add(self.staff_list_panel, self.scale(tuple(offset))) for offset in staff_entry_offsets]
        
        self.selected_tile_panel = np.add(self.top_panel, self.scale(tuple(top_panel["selected_tile_panel_offset"])))
        
        # Change attributes box
        change_attrs_offsets = top_panel["change_attributes_box_offsets"]
        self.change_attributes_box = [np.add(self.top_panel, self.scale(tuple(offset))) for offset in change_attrs_offsets]

        # Bottom panel element coordinates
        bottom_panel = self.coords_data["bottom_panel"]
        
        # Action type tabs - load configuration and calculate positions
        tab_config = bottom_panel["action_type_tabs"]
        button_types = tab_config["button_types"]
        tab_start_x = tab_config["tab_start_x"]
        tab_spacing = tab_config["tab_spacing"]
        tab_y = tab_config["tab_y"]
        
        self.action_type_tabs = {}
        for i, button_type in enumerate(button_types):
            x, y = tab_start_x + i * tab_spacing, tab_y
            self.action_type_tabs[button_type] = np.add(self.bottom_panel, self.scale((x, y)))

        # Shared coords
        self.place_button = np.add(self.bottom_panel, self.scale(tuple(bottom_panel["place_button_offset"])))
        
        # Color selection - load configuration and calculate positions
        color_config = bottom_panel["color_selection"]
        colors = color_config["colors"]
        start_x = color_config["start_x"]
        spacing = color_config["spacing"]
        y = color_config["y"]
        
        self.color_selection = {}
        for i, color in enumerate(colors):
            x = start_x + i * spacing
            self.color_selection[color] = np.add(self.bottom_panel, self.scale((x, y)))
        
        # Subtypes choices - load configuration and calculate positions
        subtypes_config = bottom_panel["subtypes_choices"]
        start_x = subtypes_config["start_x"]
        spacing = subtypes_config["spacing"]
        y = subtypes_config["y"]
        count = subtypes_config["count"]
        self.subtypes_choices = [np.add(self.bottom_panel, self.scale((start_x + spacing * i, y))) for i in range(count)]
        
        # Attributes box - load configuration and calculate positions
        attrs_config = bottom_panel["attributes_box"]
        start_x = attrs_config["start_x"]
        start_y = attrs_config["start_y"]
        col_spacing = attrs_config["col_spacing"]
        row_spacing = attrs_config["row_spacing"]
        cols = attrs_config["cols"]
        rows = attrs_config["rows"]
        
        self.attributes_box = []
        for i in range(cols * rows):
            row, col = i // cols, i % cols
            x, y = start_x + col * col_spacing, start_y + row * row_spacing
            self.attributes_box.append(np.add(self.bottom_panel, self.scale((x, y))))
        
        self.description_box = np.add(self.bottom_panel, self.scale(tuple(bottom_panel["description_box_offset"])))
        self.big_description_box = np.add(self.bottom_panel, self.scale(tuple(bottom_panel["big_description_box_offset"])))

        # Research tab coords
        research_tab = self.coords_data["research_tab"]
        self.set_research_button = np.add(self.bottom_panel, self.scale(tuple(research_tab["set_research_button_offset"])))
        
        # Speed choices - load configuration and calculate positions
        speed_config = research_tab["speed_choices"]
        speeds = speed_config["speeds"]
        start_x = speed_config["start_x"]
        start_y = speed_config["start_y"]
        spacing = speed_config["spacing"]
        
        self.res_speed_choices = {}
        for i, speed in enumerate(speeds):
            self.res_speed_choices[speed] = np.add(self.bottom_panel, self.scale((start_x, start_y + i * spacing)))

        # Research entities - load configuration and calculate positions
        entities_config = research_tab["entities"]
        entity_types = entities_config["entity_types"]
        start_x = entities_config["start_x"]
        start_y = entities_config["start_y"]
        col_spacing = entities_config["col_spacing"]
        row_spacing = entities_config["row_spacing"]
        cols = entities_config["cols"]
        
        self.res_entities = {}
        for i, entity in enumerate(entity_types):
            row, col = i // cols, i % cols
            x, y = start_x + col * col_spacing, start_y + row * row_spacing
            self.res_entities[entity] = np.add(self.bottom_panel, self.scale((x, y)))

        # Survey guests tab coords
        survey_tab = self.coords_data["survey_guests_tab"]
        self.guest_survey_results_panel = self.scale(tuple(survey_tab["guest_survey_results_panel"]))
        self.num_guests_input_box = np.add(self.bottom_panel, self.scale(tuple(survey_tab["num_guests_input_box_offset"])))
        self.survey_guests_button = np.add(self.bottom_panel, self.scale(tuple(survey_tab["survey_guests_button_offset"])))
        self.show_results_button = np.add(self.bottom_panel, self.scale(tuple(survey_tab["show_results_button_offset"])))
        self.guest_survey_up_button = np.add(self.guest_survey_results_panel, self.scale(tuple(survey_tab["guest_survey_up_button_offset"])))
        self.guest_survey_down_button = np.add(self.guest_survey_results_panel, self.scale(tuple(survey_tab["guest_survey_down_button_offset"])))
        
        # Terraform tab coords
        terraform_tab = self.coords_data["terraform_tab"]
        buttons_config = terraform_tab["buttons"]
        
        self.terraform_buttons = {
            "add": {
                "path": np.add(self.bottom_panel, self.scale(tuple(buttons_config["add"]["path_offset"]))),
                "water": np.add(self.bottom_panel, self.scale(tuple(buttons_config["add"]["water_offset"])))
            },
            "remove": {
                "path": np.add(self.bottom_panel, self.scale(tuple(buttons_config["remove"]["path_offset"]))),
                "water": np.add(self.bottom_panel, self.scale(tuple(buttons_config["remove"]["water_offset"])))
            }
        }

        # Wait/Sandbox tab coords
        wait_tab = self.coords_data["wait_tab"]
        self.wait_button = np.add(self.bottom_panel, self.scale(tuple(wait_tab["wait_button_offset"])))
        self.sandbox_actions_y_offset = wait_tab["sandbox_actions_y_offset"] * self.scale_factor
        self.undo_day_button = np.add(self.bottom_panel, self.scale(tuple(wait_tab["undo_day_button_offset"])))
        self.max_research_button = np.add(self.bottom_panel, self.scale(tuple(wait_tab["max_research_button_offset"])))
        self.max_money_button = np.add(self.bottom_panel, self.scale(tuple(wait_tab["max_money_button_offset"])))
        self.reset_button = np.add(self.bottom_panel, self.scale(tuple(wait_tab["reset_button_offset"])))
        self.switch_layouts_button = np.add(self.bottom_panel, self.scale(tuple(wait_tab["switch_layouts_button_offset"])))
        self.done_button_sandbox = np.add(self.bottom_panel, self.scale(tuple(wait_tab["done_button_offset"])))
        self.remaining_days_to_learn_from_y_offset = wait_tab["remaining_days_to_learn_from_y_offset"] * self.scale_factor

        # Selection screen coords
        selection_screen = self.coords_data["selection_screen"]
        self.start_button = self.scale(tuple(selection_screen["start_button_offset"]))

        # Updated for horizontal layout
        self.choices_x_spacing = selection_screen["choices"].get("x_spacing", 0) * self.scale_factor
        self.choices_y = selection_screen["choices"].get("y", 0) * self.scale_factor
        self.choices_textbox_y = selection_screen["choices"].get("textbox_y", 0) * self.scale_factor

        # Keep old vertical layout for backwards compatibility
        self.choices = []
        for i in range(8):
            if "start_y" in selection_screen["choices"] and "spacing" in selection_screen["choices"]:
                self.choices.append(self.scale((selection_screen["choices"]["start_x"], selection_screen["choices"]["start_y"] + i * selection_screen["choices"]["spacing"])))
            else:
                # For horizontal layout, calculate positions dynamically
                self.choices.append((0, 0))  # Placeholder, will be calculated at runtime

        # Tutorial screen coords
        if "tutorial_screen" in self.coords_data:
            tutorial_screen = self.coords_data["tutorial_screen"]
            self.tutorial_mascot = self.scale(tuple(tutorial_screen["mascot"]))
            self.tutorial_textbox = self.scale(tuple(tutorial_screen["textbox"]))
            self.tutorial_arrow_offset = self.scale(tuple(tutorial_screen["arrow_offset"]))
            self.tutorial_ok_button_offset = self.scale(tuple(tutorial_screen["ok_button_offset"]))

            # Parse tutorial steps
            self.tutorial_steps = []
            for step in tutorial_screen.get("steps", []):
                step_data = {
                    "step_idx": step["step_idx"],
                    "text": step["text"],
                    "highlight_pos": self.scale(tuple(step["highlight_pos"])) if step.get("highlight_pos") else None,
                    "include_arrow": step.get("include_arrow", False),
                    "include_ok_button": step.get("include_ok_button", False)
                }
                self.tutorial_steps.append(step_data)
        else:
            # Default values if tutorial_screen not in coords
            self.tutorial_mascot = (0, 0)
            self.tutorial_textbox = (0, 0)
            self.tutorial_arrow_offset = (0, 0)
            self.tutorial_ok_button_offset = (0, 0)
            self.tutorial_steps = []

        # End screen coords
        end_screen = self.coords_data["end_screen"]
        self.final_score_panel = self.scale(tuple(end_screen["final_score_panel"]))
        self.final_score = np.add(self.final_score_panel, self.scale(tuple(end_screen["final_score_offset"])))
        self.final_score_text_offset = self.scale(tuple(end_screen["final_score_text_offset"]))
