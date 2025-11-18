import gymnasium as gym
from gymnasium import spaces
import numpy as np
import yaml
from typing import Dict, Any, List, Union
import importlib.resources
MODULE_PATH = importlib.resources.files(__package__)

class ParkActionSpace(gym.spaces.Dict):
    """
    Gymnasium compatible action space for the MAP environment.
    
    This action space supports all the actions defined in action_spec.py:
    - place_attraction, move_attraction, sell_attraction, change_price
    - hire_staff, fire_staff, move_staff
    - set_research, survey_guests
    - add_path, remove_path, add_water, remove_water
    - wait
    """
    
    def __init__(self):
        with open(MODULE_PATH/'../../shared/config.yaml', 'r') as infile:
            config = yaml.safe_load(infile)
        max_price = max(config['shops']['drink']['red']['max_item_price'], config['shops']['food']['red']['max_item_price'], config['shops']['specialty']['red']['max_item_price'], config['rides']['roller_coaster']['red']['max_ticket_price'])
        super().__init__({
            # Action type (discrete choice among all available actions)
            "action_type": spaces.Discrete(14),  # 14 unique actions
            
            # Position parameters (x, y coordinates)
            "x": spaces.Box(low=0, high=20, shape=(), dtype=np.int32),  # Assuming max grid size of 100x100
            "y": spaces.Box(low=0, high=20, shape=(), dtype=np.int32),
            "new_x": spaces.Box(low=0, high=20, shape=(), dtype=np.int32),
            "new_y": spaces.Box(low=0, high=20, shape=(), dtype=np.int32),
            
            # Type parameters (discrete choices)
            "type": spaces.Discrete(4),  # 0: ride, 1: shop, 2: janitor, 3: mechanic
            "subtype": spaces.Discrete(6),  # 0: carousel, 1: ferris_wheel, 2: roller_coaster, 3: drink, 4: food, 5: specialty
            "subclass": spaces.Discrete(4),  # 0: yellow, 1: blue, 2: green, 3: red, 
            # Numeric parameters
            "price": spaces.Box(low=0, high=max_price, shape=(), dtype=np.int32),  # Price range 0-1000
            "num_guests": spaces.Box(low=1, high=25, shape=(), dtype=np.int32),  # Survey 1-25 guests
            
            # Research parameters
            "research_speed": spaces.Discrete(4),  # 0: none, 1: slow, 2: medium, 3: fast
            "research_topics": spaces.MultiBinary(6),  # Binary mask for 6 research topics
        })
        
        # Define action mappings
        self.action_names = [
            "place_attraction",
            "move_attraction", 
            "sell_attraction",
            "change_price",
            "hire_staff",
            "fire_staff",
            "move_staff",
            "set_research",
            "survey_guests",
            "add_path",
            "remove_path",
            "add_water",
            "remove_water",
            "wait"
        ]
        
        # Define parameter mappings for discrete spaces
        self.type_mapping = ["ride", "shop", "janitor", "mechanic"]
        self.subtype_mapping = ["carousel", "ferris_wheel", "roller_coaster", "drink", "food", "specialty"]
        self.subclass_mapping = ["yellow", "blue", "green", "red", "custom"]
        self.research_speed_mapping = ["none", "slow", "medium", "fast"]
        self.research_topics_mapping = ["carousel", "ferris_wheel", "roller_coaster", "drink", "food", "specialty"]
        
        # Define which parameters are required for each action
        self.action_parameters = {
            0: ["x", "y", "type", "subtype", "subclass", "price"],  # place_attraction
            1: ["type", "x", "y", "new_x", "new_y"],  # move_attraction
            2: ["type", "x", "y"],  # sell_attraction
            3: ["type", "x", "y", "price"],  # change_price
            4: ["type", "x", "y"],  # hire_staff
            5: ["type", "x", "y"],  # fire_staff
            6: ["type", "x", "y", "new_x", "new_y"],  # move_staff
            7: ["research_speed", "research_topics"],  # set_research
            8: ["num_guests"],  # survey_guests
            9: ["x", "y"],  # add_path
            10: ["x", "y"],  # remove_path
            11: ["x", "y"],  # add_water
            12: ["x", "y"],  # remove_water
            13: []  # wait
        }
    
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
    
    def decode_action(self, action: Dict[str, Any]) -> str:
        """
        Decode a gymnasium action into a natural language string format.
        
        Args:
            action: Dictionary containing the gymnasium action
            
        Returns:
            String in natural language format like "place_attraction(x=3, y=7, type='ride', subtype='carousel', subclass='green', price=5)"
        """
        action_type = action["action_type"]
        action_name = self.action_names[action_type]
        
        # Build parameters string based on action type
        if action_type == 0:  # place_attraction
            params = [
                f"x={int(action['x'])}",
                f"y={int(action['y'])}",
                f"type='{self.type_mapping[action['type']]}'",
                f"subtype='{self.subtype_mapping[action['subtype']]}'",
                f"subclass='{self.subclass_mapping[action['subclass']]}'",
                f"price={int(action['price'])}"
            ]
        elif action_type == 1:  # move_attraction
            params = [
                f"type='{self.type_mapping[action['type']]}'",
                f"x={int(action['x'])}",
                f"y={int(action['y'])}",
                f"new_x={int(action['new_x'])}",
                f"new_y={int(action['new_y'])}"
            ]
        elif action_type == 2:  # sell_attraction
            params = [
                f"type='{self.type_mapping[action['type']]}'",
                f"x={int(action['x'])}",
                f"y={int(action['y'])}"
            ]
        elif action_type == 3:  # change_price
            params = [
                f"type='{self.type_mapping[action['type']]}'",
                f"x={int(action['x'])}",
                f"y={int(action['y'])}",
                f"price={int(action['price'])}"
            ]
        elif action_type in [4, 5]:  # hire_staff, fire_staff
            params = [
                f"type='{self.type_mapping[action['type']]}'",
                f"x={int(action['x'])}",
                f"y={int(action['y'])}"
            ]
        elif action_type == 6:  # move_staff
            params = [
                f"type='{self.type_mapping[action['type']]}'",
                f"x={int(action['x'])}",
                f"y={int(action['y'])}",
                f"new_x={int(action['new_x'])}",
                f"new_y={int(action['new_y'])}"
            ]
        elif action_type == 7:  # set_research
            # Convert binary mask to list of topics
            topics = []
            for i, bit in enumerate(action["research_topics"]):
                if bit:
                    topics.append(self.research_topics_mapping[i])
            topics_str = "[" + ", ".join(f"'{topic}'" for topic in topics) + "]"
            
            params = [
                f"research_speed='{self.research_speed_mapping[action['research_speed']]}'",
                f"research_topics={topics_str}"
            ]
        elif action_type == 8:  # survey_guests
            params = [f"num_guests={int(action['num_guests'])}"]
        elif action_type in [9, 10, 11, 12]:  # add_path, remove_path, add_water, remove_water
            params = [
                f"x={int(action['x'])}",
                f"y={int(action['y'])}"
            ]
        elif action_type == 13:  # wait
            params = []
        
        return f"{action_name}({', '.join(params)})"
    
    def encode_action(self, action_string: str) -> Dict[str, Any]:
        """
        Encode a natural language action string into gymnasium format.
        
        Args:
            action_string: String like "place_attraction(x=3, y=7, type='ride', subtype='carousel', subclass='green', price=5)"
            
        Returns:
            Dictionary in gymnasium action space format
        """
        # Parse the action string
        # Extract action name and parameters
        action_name = action_string[:action_string.find("(")]
        params_str = action_string[action_string.find("(")+1:action_string.rfind(")")]
        
        # Parse parameters
        parameters = {}
        if params_str.strip():
            for param in params_str.split(","):
                param = param.strip()
                if "=" in param:
                    key, value = param.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Handle different value types
                    if value.startswith("'") and value.endswith("'"):
                        # String value
                        parameters[key] = value[1:-1]
                    elif value.startswith("[") and value.endswith("]"):
                        # List value (for research_topics)
                        if value == "[]":
                            parameters[key] = []
                        else:
                            # Parse list of strings
                            list_content = value[1:-1]
                            if list_content:
                                topics = [topic.strip().strip("'") for topic in list_content.split(",")]
                                parameters[key] = topics
                            else:
                                parameters[key] = []
                    elif value.lower() in ["true", "false"]:
                        # Boolean value
                        parameters[key] = value.lower() == "true"
                    else:
                        # Numeric value
                        try:
                            parameters[key] = int(value)
                        except ValueError:
                            try:
                                parameters[key] = float(value)
                            except ValueError:
                                parameters[key] = value
        
        # Find action type index
        try:
            action_type = self.action_names.index(action_name)
        except ValueError:
            raise ValueError(f"Unknown action: {action_name}")
        
        # Initialize action with defaults
        action = {
            "action_type": action_type,
            "x": 0, "y": 0, "new_x": 0, "new_y": 0,
            "type": 0, "subtype": 0, "subclass": 0,
            "price": 0, "num_guests": 1,
            "research_speed": 0,
            "research_topics": np.zeros(6, dtype=np.int8)
        }
        
        # Encode parameters based on action type
        if action_type == 0:  # place_attraction
            action.update({
                "x": parameters.get("x", 0),
                "y": parameters.get("y", 0),
                "type": self.type_mapping.index(parameters.get("type", "ride")),
                "subtype": self.subtype_mapping.index(parameters.get("subtype", "carousel")),
                "subclass": self.subclass_mapping.index(parameters.get("subclass", "yellow")),
                "price": parameters.get("price", 0)
            })
        elif action_type == 1:  # move_attraction
            action.update({
                "type": self.type_mapping.index(parameters.get("type", "ride")),
                "x": parameters.get("x", 0),
                "y": parameters.get("y", 0),
                "new_x": parameters.get("new_x", 0),
                "new_y": parameters.get("new_y", 0)
            })
        elif action_type == 2:  # sell_attraction
            action.update({
                "type": self.type_mapping.index(parameters.get("type", "ride")),
                "x": parameters.get("x", 0),
                "y": parameters.get("y", 0)
            })
        elif action_type == 3:  # change_price
            action.update({
                "type": self.type_mapping.index(parameters.get("type", "ride")),
                "x": parameters.get("x", 0),
                "y": parameters.get("y", 0),
                "price": parameters.get("price", 0)
            })
        elif action_type in [4, 5]:  # hire_staff, fire_staff
            action.update({
                "type": self.type_mapping.index(parameters.get("type", "janitor")),
                "x": parameters.get("x", 0),
                "y": parameters.get("y", 0)
            })
        elif action_type == 6:  # move_staff
            action.update({
                "type": self.type_mapping.index(parameters.get("type", "janitor")),
                "x": parameters.get("x", 0),
                "y": parameters.get("y", 0),
                "new_x": parameters.get("new_x", 0),
                "new_y": parameters.get("new_y", 0)
            })
        elif action_type == 7:  # set_research
            action.update({
                "research_speed": self.research_speed_mapping.index(parameters.get("research_speed", "none")),
                "research_topics": self._encode_research_topics(parameters.get("research_topics", []))
            })
        elif action_type == 8:  # survey_guests
            action.update({
                "num_guests": parameters.get("num_guests", 1)
            })
        elif action_type in [9, 10, 11, 12]:  # add_path, remove_path, add_water, remove_water
            action.update({
                "x": parameters.get("x", 0),
                "y": parameters.get("y", 0)
            })
        # action_type == 13 (wait) doesn't need additional parameters
        
        return action
    
    def _encode_research_topics(self, topics: List[str]) -> np.ndarray:
        """Encode research topics list into binary mask."""
        mask = np.zeros(6, dtype=np.int8)
        for topic in topics:
            if topic in self.research_topics_mapping:
                idx = self.research_topics_mapping.index(topic)
                mask[idx] = 1
        return mask