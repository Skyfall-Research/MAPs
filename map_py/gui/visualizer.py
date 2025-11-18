from typing import ParamSpecArgs
import pygame, time
import numpy as np
import yaml
import copy
from map_py.gui.asset_manager import Assets, Coords
from map_py.shared_constants import MAP_CONFIG, HORIZON_BY_DIFFICULTY
from enum import Enum

class GameState(Enum):
    MODE_SELECTION_SCREEN = "MODE_SELECTION_SCREEN"
    LAYOUT_SELECTION_SCREEN = "LAYOUT_SELECTION_SCREEN"
    DIFFICULTY_SELECTION_SCREEN = "DIFFICULTY_SELECTION_SCREEN"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    RUNNING_SIMULATION = "RUNNING_SIMULATION"
    END_SCREEN = "END_SCREEN"
    TERMINATE_GAME = "TERMINATE_GAME"

def format_guests_state(curr_state, new_guests_info):
    for id, guest in curr_state["guests"].items():
        guest["has_been_updated"] = False

    for guest in new_guests_info:
        id, x, y = guest['id'], guest['x'], guest['y']
        # get previous position from current state if exists, otherwise use current position
        prev_pos = curr_state["guests"].get(id, {}).get("curr_pos", (x, y))
        guest_subclass = curr_state["guests"].get(id, {}).get("subclass", np.random.randint(0,6))
        curr_state["guests"][id] = {
            "prev_pos": prev_pos,
            "curr_pos": (x, y),
            "subclass": guest_subclass
        }
        curr_state["guests"][id]["has_been_updated"] = True

    curr_state["guests"] = {id: guest for id, guest in curr_state["guests"].items() if guest["has_been_updated"]}

def format_staff_state(curr_state, new_staff_info):
    curr_state["janitors"] = {}
    curr_state["mechanics"] = {}
    curr_state["specialists"] = {}

    for employee in new_staff_info['staff_list']:
        plural_subtype = employee["subtype"] + "s"
        id, x, y = employee['id'], employee['x'], employee['y']
        # get previous position from current state if exists, otherwise use current position
        if id in curr_state[plural_subtype]:
            prev_pos = (curr_state["staff"][id]["x"], curr_state["staff"][id]["y"])
        else:
            prev_pos = (x, y)
        curr_state["staff"][id] = {
            "prev_pos": prev_pos,
            **employee,
        }
        if (x, y) not in curr_state[plural_subtype]:
            curr_state[plural_subtype][(x, y)] = []
        curr_state[plural_subtype][(x, y)].append(id)

def format_mid_day_state(curr_state, new_mid_day_info):
    curr_state["step"] = new_mid_day_info['step']
    curr_state["value"] = new_mid_day_info['value']
    curr_state["money"] = new_mid_day_info['money']
    curr_state["profit"] = new_mid_day_info['profit']
    curr_state["park_rating"] = new_mid_day_info['park_rating']
    curr_state["capacity"] = new_mid_day_info['capacity']
    curr_state["total_guests"] = new_mid_day_info['total_guests']
    curr_state["revenue"] = new_mid_day_info['revenue']
    curr_state["expenses"] = new_mid_day_info['expenses']
    format_guests_state(curr_state, new_mid_day_info['guests'])
    format_staff_state(curr_state, new_mid_day_info['staff'])
    curr_state["oos_attractions"] = []
    curr_state["tile_dirtiness"] = []
    for ride in new_mid_day_info['rides']:
        x, y = ride['x'], ride['y']
        if ride['out_of_service']:
            curr_state["oos_attractions"].append((x, y))
        curr_state["rides"][(x, y)].update(ride)
    for shop in new_mid_day_info['shops']:
        x, y = shop['x'], shop['y']
        if shop['out_of_service']:
            curr_state["oos_attractions"].append((x, y))
        curr_state["shops"][(x, y)].update(shop)
    for tile in new_mid_day_info['tile_dirtiness']:
        x, y, cleanliness = tile['x'], tile['y'], tile['cleanliness']
        curr_state["tile_dirtiness"].append((x, y, cleanliness))

def format_full_state(new_full_state):
    curr_state = {
        "rides": {},
        "shops": {},
        "staff": {},
        "guests": {},
        "guest_survey_results": new_full_state['guest_survey_results'],
        "entrance": new_full_state['entrance'],
        "exit": new_full_state['exit'],
        "paths": {},
        "waters": {},
        "oos_attractions": [],
        "tile_dirtiness": [],
        "step": new_full_state['step'],
        "horizon": new_full_state['horizon'],
        "money": new_full_state['money'],
        "value": new_full_state['value'],
        "revenue": new_full_state['revenue'],
        "expenses": new_full_state['expenses'],
        "profit": new_full_state['profit'],
        "park_rating": new_full_state['park_rating'],
        "min_cleanliness": new_full_state['min_cleanliness'],
        # Research info
        "research_speed": new_full_state['research_speed'],
        "research_topics": new_full_state['research_topics'],
        "research_operating_cost": new_full_state["research_operating_cost"],
        "available_entities": new_full_state['available_entities'],
        "new_entity_available": new_full_state['new_entity_available'],
        "fast_days_since_last_new_entity": new_full_state['fast_days_since_last_new_entity'],
        "medium_days_since_last_new_entity": new_full_state['medium_days_since_last_new_entity'],
        "slow_days_since_last_new_entity": new_full_state['slow_days_since_last_new_entity'],
        # Shop info
        "shops_total_revenue_generated": new_full_state['shops']['total_revenue_generated'],
        "shops_total_operating_cost": new_full_state['shops']['total_operating_cost'],
        "shops_min_uptime": new_full_state['shops']['min_uptime'],
        # Ride info
        "total_capacity": new_full_state['rides']['total_capacity'],
        "total_excitement": new_full_state['rides']['total_excitement'],
        "avg_intensity": new_full_state['rides']['avg_intensity'],
        "ride_min_uptime": new_full_state['rides']['min_uptime'],
        "rides_total_operating_cost": new_full_state['rides']['total_operating_cost'],
        "rides_total_revenue_generated": new_full_state['rides']['total_revenue_generated'],
        # Staff info
        "total_janitors": new_full_state['staff']['total_janitors'],
        "total_mechanics": new_full_state['staff']['total_mechanics'],
        "total_specialists": new_full_state['staff']['total_specialists'],
        "total_salary_paid": new_full_state['staff']['total_salary_paid'],
        "total_operating_cost": new_full_state['staff']['total_operating_cost'],
        # Guest info
        "total_guests": new_full_state['guests']['total_guests'],
        "avg_time_in_park": new_full_state['guests']['avg_time_in_park'],
        "avg_money_spent": new_full_state['guests']['avg_money_spent'],
        "avg_attractions_visited": (new_full_state['guests']['avg_rides_visited'] + 
                                    new_full_state['guests']['avg_food_shops_visited'] + 
                                    new_full_state['guests']['avg_drink_shops_visited'] + 
                                    new_full_state['guests']['avg_specialty_shops_visited'])
    }

    for ride in new_full_state['rides']['ride_list']:
        x, y = ride['x'], ride['y']
        curr_state["rides"][(x, y)] = ride
        if ride['out_of_service']:
            curr_state["oos_attractions"].append((x, y))
        if ride['cleanliness'] < 1.0:
            curr_state["tile_dirtiness"].append((x, y, ride['cleanliness']))

    for shop in new_full_state['shops']['shop_list']:
        x, y = shop['x'], shop['y']
        curr_state["shops"][(x, y)] = shop
        if shop['out_of_service']:
            curr_state["oos_attractions"].append((x, y))
        if shop['cleanliness'] < 1.0:
            curr_state["tile_dirtiness"].append((x, y, shop['cleanliness']))

    for path in new_full_state['paths']:
        x, y = path['x'], path['y']
        curr_state["paths"][(x, y)] = path
        curr_state["tile_dirtiness"].append((x, y, path['cleanliness']))
        
    for water in new_full_state['waters']:
        x, y = water['x'], water['y']
        curr_state["waters"][(x, y)] = water

    format_staff_state(curr_state, new_full_state['staff'])
    return curr_state

    
