"""
Simple Gymnasium compatible action space for the MAPs environment.

This version is simpler at the cost of expressiveness. It removes the need to predict several of the parameters during action selection/
Instead, it uses the raw observation during action decoding and uses simple heuristics to determine these parameters.
While these heuristics provide reasonable parameters, they are inherently suboptimal.
"""

from re import S
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Any, Tuple, List
from collections import deque
from map_py.observations_and_actions.shared_constants import MAP_CONFIG

class MapsSimpleGymActionSpace(gym.spaces.MultiDiscrete):
    """
    Simplified Gymnasium compatible action space for the MAP environment.

    This is a simplified version that only includes:
    - Action types: place, move, remove, modify, set_research, wait
    - Parameters: type, subtype, subclass only
    - All other parameters (x, y, price, etc.) are set using a simple heuristic
    """

    num_actions = 5

    # Define simplified action mappings
    action_names = [
        "place",   # 0
        "move",    # 1
        "remove",  # 2
        "modify",  # 3
        "set_research",  # 4
        "wait"     # 5
    ]

    # Define parameter mappings for discrete spaces
    type_mapping = ["ride", "shop", "staff"]
    subtype_mapping = ["carousel", "ferris_wheel", "roller_coaster", "drink", "food", "specialty", "janitor", "mechanic", "specialist"]
    subclass_mapping = ["yellow", "blue", "green", "red"]
    research_speed_mapping = ["none", "slow", "medium", "fast"]
    research_topics_mapping = ["carousel", "ferris_wheel", "roller_coaster", "drink", "food", "specialty", "janitor", "mechanic", "specialist"]

    # Define which parameters are required for each action
    action_parameters = {
        0: ["type", "subtype", "subclass"],  # place
        1: ["type", "subtype", "subclass"],  # move
        2: ["type", "subtype", "subclass"],  # remove
        3: ["type", "subtype", "subclass"],  # modify
        4: ["research_speed", "research_topics"],  # set_research
        5: []  # wait
    }

    # Simplified nvec: [action_type, type, subtype, subclass]
    nvec = [
        6,   # action_type: 5 different actions
        3,   # type: ride/shop/staff
        9,   # subtype: 9 different subtypes
        4,   # subclass: yellow/blue/green/red
        4,   # research_speed: none/slow/medium/fast
        2,   # research_topic_carousel
        2,   # research_topic_ferris_wheel
        2,   # research_topic_roller_coaster
        2,   # research_topic_drink
        2,   # research_topic_food
        2,   # research_topic_specialty
        2,   # research_topic_janitor
        2,   # research_topic_mechanic
        2,   # research_topic_specialist
    ]

    dim_to_param_mapping = {
        0: "type",
        1: "subtype",
        2: "subclass",
        3: "research_speed",
        4: "research_topics_carousel",
        5: "research_topics_ferris_wheel",
        6: "research_topics_roller_coaster",
        7: "research_topics_drink",
        8: "research_topics_food",
        9: "research_topics_specialty",
        10: "research_topics_janitor",
        11: "research_topics_mechanic",
        12: "research_topics_specialist",
    }

    param_to_dim_mapping = {v: k for k, v in dim_to_param_mapping.items()}

    # Action masks (which parameters are used for each action)
    action_masks = {
        0: [True, True, True, False, False, False, False, False, False, False, False, False, False],   # place: type, subtype, subclass
        1: [True, True, True, False, False, False, False, False, False, False, False, False, False],   # move: type, subtype, subclass
        2: [True, True, True, False, False, False, False, False, False, False, False, False, False],   # remove: type, subtype, subclass
        3: [True, True, True, False, False, False, False, False, False, False, False, False, False],   # modify: type, subtype, subclass
        4: [False, False, False, True, True, True, True, True, True, True, True, True, True],   # set_research: research_speed, research_topics
        5: [False, False, False, False, False, False, False, False, False, False, False, False, False] # wait: no parameters
    }

    def __init__(self):
        super().__init__(MapsSimpleGymActionSpace.nvec)

    def sample(self) -> np.ndarray:
        """Sample a random action from the action space."""
        action = super().sample()
        return action

    def contains(self, x: np.ndarray) -> bool:
        """Check if the action is valid."""
        if not super().contains(x):
            return False

        # Check if action type is valid
        if x[0] >= self.num_actions:
            return False

        return True

    @classmethod
    def decode_action(cls, action: np.ndarray, state: Dict[str, Any]) -> str:
        """
        Decode a gymnasium action into action_spec.json format with simplified parameters.

        Args:
            action: numpy array containing the gymnasium action [action_type, type, subtype, subclass]

        Returns:
            String like "place(type='ride', subtype='carousel', subclass='green', x=-1, y=-1, price=-1, order_quantity=-1)"
            All parameters except type/subtype/subclass are set to -1.
        """
        action_type = int(action[0])
        action_name = cls.action_names[action_type]

        action_params = action[1:]

        params = []

        entity_type = cls.type_mapping[int(action_params[cls.param_to_dim_mapping["type"]])]
        entity_subtype = cls.subtype_mapping[int(action_params[cls.param_to_dim_mapping["subtype"]])]
        entity_subclass = cls.subclass_mapping[int(action_params[cls.param_to_dim_mapping["subclass"]])]

        # Build parameters string based on action type
        if action_type == 0:  # place
            params.append(f"type='{entity_type}'")
            params.append(f"subtype='{entity_subtype}'")
            params.append(f"subclass='{entity_subclass}'")
            if entity_type == "staff":
                x, y = cls.get_place_staff_xy(state)
            else:
                x, y = cls.get_place_attraction_xy(entity_type, state)
            params.append(f"x={x}")
            params.append(f"y={y}")

            if entity_type in ['ride', 'shop']:
                key = "max_item_price" if entity_type == 'shop' else "max_ticket_price"
                price = MAP_CONFIG[entity_type + "s"][entity_subtype][entity_subclass][key]
                params.append(f"price={price}")

            if entity_type == 'shop':
                order_quantity = max(10, state["guestStats"]["total_guests"] * 2)
                params.append(f"order_quantity={order_quantity}")

        elif action_type == 1:  # move
            params.append(f"type='{entity_type}'")
            params.append(f"subtype='{entity_subtype}'")
            params.append(f"subclass='{entity_subclass}'")
            x, y = cls.get_xy_or_worst_attraction(entity_type, entity_subtype, entity_subclass, state)
            if entity_type == "staff":
                new_x, new_y = cls.get_place_staff_xy(state)
            else:
                new_x, new_y = cls.get_place_attraction_xy(entity_type, state)
            params.append(f"x={x}")
            params.append(f"y={y}")
            params.append(f"new_x={new_x}")
            params.append(f"new_y={new_y}")

        elif action_type == 2:  # remove
            params.append(f"type='{entity_type}'")
            params.append(f"subtype='{entity_subtype}'")
            params.append(f"subclass='{entity_subclass}'")
            x, y = cls.get_xy_or_worst_attraction(entity_type, entity_subtype, entity_subclass, state)
            params.append(f"x={x}")
            params.append(f"y={y}")

        elif action_type == 3:  # modify
            params.append(f"type='{entity_type}'")
            params.append(f"subtype='{entity_subtype}'")
            params.append(f"subclass='{entity_subclass}'")
            x, y = cls.get_xy_or_worst_attraction(entity_type, entity_subtype, entity_subclass, state)
            params.append(f"x={x}")
            params.append(f"y={y}")

            if entity_type in ['ride', 'shop']:
                key = "max_item_price" if entity_type == 'shop' else "max_ticket_price"
                price = MAP_CONFIG[entity_type + "s"][entity_subtype][entity_subclass][key]
                params.append(f"price={price}")

            if entity_type == 'shop':
                order_quantity = max(10, state["guestStats"]["total_guests"] * 2)
                params.append(f"order_quantity={order_quantity}")

        elif action_type == 4:  # set_research
            params.append(f"research_speed='{cls.research_speed_mapping[int(action_params[cls.param_to_dim_mapping["research_speed"]])]}'")
            topics = []
            for i, bit in enumerate(action_params[cls.param_to_dim_mapping["research_topics_carousel"]:cls.param_to_dim_mapping["research_topics_specialist"]]):
                if bit:
                    topics.append(cls.research_topics_mapping[i])
            topics_str = "[" + ", ".join(f"'{topic}'" for topic in topics) + "]"
            params.append(f"research_topics={topics_str}")

        elif action_type == 5:  # wait
            pass

        return f"{action_name}({', '.join(params)})"

    @staticmethod
    def get_neighbors(current: Tuple[int, int]) -> List[Tuple[int, int]]:
        x, y = current
        neighbors = []
        if (x - 1) >= 0:
            neighbors.append((x-1, y))
        if (x + 1) < 20:
            neighbors.append((x+1, y))
        if (y - 1) >= 0:
            neighbors.append((x, y-1))
        if (y + 1) < 20:
            neighbors.append((x, y+1))
        return neighbors

    @staticmethod
    def get_place_attraction_xy(entity_type: str, state: Dict[str, Any]) -> Tuple[int, int]:
        TOP=5     # Top-N positions

        grid = np.zeros((20, 20))
        for terrain in state["terrain"]:
            if terrain['type'] == 'path':
                grid[terrain['x'], terrain['y']] = 1
            elif terrain['type'] == 'water':
                grid[terrain['x'], terrain['y']] = 2
        for ride in state["rides"]:
            grid[ride['x'], ride['y']] = 3
        for shop in state["shops"]:
            grid[shop['x'], shop['y']] = 4
        grid[state["entrance"]["x"], state["entrance"]["y"]] = 5
        grid[state["exit"]["x"], state["exit"]["y"]] = 6

        valid_options = []
        wavefront = (state["entrance"]["x"], state["entrance"]["y"])
        visited = set()
        visited.add(wavefront)
        queue = deque([wavefront])
        while queue and len(valid_options) < TOP:
            current = queue.popleft()
            for neighbor in MapsSimpleGymActionSpace.get_neighbors(current):
                # If neighbor is a path, add to queue and visited
                if neighbor not in visited and grid[neighbor[0], neighbor[1]] == 1:
                    visited.add(neighbor)
                    queue.append(neighbor)
                # If neighbor is empty, add to valid options
                elif neighbor not in visited and grid[neighbor[0], neighbor[1]] == 0 and current != wavefront:
                    visited.add(neighbor)
                    valid_options.append(neighbor)

        # Handle case where no valid positions found
        if not valid_options:
            return (state["entrance"]["x"], state["entrance"]["y"])

        scoring = {0: -1, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0, 6: 0} if entity_type == 'ride' else {0: 1, 1: 0, 2: -1, 3: 0, 4: 0, 5: 0, 6: 0}
        scores = {option: sum([scoring[grid[neighbor[0], neighbor[1]]] for neighbor in MapsSimpleGymActionSpace.get_neighbors(option)]) for option in valid_options}
        sorted_options = sorted(valid_options, key=lambda x: scores[x], reverse=True)
        return sorted_options[0]

    @staticmethod
    def get_place_staff_xy(state: Dict[str, Any]) -> Tuple[int, int]:
        return state["entrance"]["x"], state["entrance"]["y"]

    @staticmethod
    def modify_order_quantity(shop_subtype: str, shop_subclass: str, state: Dict[str, Any]) -> Tuple[int, int, int]:
        most_offset_shop = None
        most_offset_inventory = 0
        new_inventory = 0
        for shop in state["shops"]:
            if shop['subtype'] == shop_subtype and shop['subclass'] == shop_subclass:
                ideal_inventory = 0
                if shop['uptime'] < 1.0:
                    ideal_inventory = shop['guests_served'] / shop['uptime']
                else:
                    ideal_inventory = shop['guests_served']
                ideal_inventory = int(1.2 * ideal_inventory)

                offset = abs(shop['inventory'] - ideal_inventory)
                if offset > most_offset_inventory:
                    most_offset_inventory = offset
                    most_offset_shop = shop
                    new_inventory = ideal_inventory
        return most_offset_shop['x'], most_offset_shop['y'], new_inventory

    @staticmethod
    def get_xy_or_worst_attraction(entity_type: str, entity_subtype: str, entity_subclass: str, state: Dict[str, Any]) -> Tuple[int, int]:
        worst_entity = None
        worst_metric = float('inf')
        entity_key = entity_type if entity_type == 'staff' else f"{entity_type}s"

        for entity in state[entity_key]:
            if entity['subtype'] == entity_subtype and entity['subclass'] == entity_subclass:
                metric = entity['success_metric_value'] if entity_type == 'staff' else entity['revenue_generated'] - entity['operating_cost']
                if metric < worst_metric:
                    worst_metric = metric
                    worst_entity = entity
        return worst_entity['x'], worst_entity['y']