from abc import abstractmethod
from typing import Optional, Any, Union, cast
import copy

from map_py.observations_and_actions.pydantic_obs import FullParkObs
from map_py.eval.utils import GameState, GameResponse, ObsState, GameAttributeNotSetError

class MapGameResponse(GameResponse):
    """Stores a response from the MAP Gymnasium environment, or the results of a world model's
    prediction of the same.

    Specifically, this object stores: "obs", "reward", "terminated", "truncated", "info"
    (see https://gymnasium.farama.org/api/env/#gymnasium.Env.step for details)

    Any attribute that are not set will raise a GameAttributeNotSetError when accessed by default,
    but can be configured to instead return a default value.
    """
    def __init__(self, 
                 obs: GameState | dict | ObsState = ObsState.NOT_SET, 
                 reward: float | ObsState = ObsState.NOT_SET,
                 terminated: bool | ObsState = ObsState.NOT_SET,
                 truncated: bool | ObsState = ObsState.NOT_SET,
                 info: dict | ObsState = ObsState.NOT_SET,) -> None:
        """Store the environments response. Any values that are not provided are recorded as being not set.
        By default, accessing an attribute that was not set will raise an GameAttributeNotSetError.
        """
        self._obs: Union[GameState, dict, ObsState] = obs 
        self._reward: Union[float, ObsState] = reward
        self._terminated: Union[bool, ObsState] = terminated
        self._truncated: Union[bool, ObsState] = truncated
        self._info: Union[dict, ObsState] = info 
        self.defaults: dict = {}

    def enable_defaults(self, defaults: Optional[dict] = None) -> None:
        """Provide a default value for key(s) of your choice. Any keys without defaults will continue to raise an exception if not set.

        If no "defaults" is provided, then a default "defaults" will be used:
            - reward will map to 0, 
            - terminated & truncated to False, 
            - info will map to an empty dictionary
            - obs will not have a default value and will raise an exception 

        Args:
            defaults (Optional[dict]): A dictionary mapping any subset of the keys 
            "obs", "reward", "terminated", "truncated", "info" to the intended default value.
        """
        if defaults is None:
            defaults = {'reward': 0, 'terminated': False, 'truncated': False, 'info': dict()}

        assert set(defaults.keys()).issubset({'reward', 'terminated', 'truncated', 'info'})

        self.defaults = copy.deepcopy(defaults)

    def disable_defaults(self) -> None:
        """Disable defaults so that attempting to access an unset attribute will raise an exception."""
        self.defaults = {}

    def _retrieve(self, key: str) -> Any:
        """Retrieve an attribute value, using defaults if configured and the attribute is not set.
        
        Args:
            key: The name of the attribute to retrieve (e.g., "obs", "reward", "terminated", etc.).
            
        Returns:
            The value of the requested attribute.
            
        Raises:
            GameAttributeNotSetError: If the attribute is not set and no default is configured.
        """
        if getattr(self, f'_{key}') != ObsState.NOT_SET:
            return getattr(self, f'_{key}')
        elif key in self.defaults:
            return copy.deepcopy(self.defaults[key])
        else:
            raise GameAttributeNotSetError(f'The attribute {key} was not set for this GameResponse.')
        
    @property
    def obs(self) -> Union[GameState, dict]:
        """Get the observation from the game response.
        
        Returns:
            The observation (GameState or dict), or raises GameAttributeNotSetError if not set.
        """
        return self._retrieve("obs")
    @obs.setter
    def obs(self, value: Union[GameState, dict, ObsState]) -> None:
        """Set the observation value.
        
        Args:
            value: The observation to store, or ObsState.NOT_SET to mark as unset.
        """
        self._obs = value
    
    @property
    def reward(self) -> float:
        """Get the reward from the game response.
        
        Returns:
            The reward value, or raises GameAttributeNotSetError if not set.
        """
        return self._retrieve("reward")
    @reward.setter
    def reward(self, value: Union[float, ObsState]) -> None:
        """Set the reward value.
        
        Args:
            value: The reward to store, or ObsState.NOT_SET to mark as unset.
        """
        self._reward = value
    
    @property
    def terminated(self) -> bool:
        """Get the terminated flag from the game response.
        
        Returns:
            True if the episode terminated, False otherwise, or raises GameAttributeNotSetError if not set.
        """
        return self._retrieve("terminated")
    @terminated.setter
    def terminated(self, value: Union[bool, ObsState]) -> None:
        """Set the terminated flag.
        
        Args:
            value: The terminated flag to store, or ObsState.NOT_SET to mark as unset.
        """
        self._terminated = value
    
    @property
    def truncated(self) -> bool:
        """Get the truncated flag from the game response.
        
        Returns:
            True if the episode was truncated, False otherwise, or raises GameAttributeNotSetError if not set.
        """
        return self._retrieve("truncated")
    @truncated.setter
    def truncated(self, value: Union[bool, ObsState]) -> None:
        """Set the truncated flag.
        
        Args:
            value: The truncated flag to store, or ObsState.NOT_SET to mark as unset.
        """
        self._truncated = value
    
    @property
    def info(self) -> dict:
        """Get the info dictionary from the game response.
        
        Returns:
            The info dictionary, or raises GameAttributeNotSetError if not set.
        """
        return self._retrieve("info")
    @info.setter
    def info(self, value: Union[dict, ObsState]) -> None:
        """Set the info dictionary.
        
        Args:
            value: The info dictionary to store, or ObsState.NOT_SET to mark as unset.
        """
        self._info = value

    @property
    def action_succeeded(self) -> bool:
        """Check if the action succeeded by verifying that 'error' is not in the info dictionary.
        
        Returns:
            True if the action succeeded (no error in info), False otherwise.
        """
        return 'error' not in self._retrieve("info")  

    @property
    def raw_obs(self) -> Any:
        """Return the raw state from the info dictionary.
        
        Returns:
            The raw state stored in info['raw_state'].
            
        Raises:
            KeyError: If 'raw_state' is not present in the info dictionary.
        """
        return self.info['raw_state']

    def calculate_reward_from_raw(self, state: dict) -> float:
        """Calculate reward as profit (revenue - expenses) from a raw state dictionary.
        
        Args:
            state: A dictionary containing state information with 'state' key containing
                'revenue' and 'expenses' keys.
                
        Returns:
            The calculated reward (profit) as a float.
        """
        return state['state']['revenue'] - state['state']['expenses'] 

    @property
    @abstractmethod
    def step(self) -> int:
        """Return the current step number from the game state.
        
        Returns:
            The current step number as an integer.
        """
        raise NotImplementedError

