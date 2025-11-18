"""Python wrapper for the business simulator game Mini Amusement Parks
"""

from map_py.helpers import post_endpoint, get_endpoint, put_endpoint, delete_endpoint, delete_park_endpoint, get_action_name_and_args, ParkResponse
from map_py.observations_and_actions.shared_constants import ACTION_PARAMS, ACTION_PARAM_TYPES, SANDBOX_ACTION_NAMES, SANDBOX_ACTION_PARAMS, SANDBOX_ACTION_PARAM_TYPES
from map_py.observations_and_actions.pydantic_obs import format_pydantic_observation, FullParkObs, ParkDataGranularity, ParkObservabilityMode
from map_py.observations_and_actions.gym_obs import format_gym_observation, ParkObservationSpace, obs_pydantic_to_array, obs_array_to_pydantic
from map_py.observations_and_actions.gym_action import ParkActionSpace
from map_py.shared_constants import LAYOUTS_DIR
from map_py.gui.visualizer import Visualizer, format_full_state, GameState
import requests
from typing import List, Optional, Union, Tuple, Any
import gymnasium as gym
import numpy as np
from pathlib import Path
import os
import csv
import json

class MiniAmusementPark(gym.Env):
    def __init__(self,
                 host: str,
                 port: str,
                 park_id: Optional[int] = None,
                 observation_type: str = "pydantic", # one of "pydantic", "gym", "raw"
                 exp_name: str = "default_exp",
                 render_park: bool = False,
                 visualizer: Optional[Visualizer] = None,
                 data_level: ParkDataGranularity = ParkDataGranularity.HIGH,
                 observability_mode: ParkObservabilityMode = ParkObservabilityMode.NORMAL,
                 return_raw_in_info: bool = False,
                 return_detailed_guest_info: bool = False,
                 difficulty: Optional[str] = None,
                 layout: Optional[str] = None,
                 starting_money: Optional[int] = None,
                 horizon: Optional[int] = None,
                 noop_on_invalid_action: bool = True,
                 seed: Optional[int] = None):
        """Initialize a MiniAmusementPark environment instance.

        Args:
            host: The host address for the park's API server.
            port: The port number for the park's API server.
            park_id: Optional park ID to use. If None, a new park ID will be requested from the server.
            observation_type: Type of observation to return. Must be one of "pydantic", "gym", "raw", or "test".
                Defaults to "pydantic".
            exp_name: Experiment name used for organizing rendered images. Defaults to "default_exp".
            render_park: Whether to render the park state. If True, a Visualizer will be created if not provided.
            visualizer: Optional Visualizer instance for rendering. If None and render_park is True, one will be created.
            data_level: Granularity level for park data observations (HIGH or LOW). Defaults to HIGH.
            observability_mode: Observability mode for the park (NORMAL or ORACLE). Defaults to NORMAL.
            return_raw_in_info: Whether to include raw state in the info dictionary returned by step/reset.
            return_detailed_guest_info: Whether to include detailed guest information in observations.
            difficulty: Optional difficulty setting for the park (e.g., "easy", "medium").
            layout: Optional layout name to use for the park. Must correspond to a YAML file in the layouts directory.
            starting_money: Optional starting money amount for the park.
            horizon: Optional maximum number of steps/episodes for the park.
            noop_on_invalid_action: If True, the park will proceed even if an invalid action is taken (no-op behavior).
            seed: Optional random seed for reproducibility.

        Raises:
            ValueError: If the park settings cannot be initialized (e.g., invalid layout file).
        """
        self.host = host
        self.port = port
        self.prev_money = None
        self.settings = {}
        self.game_size = 20
        self.session = requests.Session()
        self.render_park = render_park
        self.visualizer = visualizer
        self.exp_name = exp_name
        if render_park:
            self.visualizer = self.visualizer or Visualizer()
            self.image_dir = Path(__file__).parent.parent / "game_images" / self.exp_name
            os.makedirs(self.image_dir, exist_ok=True)

        self.park_id = get_endpoint(host, port, "park/get_new_park_id", {}, self.session).data['parkId'] if park_id is None else park_id
        self.seed = seed
        self.set_seed(seed)

        self.observation_type = observation_type

        self.action_space = ParkActionSpace()
        self.observation_space = ParkObservationSpace()

        self.data_level = data_level
        self.observability_mode = observability_mode
        self.return_raw_in_info = return_raw_in_info
        # State to reset to after a reset. Used for random resets since we only randomize on the first reset unless hard_reset is True.
        self.reset_state = None

        self.return_detailed_guest_info = return_detailed_guest_info
        self.noop_on_invalid_action = noop_on_invalid_action
        # If true, make all pydantic observations None. You need return_raw_in_info to make this useful.
        if self.observation_type == "raw":
            self.return_raw_in_info = False

        self.difficulty = None
        self.layout = None
        self.starting_money = None
        self.horizon = None
        self.guest_preferences = None

        # Set initial settings.
        response = self.update_settings(layout, difficulty, starting_money, horizon)
        if response.status_code != 200:
            raise ValueError(f"Failed to set the park: {response.message}")

    def __enter__(self):
        """Enter the context manager.

        Returns:
            self: The MiniAmusementPark instance
        """
        return self

    def __exit__(self, *args: Any) -> bool:
        """Exit the context manager and clean up resources.

        Args:
            *args: Exception information if an exception was raised in the with block.

        Returns:
            False to propagate any exceptions that occurred in the with block.
        """
        try:
            self.delete_park()
        except Exception as e:
            print(f"Warning: Failed to clear park during cleanup: {e}")

        self.shutdown()

        # Return False to propagate any exceptions that occurred in the with block
        return False

    def set_park_id(self, park_id: int) -> None:
        """Set the park ID for this environment instance.

        Args:
            park_id: The park ID to use.
        """
        # TODO close / clear previous park id
        self.park_id = park_id

    def update_settings(self, layout: Optional[str] = None, difficulty: Optional[str] = None, 
                        starting_money: Optional[int] = None, horizon: Optional[int] = None) -> ParkResponse:
        """Update the settings of the environment.

        Args:
            layout: Optional layout name to use. Must correspond to a YAML file in the layouts directory.
            difficulty: Optional difficulty setting (e.g., "easy", "medium"). Defaults to "easy" if not set.
            starting_money: Optional starting money amount for the park.
            horizon: Optional maximum number of steps/episodes for the park.

        Returns:
            ParkResponse with status_code 200 if successful, or 400 if layout file doesn't exist.
        """
        
        # Check if layout file exists when layout is provided
        if layout is not None:
            layout_yaml = LAYOUTS_DIR / f"{layout}.yaml"  
            if not layout_yaml.exists():
                return ParkResponse(status_code=400, message=f"Layout file {layout_yaml} does not exist", data={}, error=True)
        
        self.layout = layout or self.layout
        self.difficulty = difficulty or self.difficulty or "easy"
        self.starting_money = starting_money or self.starting_money
        self.horizon = horizon or self.horizon
        
        return ParkResponse(status_code=200, message=f"Settings updated", data={}, error=False)

    def shutdown(self) -> None:
        """Close the HTTP session connection.

        Safely closes the requests session, ignoring any errors that may occur.
        """
        try:
            self.session.close()
        except:
            pass

    def set(self, raw_state: dict) -> Tuple[Union[FullParkObs, dict], dict]:
        """Set the environment to a particular state.

        Args:
            raw_state: The raw state dictionary to set the environment to. Must be a complete raw state dictionary.

        Returns:
            A tuple containing:
                - The observation (formatted according to observation_type) or raw state if observation_type is "raw"
                - An info dictionary, which may contain error messages if the set operation failed

        Raises:
            RuntimeError: If there is an error setting the park state.
        """
        raw_state = raw_state.copy()  # Shallow copy

        params = {'parkId': self.park_id, 'state': raw_state}
        
        result = post_endpoint(self.host, self.port, "park/set", params, session=self.session)
        info = {}
        if result.error:
            info['error'] = {
                'message': result.message,
                'type': 'set_error'
            }
            raise RuntimeError(f"Error setting park: {result.message}")

        self.prev_money = raw_state['state']['money']

        if self.observation_type != "raw":
            if self.observation_type == "pydantic":
                obs = format_pydantic_observation(raw_state, self.observability_mode, self.data_level, as_dict=False)
            elif self.observation_type == "gym":
                obs = format_gym_observation(raw_state)
            else:
                raise ValueError(f"Invalid observation type: {self.observation_type}")
        
            if self.return_raw_in_info:
                info['raw_state'] = raw_state
        else:
            obs = raw_state

        return obs, info

    def get_raw_state(self) -> dict:
        """
        Observe the environment specified by park_id.
        Returns the raw state of the environment.
        NOTE: This differs from the observe method that only returns the observation.
        """
        params = {'parkId': self.park_id, 'fullState': True, 'includeGuests': self.return_detailed_guest_info}
        result = get_endpoint(self.host, self.port, "park/", params, self.session)
        if result.error:
            raise RuntimeError(f'Server encountered the error while observing: {result.message}. \nFull response: {result}')
        
        return result.data

    def get_observation_and_raw_state(self) -> Tuple[Union[FullParkObs, dict], dict]:
        """Observe the environment specified by self.park_id (i.e., the current park)

        Returns both the formatted observation and the raw state of the environment.
        The observation format depends on the observation_type setting.

        Returns:
            A tuple containing:
                - The observation (formatted according to observation_type: FullParkObs for "pydantic",
                  dict for "gym" or "raw")
                - The raw state dictionary

        Raises:
            RuntimeError: If the server encounters an error while observing.
        """
        params = {'parkId': self.park_id, 'fullState': True, 'includeGuests': self.return_detailed_guest_info}
        result = get_endpoint(self.host, self.port, "park/", params, self.session)
        if result.error:
            raise RuntimeError(f'Server encountered the error while observing: {result.message}. \nFull response: {result}')

        if self.observation_type == "test":
            pyd_obs = format_pydantic_observation(result.data, self.observability_mode, self.data_level, as_dict=False)
            gym_obs = format_gym_observation(result.data)
            gym_obs2 = obs_pydantic_to_array(pyd_obs)
            pyd_obs2 = obs_array_to_pydantic(gym_obs, self.data_level, self.observability_mode, as_dict=False)
            
            # Simple comparison of pydantic model attributes
            if pyd_obs != pyd_obs2:
                print("Pydantic Observations differ:")
                for attr_name in pyd_obs.__dict__.keys():
                    if getattr(pyd_obs, attr_name) != getattr(pyd_obs2, attr_name):
                        print(f"  {attr_name}:")
                        print(f"    Original: {getattr(pyd_obs, attr_name)}")
                        print(f"    Converted: {getattr(pyd_obs2, attr_name)}")
                raise ValueError("Pydantic Observations differ")

            # Compare gym observations by comparing each key's arrays
            gym_obs_diff = False
            for key in gym_obs.keys():
                if not np.array_equal(gym_obs[key], gym_obs2[key]):
                    gym_obs_diff = True
                    break
            
            if gym_obs_diff:
                print("Gym Observations differ:")
                for attr_name in gym_obs.keys():
                    if not np.array_equal(gym_obs[attr_name], gym_obs2[attr_name]):
                        print(f"  {attr_name}:")
                        print(f"    Original: {gym_obs[attr_name]}")
                        print(f"    Converted: {gym_obs2[attr_name]}")
                raise ValueError("Gym Observations differ")
            
            obs = pyd_obs
        elif self.observation_type == "pydantic":
            obs = format_pydantic_observation(result.data, self.observability_mode, self.data_level, as_dict=False)
        elif self.observation_type == "gym":
            obs = format_gym_observation(result.data)
        elif self.observation_type == "raw":
            obs = result.data
        else:
            raise ValueError(f"Invalid observation type: {self.observation_type}")

        return obs, result.data

    def observe(self) -> Union[FullParkObs, dict]:
        """Observe the environment specified by park_id.

        Returns only the observation, not the raw state. Use get_observation_and_raw_state()
        if you need both the observation and raw state.

        Returns:
            The observation of the environment. Format depends on observation_type:
                - FullParkObs for "pydantic"
                - dict for "gym" or "raw"
        """
        return self.get_observation_and_raw_state()[0]

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None) -> Tuple[Union[FullParkObs, dict], dict]:
        """Reset the environment to an initial state or creates a new environment.

        Args:
            seed: the seed to be used after the reset, if provided.
            options: if the 'hard_reset' is provided and set to True, then this forces a full reset 
                     even if a reset_state is cached.
                     Otherwise, if layout is not specified, the reset uses the cached reset_state for faster resets.

        Returns:
            A tuple containing:
                - The park observation (formatted according to observation_type)
                - An info dictionary. If an error occurred, 'error' will be a key in info.
                  See https://gymnasium.farama.org/api/env/#gymnasium.Env.reset
        """
        info = {}            
        # NOTE: If this MAP did not create this environment, then the 
        #       reset will not reset to the correct state.

        hard_reset = False 
        if options is not None and 'hard_reset' in options:
            hard_reset = options['hard_reset']
            if not isinstance(hard_reset, bool):
                raise ValueError('hard_reset provided in options must be a bool')

        # If this has been randomly reset before, then restore stored start state
        if self.layout is None and self.reset_state is not None and not hard_reset:
            _, set_info = self.set(self.reset_state)
            if 'error' in set_info:
                info['error'] = {
                    'message': set_info.message,
                    'type': 'reset_error'
                }
            
        else:
            # Otherwise, proceed with java-side reset
            reset_args = {'parkId': self.park_id, 
                          'layout': self.layout if self.layout is not None else "",
                          'difficulty': self.difficulty,
                          'starting_money': self.starting_money,
                          'horizon': self.horizon}
            
            result = post_endpoint(self.host, self.port, "park/reset", reset_args, self.session)
            if result.error:
                info['error'] = {
                    'message': result.message,
                    'type': 'reset_error'
                }
                print(f"Error resetting park: {result.message}")

        if seed is not None:
            self.set_seed(seed)

        obs, raw_state = self.get_observation_and_raw_state()

        if self.layout is None:
            self.reset_state = raw_state

        self.prev_money = raw_state['state']['money']
        
        if self.return_raw_in_info:
            info['raw_state'] = raw_state

        if self.render_park:
            self.render_frame(raw_state, obs, action=None, info=info)

        return obs, info
        
    def step(self, action: Union[str, ParkActionSpace]) -> Tuple[Union[FullParkObs, dict], float, bool, bool, dict]:
        """Perform a step action in the environment.

        Args:
            action: The action to be performed.

        Returns:
            A 5-tuple containing:
                - Environment observation (formatted according to observation_type)
                - reward: The reward for this step
                - terminated: Whether the episode has terminated
                - truncated: Whether the episode was truncated
                - info: Info dictionary. If an error occurred, 'error' will be a key in info.
                  See https://gymnasium.farama.org/api/env/#gymnasium.Env.step
        """

        if isinstance(action, ParkActionSpace):
            action = self.action_space.decode_action(action)
        
        info = {}
        # Apply action
        action_result = None  # Must be defined to check if it's a tuple later on
        if action is not None:
            action_result = self._act(action)
        
        reward = 0


        # Check if action was invalid
        if action_result.error:
            # print("ERROR: ", action_result.message)
            info['error'] = {
                'message': action_result.message,
                'type': 'invalid_action'
            }

        terminated, truncated = False, False
        if not action_result.error or self.noop_on_invalid_action:
            # Run park for a day
            data = {'parkId': self.park_id}

            proceed_result = post_endpoint(self.host, self.port, "park/proceed", data, self.session)

            # Check if park encountered an error
            if proceed_result.error:
                info['error'] = {
                    'message': proceed_result.message,
                    'type': 'proceed_error'
                }
            else:
                # Action OK & no park server error, advance number of steps
                reward = proceed_result.data['reward']
                terminated = proceed_result.data['terminated']
                truncated = proceed_result.data['truncated']

        # Get observation and raw state
        obs, raw_state = self.get_observation_and_raw_state()

        if self.return_raw_in_info:
            info['raw_state'] = raw_state

        if self.render_park:
            self.render_frame(raw_state, obs, action=action, info=info)

        return obs, reward, terminated, truncated, info

    def set_seed(self, seed: Optional[int]) -> None:
        """Set the random seed for the park environment.

        Args:
            seed: The random seed value. If None, uses the seed from initialization.
        """
        seed = seed or self.seed
        if seed is not None:
            result = post_endpoint(self.host, self.port, "park/seed", {"parkId": self.park_id, "seed": seed}, self.session)
            if result.error:
                print("ERROR: ", result.message)

    @staticmethod
    def parse_action(action: str, park_id: int) -> ParkResponse:
        """Parse and validate an action string.

        Args:
            action: The action string to parse (e.g., "place_ride(x=1, y=2, type='ride', ...)").
            park_id: The park ID to associate with this action.

        Returns:
            ParkResponse with status_code 200 and data=(action_name, action_args) if valid,
            or status_code 400 with error message if invalid.
        """
        # Parse action
        try:
            action_name, action_args = get_action_name_and_args(action)
        except Exception as e:
            return ParkResponse(status_code=400, message=f"Error parsing action: {e}", data={}, error=True)
        action_args['parkId'] = park_id

        # Validate action type
        if action_name not in ACTION_PARAMS:
            return ParkResponse(status_code=400, message=f"Invalid action type: {action_name} must be in {list(ACTION_PARAMS.keys())}", data={}, error=True)

        # Place has an optional price & order_quantity argument, make sure its absence does not cause an error for staff or rides
        if action_name == "place" and "type" in action_args and action_args["type"] == "staff":
            action_args["price"] = action_args.get("price", 1)
            action_args["order_quantity"] = action_args.get("order_quantity", -1)
        if action_name in ["place", "modify"] and "type" in action_args and action_args["type"] == "ride":
            action_args["order_quantity"] = action_args.get("order_quantity", -1)

        # Validate presence of arguments
        action_params = set(action_args.keys())
        if not action_params.issuperset(ACTION_PARAMS[action_name]):
            return ParkResponse(status_code=400, message=f"Invalid action: {action} is missing the arguments {ACTION_PARAMS[action_name] - action_params}", data={}, error=True)
        if not action_params.issubset(ACTION_PARAMS[action_name]):
            return ParkResponse(status_code=400, message=f"Invalid action: {action} has excess arguments {action_params - ACTION_PARAMS[action_name]}", data={}, error=True)

        # Validate argument types
        for param_name in action_params:
            if param_name == "parkId":
                # parkId is added later
                continue
            expected_type = ACTION_PARAM_TYPES[param_name]
            param_value = action_args[param_name]
            
            # Special handling for list[str] type
            if expected_type == list[str]:
                if not isinstance(param_value, list):
                    return ParkResponse(status_code=400, message=f"Invalid action: {action} has argument {param_name} of type {type(param_value)} but expected type list", data={}, error=True)
                if not all(isinstance(item, str) for item in param_value):
                    return ParkResponse(status_code=400, message=f"Invalid action: {action} has argument {param_name} with non-string items in list", data={}, error=True)
            else:
                if not isinstance(param_value, expected_type):
                    return ParkResponse(status_code=400, message=f"Invalid action: {action} has argument {param_name} of type {type(param_value)} but expected type {expected_type}", data={}, error=True)

        return ParkResponse(status_code=200, message=f"Action {action} is valid", data=(action_name, action_args), error=False)

    def _act(self, action: str) -> ParkResponse:
        """Perform an action in the environment.

        Actions must be of the form action_name(kwargs) and must have valid Python syntax.
        For example, to place a ride: "place_ride(x=1, y=2, type='ride', subtype='roller_coaster', ...)".

        Args:
            action: The action to be performed, represented as a string.

        Returns:
            ParkResponse containing the result of the action. If successful, status_code is 200.
            If the action is invalid or fails, status_code is 400 and error is True.
        """
        action_result = self.parse_action(action, self.park_id)
        if action_result.error:
            print(f"Error parsing action: {action_result.message}")
            return action_result
        action_name, action_args = action_result.data
        action_name_keywords = action_name.split("_")

        # Apply action
        # place ride, shop, or staff
        if action_name_keywords[0] == "place":
            object_to_place = action_args['type']
            if object_to_place in ['ride', 'shop', 'staff']:
                return post_endpoint(self.host, self.port, object_to_place, action_args, self.session)
            else:
                return ParkResponse(status_code=400, message=f"Object to place must be ride, shop, or staff, got {object_to_place}", data={}, error=True)
            
        # move or modify ride, shop, or staff
        if action_name_keywords[0] in ["move", "modify"]:
            object_to_modify = action_args['type']
            if object_to_modify in ['ride', 'shop', 'staff']:
                return put_endpoint(self.host, self.port, object_to_modify, action_args, self.session)
            else:
                return ParkResponse(status_code=400, message=f"Object to move must be ride, shop, or staff, got {object_to_modify}", data={}, error=True)
        

        # remove ride, shop, or staff
        if action_name_keywords[0] in ['remove'] and len(action_name_keywords) == 1:
            object_to_remove = action_args['type']
            if object_to_remove in ['ride', 'shop', 'staff']:
                return delete_endpoint(self.host, self.port, object_to_remove, action_args, self.session)
            else:
                return ParkResponse(status_code=400, message=f"Object to remove must be ride, shop, or staff, got {object_to_remove}", data={}, error=True)
            
        # get guest information
        if action_name == 'survey_guests':
            return post_endpoint(self.host, self.port, "park/survey_guests", action_args, self.session)
        
        # set research
        if action_name == 'set_research':
            return post_endpoint(self.host, self.port, "park/research", action_args, self.session)
        
        # add path tile
        if action_name == 'add_path':
            return post_endpoint(self.host, self.port, "park/path", action_args, self.session)
        
        # remove path tile
        if action_name == 'remove_path':
            return delete_endpoint(self.host, self.port, "park/path", action_args, self.session)
        
        # add water tile
        if action_name == 'add_water':
            return post_endpoint(self.host, self.port, "park/water", action_args, self.session)
        
        # remove water tile
        if action_name == 'remove_water':
            return delete_endpoint(self.host, self.port, "park/water", action_args, self.session)

        # wait
        if action_name == 'wait':
            return post_endpoint(self.host, self.port, "park/noop", action_args, self.session)
        
        return ParkResponse(status_code=400, message=f"Invalid action: {action}", data={}, error=True)

    @staticmethod
    def is_sandbox_action(action: str) -> bool:
        try:
            action_name, _ = get_action_name_and_args(action)
            return action_name in SANDBOX_ACTION_NAMES
        except:
            return False

    @staticmethod
    def parse_sandbox_action(action: str, park_id: int) -> ParkResponse:
        """Parse and validate a sandbox action string.

        Args:
            action: The sandbox action string to parse.
            park_id: The park ID to associate with this action.

        Returns:
            ParkResponse with status_code 200 and data=(action_name, action_args) if valid,
            or status_code 400 with error message if invalid.
        """
        try:
            action_name, action_args = get_action_name_and_args(action)
        except Exception as e:
            return ParkResponse(status_code=400, message=f"Error parsing action: {e}", data={}, error=True)
        
        action_args['parkId'] = park_id
        # Validate action type
        if action_name not in SANDBOX_ACTION_NAMES:
            return ParkResponse(status_code=400, message=f"Invalid sandbox action type: {action_name} must be in {list(SANDBOX_ACTION_NAMES)}", data={}, error=True)

        # Add in optional arguments in case they are not provided
        if action_name == "change_settings":
            action_args["difficulty"] = action_args.get("difficulty", None)
            action_args["layout"] = action_args.get("layout", None)

        # Validate presence of arguments
        action_params = set(action_args.keys())
        if not action_params.issuperset(SANDBOX_ACTION_PARAMS[action_name]):
            return ParkResponse(status_code=400, message=f"Invalid sandbox action: {action} is missing the arguments {SANDBOX_ACTION_PARAMS[action_name] - action_params}", data={}, error=True)
        if not action_params.issubset(SANDBOX_ACTION_PARAMS[action_name]):
            return ParkResponse(status_code=400, message=f"Invalid sandbox action: {action} has excess arguments {action_params - SANDBOX_ACTION_PARAMS[action_name]}", data={}, error=True)

        return ParkResponse(status_code=200, message=f"Sandbox action {action} is valid", data=(action_name, action_args), error=False)

    def sandbox_action(self, action: str) -> Tuple[Union[FullParkObs, dict], dict]:
        """Perform a sandbox action in the environment.

        Sandbox actions are special actions that allow modifying the environment state
        or settings outside of normal gameplay (e.g., undo_day, max_money, reset, change_settings).

        Args:
            action: The sandbox action string to perform.

        Returns:
            A tuple containing:
                - The observation after the action (formatted according to observation_type)
                - An info dictionary. If an error occurred, 'error' will be a key in info.
        """
        info = {}
        action_result = self.parse_sandbox_action(action, self.park_id)
        if action_result.error:
            info['error'] = {
                'message': action_result.message,
                'type': 'invalid_sandbox_action'
            }
            print("Error parsing sandbox action: ", action_result.message)
            action_name, action_args = None, None
        else:
            action_name, action_args = action_result.data
        
        if action_name in ["undo_day", "max_money", "max_research", "set_sandbox_mode"]:
            data = {"parkId": self.park_id}
            if action_name == "set_sandbox_mode":
                data["sandbox_steps"] = action_args['sandbox_steps']
            result = post_endpoint(self.host, self.port, f"park/{action_name}", data, self.session)
            if result.error:
                info['error'] = {
                    'message': result.message,
                    'type': f'{action_name}_error'
                }
            obs, raw_state = self.get_observation_and_raw_state()
            if self.return_raw_in_info:
                info['raw_state'] = raw_state
            return obs, info
        elif action_name == "reset":
            return self.reset(options={'hard_reset':True})
        elif action_name == "change_settings":
            result = self.update_settings(layout=action_args["layout"], difficulty=action_args["difficulty"])
            if result.error:
                info['error'] = {
                    'message': result.message,
                    'type': 'change_settings_error'
                }
                obs, raw_state = self.get_observation_and_raw_state()
                if self.return_raw_in_info:
                    info['raw_state'] = raw_state
                return obs, info
            return self.reset(options={'hard_reset':True})
        else:
            if 'error' not in info:
                info['error'] = {
                    'message': f"Invalid sandbox action: {action_name}",
                    'type': 'invalid_sandbox_action'
                }
            obs, raw_state = self.get_observation_and_raw_state()
            if self.return_raw_in_info:
                info['raw_state'] = raw_state
            return obs, info
        

    def render_frame(self, raw_state: dict, obs: Optional[FullParkObs] = None, action: Optional[str] = None, 
               info: Optional[dict] = None, filepath: Optional[str] = None) -> Union[Path, str]:
        """Render the environment state to an image file.

        Args:
            raw_state: The raw state dictionary of the park.
            obs: Optional observation object. If None and observation_type is "pydantic", will be formatted from raw_state.
            action: Optional action string that was taken, used for highlighting in the visualization.
            info: Optional info dictionary, used for displaying error messages.
            filepath: Optional path to save the rendered image. If None, saves to image_dir/step_{step}.png.

        Returns:
            The path to the saved image file.

        Note:
            Requires render_park=True or a visualizer to be set during initialization.
        """
        if self.observation_type == "pydantic" and obs is not None:
            state = obs.model_dump()
        else:
            state = format_pydantic_observation(raw_state, as_dict=True)

        state["staff"]["staff_list"] = raw_state["staff"]

        formatted_state = format_full_state(state)
        self.visualizer.game_mode = GameState.WAITING_FOR_INPUT

        if action is not None and "x=" in action:
            parse_succ = True
            try:
                x = int(action.split("x=")[1].split(",")[0].strip(" )"))
                y = int(action.split("y=")[1].split(",")[0].strip(" )"))
            except:
                x, y = 0, 0
                parse_succ = False

            if not parse_succ:
                new_selected_tile = {"x": x, "y": y}
                self.visualizer.selected_tile_type = None
                self.visualizer.top_panel_selection_type = None
            else:
                if (x, y) in formatted_state["paths"]:
                    new_selected_tile = formatted_state["paths"][(x, y)]
                    self.visualizer.selected_tile_type = "path"
                    self.visualizer.top_panel_selection_type = None
                elif (x, y) in formatted_state["waters"]:
                    new_selected_tile = formatted_state["waters"][(x, y)]
                    self.visualizer.selected_tile_type = "water"
                    self.visualizer.top_panel_selection_type = None
                elif (x, y) in formatted_state["shops"]:
                    new_selected_tile = formatted_state["shops"][(x, y)]
                    self.visualizer.selected_tile_type = "shop"
                elif (x, y) in formatted_state["rides"]:
                    new_selected_tile = formatted_state["rides"][(x, y)]
                    self.visualizer.selected_tile_type = "ride"
                elif (x, y) == formatted_state["entrance"]:
                    new_selected_tile = {"x": x, "y": y}
                    self.visualizer.selected_tile_type = "entrance"
                elif (x, y) == formatted_state["exit"]:
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

        elif action is not None:
            for bottom_panel_type in ["ride", "shop", "staff", "research", "survey_guests"]:
                if bottom_panel_type in action:
                    self.visualizer.bottom_panel_action_type = bottom_panel_type
                    break


        self.visualizer.render_background()
        self.visualizer.draw_playback_panel(16)
        self.visualizer.draw_game_ticks(0)
        self.visualizer.draw_game_grid(formatted_state)
        self.visualizer.draw_people(formatted_state)
        self.visualizer.draw_tile_state(formatted_state)
        self.visualizer.draw_top_panel(formatted_state)
        self.visualizer.draw_bottom_panel(formatted_state)
        self.visualizer.draw_state_info(formatted_state)
        self.visualizer.draw_aggregate_info(formatted_state)
        self.visualizer.render_grid()


        y_offset = 0
        if info and "error" in info:
            self.visualizer.draw_error_message(info['error']['message'], y_offset)
            y_offset += 75

        if action is not None:
            self.visualizer.show_new_notification = True
            self.visualizer.draw_new_notification(f"Action: {action.replace(' ', '')}" if action else None, y_offset)

        filepath = filepath or self.image_dir / f"step_{formatted_state['step']}.png"
        self.visualizer.save_image(filepath)
        return filepath

    def save_trajectory(self, username: str = "anon", 
                       save_local: bool = False, save_to_cloud: bool = False) -> Union[dict, ParkResponse]:
        """Save the current trajectory to the leaderboard.

        Args:
            username: The username to associate with this trajectory.
            save_local: Whether to save the trajectory locally.
            save_to_cloud: Whether to save the trajectory to the cloud.

        Returns:
            The response data dictionary if successful, or ParkResponse if an error occurred.
        """
        data = {
            "parkId": self.park_id,
            "saveLocal": save_local,
            "saveToCloud": save_to_cloud,
            "name": username or "anon",
        }
        result = post_endpoint(self.host, self.port, "leaderboard/", data, self.session)
        if result.error:
            print("ERROR: ", result.message)
            return result
        else:
            print("Successfully saved trajectory to leaderboard: ", result.message)
        return result.data

    def delete_park(self) -> dict:
        """Clear all data related to the current parkId.

        Deletes the park instance from the backend server.

        Returns:
            dict: Response data from the server
        """
        result = delete_park_endpoint(
            self.host,
            self.port,
            self.park_id,
            self.session
        )

        if result.error:
            print(f"ERROR clearing park: {result.message}")
        else:
            print(f"Successfully cleared park {self.park_id}")

        return result.data

    def _load_trajectory_tsv(self, tsv_path: str) -> List[dict]:
        """Load a trajectory from a TSV file.

        Args:
            tsv_path: Path to the TSV file containing the logged trajectory

        Returns:
            List of trajectory entries, each containing:
                - step: int
                - action_valid: bool
                - duration: float
                - action: str
                - end_state: dict
                - reward: float
                - info: dict
        """
        trajectory = []

        with open(tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')

            for row in reader:
                entry = {
                    'step': int(row['step']),
                    'action_valid': row['action_valid'].lower() == 'true',
                    'duration': float(row['duration']),
                    'action': row['action'],
                    'end_state': json.loads(row['end_state']),  # Parse JSON string
                    'reward': float(row['reward']),
                    'info': row['info']  # Parse JSON string
                }
                trajectory.append(entry)

        return trajectory

    def replay(self, tsv_path: str, replay_mode: str = "replay_actions", visualize: bool = False) -> Tuple[List[bool], float, float, List[float]]:
        """Replay a logged trajectory from a TSV file.

        Args:
            tsv_path: Path to the TSV file containing the logged trajectory.
            replay_mode: Either "replay_actions" or "replay_states"
                - "replay_actions": Uses initial state and action sequence to replay (calls step()).
                - "replay_states": Iterates through logged states without calling step().
            visualize: If True, calls render() on each state.

        Returns:
            A tuple containing:
                - action_validity: List of booleans indicating whether each action was valid.
                - score: The total score accumulated during replay.
                - final_money: The final money value at the end of replay.
                - revenues: List of revenue values for each step.

        Raises:
            ValueError: If replaying the trajectory is not possible.
        """
        if replay_mode not in ["replay_actions", "replay_states"]:
            raise ValueError(f"replay_mode must be 'replay_actions' or 'replay_states', got {replay_mode}")

        if visualize and not self.render_park and not self.visualizer:
            raise ValueError("To visualize, please set render_park=True or pass in a visualizer when initializing the park.")

        if self.observation_type != 'pydantic':
            raise ValueError("To replay, environment must be using pydantic observations")

        # Load trajectory from TSV
        trajectory = self._load_trajectory_tsv(tsv_path)

        if len(trajectory) == 0:
            raise ValueError(f"Empty trajectory loaded from {tsv_path}")

        score = 0
        start_money = 0
        action_validity = []
        revenues = []

        if replay_mode == "replay_states":
            # Mode 1: Replay states - just iterate through logged states
            for i, entry in enumerate(trajectory):
                if i == 0:
                    score = entry['end_state']['state']['money']
                # Set the environment to this state
                obs, info = self.set(entry['end_state'])

                # Get terminated/truncated from info if available
                reward = entry['reward']
                action = entry['action']

                if visualize:
                    raw_state = entry['end_state']
                    self.render_frame(raw_state, obs, action=action, info=info)

                action_validity.append(bool(entry['action_valid']))
                revenues.append(obs.revenue if obs.revenue is not None else 0)
                score += reward

            final_money = obs.money

            print(f"Final money: {obs.money}, start money: {start_money}, score: {score}")
            # assert entry['end_state']['state']['money'] - start_money == score

        else:  # replay_mode == "replay_actions"
            # Mode 2: Replay actions - use initial state and execute actions
            # First entry should be the reset() action
            if trajectory[0]['action'] != "reset()":
                raise ValueError(f"Expected first action to be 'reset()', got {trajectory[0]['action']}")

            # Set to initial state
            score = 0;
            if True:
                initial_state = trajectory[0]['end_state']
                obs, info = self.set(initial_state)
            else:
                self.update_settings(difficulty="medium", layout=trajectory[0]['end_state']['layout'])
                self.return_raw_in_info = True
                obs, info = self.reset()
                score = 500;

            # Execute each subsequent action
            for i in range(1, len(trajectory)):
                entry = trajectory[i]
                action = entry['action']
                # Execute the action
                obs, reward, terminated, truncated, info = self.step(action)
                if 'error' in info:
                    print(f"Error in action {action}: {info['error']['message']}")
                action_validity.append(bool('error' not in info))
                revenues.append(obs.revenue)

                score += reward

            print(f"Final value: {obs.value}, score: {score}")
            final_money = obs.money
            assert obs.value == score

        return action_validity, score, final_money, revenues
