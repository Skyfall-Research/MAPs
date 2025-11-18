from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional

class EvalConfig:
    """Configuration class for evaluation runs.
    
    Stores configuration parameters for running evaluations of agents in the MAP
    (Mini Amusement Park) environment. Validates difficulty and observation type
    parameters during initialization.
    
    Attributes:
        run_idx: The index/identifier for this evaluation run.
        observation_type: The type of observation format to use. Must be one of:
            'pydantic', 'gym', or 'raw'.
        difficulty: The difficulty level for the evaluation. Must be 'easy' or 'medium'.
        logging_id: Optional identifier for logging purposes. Defaults to empty string.
        horizon: The maximum number of steps for the evaluation episode.
    
    Raises:
        ValueError: If difficulty is not 'easy' or 'medium', or if observation_type
            is not one of the valid options.
    """
    run_idx: int 
    observation_type: str 
    difficulty: str
    logging_id: str
    horizon: int
    
    def __init__(self, 
                 run_idx: int,
                 observation_type: str, 
                 difficulty: str, 
                 horizon: int,
                 logging_id: str = '') -> None:
        """Initialize an EvalConfig instance.
        
        Args:
            run_idx: The index/identifier for this evaluation run.
            observation_type: The type of observation format to use. Must be one of:
                'pydantic', 'gym', or 'raw'.
            difficulty: The difficulty level for the evaluation. Must be 'easy' or 'medium'.
            horizon: The maximum number of steps for the evaluation episode.
            logging_id: Optional identifier for logging purposes. Defaults to empty string.
        
        Raises:
            ValueError: If difficulty is not 'easy' or 'medium', or if observation_type
                is not one of the valid options.
        """
        if difficulty not in ['easy', 'medium']:
            raise ValueError(f"difficulty must be one of 'easy', 'medium'")
        if observation_type not in ['pydantic', 'gym', 'raw', 'test']:
            raise ValueError(f"obsevation_type must be one of 'pydantic', 'gym', 'raw', or 'test'")

        self.difficulty = difficulty
        self.run_idx = run_idx
        self.observation_type = observation_type
        self.horizon = horizon
        self.logging_id = logging_id

class GameAttributeNotSetError(Exception):
    """An error indicating that the MAP game value being accessed does not exist"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class ObsState(Enum):
    """Enumeration for tracking whether game state attributes have been set.
    
    Used in GameResponse classes to indicate that a particular attribute (obs, reward,
    terminated, truncated, or info) has not been set yet. This allows for lazy
    initialization and validation of game state attributes.
    
    Attributes:
        NOT_SET: Indicates that an attribute has not been set.
    """
    NOT_SET = 1

class GameState:
    """Base class for game state observations.
    
    This is a marker class used for type hints to represent the state of the game.
    Concrete implementations of game states (such as FullParkObs) should inherit
    from this class. The class itself contains no implementation and serves purely
    as a type annotation marker.
    """
    pass

class GameResponse(ABC):
    """Stores the response from a Gymnasium environment, or the results of a world model's
    prediction of the same.

    Specifically, this object stores: "obs", "reward", "terminated", "truncated", "info"
    (see https://gymnasium.farama.org/api/env/#gymnasium.Env.step for details)

    Any attribute that are not set will raise a GameAttributeNotSetError when accessed by default,
    but can be configured to instead return a default value.
    """
    @abstractmethod
    def __init__(self, 
                 obs: GameState | dict | ObsState = ObsState.NOT_SET, 
                 reward: float | ObsState = ObsState.NOT_SET,
                 terminated: bool | ObsState = ObsState.NOT_SET,
                 truncated: bool | ObsState = ObsState.NOT_SET,
                 info: dict | ObsState = ObsState.NOT_SET,) -> None:
        """Store the environments response. Any values that are not provided are recorded as being not set.
        By default, accessing an attribute that was not set will raise an GameAttributeNotSetError.
        """
        raise NotImplementedError

    @abstractmethod
    def enable_defaults(self, defaults: Optional[dict] = None):
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
        raise NotImplementedError

    @abstractmethod
    def disable_defaults(self):
        """Disable defaults so that attempting to access an unset attribute will raise an exception."""
        raise NotImplementedError
        
    @property
    @abstractmethod
    def obs(self):
        raise NotImplementedError
    @obs.setter
    @abstractmethod
    def obs(self, value):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def reward(self):
        raise NotImplementedError
    @reward.setter
    @abstractmethod
    def reward(self, value):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def terminated(self):
        raise NotImplementedError
    @terminated.setter
    @abstractmethod
    def terminated(self, value):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def truncated(self):
        raise NotImplementedError
    @truncated.setter
    @abstractmethod
    def truncated(self, value):
        raise NotImplementedError
    
    @property
    @abstractmethod
    def info(self):
        raise NotImplementedError
    @info.setter
    @abstractmethod
    def info(self, value):
        raise NotImplementedError

    @property
    @abstractmethod
    def action_succeeded(self):
        raise NotImplementedError   

