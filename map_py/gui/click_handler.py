import numpy as np
import pygame
from map_py.gui.visualizer import GameState
from map_py.shared_constants import MAP_CONFIG


class ClickHandler:
    def __init__(self, visualizer):
        self.visualizer = visualizer
        self.visualizer.waiting_for_grid_click = False
        self.visualizer.waiting_for_move = False

    def format_place_action(self, mouse_pos):
        self.visualizer.waiting_for_grid_click = False
        y = mouse_pos[0] // self.visualizer.tile_size
        x = mouse_pos[1] // self.visualizer.tile_size
        entity_type = self.visualizer.bottom_panel_action_type
        entity_subtype = self.visualizer.subtype_selection[self.visualizer.bottom_panel_action_type]
        entity_subclass = self.visualizer.color_selection[entity_subtype]

        extra_args = ""
        if self.visualizer.bottom_panel_action_type == "ride":
            if self.visualizer.text_inputs["ticket_price"][f"{entity_subtype}_{entity_subclass}"]["value"] == '':
                return "Error: missing price input field"
            extra_args = f', price={self.visualizer.text_inputs["ticket_price"][f"{entity_subtype}_{entity_subclass}"]["value"]}'
        elif self.visualizer.bottom_panel_action_type == "shop":
            if self.visualizer.text_inputs["item_price"][f"{entity_subtype}_{entity_subclass}"]["value"] == '':
                return "Error: missing price input field"
            if self.visualizer.text_inputs["order_quantity"][f"{entity_subtype}_{entity_subclass}"]["value"] == '':
                return "Error: missing order_quantity input field"
            extra_args = f', price={self.visualizer.text_inputs["item_price"][f"{entity_subtype}_{entity_subclass}"]["value"]}'
            extra_args += f', order_quantity={self.visualizer.text_inputs["order_quantity"][f"{entity_subtype}_{entity_subclass}"]["value"]}'

        action = f'place(x={x}, y={y}, type="{entity_type}", subtype="{entity_subtype}", subclass="{entity_subclass}"{extra_args})'
     
        return action

    def format_move_action(self, mouse_pos):
        self.visualizer.waiting_for_move = False
        y = mouse_pos[0] // self.visualizer.tile_size
        x = mouse_pos[1] // self.visualizer.tile_size
        selected_entity = self.visualizer.entity_to_move
        selected_entity_type = self.visualizer.entity_to_move_type
        action = f'move(type="{selected_entity_type}", subtype="{selected_entity["subtype"]}", subclass="{selected_entity["subclass"]}", x={selected_entity["x"]}, y={selected_entity["y"]}, new_x={x}, new_y={y})'
        return action

    def format_remove_action(self):
        selected_entity = self.visualizer.entity_to_remove
        selected_entity_type = self.visualizer.entity_to_remove_type
        action = f'remove(type="{selected_entity_type}", subtype="{selected_entity["subtype"]}", subclass="{selected_entity["subclass"]}", x={selected_entity["x"]}, y={selected_entity["y"]})'
        return action
    
    def format_terraform_action(self, mouse_pos):
        self.visualizer.waiting_for_grid_click = False
        y = mouse_pos[0] // self.visualizer.tile_size
        x = mouse_pos[1] // self.visualizer.tile_size
        action = f'{self.visualizer.terraform_action}(x={x}, y={y})'
        self.visualizer.terraform_action = ""
        return action

    def format_modify_action(self):
        if self.visualizer.text_inputs["modify_price"]["modify"]["value"] == '':
            return "Error: missing price input field"
        if self.visualizer.text_inputs["modify_order_quantity"]["modify"]["value"] == '' and self.visualizer.selected_tile_type == "shop":
            return "Error: missing order_quantity input field"

        entity_type = self.visualizer.selected_tile_type
        entity_x, entity_y = self.visualizer.selected_tile["x"], self.visualizer.selected_tile["y"]

        new_price = int(self.visualizer.text_inputs["modify_price"]["modify"]["value"])
        extra_args = ""
        if entity_type == "shop":
            extra_args += f', order_quantity={self.visualizer.text_inputs["modify_order_quantity"]["modify"]["value"]}'
        action = f'modify(type="{entity_type}", x={entity_x}, y={entity_y}, price={new_price}{extra_args})'
        return action

    def format_research_action(self):
        if not self.visualizer.res_attraction_selections:
            return "Error: No research direction selected"
        speed = self.visualizer.res_speed_choice
        attraction_list = []
        for attraction in self.visualizer.res_attraction_selections:
            attraction_list.append(attraction)
        action = f'set_research(research_speed="{speed}", research_topics={attraction_list})'
        return action
    
    def format_survey_guest_action(self):
        if self.visualizer.text_inputs["survey_guests"]["survey_guests"]["value"] == "":
            return "Error: missing number of guests input"
        num_guests = int(self.visualizer.text_inputs["survey_guests"]["survey_guests"]["value"])
        return f"survey_guests(num_guests={num_guests})"

    def format_wait_action(self):
        return "wait()"
    
    def format_undo_day_action(self):
        return "undo_day()"
    
    def format_max_research_action(self):
        return "max_research()"
    
    def format_max_money_action(self):
        return "max_money()"
    
    def format_reset_action(self):
        return "reset()"
    
    def format_change_settings_action(self):
        difficulty = self.visualizer.difficulty_choices[self.visualizer.difficulty_choice]
        layout = self.visualizer.layout_choices[self.visualizer.layout_choice]
        return f"change_settings(difficulty='{difficulty}', layout='{layout}')"
    
    def handle_top_panel_selection_buttons(self, pos):
        """
        Handles buttons that select different option in the top panel
        """
        # Identify entry type
        if pygame.Rect(self.visualizer.coords.selected_tile_panel, self.visualizer.assets.selected_tile_selection.get_size()).collidepoint(pos):
            self.visualizer.top_panel_selection_type = "attraction"
        if pygame.Rect(self.visualizer.coords.staff_list_panel, self.visualizer.assets.staff_list_panel.get_size()).collidepoint(pos):
            self.visualizer.top_panel_selection_type = "staff"
            # If entry type is staff, identify subtype
            for staff_type in ["janitors", "mechanics", "specialists"]:
                if pygame.Rect(self.visualizer.coords.top_panel_staff_type[staff_type], self.visualizer.assets.staff_type_selection.get_size()).collidepoint(pos):
                    self.visualizer.top_panel_staff_type = staff_type

            # If entry type is staff, get the index of the selected staff
            for i, coord in enumerate(self.visualizer.coords.top_panel_staff_entry):
                if pygame.Rect(coord, self.visualizer.assets.staff_entry_selection.get_size()).collidepoint(pos):
                    self.visualizer.staff_entry_index = i

        if pygame.Rect(self.visualizer.coords.staff_list_up_button, self.visualizer.assets.up_button.get_size()).collidepoint(pos):
            self.visualizer.staff_list_index -= 1
        if pygame.Rect(self.visualizer.coords.staff_list_down_button, self.visualizer.assets.down_button.get_size()).collidepoint(pos):
            self.visualizer.staff_list_index += 1
    
    def handle_top_panel_action_buttons(self, pos):
        """
        Handles buttons that perform actions in the top panel
        """
        action = None
        # Attraction actions
        if self.visualizer.top_panel_selection_type == "attraction":
            # Change price
            if pygame.Rect(self.visualizer.coords.modify_button, self.visualizer.assets.modify_button.get_size()).collidepoint(pos):
                if self.visualizer.selected_tile:
                    action = self.format_modify_action() or action
            # Sell
            if pygame.Rect(self.visualizer.coords.sell_button, self.visualizer.assets.sell_button.get_size()).collidepoint(pos):
                if self.visualizer.selected_tile:
                    self.visualizer.entity_to_remove = self.visualizer.selected_tile
                    self.visualizer.entity_to_remove_type = self.visualizer.selected_tile_type
                    action = self.format_remove_action() or action

        # Staff actions (fire staff)
        if self.visualizer.top_panel_selection_type == "staff":
            if pygame.Rect(self.visualizer.coords.fire_button, self.visualizer.assets.fire_button.get_size()).collidepoint(pos):
                if len(self.visualizer.selected_tile_staff_list) > self.visualizer.staff_entry_index:
                    self.visualizer.entity_to_remove = self.visualizer.selected_tile_staff_list[self.visualizer.staff_entry_index]
                    self.visualizer.entity_to_remove_type = "staff"
                    action = self.format_remove_action() or action

        # Move attraction or staff
        if pygame.Rect(self.visualizer.coords.move_button, self.visualizer.assets.move_button.get_size()).collidepoint(pos):
            if self.visualizer.top_panel_selection_type == "attraction" and self.visualizer.selected_tile:
                self.visualizer.entity_to_move = self.visualizer.selected_tile
                self.visualizer.entity_to_move_type = self.visualizer.selected_tile_type
                self.visualizer.waiting_for_move = True
            elif self.visualizer.staff_entry_index < len(self.visualizer.selected_tile_staff_list):
                self.visualizer.entity_to_move = self.visualizer.selected_tile_staff_list[self.visualizer.staff_entry_index]
                self.visualizer.entity_to_move_type = "staff" # -1 to remove "s"
                self.visualizer.waiting_for_move = True
           
        return action
    
    def handle_bottom_panel_selection_buttons(self, pos):
        """
        Handles buttons that select different option in the bottom panel
        """
        # Picking action tab
        for button_type in self.visualizer.assets.action_type_tabs:
            if pygame.Rect(self.visualizer.coords.action_type_tabs[button_type], self.visualizer.assets.action_type_tabs[button_type].get_size()).collidepoint(pos):
                self.visualizer.bottom_panel_action_type = button_type

                # Tutorial step progression for tab selection
                if self.visualizer.in_tutorial_mode:
                    if (self.visualizer.tutorial_step == 21 and button_type == "shop") or \
                       (self.visualizer.tutorial_step == 26 and button_type == "staff") or \
                       (self.visualizer.tutorial_step == 28 and button_type == "research") or \
                       (self.visualizer.tutorial_step == 29 and button_type == "survey_guests") or \
                       (self.visualizer.tutorial_step == 30 and button_type == "wait"):
                        self.visualizer.tutorial_step += 1
                return
            
        # Changing options
        if self.visualizer.bottom_panel_action_type in ["ride", "shop", "staff"]:
            for i in range(3):
                asset = self.visualizer.assets.base_box
                if pygame.Rect(self.visualizer.coords.subtypes_choices[i], asset.get_size()).collidepoint(pos) and self.visualizer.bottom_panel_action_type in ["ride", "shop", "staff"]:
                    self.visualizer.subtype_selection_idx[self.visualizer.bottom_panel_action_type] = i

                    # Tutorial step progression for subtype selection
                    if self.visualizer.in_tutorial_mode:
                        # Step 3: Click carousel (first ride subtype, index 0)
                        if self.visualizer.tutorial_step == 3 and i == 0:
                            self.visualizer.tutorial_step += 1
                        # Step 22: Select any shop subtype
                        elif self.visualizer.tutorial_step == 22:
                            self.visualizer.tutorial_step += 1
                    return

            # Changing color for rides or shops or staff
            for color in ["yellow", "blue", "green", "red"]:
                if (pygame.Rect(self.visualizer.coords.color_selection[color], self.visualizer.assets.colored_buttons[color].get_size()).collidepoint(pos) and
                    color in self.visualizer.current_available_colors[self.visualizer.subtype_selection[self.visualizer.bottom_panel_action_type]]):
                    self.visualizer.color_selection[self.visualizer.subtype_selection[self.visualizer.bottom_panel_action_type]] = color

                    # Tutorial step progression for color selection
                    if self.visualizer.in_tutorial_mode:
                        # Step 5: Select green color
                        if self.visualizer.tutorial_step == 5 and color == "green":
                            self.visualizer.tutorial_step += 1
                        # Step 7: Select yellow color
                        elif self.visualizer.tutorial_step == 7 and color == "yellow":
                            self.visualizer.tutorial_step += 1
                    return

        # Picking research direction
        if self.visualizer.bottom_panel_action_type == "research":
            # Research attraction selection
            for choice in ["carousel", "ferris_wheel", "roller_coaster", "drink", "food", "specialty", "janitor", "mechanic", "specialist"]:
                coord = self.visualizer.coords.res_entities[choice]
                if pygame.Rect(coord, self.visualizer.assets.res_box.get_size()).collidepoint(pos):
                    if choice not in self.visualizer.res_attraction_selections:
                        self.visualizer.res_attraction_selections.append(choice)
                    else:
                        self.visualizer.res_attraction_selections.remove(choice)
                    break
                        
            # Research speed selection
            for choice in ["none", "slow", "medium", "fast"]:
                coord = self.visualizer.coords.res_speed_choices[choice]
                button = self.visualizer.assets.res_speed_choices[choice]
                if pygame.Rect(coord, button.get_size()).collidepoint(pos):
                    self.visualizer.res_speed_choice = choice
                    break

        # Survey guests
        if self.visualizer.bottom_panel_action_type == "survey_guests":
            if pygame.Rect(self.visualizer.coords.show_results_button, self.visualizer.assets.show_results_button_active.get_size()).collidepoint(pos):
                self.visualizer.guest_survey_results_is_open = True
                return

    def handle_bottom_panel_action_buttons(self, pos):
        """
        Handles buttons that perform actions in the bottom panel
        """  
        action, sandbox_action = None, None

        # Place ride/shop/staff
        if self.visualizer.bottom_panel_action_type in ["ride", "shop", "staff"]:
            if (pygame.Rect(self.visualizer.coords.place_button, self.visualizer.assets.place_button.get_size()).collidepoint(pos) and
                self.visualizer.game_mode == GameState.WAITING_FOR_INPUT):
                self.visualizer.waiting_for_grid_click = True

                # Tutorial step progression for place button
                if self.visualizer.in_tutorial_mode and self.visualizer.tutorial_step == 9:
                    self.visualizer.tutorial_step += 1

        # Research
        elif self.visualizer.bottom_panel_action_type == "research":
            if pygame.Rect(self.visualizer.coords.set_research_button, self.visualizer.assets.set_research_button.get_size()).collidepoint(pos):
                action = self.format_research_action() or action

        # Survey guests
        elif self.visualizer.bottom_panel_action_type == "survey_guests":
            if pygame.Rect(self.visualizer.coords.survey_guests_button, self.visualizer.assets.survey_guests_button.get_size()).collidepoint(pos):
                action = self.format_survey_guest_action() or action

        # Terraform
        elif self.visualizer.bottom_panel_action_type == "terraform":
            for terraform_type in ["path", "water"]:
                for terraform_action in ["add", "remove"]:
                    if pygame.Rect(self.visualizer.coords.terraform_buttons[terraform_action][terraform_type], self.visualizer.assets.terraform_buttons[terraform_action][terraform_type][0].get_size()).collidepoint(pos):
                        self.visualizer.waiting_for_grid_click = True
                        self.visualizer.terraform_action = f"{terraform_action}_{terraform_type}"

        # Wait/Sandbox
        elif self.visualizer.bottom_panel_action_type == "wait":
            if pygame.Rect(self.visualizer.coords.wait_button, self.visualizer.assets.wait_button.get_size()).collidepoint(pos):
                action = self.format_wait_action() or action
                return action, None

            if self.visualizer.sandbox_mode:
                if pygame.Rect(self.visualizer.coords.undo_day_button, self.visualizer.assets.undo_day_button.get_size()).collidepoint(pos):
                    sandbox_action = self.format_undo_day_action() or sandbox_action
                elif pygame.Rect(self.visualizer.coords.max_research_button, self.visualizer.assets.max_research_button.get_size()).collidepoint(pos):
                    sandbox_action = self.format_max_research_action() or sandbox_action
                elif pygame.Rect(self.visualizer.coords.max_money_button, self.visualizer.assets.max_money_button.get_size()).collidepoint(pos):
                    sandbox_action = self.format_max_money_action() or sandbox_action
                elif pygame.Rect(self.visualizer.coords.reset_button, self.visualizer.assets.reset_button.get_size()).collidepoint(pos):
                    sandbox_action = self.format_reset_action() or sandbox_action
                elif pygame.Rect(self.visualizer.coords.switch_layouts_button, self.visualizer.assets.switch_layouts_button.get_size()).collidepoint(pos):
                    self.visualizer.game_mode = GameState.LAYOUT_SELECTION_SCREEN
                elif hasattr(self.visualizer.coords, 'done_button_sandbox') and pygame.Rect(self.visualizer.coords.done_button_sandbox, self.visualizer.assets.done_button.get_size()).collidepoint(pos):
                    # Return to mode selection
                    self.visualizer.game_mode = GameState.MODE_SELECTION_SCREEN
                    self.visualizer.tutorial_step = -1
                    self.visualizer.in_tutorial_mode = False

        return action, sandbox_action
    
    def handle_misc_selection_buttons(self, pos):
        """
        Handles playback, Error message box, Research, and Guest Info buttons
        """     
        # Animation speed
        if pygame.Rect(self.visualizer.coords.playback_increase, self.visualizer.assets.up_button.get_size()).collidepoint(pos):
            if self.visualizer.update_delay != 1:
                self.visualizer.update_delay /= 2
            return
        
        if pygame.Rect(self.visualizer.coords.playback_decrease, self.visualizer.assets.down_button.get_size()).collidepoint(pos):
            if self.visualizer.update_delay != 64:
                self.visualizer.update_delay *= 2
            return
        
        # Animate day
        if pygame.Rect(self.visualizer.coords.animate_day, self.visualizer.assets.animate_day_active.get_size()).collidepoint(pos):
            self.visualizer.animate_day = not self.visualizer.animate_day
            return
        
        # Error message box
        if (pygame.Rect(np.add(self.visualizer.coords.alert_textbox, self.visualizer.scale_coord((-4,-4))), self.visualizer.assets.close_button.get_size()).collidepoint(pos) and 
            (self.visualizer.show_result_message or self.visualizer.show_new_notification)):
            self.visualizer.show_result_message = False
            self.visualizer.show_new_notification = False

        # Close guest info panel
        if self.visualizer.guest_survey_results_is_open:
            if pygame.Rect(np.add(self.visualizer.coords.guest_survey_results_panel, self.visualizer.scale_coord((47,9))), self.visualizer.assets.close_button.get_size()).collidepoint(pos):
                self.visualizer.guest_survey_results_is_open = False
            if pygame.Rect(self.visualizer.coords.guest_survey_up_button, self.visualizer.assets.up_button.get_size()).collidepoint(pos) and \
                 self.visualizer.guest_survey_start_index > 0:
                self.visualizer.guest_survey_start_index -= 1
                return
            if pygame.Rect(self.visualizer.coords.guest_survey_down_button, self.visualizer.assets.down_button.get_size()).collidepoint(pos) and \
                 len(self.visualizer.survey_results) - self.visualizer.guest_survey_start_index > 12:
                self.visualizer.guest_survey_start_index += 1
                return

    def handle_tutorial_screen_buttons(self, pos):
        """Handle clicks on the tutorial OK button"""
        if self.visualizer.ok_button_pos:
            ok_button_rect = pygame.Rect(
                self.visualizer.ok_button_pos,
                self.visualizer.assets.ok_button.get_size()
            )
            if ok_button_rect.collidepoint(pos):
                self.visualizer.tutorial_step += 1
                return True
        return False
    
    def handle_action_buttons(self, pos):
        action, sandbox_action = None, None
        # Tile selection
        if pos[0] < self.visualizer.grid_size:
            if self.visualizer.waiting_for_move:
                action = self.format_move_action(pos)
            if self.visualizer.waiting_for_grid_click:
                if self.visualizer.bottom_panel_action_type == "terraform":
                    action = self.format_terraform_action(pos)
                else:
                    action = self.format_place_action(pos)
                    
        self.visualizer.waiting_for_move = False
        self.visualizer.waiting_for_grid_click = False
        self.visualizer.terraform_action = ""
        
        # Handle action button clicks
        action = self.handle_top_panel_action_buttons(pos) or action
        bp_action, bp_sandbox_action = self.handle_bottom_panel_action_buttons(pos)
        action = bp_action or action
        sandbox_action = bp_sandbox_action or sandbox_action
        sandbox_action = self.handle_selection_screen_buttons(pos) or sandbox_action
        return action, sandbox_action
    
    def handle_end_screen_buttons(self, pos):
        if self.visualizer.game_mode == GameState.END_SCREEN:
            if pygame.Rect(self.visualizer.coords.center_main_button, self.visualizer.assets.done_button_big.get_size()).collidepoint(pos):
                self.visualizer.game_mode = GameState.MODE_SELECTION_SCREEN
                # Reset tutorial state
                self.visualizer.tutorial_step = -1
                self.visualizer.in_tutorial_mode = False
        return None

    def handle_selection_screen_buttons(self, pos):
        # Mode selection (Tutorial/Sandbox/Play Game)
        if self.visualizer.game_mode == GameState.MODE_SELECTION_SCREEN:
            # Calculate box positions (same as in draw method)
            num_choices = len(self.visualizer.mode_choices)
            box_width = self.visualizer.assets.box.get_width()
            total_width = num_choices * box_width + (num_choices - 1) * self.visualizer.coords.choices_x_spacing
            choices_start_x = (self.visualizer.dims[0] - total_width) // 2

            # Check for mode box clicks
            for i in range(num_choices):
                x_pos = choices_start_x + i * (box_width + self.visualizer.coords.choices_x_spacing)
                choice_rect = pygame.Rect(x_pos, self.visualizer.coords.choices_y, box_width, self.visualizer.assets.box.get_height())
                if choice_rect.collidepoint(pos):
                    self.visualizer.mode_choice = i
                    return

            # Check for start button click
            if pygame.Rect(self.visualizer.coords.start_button, self.visualizer.assets.start_button.get_size()).collidepoint(pos):
                if self.visualizer.mode_choice == 0:  # Tutorial
                    self.visualizer.tutorial_step = 0
                    self.visualizer.in_tutorial_mode = True
                    self.visualizer.sandbox_mode = True
                    self.visualizer.game_mode = GameState.WAITING_FOR_INPUT
                    return [
                        f"set_sandbox_mode(sandbox_steps=100)",
                        f"change_settings(layout='tutorial')"
                    ]
                elif self.visualizer.mode_choice == 1:  # Sandbox
                    self.visualizer.sandbox_mode = True
                    self.visualizer.game_mode = GameState.DIFFICULTY_SELECTION_SCREEN
                    return f"set_sandbox_mode(sandbox_steps=9999)"
                else:  # Play Game (Evaluation)
                    self.visualizer.sandbox_mode = False
                    self.visualizer.game_mode = GameState.DIFFICULTY_SELECTION_SCREEN
                    return f"set_sandbox_mode(sandbox_steps=-1)"

        # Difficulty selection
        elif self.visualizer.game_mode == GameState.DIFFICULTY_SELECTION_SCREEN:
            # Calculate box positions
            num_choices = len(self.visualizer.difficulty_choices)
            box_width = self.visualizer.assets.box.get_width()
            total_width = num_choices * box_width + (num_choices - 1) * self.visualizer.coords.choices_x_spacing
            choices_start_x = (self.visualizer.dims[0] - total_width) // 2

            for i in range(num_choices):
                x_pos = choices_start_x + i * (box_width + self.visualizer.coords.choices_x_spacing)
                choice_rect = pygame.Rect(x_pos, self.visualizer.coords.choices_y, box_width, self.visualizer.assets.box.get_height())
                if choice_rect.collidepoint(pos):
                    self.visualizer.difficulty_choice = i
                    return

            if pygame.Rect(self.visualizer.coords.start_button, self.visualizer.assets.start_button.get_size()).collidepoint(pos):
                self.visualizer.game_mode = GameState.LAYOUT_SELECTION_SCREEN
                return f"change_settings(difficulty='{self.visualizer.difficulty_choices[self.visualizer.difficulty_choice]}')"

        # Layout selection
        elif self.visualizer.game_mode == GameState.LAYOUT_SELECTION_SCREEN:
            # Calculate box positions
            num_choices = len(self.visualizer.layout_choices)
            box_width = self.visualizer.assets.box.get_width()
            total_width = num_choices * box_width + (num_choices - 1) * self.visualizer.coords.choices_x_spacing
            choices_start_x = (self.visualizer.dims[0] - total_width) // 2

            for i in range(num_choices):
                x_pos = choices_start_x + i * (box_width + self.visualizer.coords.choices_x_spacing)
                choice_rect = pygame.Rect(x_pos, self.visualizer.coords.choices_y, box_width, self.visualizer.assets.box.get_height())
                if choice_rect.collidepoint(pos):
                    self.visualizer.layout_choice = i
                    return

            if pygame.Rect(self.visualizer.coords.start_button, self.visualizer.assets.start_button.get_size()).collidepoint(pos):
                self.visualizer.game_mode = GameState.WAITING_FOR_INPUT
                return f"change_settings(layout='{self.visualizer.layout_choices[self.visualizer.layout_choice]}')"
        return None


    def handle_grid_selection(self, x, y, state):
        if (x, y) in state["paths"]:
            new_selected_tile = state["paths"][(x, y)]
            self.visualizer.selected_tile_type = "path"
            self.visualizer.top_panel_selection_type = None
        elif (x, y) in state["waters"]:
            new_selected_tile = state["waters"][(x, y)]
            self.visualizer.selected_tile_type = "water"
            self.visualizer.top_panel_selection_type = None
        elif (x, y) in state["shops"]:
            new_selected_tile = state["shops"][(x, y)]
            self.visualizer.selected_tile_type = "shop"
        elif (x, y) in state["rides"]:
            new_selected_tile = state["rides"][(x, y)]
            self.visualizer.selected_tile_type = "ride"
        elif (x, y) == state["entrance"]:
            new_selected_tile = {"x": x, "y": y}
            self.visualizer.selected_tile_type = "entrance"
        elif (x, y) == state["exit"]:
            new_selected_tile = {"x": x, "y": y}
            self.visualizer.selected_tile_type = "exit"
        else:
            new_selected_tile = {"x": x, "y": y}
            self.visualizer.selected_tile_type = None
            self.visualizer.top_panel_selection_type = None

        if new_selected_tile != self.visualizer.selected_tile:
            self.visualizer.new_tile_selected = True
            self.visualizer.selected_tile = new_selected_tile
            if self.visualizer.selected_tile_type in ["ride", "shop"]:
                self.visualizer.top_panel_selection_type = "attraction" 
            # If the tile we selected can contain people, get the staff on that tile
            self.visualizer.staff_list_index = 0

    def handle_selection_buttons(self, pos, state):
        # grid clicks
        if pos[0] < self.visualizer.grid_size:
            y = pos[0] // self.visualizer.tile_size
            x = pos[1] // self.visualizer.tile_size
            self.handle_grid_selection(x, y, state)

        self.handle_top_panel_selection_buttons(pos)
        self.handle_bottom_panel_selection_buttons(pos)
        self.handle_misc_selection_buttons(pos)
