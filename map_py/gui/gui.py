import pygame
import sys
import pyperclip
import yaml
import time
import numpy as np

from map_py.gui.visualizer import Visualizer, GameState, format_full_state, format_mid_day_state, format_guests_state
from map_py.gui.game_state_listener import GameStateListener, Queue
from map_py.gui.click_handler import ClickHandler
from map_py.mini_amusement_park import MiniAmusementPark

class GUI:
    def __init__(self, 
                 eval_layout:str = None,
                 difficulty:str = "easy", 
                 mode:str = "few-shot",  # one of "few-shot", "few-shot+docs", "unlimited"
                 scale_factor=0.75,
                 port = '3000'):
        # State Queue
        self.buffer = Queue()
        # Initialize components
        self.visualizer = Visualizer(scale_factor=scale_factor, mode=mode)
        self.click_handler = ClickHandler(self.visualizer)
        self.game_state_listener = GameStateListener(self.buffer, accept_midday_updates=self.visualizer.animate_day)
        self.mode = mode
        self.map = MiniAmusementPark("localhost", port, 
            difficulty=difficulty, 
            visualizer=self.visualizer, 
            return_raw_in_info=True,
            seed=1234,
            render_park=False)
        self.map.reset()

        sandbox_steps = 9999 if mode == "unlimited" else MAP_CONFIG['sandbox_mode_steps']
        self.map.sandbox_action(f"set_sandbox_mode(sandbox_steps={sandbox_steps})")

        self.port = port
        self.eval_layout = eval_layout
        self.raw_start_state = {}
        
        self.current_state = {}
        # Game state
        self.error_msgs = []
        self.running = True
        self.update_counter = 0
        self.frame_counter = 0
        self.previous_update = None
        self.unchanged_count = 0
        self.speed_multiplier = 1
        self.deferred_position_update = None
        self.waiting_for_last_full_state = False
        self.game_is_done = False
        self.prev_update_type = None
        self.new_notification = None
    

    def extract_positions(self, data):
        return {
            "guests": sorted([(g["id"], g["x"], g["y"]) for g in data.get("guests", [])]),
            "staff": sorted([(s["id"], s["x"], s["y"]) for s in data.get("staff", [])])
        }

    def start_socketio_listener(self):
        self.game_state_listener.start_socketio_listener(server=f"http://localhost:{self.port}")

    def update_and_draw_grid(self, next_update):
        if "day_start" in next_update:
            self.day_end = False
            next_update = {"full_state": next_update["day_start"]}

        if "day_end" in next_update:
            self.day_end = True
            if self.waiting_for_last_full_state:
                self.game_is_done = True
            next_update = {"full_state": next_update["day_end"]}
            # Tutorial step advancement based on game state
            if self.visualizer.in_tutorial_mode and self.visualizer.tutorial_step >= 0:
                num_rides = len(next_update['full_state']['rides']['ride_list'])
                num_shops = len(next_update['full_state']['shops']['shop_list'])
                num_staff = len(next_update['full_state']['staff']['staff_list'])

                # Advance tutorial based on entities placed
                if num_rides > 0 and self.visualizer.tutorial_step < 14:
                    self.visualizer.tutorial_step = 14
                if num_shops > 0 and self.visualizer.tutorial_step < 26:
                    self.visualizer.tutorial_step = 26
                if num_staff > 0 and self.visualizer.tutorial_step < 28:
                    self.visualizer.tutorial_step = 28

        if "full_state" in next_update:
            self.current_state = format_full_state(next_update["full_state"])
            self.visualizer.draw_game_grid(self.current_state)
            self.visualizer.draw_people(self.current_state)
            self.visualizer.draw_tile_state(self.current_state)
            if self.visualizer.selected_tile is not None:
                self.click_handler.handle_grid_selection(self.visualizer.selected_tile["x"], self.visualizer.selected_tile["y"], self.current_state)
            # Set research selections to the current state
            self.visualizer.res_attraction_selections = self.current_state['research_topics']
            self.visualizer.res_speed_choice = self.current_state['research_speed']
            
        if "mid_day" in next_update:
            format_mid_day_state(self.current_state, next_update["mid_day"])
            self.visualizer.draw_people(self.current_state)
            self.visualizer.draw_tile_state(self.current_state)

        if "exit_time" in next_update:
            format_guests_state(self.current_state, next_update["exit_time"]["guests"])
            self.visualizer.draw_people(self.current_state)

    def update_game_state(self):
        if self.visualizer.game_mode == GameState.RUNNING_SIMULATION:
            if not self.buffer.is_empty():
                self.update_counter += self.speed_multiplier
                if self.update_counter >= self.visualizer.update_delay:
                    self.update_counter = 0
                    self.frame_counter += 1
                    next_update = self.buffer.dequeue()
                    while not self.visualizer.animate_day and next(iter(next_update.keys())) in ["mid_day", "exit_time"]:
                        if self.buffer.is_empty():
                            return
                        next_update = self.buffer.dequeue()
                    self.update_and_draw_grid(next_update)
                    self.prev_update_type = next_update.keys()
                    
            elif self.day_end:
                # All updates for current step shown — now switch to input
                self.day_end = False
                if not self.buffer.is_empty():
                    print(f"There is still {self.buffer.size()} updates in the buffer!")
                    self.buffer.clear()

                if not self.game_is_done:
                    self.frame_counter = 0
                    self.prev_time = time.time()
                    self.visualizer.game_mode = GameState.WAITING_FOR_INPUT
                else:
                    self.visualizer.final_score = self.score
                    self.visualizer.game_mode = GameState.END_SCREEN

    def handle_input_events(self):
        action, sandbox_action = None, None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif self.visualizer.game_mode in [GameState.MODE_SELECTION_SCREEN, GameState.LAYOUT_SELECTION_SCREEN, GameState.DIFFICULTY_SELECTION_SCREEN]:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    sandbox_action = self.click_handler.handle_selection_screen_buttons(event.pos) or sandbox_action

            elif self.visualizer.game_mode == GameState.END_SCREEN:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.click_handler.handle_end_screen_buttons(pygame.mouse.get_pos())
                
            elif self.visualizer.game_mode in [GameState.WAITING_FOR_INPUT, GameState.RUNNING_SIMULATION]:
                if not self.visualizer.animate_day and self.visualizer.game_mode == GameState.RUNNING_SIMULATION:
                    return None, None
                elif event.type == pygame.MOUSEBUTTONDOWN and self.visualizer.game_mode == GameState.WAITING_FOR_INPUT:
                    action, sandbox_action = self.click_handler.handle_action_buttons(event.pos)
                # Check for tutorial button clicks first
                if event.type == pygame.MOUSEBUTTONDOWN and self.visualizer.in_tutorial_mode and self.visualizer.tutorial_step >= 0:
                    if self.click_handler.handle_tutorial_screen_buttons(event.pos):
                        continue  # Tutorial button was clicked, don't process other clicks
                self.handle_selection_events(event)

        return action, sandbox_action

    def handle_selection_events(self, event):
        if event.type == pygame.KEYDOWN:
            self.handle_keyboard_input(event)
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_text_box_selection(event.pos)
            self.click_handler.handle_selection_buttons(event.pos, self.current_state)

    def handle_keyboard_input(self, event):
        # Handle all the text input fields
        for key1 in self.visualizer.text_inputs:
            for key2 in self.visualizer.text_inputs[key1]:
                if self.visualizer.text_inputs[key1][key2]["active"]:
                    if event.key == pygame.K_BACKSPACE:
                        self.visualizer.text_inputs[key1][key2]["value"] = self.visualizer.text_inputs[key1][key2]["value"][:-1]
                    elif event.unicode.isdigit():
                        if len(self.visualizer.text_inputs[key1][key2]["value"]) < 4:
                            self.visualizer.text_inputs[key1][key2]["value"] += event.unicode

                            # Tutorial step progression for text input
                            if self.visualizer.in_tutorial_mode:
                                if key1 == "ticket_price":
                                    self.visualizer.tutorial_step = 9
                                elif key1 == "item_price":
                                    self.visualizer.tutorial_step = 24
                                elif key1 == "order_quantity":
                                    self.visualizer.tutorial_step = 25
                    elif event.key == pygame.K_TAB:
                        # Tab to the next text box that is available
                        switches = [("modify_price", "modify_order_quantity"), ("item_price", "order_quantity")]
                        for switch in switches:
                            if key1 == switch[0] and self.visualizer.text_inputs[switch[0]][key2]["active"]:
                                self.visualizer.text_inputs[switch[0]][key2]["active"] = False
                                self.visualizer.text_inputs[switch[1]][key2]["active"] = True
                                self.visualizer.text_inputs[switch[1]][key2]["value"] = ""
                                return
                            elif key1 == switch[1] and self.visualizer.text_inputs[switch[1]][key2]["active"]:
                                self.visualizer.text_inputs[switch[1]][key2]["active"] = False
                                self.visualizer.text_inputs[switch[0]][key2]["active"] = True
                                self.visualizer.text_inputs[switch[0]][key2]["value"] = ""
                                return

    def handle_text_box_selection(self, pos):
        # Define text box rectangles and their corresponding active flags
        text_boxes = [
            ('modify_price', self.visualizer.coords.change_attributes_box[0], self.visualizer.assets.attributes_box),
            ('modify_order_quantity', self.visualizer.coords.change_attributes_box[1], self.visualizer.assets.attributes_box),
            ('survey_guests', self.visualizer.coords.big_description_box, self.visualizer.assets.big_description_box),
            ('item_price', self.visualizer.coords.attributes_box[1], self.visualizer.assets.attributes_box),
            ('order_quantity', self.visualizer.coords.attributes_box[2], self.visualizer.assets.attributes_box),
            ('ticket_price', self.visualizer.coords.attributes_box[5], self.visualizer.assets.attributes_box),
        ]
        
        for key1, coord, asset in text_boxes:
            box_type = None
            if key1 in ["modify_price", "modify_order_quantity"]:
                key2 = "modify"
            elif key1 == "survey_guests":
                box_type = "survey_guests"
                key2 = "survey_guests"
            else:
                box_type = "ride" if key1 == "ticket_price" else "shop"
                entity_subtype = self.visualizer.subtype_selection[box_type]
                key2 = f"{entity_subtype}_{self.visualizer.color_selection[entity_subtype]}"

            if (pygame.Rect(coord, asset.get_size()).collidepoint(pos) and
                ((self.visualizer.selected_tile_type == "ride" and key2 == "modify") or
                 (self.visualizer.selected_tile_type == "shop" and key2 == "modify") or 
                 (self.visualizer.bottom_panel_action_type == box_type))):
                    self.visualizer.text_inputs[key1][key2]["active"] = True
                    self.visualizer.text_inputs[key1][key2]["value"] = "" #value or self.visualizer.text_inputs[key1][key2]["value"]
            # Can only change the price of the current entry
            else:
                self.visualizer.text_inputs[key1][key2]["active"] = False

    def run(self):
        self.start_socketio_listener()

        self.buffer.clear()

        self.score = 0
        self.turn_times = []
        self.prev_time = time.time()

        if self.raw_start_state:
            obs, info = self.map.set(self.raw_start_state, hard_reset=True)
            obs = obs.model_dump()
            obs["staff"]["staff_list"] = info["raw_state"]["staff"]
        else:
            obs, info = self.map.reset()
            obs = obs.model_dump()

        self.visualizer.sandbox_mode = info["raw_state"]["state"]["sandbox_mode"]
        self.visualizer.sandbox_steps = info["raw_state"]["state"]["sandbox_steps"]
        
        self.previously_available_entities = obs["available_entities"]
        self.research_ongoing = False
        self.update_and_draw_grid({"full_state": obs})

        print("Starting game")
        
        while self.running:
            self.update_game_state()
            self.visualizer.render_background()
            if self.visualizer.game_mode == GameState.MODE_SELECTION_SCREEN:
                self.visualizer.draw_mode_selection_screen()

            elif self.visualizer.game_mode == GameState.LAYOUT_SELECTION_SCREEN:
                self.visualizer.draw_layout_selection_screen()

            elif self.visualizer.game_mode == GameState.DIFFICULTY_SELECTION_SCREEN:
                self.visualizer.draw_difficulty_selection_screen()

            elif self.visualizer.game_mode == GameState.END_SCREEN:
                self.visualizer.draw_end_screen()

            elif self.visualizer.game_mode == GameState.WAITING_FOR_INPUT:
                self.visualizer.draw_game_ticks(self.frame_counter)
                self.visualizer.draw_playback_panel(self.visualizer.update_delay)
                self.visualizer.render_grid()
                y_offset = 0
                if self.error_msgs:
                    for error_msg in self.error_msgs:
                        self.visualizer.draw_error_message(error_msg, y_offset)
                        y_offset += 75
                if self.new_notification:
                    self.visualizer.draw_new_notification(self.new_notification, y_offset)
                self.visualizer.draw_top_panel(self.current_state)
                self.visualizer.draw_bottom_panel(self.current_state)
                self.visualizer.draw_state_info(self.current_state)
                self.visualizer.draw_aggregate_info(self.current_state)
                if self.visualizer.guest_survey_results_is_open:
                    self.visualizer.draw_guest_survey_results(self.current_state)
                # Draw tutorial overlay if in tutorial mode
                if self.visualizer.in_tutorial_mode and self.visualizer.tutorial_step >= 0:
                    self.visualizer.draw_tutorial_overlay()

            elif self.visualizer.game_mode == GameState.RUNNING_SIMULATION:
                if self.visualizer.animate_day:
                    self.game_state_listener.set_accept_midday_updates(True)
                    self.visualizer.draw_top_panel(self.current_state)
                    self.visualizer.draw_bottom_panel(self.current_state)
                    self.visualizer.draw_game_ticks(self.frame_counter)
                    self.visualizer.draw_playback_panel(self.visualizer.update_delay)
                    self.visualizer.draw_state_info(self.current_state)
                    self.visualizer.render_grid()
                    y_offset = 0
                    if self.error_msgs:
                        for error_msg in self.error_msgs:
                            self.visualizer.draw_error_message(error_msg, y_offset)
                            y_offset += 75
                    # Draw tutorial overlay if in tutorial mode
                    if self.visualizer.in_tutorial_mode and self.visualizer.tutorial_step >= 0:
                        self.visualizer.draw_tutorial_overlay()
                else:
                    self.game_state_listener.set_accept_midday_updates(False)
                    self.visualizer.update_delay = 1
                    self.visualizer.draw_updating_day()
                    
            elif self.visualizer.game_mode == GameState.TERMINATE_GAME:
                self.running = False
            else:
                raise ValueError(f"Invalid game mode: {self.visualizer.game_mode}")
                    
            action, sandbox_actions = self.handle_input_events()

            if action is not None:
                self.error_msgs = []
                self.visualizer.show_result_message = True
                self.new_notification = None

                if "Error" in action:
                    self.error_msgs.append(action)
                    continue
                self.turn_times.append(time.time() - self.prev_time)
                obs, reward, done, truncated, info = self.map.step(action)

                self.score = obs.value
                if "error" in info:
                    self.error_msgs.append(info['error'].get("message"))
                    # Set tutorial to error step
                    if self.visualizer.in_tutorial_mode and self.visualizer.tutorial_step >= 0 and self.visualizer.tutorial_step < 100:
                        self.visualizer.tutorial_step = 100
                        self.visualizer.animate_day = True
                else:
                    # Check if day 1 started (tutorial step 1 trigger)
                    if self.visualizer.in_tutorial_mode and info["raw_state"]["state"]["step"] == 1:
                        if self.visualizer.tutorial_step < 11:
                            self.visualizer.tutorial_step = 11

                self.visualizer.sandbox_mode = info["raw_state"]["state"]["sandbox_mode"] and self.visualizer.sandbox_mode
                self.visualizer.sandbox_steps = info["raw_state"]["state"]["sandbox_steps"] if self.visualizer.sandbox_mode else -1

                if obs.new_entity_available:
                    for attraction in obs.available_entities:
                        for color in obs.available_entities[attraction]:
                            if color not in self.previously_available_entities[attraction]:
                                self.new_notification = f"Research Complete: {color.title()} {attraction.replace('_', ' ').title()}!"
                                self.previously_available_entities[attraction].append(color)
                                self.visualizer.show_new_notification = True

                # if no errors or noop on invalid action, run day
                if self.error_msgs == [] or self.map.noop_on_invalid_action: 
                    self.visualizer.guest_survey_results_is_open = False
                    self.visualizer.game_mode = GameState.RUNNING_SIMULATION

                # research banner no funds logic
                if "set_research" in action:
                    if "none" in action:
                        self.research_ongoing = False
                    else:
                        self.research_ongoing = True

                if self.research_ongoing and \
                    info["raw_state"]["state"]["research_speed"] == "none":
                    self.error_msgs.append("Research has stopped.")
                    self.research_ongoing = False

                if done or truncated:
                    self.waiting_for_last_full_state = True
                    self.map.save_trajectory(username="anon", save_local=True, save_to_cloud=False)

            if sandbox_actions is not None:
                if not isinstance(sandbox_actions, list):
                    sandbox_actions = [sandbox_actions]

                for sandbox_action in sandbox_actions:
                    self.visualizer.show_result_message = True
                    obs, info = self.map.sandbox_action(sandbox_action)
                    print("Sandbox action: ", sandbox_action)
                    if "error" in info:
                        self.error_msgs.append(info['error'].get("message"))
                    if sandbox_action == "max_research()":
                        self.new_notification = "Research Complete: Everything!"
                        self.visualizer.show_new_notification = True

                    if sandbox_action.startswith("reset") or sandbox_action.startswith("change_settings"):
                        self.research_ongoing = False
                        self.buffer.clear()
                        self.score = 0
                        self.visualizer.reset()
                        seed_to_use = MAP_CONFIG["train_seed"] if self.visualizer.sandbox_mode else MAP_CONFIG["test_seed"]
                        print(f"Self.visualizer.sandbox_mode: {self.visualizer.sandbox_mode}, seed_to_use: {seed_to_use}")
                        self.map.set_seed(seed_to_use)

                obs = obs.model_dump()
                obs["staff"]["staff_list"] = info["raw_state"]["staff"]
                    
                self.visualizer.sandbox_mode = info["raw_state"]["state"]["sandbox_mode"] and self.visualizer.sandbox_mode
                self.visualizer.sandbox_steps = info["raw_state"]["state"]["sandbox_steps"] if self.visualizer.sandbox_mode else -1
                self.update_and_draw_grid({"full_state": obs})
                self.previously_available_entities = obs["available_entities"]

            pygame.display.flip()
            ms_since_last_call = self.visualizer.clock.tick(125)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    import argparse
    import random
    from map_py.shared_constants import MAP_CONFIG

    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-layout", type=str, default=None, help="The layout to load.")
    parser.add_argument("--difficulty", type=str, choices=["easy", "medium", "hard"], default="easy", help="Difficulty of the game.")
    parser.add_argument("--mode", type=str, choices=["few-shot", "few-shot+docs", "unlimited"], default="few-shot", help="Mode of the game.")
    parser.add_argument("--scale", type=float, default=0.75, help="The scale factor for the game")
    parser.add_argument("--port", type=str, default='3000', help="Game Port")
    args = parser.parse_args()

    if args.eval_layout is None:
        args.eval_layout = random.choice(MAP_CONFIG['test_layouts'])

    game = GUI(eval_layout=args.eval_layout, difficulty=args.difficulty, mode=args.mode, scale_factor=args.scale, port=args.port)

    game.run()
