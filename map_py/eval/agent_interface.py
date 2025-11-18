from abc import ABC, abstractmethod
from typing import Optional

from map_py.eval.state_interface import GameResponse
from map_py.eval.resource_interface import ResourceCost
from map_py.eval.utils import EvalConfig

class ActionGenerationError(Exception):
    """An error indicating that an agent cannot generate an action
    """
    def __init__(self, error_message: str):
        self.error_message = error_message
        super().__init__(self.error_message) 

class AbstractAgent(ABC):
    """
    Abstract base class for MAPs agents.
    """
    def __init__(self, name: Optional[str] = None):
        super().__init__()
        if name is None:
            name = self.__class__.__name__
        self.name = name

    @abstractmethod
    def supports_config(self, eval_config: EvalConfig) -> bool:
        """Returns True iff this agent can be evaluated using this eval config."""
        raise NotImplementedError
    
    @abstractmethod
    def act(self, game_inputs: GameResponse, run_id: int, logging_id: Optional[str] = None) -> str:
        """Generates an action to execute in the map

        Given the current game (game_inputs) and policy state (run_id),
        return a valid (python formatted) action to execute in the environment.

        If the run_id does not exist then a new history for this policy, starting from scratch, should be created.

        Args:
            game_inputs: The current game state.
            run_id: A unique ID for the rollout to be continued.
              This is useful for retrieving the history of a given rollout. Note that 
              run_id does *not* change with game state. i.e., if the agent is playing
              a single game, then the run_id is constant throughout the game. If the agent
              is playing 2 games at the same time (i.e. performing 2 rollouts at once), 
              then there will be two run_ids -- one for each rollout.
            logging_id: 
              A human-readable id for logging purposes only, for identifying this particular act() call.

        Returns:
            An action to be executed. The action must be formatted as a Python
            function call. See MAP documentation.

        Raises:
            ActionGenerationError: If the agent is unable to generate an action for this state.
        """
        raise NotImplementedError

    @abstractmethod
    def get_action_resource_usage(self, reset: bool = True) -> ResourceCost:
        """Get the cumulative resource usage of this agent.

        This method should accurately track resources even if self.act failed with an exception.

        Args:
            reset: Whether to reset any internal resource usage counters.
        Returns:
            A ResourceCost object with all of the different resources and how much was consumed.
        """
        raise NotImplementedError