class MapPydanticGameResponse(MapGameResponse):
    """A pydantic gymasium game response (or prediction thereof) from the MAP environment.

    Specifically, this object stores: "obs", "reward", "terminated", "truncated", "info"
    (see https://gymnasium.farama.org/api/env/#gymnasium.Env.step for details)

    Any attribute that are not set will raise a GameAttributeNotSetError when accessed by default,
    but can be configured to instead return a default value.

    Note that if not set, this object will attempt to compute the "reward" as profit
    from the provided "obs" state.
    """

    def __init__(self, 
                 obs: Union[FullParkObs, ObsState] = ObsState.NOT_SET, 
                 reward: Union[float, ObsState] = ObsState.NOT_SET, 
                 terminated: Union[bool, ObsState] = ObsState.NOT_SET, 
                 truncated: Union[bool, ObsState] = ObsState.NOT_SET, 
                 info: Union[dict, ObsState] = ObsState.NOT_SET, 
                 disable_validation: bool = False) -> None:
        """Store the environments response. Any values that are not provided are recorded as being not set.
        By default, accessing an attribute that was not set will raise an GameAttributeNotSetError.

        Args:
            obs: The observation (FullParkObs instance) or ObsState.NOT_SET if not provided.
            reward: The reward value or ObsState.NOT_SET if not provided.
            terminated: The terminated flag or ObsState.NOT_SET if not provided.
            truncated: The truncated flag or ObsState.NOT_SET if not provided.
            info: The info dictionary or ObsState.NOT_SET if not provided.
            disable_validation: If True, skip validation that obs must be a FullParkObs instance.
            
        Raises:
            ValueError: If disable_validation is False and obs is not a FullParkObs instance or ObsState.NOT_SET.
        """
        if not disable_validation and not isinstance(obs, FullParkObs):
            raise ValueError(f"obs should be a FullParkObs or unset. Instead, got {type(obs)}")
        
        super().__init__(obs, reward, terminated, truncated, info)

    def _retrieve(self, key: str) -> Any:
        """Retrieve an attribute value, with special handling for reward calculation from obs.
        
        If the reward is not set, this method attempts to calculate it from the observation's
        profit attribute. For other attributes, it falls back to the parent class behavior.
        
        Args:
            key: The name of the attribute to retrieve.
            
        Returns:
            The value of the requested attribute.
            
        Raises:
            GameAttributeNotSetError: If the attribute is not set and cannot be calculated.
        """
        try:
            return super()._retrieve(key)
        except GameAttributeNotSetError:
            if key == 'reward':
                try:
                    return self.obs.profit  # type: ignore[attr-defined]
                except GameAttributeNotSetError as e:
                    raise GameAttributeNotSetError('Reward was not set, and cannot calculate from state because state is not set.') from e
            else:
                raise

    @property
    def step(self) -> int:
        return self.obs.step  # type: ignore[attr-defined]


