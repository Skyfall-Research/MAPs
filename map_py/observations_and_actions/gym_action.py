"""
Gymnasium compatible action space for the MAPs environment.

This action space supports all the actions defined in action_spec.json and provides full expressiveness.
- place, move, remove, modify
- set_research, survey_guests
- add_path, remove_path, add_water, remove_water
- wait
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import yaml
from typing import Dict, Any, List, Union
import importlib.resources
from map_py.observations_and_actions.shared_constants import MAP_CONFIG
MODULE_PATH = importlib.resources.files(__package__)

class MapsGymActionSpace(gym.spaces.MultiDiscrete):
    """
    Gymnasium compatible action space for the MAP environment.

    This action space supports all the actions defined in action_spec.json:
    - place, move, remove, modify
    - set_research, survey_guests
    - add_path, remove_path, add_water, remove_water
    - wait
    """

    num_actions = 11

    # Define action mappings (matching action_spec.json)
    action_names = [
        "place",           # 0
        "move",            # 1
        "remove",          # 2
        "modify",          # 3
        "set_research",    # 4
        "survey_guests",   # 5
        "add_path",        # 6
        "remove_path",     # 7
        "add_water",       # 8
        "remove_water",    # 9
        "wait"             # 10
    ]

    # Define parameter mappings for discrete spaces
    type_mapping = ["ride", "shop", "staff"]
    subtype_mapping = ["carousel", "ferris_wheel", "roller_coaster", "drink", "food", "specialty", "janitor", "mechanic", "specialist"]
    subclass_mapping = ["yellow", "blue", "green", "red"]
    research_speed_mapping = ["none", "slow", "medium", "fast"]
    research_topics_mapping = ["carousel", "ferris_wheel", "roller_coaster", "drink", "food", "specialty", "janitor", "mechanic", "specialist"]

    # Define which parameters are required for each action (per action_spec.json)
    action_parameters = {
        0: ["type", "subtype", "subclass", "x", "y", "order_quantity"],  # place, "price",
        1: ["type", "subtype", "subclass", "x", "y", "new_x", "new_y"],  # move
        2: ["type", "subtype", "subclass", "x", "y", "order_quantity"],  # modify, "price", 
        3: ["type", "subtype", "subclass", "x", "y"],  # remove
        4: ["research_speed", "research_topics"],  # set_research
        5: ["num_guests"],  # survey_guests
        6: ["x", "y"],  # add_path
        7: ["x", "y"],  # remove_path
        8: ["x", "y"],  # add_water
        9: ["x", "y"],  # remove_water
        10: []  # wait
    }

    nvec = [
        11,  # action_type: 11 different actions (updated to match action_spec.json)
        3,   # type: ride/shop/staff (updated from 4 to 3)
        9,   # subtype: carousel/ferris_wheel/roller_coaster/drink/food/specialty/janitor/mechanic/specialist
        4,   # subclass: yellow/blue/green/red
        20,  # x: 0-20 (21 positions)
        20,  # y: 0-20 (21 positions)
        20,  # new_x: 0-20 (21 positions)
        20,  # new_y: 0-20 (21 positions)
        51, # price: 0-50 (50 discrete values)
        100, # order_quantity: 1-2500 (discretized from original range into buckets of 25)
        26,  # num_guests: 1-25
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
        3: "x",
        4: "y",
        5: "new_x",
        6: "new_y",
        7: "price",
        8: "order_quantity",
        9: "num_guests",
        10: "research_speed",
        11: "research_topics_carousel",
        12: "research_topics_ferris_wheel",
        13: "research_topics_roller_coaster",
        14: "research_topics_drink",
        15: "research_topics_food",
        16: "research_topics_specialty",
        17: "research_topics_janitor",
        18: "research_topics_mechanic",
        19: "research_topics_specialist",
    }

    param_to_dim_mapping = {v: k for k, v in dim_to_param_mapping.items()}

    action_masks = {
        0: [True, True, True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, False, False, False],
        1: [True, True, True, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False],
        2: [True, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False],
        3: [True, True, True, True, True, False, False, True, True, False, False, False, False, False, False, False, False, False, False, False],
        4: [False, False, False, False, False, False, False, False, False, False, True, True, True, True, True, True, True, True, True, True],
        5: [False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False],
        6: [False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False],
        7: [False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False],
        8: [False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False],
        9: [False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False],
        10: [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False],
    }

    def __init__(self):
        with open(MODULE_PATH/'../../shared/config.yaml', 'r') as infile:
            config = yaml.safe_load(infile)
        max_price = max(
            config['shops']['drink']['red']['max_item_price'],
            config['shops']['food']['red']['max_item_price'],
            config['shops']['specialty']['red']['max_item_price'],
            config['rides']['roller_coaster']['red']['max_ticket_price']
        )
        # Use reasonable default for max_order_quantity (not defined in config)
        super().__init__(MapsGymActionSpace.nvec)


    def sample(self) -> Dict[str, Any]:
        """Sample a random action from the action space."""
        action = super().sample()

        # Set unused parameters to default values
        action_type = action["action_type"]
        required_params = self.action_parameters[action_type]

        # Reset unused parameters to safe defaults
        for param in self.spaces.keys():
            if param not in required_params and param != "action_type":
                if isinstance(self.spaces[param], spaces.Discrete):
                    action[param] = 0
                elif isinstance(self.spaces[param], spaces.Box):
                    action[param] = 0
                elif isinstance(self.spaces[param], spaces.MultiBinary):
                    action[param] = np.zeros(self.spaces[param].n, dtype=np.int8)

        return action

    def contains(self, x: Dict[str, Any]) -> bool:
        """Check if the action is valid."""
        if not super().contains(x):
            return False

        # Check if required parameters are present for the action type
        action_type = x["action_type"]
        if action_type not in self.action_parameters:
            return False

        required_params = self.action_parameters[action_type]
        for param in required_params:
            if param not in x:
                return False

        return True

    @classmethod
    def decode_action(cls, action: Dict[str, Any]) -> str:
        """
        Decode a gymnasium action into action_spec.json format.

        Args:
            action: numpy array containing the gymnasium action

        Returns:
            String like "place(x=3, y=7, type='ride', subtype='carousel', subclass='green', price=5)"
        """
        action_type = int(action[0])
        action_name = cls.action_names[action_type]

        action_params = action[1:]

        params = []

        # Build parameters string based on action type
        if action_type == 0:  # place
            entity_type = cls.type_mapping[int(action_params[cls.param_to_dim_mapping["type"]])]
            entity_subtype = cls.subtype_mapping[int(action_params[cls.param_to_dim_mapping["subtype"]])]
            entity_subclass = cls.subclass_mapping[int(action_params[cls.param_to_dim_mapping["subclass"]])]
            params.append(f"x={int(action_params[cls.param_to_dim_mapping["x"]])}")
            params.append(f"y={int(action_params[cls.param_to_dim_mapping["y"]])}")
            params.append(f"type='{entity_type}'")
            params.append(f"subtype='{cls.subtype_mapping[int(action_params[cls.param_to_dim_mapping["subtype"]])]}'")
            params.append(f"subclass='{cls.subclass_mapping[int(action_params[cls.param_to_dim_mapping["subclass"]])]}'")

            # Price only for rides and shops
            if entity_type in ['ride', 'shop']:
                # key = "max_item_price" if entity_type == 'shop' else "max_ticket_price"
                # price = MAP_CONFIG[entity_type + "s"][entity_subtype][entity_subclass][key]
                # params.append(f"price={price}")
                params.append(f"price={int(action_params[cls.param_to_dim_mapping["price"]])}")

            # Order quantity only for shops
            if entity_type == 'shop':
                order_quantity = int(action_params[cls.param_to_dim_mapping["order_quantity"]]) * 25
                params.append(f"order_quantity={order_quantity}")

        elif action_type == 1:  # move
            entity_type = cls.type_mapping[int(action_params[cls.param_to_dim_mapping["type"]])]
            params.append(f"type='{entity_type}'")
            params.append(f"subtype='{cls.subtype_mapping[int(action_params[cls.param_to_dim_mapping["subtype"]])]}'")
            params.append(f"subclass='{cls.subclass_mapping[int(action_params[cls.param_to_dim_mapping["subclass"]])]}'")
            params.append(f"x={int(action_params[cls.param_to_dim_mapping["x"]])}")
            params.append(f"y={int(action_params[cls.param_to_dim_mapping["y"]])}")
            params.append(f"new_x={int(action_params[cls.param_to_dim_mapping["new_x"]])}")
            params.append(f"new_y={int(action_params[cls.param_to_dim_mapping["new_y"]])}")

        elif action_type == 2:  # remove
            entity_type = cls.type_mapping[int(action_params[cls.param_to_dim_mapping["type"]])]
            params.append(f"type='{entity_type}'")
            params.append(f"subtype='{cls.subtype_mapping[int(action_params[cls.param_to_dim_mapping["subtype"]])]}'")
            params.append(f"subclass='{cls.subclass_mapping[int(action_params[cls.param_to_dim_mapping["subclass"]])]}'")
            params.append(f"x={int(action_params[cls.param_to_dim_mapping["x"]])}")
            params.append(f"y={int(action_params[cls.param_to_dim_mapping["y"]])}")

        elif action_type == 3:  # modify
            entity_type = cls.type_mapping[int(action_params[cls.param_to_dim_mapping["type"]])]
            entity_subtype = cls.subtype_mapping[int(action_params[cls.param_to_dim_mapping["subtype"]])]
            entity_subclass = cls.subclass_mapping[int(action_params[cls.param_to_dim_mapping["subclass"]])]
            params.append(f"type='{entity_type}'")
            params.append(f"subtype='{entity_subtype}'")
            params.append(f"subclass='{entity_subclass}'")
            params.append(f"x={int(action_params[cls.param_to_dim_mapping["x"]])}")
            params.append(f"y={int(action_params[cls.param_to_dim_mapping["y"]])}")

            # key = "max_item_price" if entity_type == 'shop' else "max_ticket_price"
            # price = MAP_CONFIG[entity_type + "s"][entity_subtype][entity_subclass][key]
            # params.append(f"price={price}")
            params.append(f"price={int(action_params[cls.param_to_dim_mapping["price"]])}")
            # Order quantity only for shops
            if cls.type_mapping[int(action_params[cls.param_to_dim_mapping["type"]])] == 'shop':
                order_quantity = int(action_params[cls.param_to_dim_mapping["order_quantity"]]) * 25
                params.append(f"order_quantity={order_quantity}")

        elif action_type == 4:  # set_research
            # Convert binary mask to list of topics
            topics = []
            for i, bit in enumerate(action_params[cls.param_to_dim_mapping["research_topics_carousel"]:cls.param_to_dim_mapping["research_topics_specialist"]]):
                if bit:
                    topics.append(cls.research_topics_mapping[i])
            topics_str = "[" + ", ".join(f"'{topic}'" for topic in topics) + "]"

            params.append(f"research_speed='{cls.research_speed_mapping[int(action_params[cls.param_to_dim_mapping["research_speed"]])]}'")
            params.append(f"research_topics={topics_str}")

        elif action_type == 5:  # survey_guests
            params.append(f"num_guests={int(action_params[cls.param_to_dim_mapping["num_guests"]])}")

        elif action_type in [6, 7, 8, 9]:  # add_path, remove_path, add_water, remove_water
            params.append(f"x={int(action_params[cls.param_to_dim_mapping["x"]])}")
            params.append(f"y={int(action_params[cls.param_to_dim_mapping["y"]])}")

        # action_type == 10 (wait) has no parameters

        return f"{action_name}({', '.join(params)})"