class Visualizer:
    guest_survey_columns = [
        ("Guest", "guest", 100),
        ("Happiness", "happiness_at_exit", 100),
        ("Hunger", "hunger_at_exit", 100),
        ("Thirst", "thirst_at_exit", 100),
        ("Energy", "remaining_energy", 100),
        ("Money", "remaining_money", 100),
        ("% of money spent", "percent_of_money_spent", 200),
        ("Reason for exit", "reason_for_exit", 275),
        ("Preference", "preference", 275),
    ]
    
    def __init__(self, scale_factor=1.0, mode:str = "few-shot"):
        # pygame setup
        pygame.init()
        self.scale_factor = scale_factor
        self.base_dims = (1900, 1000)
        self.dims = (int(self.base_dims[0] * scale_factor), int(self.base_dims[1] * scale_factor))
        self.screen = pygame.display.set_mode(self.dims)
        self.top_panel_surface = None
        self.bottom_panel_surface = None
        self.state_info_surface = None
        self.day_progress_surface = None
        self.result_message_surface = None
        self.end_screen_surface = None
        self.start_screen_surface = None
        self.survey_guests_surface = None
        pygame.display.set_caption("Mini Amusement Parks")
        self.clock = pygame.time.Clock()
        self.update_delay = 2.0  # frames between updates
        self.animate_day = True

        self.final_score = 0

        # Initialize assets and coordinates
        self.assets = Assets(scale_factor)
        self.coords = Coords(self.base_dims, scale_factor)
        
        # Load config data
        self.config = self.load_config()
        self.mode = mode
        print(self.mode)
        self.tile_size = int(50 * scale_factor)
        self.grid_size = int(1000 * scale_factor)

        # result message
        self.show_result_message = False
        self.show_new_notification = False
        #hiring
        self.pending_hire_job = None  # None, "janitor", or "mechanic"
        #place shop
        self.place_shop_price_input_active = False
        self.place_shop_top_price_input_text = ""
        self.placing_shop_type = None  # "food", "drink", or "specialty"
        #place ride

        # guest info window
        self.guest_survey_results_is_open = False
        self.guest_survey_start_index = 0
        self.survey_results = []

        # terraform window
        self.terraform_action = ""
        
        # game states
        self.game_mode = GameState.MODE_SELECTION_SCREEN
        # Surfaces
        self.grid = None
        self.people = None
        self.tile_state = None

        # input states for top panel
        self.top_panel_selection_type = None
        self.top_panel_staff_type = "janitors"
        self.staff_entry_index = 0
        self.staff_list_index = 0
        self.list_entry_choice = 0
        self.selected_tile_staff_list = []
        self.selected_tile = None
        self.selected_tile_type = None
        self.waiting_for_move = False
        # input states for bottom panel
        self.bottom_panel_action_type = "ride"
        self.choice_order = {
            "ride": ["carousel", "ferris_wheel", "roller_coaster"],
            "shop": ["drink", "food", "specialty"],
            "staff": ["janitor", "mechanic", "specialist"]
        }

        self.text_inputs = {
            "ticket_price": {f"{ride}_{color}": {"active": False, "value": ""} for color in ["yellow", "blue", "green", "red"] for ride in ["carousel", "ferris_wheel", "roller_coaster"]},
            "item_price": {f"{shop}_{color}": {"active": False, "value": ""} for color in ["yellow", "blue", "green", "red"] for shop in ["drink", "food", "specialty"]},
            "order_quantity": {f"{shop}_{color}": {"active": False, "value": ""} for color in ["yellow", "blue", "green", "red"] for shop in ["drink", "food", "specialty"]},
            "modify_price": {"modify": {"active": False, "value": ""}},
            "modify_order_quantity": {"modify": {"active": False, "value": ""}},
            "survey_guests": {"survey_guests": {"active": False, "value": ""}}
        }

        # Tutorial and mode selection variables (must be before reset())
        self.tutorial_step = -1
        self.in_tutorial_mode = False
        self.mode_choices = ["Tutorial", "Sandbox", "Play Game"]
        self.mode_choice = 0
        self.ok_button_pos = None

        self.reset()
        # research window
        self.research_open = False
        self.res_attraction_selections = ["carousel", "ferris_wheel", "roller_coaster", "drink", "food", "specialty", "janitor", "mechanic", "specialist"]
        self.res_speed_choice = "none"

        # selection screen
        self.selection_screen_open = False
        self.difficulty_choices = ["easy", "medium"]
        self.layout_choices = MAP_CONFIG['train_layouts']
        self.difficulty_choice = 0
        self.layout_choice = 0

        # control variables
        self.sandbox_mode = False
        self.sandbox_steps = 0
        self.waiting_for_grid_click = False
        self.start_time = time.time()

    def reset(self):
        self.subtype_selection_idx = {
            "ride": 0,
            "shop": 0,
            "staff": 0
        }
        # If in tutorial step 0, select carousel
        if self.tutorial_step == 0:
            self.subtype_selection_idx["ride"] = 0  # Carousel is first in the list

        self.subtype_selection = {
            "ride": self.choice_order["ride"][self.subtype_selection_idx["ride"]],
            "shop": self.choice_order["shop"][0],
            "staff": self.choice_order["staff"][0]
        }
        self.color_selection = {entity: "yellow" for entity in ["carousel", "ferris_wheel", "roller_coaster", "drink", "food", "specialty", "janitor", "mechanic", "specialist"]}

        # research window
        self.current_available_colors = {"carousel": ["yellow"], 
                                         "ferris_wheel": ["yellow"],
                                         "roller_coaster": ["yellow"],
                                         "drink": ["yellow"],
                                         "food": ["yellow"],
                                         "specialty": ["yellow"],
                                         "janitor": ["yellow"],
                                         "mechanic": ["yellow"],
                                         "specialist": ["yellow"]}

    def scale_coord(self, coord):
        return (int(coord[0] * self.scale_factor), int(coord[1] * self.scale_factor))

    def get_centered_coords(self, surface):
        return (self.dims[0] - surface.get_width()) // 2, (self.dims[1] - surface.get_height()) // 2

    def draw_difficulty_selection_screen(self):
        self.selection_screen_surface = pygame.Surface(self.dims, pygame.SRCALPHA).convert_alpha()
        self.selection_screen_surface.blit(self.assets.background, (0, 0))
        self.selection_screen_surface.blit(self.assets.start_button, self.coords.start_button)

        # Calculate horizontal layout positions
        num_choices = len(self.difficulty_choices)
        box_width = self.assets.box.get_width()
        total_width = num_choices * box_width + (num_choices - 1) * self.coords.choices_x_spacing
        choices_start_x = (self.dims[0] - total_width) // 2

        for i, difficulty in enumerate(self.difficulty_choices):
            x_pos = choices_start_x + i * (box_width + self.coords.choices_x_spacing)
            choice_pos = (x_pos, self.coords.choices_y)

            # Draw box
            self.selection_screen_surface.blit(self.assets.box, choice_pos)

            # Draw difficulty text
            difficulty_text = self.assets.large_fixed_width_font.render(difficulty.capitalize(), False, pygame.Color("black"))
            text_x = x_pos + (box_width - difficulty_text.get_width()) // 2
            text_y = self.coords.choices_y + 22 * self.scale_factor
            self.selection_screen_surface.blit(difficulty_text, (text_x, text_y))

            # Draw selection highlight
            if i == self.difficulty_choice:
                self.selection_screen_surface.blit(self.assets.selection, choice_pos)

            # Draw description textbox with multi-line text
            if i < len(self.assets.difficulty_textbox_text):
                textbox_x = x_pos + (box_width - self.assets.textbox.get_width()) // 2
                textbox_y = self.coords.choices_textbox_y
                self.selection_screen_surface.blit(self.assets.textbox, (textbox_x, textbox_y))

                # Render multi-line description text
                lines = self.assets.difficulty_textbox_text[i].split('\n')
                line_y_offset = 0
                for line in lines:
                    desc_text = self.assets.medium_fixed_width_font.render(line, False, pygame.Color("black"))
                    desc_x = textbox_x + (self.assets.textbox.get_width() - desc_text.get_width()) // 2
                    desc_y = textbox_y + 10 * self.scale_factor + line_y_offset
                    self.selection_screen_surface.blit(desc_text, (desc_x, desc_y))
                    line_y_offset += 20 * self.scale_factor

        self.screen.blit(self.selection_screen_surface, (0, 0))
    
    def draw_layout_selection_screen(self):
        if self.sandbox_mode:
            self.layout_choices = MAP_CONFIG['train_layouts']
        else:
            self.layout_choices = MAP_CONFIG['test_layouts']

        self.layout_selection_screen_surface = pygame.Surface(self.dims, pygame.SRCALPHA).convert_alpha()
        self.layout_selection_screen_surface.blit(self.assets.background, (0, 0))
        self.layout_selection_screen_surface.blit(self.assets.start_button, self.coords.start_button)

        # Calculate horizontal layout positions
        num_choices = len(self.layout_choices)
        box_width = self.assets.box.get_width()
        total_width = num_choices * box_width + (num_choices - 1) * self.coords.choices_x_spacing
        choices_start_x = (self.dims[0] - total_width) // 2

        for i, layout in enumerate(self.layout_choices):
            x_pos = choices_start_x + i * (box_width + self.coords.choices_x_spacing)
            choice_pos = (x_pos, self.coords.choices_y)

            # Draw box
            self.layout_selection_screen_surface.blit(self.assets.box, choice_pos)

            # Draw layout preview image if available
            if layout in self.assets.layout_previews:
                preview = self.assets.layout_previews[layout]
                preview_x = x_pos + (box_width - preview.get_width()) // 2
                preview_y = self.coords.choices_textbox_y
                self.layout_selection_screen_surface.blit(preview, (x_pos, preview_y))

            # Draw layout text below preview
            layout_text = self.assets.large_fixed_width_font.render(
                layout.replace("_", " ").title(), False, pygame.Color("black")
            )
            text_x = x_pos + (box_width - layout_text.get_width()) // 2
            text_y = self.coords.choices_y + 22 * self.scale_factor
            self.layout_selection_screen_surface.blit(layout_text, (text_x, text_y))

            # Draw selection highlight
            if i == self.layout_choice:
                self.layout_selection_screen_surface.blit(self.assets.selection, choice_pos)

        self.screen.blit(self.layout_selection_screen_surface, (0, 0))

    def draw_mode_selection_screen(self):
        self.mode_selection_screen_surface = pygame.Surface(self.dims, pygame.SRCALPHA).convert_alpha()
        self.mode_selection_screen_surface.blit(self.assets.background, (0, 0))
        self.mode_selection_screen_surface.blit(self.assets.start_button, self.coords.start_button)

        # Calculate horizontal layout positions
        num_choices = len(self.mode_choices)
        box_width = self.assets.box.get_width()
        total_width = num_choices * box_width + (num_choices - 1) * self.coords.choices_x_spacing
        choices_start_x = (self.dims[0] - total_width) // 2

        for i, mode in enumerate(self.mode_choices):
            x_pos = choices_start_x + i * (box_width + self.coords.choices_x_spacing)
            choice_pos = (x_pos, self.coords.choices_y)

            # Draw box
            self.mode_selection_screen_surface.blit(self.assets.box, choice_pos)

            # Draw mode text
            mode_text = self.assets.large_fixed_width_font.render(mode, False, pygame.Color("black"))
            text_x = x_pos + (box_width - mode_text.get_width()) // 2
            text_y = self.coords.choices_y + 22 * self.scale_factor
            self.mode_selection_screen_surface.blit(mode_text, (text_x, text_y))

            # Draw selection highlight
            if i == self.mode_choice:
                self.mode_selection_screen_surface.blit(self.assets.selection, choice_pos)

            # Draw description textbox with multi-line text
            if i < len(self.assets.mode_textbox_text):
                textbox_x = x_pos + (box_width - self.assets.textbox.get_width()) // 2
                textbox_y = self.coords.choices_textbox_y
                self.mode_selection_screen_surface.blit(self.assets.textbox, (textbox_x, textbox_y))

                # Render multi-line description text
                lines = self.assets.mode_textbox_text[i].split('\n')
                line_y_offset = 0
                for line in lines:
                    desc_text = self.assets.medium_fixed_width_font.render(line, False, pygame.Color("black"))
                    desc_x = textbox_x + (self.assets.textbox.get_width() - desc_text.get_width()) // 2
                    desc_y = textbox_y + 10 * self.scale_factor + line_y_offset
                    self.mode_selection_screen_surface.blit(desc_text, (desc_x, desc_y))
                    line_y_offset += 20 * self.scale_factor

        self.screen.blit(self.mode_selection_screen_surface, (0, 0))

    def draw_tutorial_overlay(self):
        """Draw tutorial overlay on top of normal gameplay"""
        if not self.in_tutorial_mode or self.tutorial_step < 0:
            return

        tutorial_surface = pygame.Surface(self.dims, pygame.SRCALPHA).convert_alpha()

        # Handle error steps (100+)
        if self.tutorial_step >= 100:
            error_idx = len(self.coords.tutorial_steps) - 2 + (self.tutorial_step - 100)
            curr_step = self.coords.tutorial_steps[error_idx]
        else:
            curr_step = self.coords.tutorial_steps[self.tutorial_step]

        # Draw mascot
        tutorial_surface.blit(self.assets.mascot, self.coords.tutorial_mascot)

        if curr_step["step_idx"] == 33:
            curr_step["text"] = "Finally, take a look at shared/documentation.md.\nIt includes detailed game mechanics and useful tips."
            curr_step["highlight_pos"] = [990 * self.scale_factor, 335 * self.scale_factor]

        # Draw multi-line text directly (no textbox background)
        lines = curr_step["text"].split('\n')
        y_offset = 0
        for line in lines:
            text_surface = self.assets.medium_fixed_width_font.render(line, False, pygame.Color("black"))
            text_x = self.coords.tutorial_textbox[0] - 7 * self.scale_factor
            text_y = self.coords.tutorial_textbox[1] + y_offset
            tutorial_surface.blit(text_surface, (text_x, text_y))
            y_offset += 40 * self.scale_factor

        # Draw arrow if needed (position relative to highlight_pos)
        if curr_step["include_arrow"] and curr_step["highlight_pos"]:
            arrow_x = curr_step["highlight_pos"][0] + self.coords.tutorial_arrow_offset[0]
            arrow_y = curr_step["highlight_pos"][1] + self.coords.tutorial_arrow_offset[1]
            tutorial_surface.blit(self.assets.arrow, (arrow_x, arrow_y))

        # Draw OK button if needed (position relative to highlight_pos)
        if curr_step["include_ok_button"] and curr_step["highlight_pos"]:
            ok_button_x = curr_step["highlight_pos"][0] + self.coords.tutorial_ok_button_offset[0]
            ok_button_y = curr_step["highlight_pos"][1] + self.coords.tutorial_ok_button_offset[1]
            self.ok_button_pos = (ok_button_x, ok_button_y)
            tutorial_surface.blit(self.assets.ok_button, self.ok_button_pos)
        else:
            self.ok_button_pos = None

        self.screen.blit(tutorial_surface, (0, 0))

    def draw_end_screen(self):
        if self.end_screen_surface is None:
            self.end_screen_surface = pygame.Surface(self.dims, pygame.SRCALPHA).convert_alpha()
            self.end_screen_surface.blit(self.assets.final_score_panel, self.coords.final_score_panel)

            final_score_text = self.assets.large_fixed_width_font.render(f"Final Score:{self.final_score:>11,}", False, pygame.Color("black"))
            self.end_screen_surface.blit(final_score_text, np.add(self.coords.final_score_panel, self.coords.final_score_text_offset))

            # Always show single "Done" button centered
            self.end_screen_surface.blit(self.assets.done_button_big, self.coords.center_main_button)

        self.screen.blit(self.end_screen_surface, (0, 0))

    def draw_updating_day(self):
        self.screen.blit(self.assets.updating_day, self.coords.updating_day)

    def draw_new_notification(self, notification, y_offset):
        if self.show_new_notification and notification:
            alert_textbox_coords = np.add(self.coords.alert_textbox, self.scale_coord((0, y_offset)))
            self.result_message_surface = pygame.Surface(self.dims, pygame.SRCALPHA).convert_alpha()
            self.result_message_surface.blit(self.assets.notification_textbox, alert_textbox_coords)
            self.result_message_surface.blit(self.assets.close_button, np.add(alert_textbox_coords, self.scale_coord((-4,-4))))
            if len(notification) >= 100:
                result_surface = self.assets.vsmall_fixed_width_font.render(notification[:97] + "...", False, pygame.Color("black"))
            elif len(notification) >= 90:
                result_surface = self.assets.vsmall_fixed_width_font.render(notification, False, pygame.Color("black"))
            elif len(notification) >= 75:
                result_surface = self.assets.small_fixed_width_font.render(notification, False, pygame.Color("black"))
            else:
                result_surface = self.assets.medium_fixed_width_font.render(notification, False, pygame.Color("black"))
            alert_message_coords = np.add(self.coords.alert_message, self.scale_coord((0, y_offset)))
            self.result_message_surface.blit(result_surface, alert_message_coords)
            self.screen.blit(self.result_message_surface, (0, 0))
            return

    def draw_error_message(self, msg, y_offset):
        self.result_message_surface = pygame.Surface(self.dims, pygame.SRCALPHA).convert_alpha()
        if self.show_result_message:
            alert_textbox_coords = np.add(self.coords.alert_textbox, self.scale_coord((0, y_offset)))
            self.result_message_surface.blit(self.assets.error_textbox, alert_textbox_coords)
            self.result_message_surface.blit(self.assets.close_button, np.add(alert_textbox_coords, self.scale_coord((-4,-4))))
            if len(msg) >= 100:
                result_surface = self.assets.vsmall_fixed_width_font.render(msg[:97] + "...", False, pygame.Color("black"))
            elif len(msg) >= 90:
                result_surface = self.assets.vsmall_fixed_width_font.render(msg, False, pygame.Color("black"))
            elif len(msg) >= 75:
                result_surface = self.assets.small_fixed_width_font.render(msg, False, pygame.Color("black"))
            else:
                result_surface = self.assets.medium_fixed_width_font.render(msg, False, pygame.Color("black"))
            alert_message_coords = np.add(self.coords.alert_message, self.scale_coord((0, y_offset)))
            self.result_message_surface.blit(result_surface, alert_message_coords)
            self.screen.blit(self.result_message_surface, (0, 0))
        else:
            self.result_message_surface = None

    def draw_playback_panel(self, delay):
        self.playback_surface = pygame.Surface(self.dims, pygame.SRCALPHA).convert_alpha()
        self.playback_surface.blit(self.assets.playback_panel, self.coords.playback_panel)
        self.playback_surface.blit(self.assets.up_button, self.coords.playback_increase)
        self.playback_surface.blit(self.assets.down_button, self.coords.playback_decrease)

        pb_rate = 16 / delay
        if pb_rate >= 1:
            pb_rate = int(pb_rate)
        delay_text = self.assets.medium_fixed_width_font.render(str(pb_rate) + 'x', False, pygame.Color("black"))
        self.playback_surface.blit(delay_text, self.coords.playback_text)

        # Animate day
        if self.animate_day:
            self.playback_surface.blit(self.assets.animate_day_active, self.coords.animate_day)
        else:
            self.playback_surface.blit(self.assets.animate_day_inactive, self.coords.animate_day)

        # noop button
        # self.playback_surface.blit(self.assets.noop_button, self.coords.noop_button)

        self.screen.blit(self.playback_surface, (0, 0))
    
    def draw_state_info(self, state):
        self.state_info_surface = pygame.Surface(self.dims, pygame.SRCALPHA).convert_alpha()
        self.state_info_surface.blit(self.assets.main_stat_panel, self.coords.main_stat_panel)
        # if not state:
        #     return  # Don't draw anything if state is empty

        profit = state.get('profit', 0)
        money = state.get('money', 0)

        info = {
            "day": ("Day: ", f"  {state.get('step', -1):>3d} / {state.get('horizon', -1):>3d}"),
            "value": ("Value: ", f"${state.get('value', 0):>10,}"),
            "money": ("Money: ", f"${money:>10,}"),
            "profit": ("Profit: ", f"${profit:>10,}"),
            "revenue": ("Revenue: ", f"${state.get('revenue', 0):>9,}"),
            "expenses": ("Expenses: ", f"${state.get('expenses', 0):>9,}"),
            "rating": f"{round(state.get('park_rating', 0), 2):>4.2f}"[:5],
            "total_capacity": f"{state.get('total_capacity', 0):>4d}",
            "guest_count": f"{state.get('total_guests', 0):>5d}",
            "avg_money_spent": f"{state.get('avg_money_spent', 0):>5.1f}",
        }

        day_label = self.assets.medium_fixed_width_font.render(info["day"][0], False, pygame.Color("black"))
        self.state_info_surface.blit(day_label, np.add(self.coords.main_stat_panel, self.scale_coord((25,32))))
        day_value = self.assets.medium_fixed_width_font.render(info["day"][1], False, pygame.Color("black"))
        self.state_info_surface.blit(day_value, np.add(self.coords.main_stat_panel, self.scale_coord((115, 32))))

        value_label = self.assets.medium_fixed_width_font.render(info["value"][0], False, pygame.Color("black"))
        self.state_info_surface.blit(value_label, np.add(self.coords.main_stat_panel, self.scale_coord((25, 74))))
        value_value = self.assets.medium_fixed_width_font.render(info["value"][1], False, pygame.Color("black"))
        self.state_info_surface.blit(value_value, np.add(self.coords.main_stat_panel, self.scale_coord((115, 74))))
        
        money_label = self.assets.medium_fixed_width_font.render(info["money"][0], False, pygame.Color("black"))
        self.state_info_surface.blit(money_label, np.add(self.coords.main_stat_panel, self.scale_coord((25, 116))))
        money_value = self.assets.medium_fixed_width_font.render(info["money"][1], False, pygame.Color("black"))
        self.state_info_surface.blit(money_value, np.add(self.coords.main_stat_panel, self.scale_coord((115, 116))))

        profit_label = self.assets.medium_fixed_width_font.render(info["profit"][0], False, pygame.Color("black"))
        self.state_info_surface.blit(profit_label, np.add(self.coords.main_stat_panel, self.scale_coord((25, 158))))
        profit_value = self.assets.medium_fixed_width_font.render(info["profit"][1], False, pygame.Color("black") if profit >= 0 else pygame.Color("red"))
        self.state_info_surface.blit(profit_value, np.add(self.coords.main_stat_panel, self.scale_coord((115, 158))))

        revenue = self.assets.small_fixed_width_font.render(info["revenue"][0], False, pygame.Color("black"))
        self.state_info_surface.blit(revenue, np.add(self.coords.main_stat_panel, self.scale_coord((23, 196))))
        revenue_value = self.assets.small_fixed_width_font.render(info["revenue"][1], False, pygame.Color("black"))
        self.state_info_surface.blit(revenue_value, np.add(self.coords.main_stat_panel, self.scale_coord((31, 210))))
        expenses = self.assets.small_fixed_width_font.render(info["expenses"][0], False, pygame.Color("black"))
        self.state_info_surface.blit(expenses, np.add(self.coords.main_stat_panel, self.scale_coord((150, 196))))
        expenses_value = self.assets.small_fixed_width_font.render(info["expenses"][1], False, pygame.Color("black"))
        self.state_info_surface.blit(expenses_value, np.add(self.coords.main_stat_panel, self.scale_coord((150, 210))))

        rating = self.assets.medium_fixed_width_font.render(info["rating"], False, pygame.Color("black"))
        self.state_info_surface.blit(rating, np.add(self.coords.main_stat_panel, self.scale_coord((64,280))))
        total_capacity = self.assets.medium_fixed_width_font.render(info['total_capacity'], False, pygame.Color("black"))
        self.state_info_surface.blit(total_capacity, np.add(self.coords.main_stat_panel, self.scale_coord((218, 280))))

        guest_count = self.assets.medium_fixed_width_font.render(info["guest_count"], False, pygame.Color("black"))
        self.state_info_surface.blit(guest_count, np.add(self.coords.main_stat_panel, self.scale_coord((64, 335))))
        avg_money_spent = self.assets.medium_fixed_width_font.render(info["avg_money_spent"], False, pygame.Color("black"))
        self.state_info_surface.blit(avg_money_spent, np.add(self.coords.main_stat_panel, self.scale_coord((207,335))))

        self.screen.blit(self.state_info_surface, (0, 0))

    def draw_aggregate_info(self,state):
        self.aggregate_info_surface = pygame.Surface(self.dims, pygame.SRCALPHA).convert_alpha()
        self.aggregate_info_surface.blit(self.assets.aggregate_stat_panel,self.coords.aggregate_stat_panel)
        park = {'Avg. Time in Park': state['avg_time_in_park'], "Min Cleanliness": state['min_cleanliness']}
        shops_keys = {'Revenue Generated': state['shops_total_revenue_generated'], 'Operating Cost': state['shops_total_operating_cost'], 'Min Uptime': state['shops_min_uptime']}
        rides_keys = {'Revenue Generated': state['rides_total_revenue_generated'], 'Operating Cost': state['rides_total_operating_cost'], 'Park Excitement': state['total_excitement'], 'Avg Intensity': state['avg_intensity'], "Total Capacity": state['total_capacity'], 'Min Uptime': state['ride_min_uptime']}
        staff_keys = {'Salary Paid': state['total_salary_paid'], 'Operating Cost': state['total_operating_cost'], '# Janitors': state['total_janitors'], '# Mechanics': state['total_mechanics'], '# Specialists': state['total_specialists']}
        research_keys = {'Operating Cost': state['research_operating_cost'], 'Fast': state['fast_days_since_last_new_entity'], 'Med.': state['medium_days_since_last_new_entity'], 'Slow': state['slow_days_since_last_new_entity']}
        x_pos,y_pos = np.add(self.coords.aggregate_stat_panel,self.scale_coord((15,22)))
        value_x_pos = x_pos + 140 * self.scale_factor
        def draw_category(header, values_dict, start_y):
            # Draw header
            header_surf = self.assets.small_fixed_width_font.render(header, False, pygame.Color("red"))
            self.aggregate_info_surface.blit(header_surf, (x_pos, start_y))
            y = start_y + 20 * self.scale_factor

            # Draw key-value pairs
            for i, (key, value) in enumerate(values_dict.items()):
                if header == "Research" and key == "Fast":
                    subtitle_text = self.assets.small_fixed_width_font.render("Days Since Discovery", False, pygame.Color("black"))
                    self.aggregate_info_surface.blit(subtitle_text, (x_pos, y))
                    y += 20 * self.scale_factor

                if isinstance(value, list):
                    value = ",".join([f"{v:>2d}" for v in value])
                else:
                    value = f"{value:>11d}" if isinstance(value, int) else f"{value:>11.2f}"
                key_text = self.assets.small_fixed_width_font.render(f"{key}: ", False, pygame.Color("black"))
                value_text = self.assets.small_fixed_width_font.render(value, False, pygame.Color("black"))
                if header == "Research" and key in ["Fast", "Med.", "Slow"]:
                    res_x_pos = x_pos + 90 * (i - 1) * self.scale_factor
                    self.aggregate_info_surface.blit(key_text, (res_x_pos, y))
                    self.aggregate_info_surface.blit(value_text, (res_x_pos - 40 * self.scale_factor, y))
                else:
                    self.aggregate_info_surface.blit(key_text, (x_pos, y))
                    self.aggregate_info_surface.blit(value_text, (value_x_pos, y))
                    y += 20 * self.scale_factor
            return y
        y_pos = draw_category("Park", park, y_pos)
        y_pos = draw_category(f"Shops ({len(state['shops'])})", shops_keys, y_pos)
        y_pos = draw_category(f"Rides ({len(state['rides'])})", rides_keys, y_pos)
        y_pos = draw_category("Staff", staff_keys, y_pos)
        y_pos = draw_category("Research", research_keys, y_pos)
        self.screen.blit(self.aggregate_info_surface, (0, 0))
        
    def draw_guest_survey_results(self, current_state):
        self.survey_guests_surface = pygame.Surface(self.dims, pygame.SRCALPHA).convert_alpha()
        self.survey_guests_surface.blit(self.assets.guest_survey_results_panel,self.coords.guest_survey_results_panel)
        self.survey_guests_surface.blit(self.assets.close_button, np.add(self.coords.guest_survey_results_panel, self.scale_coord((47,9))))

        self.survey_results = current_state["guest_survey_results"]["list_of_results"]
        # Get column headers from keys of the first dictionary
        if len(self.survey_results) == 0:
            self.screen.blit(self.survey_guests_surface, (0, 0))
            return 
        
        total_rows = min(len(self.survey_results) + 1, 13) # +1 for header row
        total_cols = len(self.guest_survey_columns)
        row_height = 25 * self.scale_factor
        start_x, start_y = self.coords.guest_survey_results_panel

        age_of_results = current_state["guest_survey_results"]["age_of_results"]
        age_of_results_text = self.assets.small_fixed_width_font.render(f"Age of Results: {age_of_results}", False, pygame.Color("black"))
        self.survey_guests_surface.blit(age_of_results_text, (start_x + 110 * self.scale_factor, start_y + 5 * self.scale_factor))

        # Draw cell backgrounds & text
        for row_idx in range(total_rows):
            col_x = start_x + 10 * self.scale_factor
            for col_idx in range(total_cols):
                column_name, column_key, column_width = self.guest_survey_columns[col_idx]

                col_width = column_width * self.scale_factor
                
                cell_x = col_x
                col_x += col_width
                cell_y = start_y + row_idx * row_height + 34 * self.scale_factor 
                if row_idx == 0:  # Header row
                    pygame.draw.rect(self.survey_guests_surface, (150,150,150), (cell_x, cell_y, col_width, row_height))
                elif col_idx == 0:  # First column
                    pygame.draw.rect(self.survey_guests_surface, (150,150,150), (cell_x, cell_y, col_width, row_height))
                # Draw cell border
                pygame.draw.rect(self.survey_guests_surface, pygame.Color("black"), (cell_x, cell_y, col_width, row_height), 1)
                # Cell text
                if row_idx == 0:
                    # Header
                    text_surface = self.assets.small_fixed_width_font.render(column_name, False, pygame.Color("black"))
                else:
                    if col_idx == 0:
                        # Guest #
                        text_surface = self.assets.small_fixed_width_font.render(f"{row_idx + self.guest_survey_start_index}", False, pygame.Color("black"))
                    else:
                        # Guest data
                        key = column_key
                        val = self.survey_results[self.guest_survey_start_index + row_idx - 1][key]
                        text_surface = self.assets.small_fixed_width_font.render(str(val), False, pygame.Color("black"))
                # Center text in the cell
                text_rect = text_surface.get_rect(center=(cell_x + col_width // 2, cell_y + row_height // 2))
                self.survey_guests_surface.blit(text_surface, text_rect)

        if len(self.survey_results) - self.guest_survey_start_index > 12:
            self.survey_guests_surface.blit(self.assets.down_button, self.coords.guest_survey_down_button)
        if self.guest_survey_start_index > 0:
            self.survey_guests_surface.blit(self.assets.up_button, self.coords.guest_survey_up_button)
        self.screen.blit(self.survey_guests_surface, (0, 0))

    def draw_game_ticks(self, frame_counter):
        self.day_progress_surface = pygame.Surface(self.dims, pygame.SRCALPHA).convert_alpha()
        self.day_progress_surface.blit(self.assets.day_progress_panel,self.coords.day_progress_panel)
        max_value = 502
        bar_x,bar_y = np.add(self.coords.day_progress_panel,self.scale_coord((123,9)))
        bar_height = self.scale_factor * 25
        bar_max_width = self.scale_factor * 447
        n = min(max_value, frame_counter + 1)
        progress_ratio = n / max_value
        fill_width = int(bar_max_width * progress_ratio)
        pygame.draw.rect(self.day_progress_surface, (50, 50, 50), (bar_x, bar_y, bar_max_width, bar_height)) # background
        pygame.draw.rect(self.day_progress_surface, (142, 190, 133), (bar_x, bar_y, fill_width, bar_height))
        self.screen.blit(self.day_progress_surface, (0, 0))
    
    def draw_top_panel(self, state):
        # background panels
        self.top_panel_surface = pygame.Surface(self.dims, pygame.SRCALPHA).convert_alpha()
        # self.top_panel_surface.blit(self.assets.panel_back, self.coords.panel_back)
        self.top_panel_surface.blit(self.assets.top_panel, self.coords.top_panel)
        self.top_panel_surface.blit(self.assets.staff_list_panel,self.coords.staff_list_panel)
        self.top_panel_surface.blit(self.assets.selected_tile_panel, self.coords.selected_tile_panel)
        # moving button
        if self.game_mode == GameState.WAITING_FOR_INPUT and self.top_panel_selection_type in ["attraction", "staff"]:
            if self.waiting_for_move:
                self.top_panel_surface.blit(self.assets.moving_button, self.coords.move_button)
            else: 
                self.top_panel_surface.blit(self.assets.move_button, self.coords.move_button)
        # staff list
        # If the tile we selected can contain people, get the staff on that tile
        self.selected_tile_staff_list = []
        if self.selected_tile_type in ["ride", "shop", "path", "entrance", "exit"]:
            staff_on_tile = state[self.top_panel_staff_type].get((self.selected_tile["x"], self.selected_tile["y"]), [])
            self.selected_tile_staff_list.extend([state["staff"][id] for id in staff_on_tile])

        self.top_panel_surface.blit(self.assets.staff_type_selection, self.coords.top_panel_staff_type[self.top_panel_staff_type])
        if self.top_panel_selection_type == "staff":
            self.top_panel_surface.blit(self.assets.staff_entry_selection, self.coords.top_panel_staff_entry[self.staff_entry_index])
            if self.game_mode == GameState.WAITING_FOR_INPUT:
                self.top_panel_surface.blit(self.assets.fire_button, self.coords.fire_button)

        page_entities = self.selected_tile_staff_list[self.staff_list_index : self.staff_list_index + 3]
        start_coord = np.add(self.coords.staff_list_panel, self.scale_coord((20,60)))
        for i, entity in enumerate(page_entities):
            current_start_coord = np.add(start_coord, self.scale_coord((0, i * 51)))
            type_text = self.assets.medium_fixed_width_font.render(f"{entity["subclass"].capitalize()} {entity["subtype"].capitalize()}", False, pygame.Color("black"))
            self.top_panel_surface.blit(type_text, current_start_coord)
            success_metric_value = f"{entity['success_metric_value']:>4.2f}" if entity['success_metric'] == "amount_cleaned" else f"{int(entity['success_metric_value']):>4}"
            success_metric_text = f"{entity['success_metric'].replace('_', ' ').title()}: {success_metric_value}"
            success_metric_text = self.assets.small_fixed_width_font.render(success_metric_text, False, pygame.Color("black"))
            self.top_panel_surface.blit(success_metric_text, np.add(current_start_coord, self.scale_coord((0,23))))
            salary_text = self.assets.small_fixed_width_font.render(f"Salary: {entity['salary']}", False, pygame.Color("black"))
            self.top_panel_surface.blit(salary_text, np.add(current_start_coord, self.scale_coord((300,0))))
            operating_cost_text = self.assets.small_fixed_width_font.render(f"Operating Cost: {entity['operating_cost']}", False, pygame.Color("black"))
            self.top_panel_surface.blit(operating_cost_text, np.add(current_start_coord, self.scale_coord((300,23))))

        if self.staff_list_index > 0:
            self.top_panel_surface.blit(self.assets.up_button, self.coords.staff_list_up_button)
        if len(self.selected_tile_staff_list) - self.staff_list_index > 3:
            self.top_panel_surface.blit(self.assets.down_button, self.coords.staff_list_down_button)

        # attraction list
        if self.selected_tile_type == "ride":
            if self.new_tile_selected:
                self.text_inputs["modify_price"]["modify"]["value"] = str(self.selected_tile["ticket_price"])
                self.new_tile_selected = False

            subtype_subclass_text = self.assets.medium_fixed_width_font.render(str(self.selected_tile["subclass"]).capitalize() + " " + str(self.selected_tile["subtype"]).capitalize().replace("_", " "), False, pygame.Color("black"))

            tile_attributes = [
                ("Cleanliness", self.selected_tile["cleanliness"]),
                ("Uptime", self.selected_tile["uptime"]),
                ("Out Of Service", self.selected_tile["out_of_service"]),
                ("Capacity", self.selected_tile["capacity"]),
                ("Intensity", self.selected_tile["intensity"]),
                ("Excitement", self.selected_tile["excitement"]),
                ("Revenue", self.selected_tile["revenue_generated"]),
                ("Costs", self.selected_tile["operating_cost"]),
                ("# Guests", self.selected_tile["guests_entertained"]),
                ("Times Op.", self.selected_tile["times_operated"]),
                ("Cost/Op.", self.selected_tile["cost_per_operation"]),
                ("Guests/Op.", self.selected_tile["avg_guests_per_operation"]),
                ("Wait Time", self.selected_tile["avg_wait_time"]),
                ("Breakdown %", self.selected_tile["breakdown_rate"] * 100),
            ]

        elif self.selected_tile_type == "shop":
            if self.new_tile_selected:
                self.text_inputs["modify_price"]["modify"]["value"] = str(self.selected_tile["item_price"])
                self.text_inputs["modify_order_quantity"]["modify"]["value"] = str(self.selected_tile["order_quantity"])
                self.new_tile_selected = False
            # id_text = self.assets.medium_fixed_width_font.render("id: " + str(self.selected_tile.get("id")), False, pygame.Color("blue"))
            subtype_subclass_text = self.assets.medium_fixed_width_font.render(str(self.selected_tile["subclass"]).capitalize() + " " + str(self.selected_tile["subtype"]).capitalize().replace("_", " ") + " Shop", False, pygame.Color("black"))
            tile_attributes = [
                ("Cleanliness", self.selected_tile["cleanliness"]),
                ("Uptime", self.selected_tile["uptime"]),
                ("Out Of Service", self.selected_tile["out_of_service"]),
                ("Item Cost", self.selected_tile["item_cost"]),
                ("Item Price", self.selected_tile["item_price"]),
                ("Order Qty.", self.selected_tile["order_quantity"]),
                ("Inventory", self.selected_tile["inventory"]),
                ("Revenue", self.selected_tile["revenue_generated"]),
                ("Costs", self.selected_tile["operating_cost"]),
                ("", ""),
                ("# Guests", self.selected_tile["guests_served"]),
                ("# Restocks", self.selected_tile["number_of_restocks"]),
            ]

        elif self.selected_tile_type == "path":
            subtype_subclass_text = self.assets.medium_fixed_width_font.render("Path", False, pygame.Color("dark grey"))
            tile_attributes = [
                ("Cleanliness", self.selected_tile["cleanliness"]),
            ]

        elif self.selected_tile_type == "water":
            subtype_subclass_text = self.assets.medium_fixed_width_font.render("Water", False, pygame.Color("blue"))
            tile_attributes = []

        # Price change text box
        if self.selected_tile_type in ["ride", "shop", "path", "water"]:
            self.top_panel_surface.blit(subtype_subclass_text, np.add(self.coords.selected_tile_panel, self.scale_coord((25,3))))

            for i, (attribute, value) in enumerate(tile_attributes):
                text_color = "black"
                if attribute == "Out Of Service":
                    if not value:
                        continue
                    else:
                        text_color = "red"
                        value = ""
                elif attribute in ["Cleanliness", "Uptime"] and value < 0.5:
                    text_color = "red"

                row, col = i // 3, i % 3
                x, y = np.add(self.coords.selected_tile_panel, self.scale_coord((23 + 183 * col, 45 + 21 * row)))
                attribute_text = self.assets.small_fixed_width_font.render(f"{attribute:<10}", False, pygame.Color(text_color))
                self.top_panel_surface.blit(attribute_text, (x, y))

                if value == "":
                    continue
                value_text = f"{value:>4.2f}" if isinstance(value, float) else f"{value:>4}"
                value_text = self.assets.small_fixed_width_font.render(value_text, False, pygame.Color(text_color))
                self.top_panel_surface.blit(value_text, np.add((x, y), self.scale_coord((116, 0))))

            if self.game_mode == GameState.WAITING_FOR_INPUT and self.top_panel_selection_type == "attraction":
                self.top_panel_surface.blit(self.assets.selected_tile_selection, self.coords.selected_tile_panel)
                changeable_attributes = ["modify_price"] if self.selected_tile_type == "ride" else ["modify_price", "modify_order_quantity"]
                for i, param in enumerate(changeable_attributes):
                    self.top_panel_surface.blit(self.assets.attributes_box, self.coords.change_attributes_box[i])
                    asset = self.assets.input_box_selected if self.text_inputs[param]["modify"]["active"] else self.assets.input_box
                    self.top_panel_surface.blit(asset, np.add(self.coords.change_attributes_box[i], self.scale_coord((100,5))))
                    value = self.text_inputs[param]["modify"]["value"]

                    param_text = param.replace("modify_", "").replace("_", " ")
                    param_text = param_text.replace("order quantity", "ord.qty.")
                    if param == "item_price":
                        param_text = "price"
                    input_text_surface = self.assets.small_fixed_width_font.render(f"{param_text + ':':<11}{value:>4}", False, pygame.Color("black"))
                    self.top_panel_surface.blit(input_text_surface, np.add(self.coords.change_attributes_box[i], self.scale_coord((10,12))))
                    if param == "item_price":
                        config_params = self.config[self.selected_tile["type"]][self.selected_tile["subtype"]][self.selected_tile["subclass"]]
                        max_item_price_input_text_surface = self.assets.vsmall_fixed_width_font.render(f"max: {config_params['max_item_price']}", False, pygame.Color("dark grey"))
                        self.top_panel_surface.blit(max_item_price_input_text_surface, np.add(self.coords.change_attributes_box[i], self.scale_coord((15,27))))
                    
                self.top_panel_surface.blit(self.assets.modify_button, self.coords.modify_button)
                self.top_panel_surface.blit(self.assets.sell_button, self.coords.sell_button)
                
        self.screen.blit(self.top_panel_surface, (0, 0))

    def draw_bottom_panel(self, state):
        self.bottom_panel_surface = pygame.Surface(self.dims, pygame.SRCALPHA).convert_alpha()
        # Main action type tabs
        for button_type in self.assets.action_type_tabs:
            assets, coords = self.assets.action_type_tabs[button_type], self.coords.action_type_tabs[button_type]
            self.bottom_panel_surface.blit(assets, coords)

        # panel background
        self.bottom_panel_surface.blit(self.assets.bottom_panel, self.coords.bottom_panel)
        self.bottom_panel_surface.blit(self.assets.action_type_tab_border, np.subtract(self.coords.action_type_tabs[self.bottom_panel_action_type], self.scale_coord((6,6))))

        cost_text = ""

        if self.bottom_panel_action_type in ["ride", "shop", "staff"]:
            self.subtype_selection[self.bottom_panel_action_type] = self.choice_order[self.bottom_panel_action_type][self.subtype_selection_idx[self.bottom_panel_action_type]]
            entity_subtype = self.subtype_selection[self.bottom_panel_action_type]

            self.current_available_colors[entity_subtype] = state["available_entities"][entity_subtype]
            self.bottom_panel_surface.blit(self.assets.color_selection_border, np.subtract(self.coords.color_selection[self.color_selection[entity_subtype]], self.scale_coord((4,4))))
            for color in ["yellow", "blue", "green", "red"]:
                if color in self.current_available_colors[entity_subtype]:
                    self.bottom_panel_surface.blit(self.assets.colored_buttons[color], self.coords.color_selection[color])

            for i in range(3):
                self.bottom_panel_surface.blit(self.assets.base_box, self.coords.subtypes_choices[i])
                entity_asset = self.assets.entity_selection[self.choice_order[self.bottom_panel_action_type][i]][self.color_selection[self.choice_order[self.bottom_panel_action_type][i]]]
                box_x, box_y = self.assets.base_box.get_size()
                entity_x, entity_y = entity_asset.get_size()
                centering_x = (box_x - entity_x) / 2
                centering_y = (box_y - entity_y) / 2
                self.bottom_panel_surface.blit(entity_asset, np.add(self.coords.subtypes_choices[i], (centering_x, centering_y)))
            
            self.bottom_panel_surface.blit(self.assets.base_selection, self.coords.subtypes_choices[self.subtype_selection_idx[self.bottom_panel_action_type]])

        # display for selected list option
        if self.bottom_panel_action_type == "staff":
            staff_params = self.config["staff"][entity_subtype][self.color_selection[entity_subtype]]
            cost_text = f"${staff_params['salary']} / day"
            self.bottom_panel_surface.blit(self.assets.big_description_box, self.coords.big_description_box)  
            
            notes = staff_params["notes"].splitlines()

            description_text1 = self.assets.medium_fixed_width_font.render(notes[0].strip(), False, pygame.Color("black"))
            self.bottom_panel_surface.blit(description_text1, np.add(self.coords.big_description_box, self.scale_coord((20,20))))
            
            if len(notes) > 1 and notes[1] != "":
                description_text2 = self.assets.medium_fixed_width_font.render(notes[1].strip(), False, pygame.Color("black"))
                self.bottom_panel_surface.blit(description_text2, np.add(self.coords.big_description_box, self.scale_coord((20,50))))

        elif self.bottom_panel_action_type == "ride":
            ride_params = self.config["rides"][entity_subtype][self.color_selection[entity_subtype]]
            for i, param in enumerate(["excitement", "intensity", "capacity", "cost_per_operation", "breakdown_rate", "ticket_price"]):
                self.bottom_panel_surface.blit(self.assets.attributes_box, self.coords.attributes_box[i])
                value = ride_params[param] 
                if value == -1:
                    selected_shop = f"{entity_subtype}_{self.color_selection[entity_subtype]}"
                    asset = self.assets.input_box_selected if self.text_inputs[param][selected_shop]["active"] else self.assets.input_box
                    self.bottom_panel_surface.blit(asset, np.add(self.coords.attributes_box[i], self.scale_coord((100,5))))
                    value = self.text_inputs[param][selected_shop]["value"]

                param_text = param
                if param == "cost_per_operation":
                    param_text = "cost / op."
                elif param == "breakdown_rate":
                    param_text = "break %"
                    value = f"{value * 100:.2f}"
                elif param == "ticket_price":
                    param_text = "price"
                else:
                    param_text = param.replace("_", " ")
                cost_text = f"${ride_params['building_cost']}"
                input_text_surface = self.assets.small_fixed_width_font.render(f"{param_text + ':':<11}{value:>4}", False, pygame.Color("black"))
                self.bottom_panel_surface.blit(input_text_surface, np.add(self.coords.attributes_box[i], self.scale_coord((10,12))))
                if param == "ticket_price":
                    max_item_price_input_text_surface = self.assets.vsmall_fixed_width_font.render(f"max: {ride_params['max_ticket_price']}", False, pygame.Color("dark grey"))
                    self.bottom_panel_surface.blit(max_item_price_input_text_surface, np.add(self.coords.attributes_box[i], self.scale_coord((15,27))))

        elif self.bottom_panel_action_type == "shop": # shop
            shop_params = self.config["shops"][entity_subtype][self.color_selection[entity_subtype]]
            for i, param in enumerate(["item_cost", "item_price", "order_quantity"]):
                self.bottom_panel_surface.blit(self.assets.attributes_box, self.coords.attributes_box[i])
                value = shop_params[param] 
                if value == -1:
                    selected_shop = f"{entity_subtype}_{self.color_selection[entity_subtype]}"
                    asset = self.assets.input_box_selected if self.text_inputs[param][selected_shop]["active"] else self.assets.input_box
                    self.bottom_panel_surface.blit(asset, np.add(self.coords.attributes_box[i], self.scale_coord((100,5))))
                    value = self.text_inputs[param][selected_shop]["value"]

                param_text = param.replace("_", " ")
                if param == "item_price":
                    param_text = "price"
                elif param == "order_quantity":
                    param_text = "ord.qty."
                input_text_surface = self.assets.small_fixed_width_font.render(f"{param_text + ':':<11}{value:>4}", False, pygame.Color("black"))
                self.bottom_panel_surface.blit(input_text_surface, np.add(self.coords.attributes_box[i], self.scale_coord((10,12))))
                if param == "item_price":
                    max_item_price_input_text_surface = self.assets.vsmall_fixed_width_font.render(f"max: {shop_params['max_item_price']}", False, pygame.Color("dark grey"))
                    self.bottom_panel_surface.blit(max_item_price_input_text_surface, np.add(self.coords.attributes_box[i], self.scale_coord((15,27))))

            self.bottom_panel_surface.blit(self.assets.description_box, self.coords.description_box) 
            description_text = self.assets.medium_fixed_width_font.render(shop_params["notes"], False, pygame.Color("black"))
            self.bottom_panel_surface.blit(description_text, np.add(self.coords.description_box, self.scale_coord((20,10))))

            try:
                daily_cost = shop_params["item_cost"] * int(self.text_inputs["order_quantity"][selected_shop]["value"])
                cost_text = f"${shop_params['building_cost']}+${daily_cost}/day"    
            except:
                cost_text = f"${shop_params['building_cost']}"    

        elif self.bottom_panel_action_type == "research":
            self.bottom_panel_surface.blit(self.assets.set_research_button, self.coords.set_research_button)
            research_price = self.assets.small_fixed_width_font.render(f"${self.config['research']['speed_cost'][self.res_speed_choice]} / day", True, pygame.Color('black'))
            self.bottom_panel_surface.blit(research_price, np.add(self.coords.set_research_button, self.scale_coord((0,45))))

            topics_text = self.assets.medium_fixed_width_font.render("Topics:", False, pygame.Color("black"))
            self.bottom_panel_surface.blit(topics_text, np.add(self.coords.bottom_panel, self.scale_coord((50,25))))
            speed_text = self.assets.medium_fixed_width_font.render("Speed:", False, pygame.Color("black"))
            self.bottom_panel_surface.blit(speed_text, np.add(self.coords.bottom_panel, self.scale_coord((400,25))))

            for entity, asset in self.assets.research_entity_choices.items():
                self.bottom_panel_surface.blit(self.assets.res_box, self.coords.res_entities[entity])
                box_x, box_y = self.assets.res_box.get_size()
                entity_x, entity_y = asset.get_size()
                centering_x = (box_x - entity_x) / 2
                centering_y = (box_y - entity_y) / 2

                self.bottom_panel_surface.blit(asset, np.add(self.coords.res_entities[entity], (centering_x, centering_y)))
                if entity in self.res_attraction_selections:
                    self.bottom_panel_surface.blit(self.assets.res_selection, self.coords.res_entities[entity])

            for speed in ["none", "slow", "medium", "fast"]:
                self.bottom_panel_surface.blit(self.assets.res_speed_box, self.coords.res_speed_choices[speed])
                speed_text = self.assets.large_fixed_width_font.render(speed.capitalize(), False, pygame.Color("black"))
                self.bottom_panel_surface.blit(speed_text, np.add(self.coords.res_speed_choices[speed], self.scale_coord((30,10))))

            self.bottom_panel_surface.blit(self.assets.res_speed_selection, self.coords.res_speed_choices[self.res_speed_choice])

        elif self.bottom_panel_action_type == "survey_guests":
            self.bottom_panel_surface.blit(self.assets.big_description_box, self.coords.big_description_box)
            asset = self.assets.input_box_selected if self.text_inputs["survey_guests"]["survey_guests"]["active"] else self.assets.input_box
            self.bottom_panel_surface.blit(asset, np.add(self.coords.big_description_box, self.scale_coord((450,30))))
            num_guests_text = self.assets.medium_fixed_width_font.render("number of guests to survey:", False, pygame.Color("black"))
            self.bottom_panel_surface.blit(num_guests_text, np.add(self.coords.big_description_box, self.scale_coord((25,26))))
            num_guests_input_text = self.assets.medium_fixed_width_font.render(f'{self.text_inputs["survey_guests"]["survey_guests"]["value"]:>2}', False, pygame.Color("black"))
            self.bottom_panel_surface.blit(num_guests_input_text, np.add(self.coords.big_description_box, self.scale_coord((478,37))))
            max_guests_text = self.assets.small_fixed_width_font.render(f"max: {self.config['max_guests_to_survey']}", False, pygame.Color("dark grey"))
            self.bottom_panel_surface.blit(max_guests_text, np.add(self.coords.big_description_box, self.scale_coord((30,49))))
            self.bottom_panel_surface.blit(self.assets.survey_guests_button, self.coords.survey_guests_button)
            if self.text_inputs["survey_guests"]["survey_guests"]["value"] != "":
                cost_text = self.assets.small_fixed_width_font.render(f"${self.config['per_guest_survey_cost'] * int(self.text_inputs['survey_guests']['survey_guests']['value'])}", False, pygame.Color("black"))
                self.bottom_panel_surface.blit(cost_text, np.add(self.coords.survey_guests_button, self.scale_coord((0,45))))

            if state["guest_survey_results"]["list_of_results"]:
                self.bottom_panel_surface.blit(self.assets.show_results_button_active, self.coords.show_results_button)
            else:
                self.bottom_panel_surface.blit(self.assets.show_results_button_inactive, self.coords.show_results_button)

        elif self.bottom_panel_action_type == "terraform":
            add_path_cost_text = self.assets.small_fixed_width_font.render(f"${self.config['path_addition_cost']}", False, pygame.Color("black"))
            remove_path_cost_text = self.assets.small_fixed_width_font.render(f"${self.config['path_removal_cost']}", False, pygame.Color("black"))
            add_water_cost_text = self.assets.small_fixed_width_font.render(f"${self.config['water_addition_cost']}", False, pygame.Color("black"))
            remove_water_cost_text = self.assets.small_fixed_width_font.render(f"${self.config['water_removal_cost']}", False, pygame.Color("black"))
            self.bottom_panel_surface.blit(add_path_cost_text, np.add(self.coords.terraform_buttons["add"]["path"], self.scale_coord((0,128))))
            self.bottom_panel_surface.blit(remove_path_cost_text, np.add(self.coords.terraform_buttons["remove"]["path"], self.scale_coord((0,128))))
            self.bottom_panel_surface.blit(add_water_cost_text, np.add(self.coords.terraform_buttons["add"]["water"], self.scale_coord((0,128))))
            self.bottom_panel_surface.blit(remove_water_cost_text, np.add(self.coords.terraform_buttons["remove"]["water"], self.scale_coord((0,128))))
            for terraform_action in ["add", "remove"]:
                for terraform_type in ["path", "water"]:
                    if self.terraform_action == f"{terraform_action}_{terraform_type}":
                        self.bottom_panel_surface.blit(self.assets.terraform_buttons[terraform_action][terraform_type][1], self.coords.terraform_buttons[terraform_action][terraform_type])
                    else:
                        self.bottom_panel_surface.blit(self.assets.terraform_buttons[terraform_action][terraform_type][0], self.coords.terraform_buttons[terraform_action][terraform_type])

        if self.bottom_panel_action_type in ["ride", "shop", "staff"]:
            if self.waiting_for_grid_click:
                self.bottom_panel_surface.blit(self.assets.placing_button, self.coords.place_button)
            else:
                self.bottom_panel_surface.blit(self.assets.place_button, self.coords.place_button)
            cost_text = self.assets.small_fixed_width_font.render(cost_text, False, pygame.Color("black"))
            self.bottom_panel_surface.blit(cost_text, np.add(self.coords.place_button, self.scale_coord((0,45))))

        elif self.bottom_panel_action_type == "wait":
            self.bottom_panel_surface.blit(self.assets.wait_button, self.coords.wait_button)
            if self.sandbox_mode:
                # sandbox actions
                sandbox_actions_text = self.assets.small_fixed_width_font.render(f"Sandbox Actions", False, pygame.Color("black"))
                # budget_value_text = self.assets.small_fixed_width_font.render(f"{state['remaining_days_to_learn_from']}", False, pygame.Color("black"))
                x_offset = (self.assets.bottom_panel.get_width() - sandbox_actions_text.get_width()) // 2
                self.bottom_panel_surface.blit(sandbox_actions_text, np.add(self.coords.bottom_panel, (x_offset, self.coords.sandbox_actions_y_offset)))
                self.bottom_panel_surface.blit(self.assets.undo_day_button, self.coords.undo_day_button)
                self.bottom_panel_surface.blit(self.assets.max_research_button, self.coords.max_research_button)
                self.bottom_panel_surface.blit(self.assets.max_money_button, self.coords.max_money_button)
                self.bottom_panel_surface.blit(self.assets.reset_button, self.coords.reset_button)
                self.bottom_panel_surface.blit(self.assets.switch_layouts_button, self.coords.switch_layouts_button)
                self.bottom_panel_surface.blit(self.assets.done_button, self.coords.done_button_sandbox)
                budget_text = self.assets.small_fixed_width_font.render(f"Remaining Days To Learn From: {self.sandbox_steps}", False, pygame.Color("black"))
                # budget_value_text = self.assets.small_fixed_width_font.render(f"{state['remaining_days_to_learn_from']}", False, pygame.Color("black"))
                x_offset = (self.assets.bottom_panel.get_width() - budget_text.get_width()) // 2
                self.bottom_panel_surface.blit(budget_text, np.add(self.coords.bottom_panel, (x_offset, self.coords.remaining_days_to_learn_from_y_offset)))

        self.screen.blit(self.bottom_panel_surface, (0, 0))

    def is_path_neighbor(self, x, y, state):
        return (
                (x, y) in state['paths'] or 
                (x, y) in state['rides'] or 
                (x, y) in state['shops'] or 
                (x, y) == state['entrance'] or (x, y) == state['exit']
            )
    
    def is_water_neighbor(self, x, y, state):
        return (x, y) in state['waters']
        

    def get_terrain_asset(self, pos, state, tile_type):
        """
        Returns the correct asset for a terrain given the surrounding tiles.
        tile_type is either "path" or "water" currently.
        TODO: clean this up, make it more readable
        """
        adj_map = []
        entrance = tuple(state['entrance'])
        exit = tuple(state['exit'])
        neighboar_diff = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        if tile_type == "water":
            neighboar_diff += [(1, -1), (-1, -1), (-1, 1), (1, 1)]
        for (dx, dy) in neighboar_diff:
            new_x, new_y = pos[0] + dx, pos[1] + dy
            
            if tile_type == "path":
                adj_map.append(self.is_path_neighbor(new_x, new_y, state))
            elif tile_type == "water":
                adj_map.append(self.is_water_neighbor(new_x, new_y, state))

        asset_list = self.assets.paths if tile_type == "path" else self.assets.water

        if adj_map[0] and adj_map[1] and adj_map[2] and adj_map[3]:
            asset = asset_list[0]
            if tile_type == "water":
                if adj_map[4] and adj_map[5] and adj_map[6] and adj_map[7]:
                    asset = asset[15]
                elif adj_map[4] and adj_map[5] and adj_map[6]:
                    asset = asset[14]
                elif adj_map[5] and adj_map[6] and adj_map[7]:
                    asset = asset[13]
                elif adj_map[6] and adj_map[7] and adj_map[4]:
                    asset = asset[12]
                elif adj_map[7] and adj_map[4] and adj_map[5]:
                    asset = asset[11]
                elif adj_map[4] and adj_map[6]:
                    asset = asset[10]
                elif adj_map[5] and adj_map[7]:
                    asset = asset[9]
                elif adj_map[4] and adj_map[5]:
                    asset = asset[8]
                elif adj_map[5] and adj_map[6]:
                    asset = asset[7]
                elif adj_map[6] and adj_map[7]:
                    asset = asset[6]
                elif adj_map[7] and adj_map[4]:
                    asset = asset[5]
                elif adj_map[4]:
                    asset = asset[4]
                elif adj_map[5]:
                    asset = asset[3]
                elif adj_map[6]:
                    asset = asset[2]
                elif adj_map[7]:
                    asset = asset[1]
                else:
                    asset = asset[0]
            return asset
        elif adj_map[0] and adj_map[2] and adj_map[3]:
            asset = asset_list[1]
            if tile_type == "water":
                if adj_map[4] and adj_map[5]:
                    asset = asset[3]
                elif adj_map[4]:
                    asset = asset[2]
                elif adj_map[5]:
                    asset = asset[1]
                else:
                    asset = asset[0]
            return asset
        elif adj_map[0] and adj_map[1] and adj_map[3]:
            asset = asset_list[2]
            if tile_type == "water":
                if adj_map[5] and adj_map[6]:
                    asset = asset[3]
                elif adj_map[5]:
                    asset = asset[2]
                elif adj_map[6]:
                    asset = asset[1]
                else:
                    asset = asset[0]
            return asset  # path3_image
        elif adj_map[0] and adj_map[1] and adj_map[2]:
            asset = asset_list[3]
            if tile_type == "water":
                if adj_map[6] and adj_map[7]:
                    asset = asset[3]
                elif adj_map[6]:
                    asset = asset[2]
                elif adj_map[7]:
                    asset = asset[1]
                else:
                    asset = asset[0]
            return asset
        elif adj_map[1] and adj_map[2] and adj_map[3]:
            asset = asset_list[4]
            if tile_type == "water":
                if adj_map[7] and adj_map[4]:
                    asset = asset[3]
                elif adj_map[7]:
                    asset = asset[2]
                elif adj_map[4]:
                    asset = asset[1]
                else:
                    asset = asset[0]
            return asset
        elif adj_map[0] and adj_map[3]:
            asset = asset_list[5]
            if tile_type == "water":
                if adj_map[5]:
                    asset = asset[1]
                else:
                    asset = asset[0]
            return asset
        elif adj_map[0] and adj_map[1]:
            asset = asset_list[6]
            if tile_type == "water":
                if adj_map[6]:
                    asset = asset[1]
                else:
                    asset = asset[0]
            return asset
        elif adj_map[1] and adj_map[2]:
            asset = asset_list[7]
            if tile_type == "water":
                if adj_map[7]:
                    asset = asset[1]
                else:
                    asset = asset[0]
            return asset
        elif adj_map[2] and adj_map[3]:
            asset = asset_list[8]
            if tile_type == "water":
                if adj_map[4]:
                    asset = asset[1]
                else:
                    asset = asset[0]
            return asset  # path9_image
        elif adj_map[1] and adj_map[3]:
            return asset_list[9]  # path10_image
        elif adj_map[0] and adj_map[2]:
            return asset_list[10]  # path11_image
        elif adj_map[0]:
            return asset_list[12]  # path13_image
        elif adj_map[1]:
            return asset_list[13]  # path14_image
        elif adj_map[2]:
            return asset_list[11]  # path12_image
        elif adj_map[3]:
            return asset_list[14]  # path16_image
        else:
            return asset_list[15]

    def draw_selected_tile(self):
        # highlight selected tile
        if self.selected_tile:
            highlight_rect = pygame.Rect(
                *self.grid_pos_to_pixel_pos((self.selected_tile['x'], self.selected_tile['y'])),
                self.tile_size,
                self.tile_size
            )
            pygame.draw.rect(self.screen, pygame.Color("red"), highlight_rect, 2)

    def grid_pos_to_pixel_pos(self, pos):
        # Flip x and y because we are using switched axes
        return (pos[1] * self.tile_size, pos[0] * self.tile_size)

    def draw_person(self, person_type, prev_pos, curr_pos, subtype=None, subclass=None, x_offset=0, y_offset=0):
        x0, y0 = prev_pos
        x1, y1 = curr_pos

        is_stationary = (x0 == x1) and (y0 == y1)
        pixel_x, pixel_y = self.grid_pos_to_pixel_pos((x1, y1))
        pixel_x += x_offset * self.scale_factor
        pixel_y += y_offset * self.scale_factor

        if person_type == "guest":
            self.people.blit(self.assets.guests[subclass], (pixel_x, pixel_y))
        elif person_type == "staff":
            self.people.blit(self.assets.staff[subtype][subclass], (pixel_x, pixel_y))

    def draw_people(self, state):
        self.people = pygame.Surface((self.grid_size, self.grid_size), pygame.SRCALPHA).convert_alpha()

        guest_counts = {}
        for id, guest in state['guests'].items():
            prev_pos = guest['prev_pos']
            curr_pos = guest['curr_pos']
            curr_count = guest_counts.get(curr_pos, 0)
            x_offset = (curr_count % 10) * 4
            y_offset = (curr_count // 10) * 2
            self.draw_person("guest", prev_pos, curr_pos, x_offset=x_offset, y_offset=y_offset, subclass=guest['subclass'])
            guest_counts[curr_pos] = curr_count + 1
        # for (x, y), ride in state['rides'].items():
        #     if self.selected_tile == (x, y):
        #         capacity = entity.get("capacity")
        #         cap_text = f"{guest_count}/{capacity}"
        #         label = self.assets.small_fixed_width_font.render(cap_text, False, pygame.Color("white"))
        #         self.grid.blit(label, (x * self.tile_size, y * self.tile_size + self.tile_size))
        staff_counts = {}
        for id, staff in state['staff'].items():
            prev_pos = staff['prev_pos']
            curr_pos = (staff['x'], staff['y'])
            subtype = staff['subtype']
            subclass = staff['subclass']
            curr_count = staff_counts.get(curr_pos, 0)
            x_offset = (curr_count % 7) * 5
            y_offset = (curr_count // 6) * 4
            self.draw_person("staff", prev_pos, curr_pos, subtype, subclass, x_offset=x_offset, y_offset=y_offset + 27)
            staff_counts[curr_pos] = curr_count + 1


    def draw_tile_state(self, state):
        """
        Draws out of operation and tile dirtiness
        """
        self.tile_state = pygame.Surface((self.grid_size, self.grid_size), pygame.SRCALPHA).convert_alpha()
        for (x, y) in state['oos_attractions']:
            x, y = self.grid_pos_to_pixel_pos((x, y))
            self.tile_state.blit(self.assets.out_of_service, (x, y))
        
        for (x, y, cleanliness) in state['tile_dirtiness']:
            x, y = self.grid_pos_to_pixel_pos((x, y))
            for i in range(4):
                if cleanliness < (0.8 - 0.2 * i):   
                    self.tile_state.blit(self.assets.cleanliness[i+1],(x - 5, y + 15))

    def draw_game_grid(self, state):
        self.grid = pygame.Surface((self.grid_size, self.grid_size), pygame.SRCALPHA).convert_alpha()

        for x in range(0, self.grid_size, self.tile_size):
            for y in range(0, self.grid_size, self.tile_size):
                pygame.draw.rect(self.grid, pygame.Color("darkgreen"), (x, y, self.tile_size, self.tile_size), 1)

        self.grid.blit(self.assets.entrance, self.grid_pos_to_pixel_pos(state['entrance']))
        self.grid.blit(self.assets.exit, self.grid_pos_to_pixel_pos(state['exit']))

        for path in state['paths']:
            tile_asset = self.get_terrain_asset(path, state, "path")
            self.grid.blit(tile_asset, self.grid_pos_to_pixel_pos(path))

        for water in state['waters']:
            water_asset = self.get_terrain_asset(water, state, "water")
            self.grid.blit(water_asset, self.grid_pos_to_pixel_pos(water))

        for (x, y), ride in state['rides'].items():
            x, y = self.grid_pos_to_pixel_pos((x, y))
            subtype, subclass = ride['subtype'], ride['subclass']
            x_offsets, y_offsets = {"carousel": (0, -7), "ferris_wheel": (-5, -10), "roller_coaster": (-1, -8)}[subtype]
            self.grid.blit(self.assets.rides[subtype][subclass], (x + x_offsets, y + y_offsets))
            
        for (x, y), shop in state['shops'].items():
            x, y = self.grid_pos_to_pixel_pos((x, y))
            subtype, subclass = shop['subtype'], shop['subclass']
            x_offsets, y_offsets = {"drink": (0, -4), "food": (0, -3), "specialty": (0, -5)}[subtype]
            self.grid.blit(self.assets.shops[subtype][subclass], (x + x_offsets, y + y_offsets))

    def render_background(self):
        self.screen.blit(self.assets.background, (0, 0))

    def render_grid(self):
        # Crop background to self.dims size\
        if self.grid != None:
            self.screen.blit(self.grid, (0, 0))
        if self.people != None:
            self.screen.blit(self.people, (0, 0))
        if self.tile_state != None:
            self.screen.blit(self.tile_state, (0, 0))

        self.draw_selected_tile()

    def save_image(self, filename):
        pygame.image.save(self.screen, filename)

    def load_config(self):
        """Load the config.yaml file"""
        # try:
        #     with open('./shared/config.yaml', 'r') as file:
        #         return yaml.safe_load(file)
        # except FileNotFoundError:
        #     print("Warning: config.yaml not found")
        #     return {}
        # except yaml.YAMLError as e:
        #     print(f"Error parsing config.yaml: {e}")
        #     return {}
        return copy.deepcopy(MAP_CONFIG)
    