class MapRawGameResponse(MapGameResponse):
    """A raw gymasium game response (or prediction thereof) from the MAP environment.

    Specifically, this object stores: "obs", "reward", "terminated", "truncated", "info"
    (see https://gymnasium.farama.org/api/env/#gymnasium.Env.step for details)

    Any attribute that are not set will raise a GameAttributeNotSetError when accessed by default,
    but can be configured to instead return a default value.

    Note that if not set, this object will attempt to compute the "reward" as profit
    from the provided "obs" state.
    """

    def __init__(self, 
                 obs: Union[dict, ObsState] = ObsState.NOT_SET, 
                 reward: Union[float, ObsState] = ObsState.NOT_SET, 
                 terminated: Union[bool, ObsState] = ObsState.NOT_SET, 
                 truncated: Union[bool, ObsState] = ObsState.NOT_SET, 
                 info: Union[dict, ObsState] = ObsState.NOT_SET, 
                 disable_validation: bool = False) -> None:
        """Store the environments response. Any values that are not provided are recorded as being not set.
        By default, accessing an attribute that was not set will raise an GameAttributeNotSetError.

        If the provided obs is a dictionary, then it is assumed to be the raw state.
        In this case, the info dictionary is modified to include the obs as the raw state,
        under the 'raw_state' key, and obs itself is not set.

        Args:
            obs: The observation (raw state dictionary) or ObsState.NOT_SET if not provided.
            reward: The reward value or ObsState.NOT_SET if not provided.
            terminated: The terminated flag or ObsState.NOT_SET if not provided.
            truncated: The truncated flag or ObsState.NOT_SET if not provided.
            info: The info dictionary or ObsState.NOT_SET if not provided. If a dict is provided,
                it will be modified to include 'raw_state' key with the obs value.
            disable_validation: Currently unused, kept for API compatibility.
        """
        if isinstance(info, dict):
            assert 'raw_state' not in info 
            info['raw_state'] = obs 
        else:
            assert info == ObsState.NOT_SET
            info = {'raw_state': obs}
        
        super().__init__(obs, reward, terminated, truncated, info)

    def _retrieve(self, key: str) -> Any:
        """Retrieve an attribute value, with special handling for reward calculation from raw obs.
        
        If the reward is not set, this method attempts to calculate the reward from the raw
        observation dictionary as profit (revenue - expenses).
        
        Args:
            key: The name of the attribute to retrieve.
            
        Returns:
            The value of the requested attribute.
            
        Raises:
            GameAttributeNotSetError: If the attribute is not set (in the case of reward, it also cannot be calculated).
        """
        try:
            return super()._retrieve(key)
        except GameAttributeNotSetError:
            if key == 'reward':
                # For MapRawGameResponse, obs is always a dict, not GameState
                obs_dict = cast(dict, self.obs)
                return obs_dict['state']['revenue'] - obs_dict['state']['expenses']
            else:
                raise

    @property
    def step(self) -> int:
        # For MapRawGameResponse, obs is always a dict, not GameState
        obs_dict = cast(dict, self.obs)
        return obs_dict['state']['step']

