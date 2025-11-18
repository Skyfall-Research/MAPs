# Standard library imports
import copy
import csv
import json
import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from datetime import datetime 
import shutil
from io import StringIO
from typing import Callable, Optional, Tuple
import copy 

# Third-party imports
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

# Local imports
from map_py.eval.state_interface import GameResponse, MapPydanticGameResponse, MapRawGameResponse
from map_py.mini_amusement_park import MiniAmusementPark
from map_py.eval.agent_interface import AbstractAgent, ActionGenerationError, ResourceCost
from map_py.shared_constants import MAP_CONFIG
from map_py.eval.utils import EvalConfig 


# Adjust logging levels
import logging 
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.basicConfig(level=logging.WARNING)

# Test and train layouts in the MAPs config
TEST_LAYOUTS = MAP_CONFIG['test_layouts']
TRAIN_LAYOUTS = MAP_CONFIG['train_layouts']

PARK_WIDTH = MAP_CONFIG['park_size']


def _server_error(info: dict) -> bool:
    return 'error' in info and info['error']['type'] == 'proceed_error'

def _multiprocess_safe_log_warning(run_idx, log_dir, message: str):
    """Log critical warnings to a file in a multi-process safe manner.
    """
    print(message, flush=True)
    log_dir = os.path.join(log_dir, 'WARNINGS_LOG')
    os.makedirs(log_dir, exist_ok=True)

    with open(os.path.join(log_dir, f'warning_run{run_idx}.txt'), 'a') as of:
        print(datetime.now(), file=of)
        print(message, file=of)


def _get_exp_dir(exp_name: str) -> str:
    return f'trajectories/{exp_name}'

class SingleAgentEvaluator:
    """Evaluator for running and evaluating a single agent across multiple game scenarios.
    
    This class manages the evaluation of an AbstractAgent across multiple starting states
    (layouts) and multiple runs per state. It supports parallel execution using multiprocessing
    and records detailed trajectory data including rewards, action validity, resource costs,
    and timing information.
    
    The evaluator creates a separate game environment for each evaluation run, executes
    the agent's actions, and logs comprehensive trajectory data to disk for later analysis.
    Results are aggregated and summary statistics are computed across all runs.
    """
    def __init__(self, 
                 port: int | str,
                 get_agent: Callable[[Optional[str | os.PathLike], EvalConfig], AbstractAgent], 
                 start_layouts: list[str],  # layout filenames
                 num_runs_per_start: int, 
                 max_processes: int, 
                 agent_config_path: Optional[os.PathLike | str],
                 exp_name: str,
                 difficulty: str = 'easy',
                 representation: str = 'pydantic',
                 verbose: bool = False) -> None:
        """Initialize the SingleAgentEvaluator.

        Args:
            port: Port number (as int or str) for the game server connection.
            get_agent: Callable that creates an AbstractAgent instance. Takes an optional
                agent config path and an EvalConfig, returns an AbstractAgent.
            start_layouts: List of starting layouts to evaluate on. Each element is a
                layout name that specifies which game layout to use for evaluation.
            num_runs_per_start: Number of independent evaluation runs to perform for each
                starting layout.
            max_processes: Maximum number of parallel processes to use for evaluation.
                Set to 0 to run sequentially (useful for debugging).
            agent_config_path: Optional path to the agent's configuration file. This will
                be used by get_agent and also copied to the experiment directory for reproducibility.
            exp_name: Name/identifier for this experiment. Used as the directory name
                where all trajectory data and results will be stored.
            difficulty: Game difficulty level. Must be one of 'easy', or 'medium'.
                Defaults to 'easy'.
            representation: The representation format for game state observations. Must be
                either 'pydantic' (structured Pydantic models) or 'raw' (dictionary format).
                Defaults to 'pydantic'.
            verbose: If True, enables verbose output including progress bars and per-step
                action logging. Defaults to False.
        """
        self.port = port 
        self.get_agent = get_agent
        self.start_states = start_layouts
        self.num_runs_per_start = num_runs_per_start
        self.agent_config_path = agent_config_path
        self.exp_name = exp_name
        self.difficulty = difficulty
        self.representation = representation
        self.verbose = verbose
    
        # Multiprocessing 
        self.max_processes = max_processes

    @staticmethod
    def _single_eval(arg_tuple) -> Tuple[float, list[float], list[int], list[ResourceCost], str, list[float], list[float]]:
        """Wrapper around _inner_single_eval that handles exceptions.
        
        This method catches exceptions from the inner evaluation and logs them to a
        warnings file in a multiprocess-safe manner before re-raising.
        
        Args:
            arg_tuple: Tuple containing evaluation parameters:
                - start_state (str): Layout filename for the starting state
                - run_idx (int): Unique index for this evaluation run
                - get_agent (Callable): Function to create the agent
                - agent_config_path (Optional[str | os.PathLike]): Path to agent config
                - port (int | str): Port for game server connection
                - global_id (str): Experiment identifier
                - difficulty (str): Game difficulty level
                - representation (str): Observation representation type
                - verbose (bool): Verbosity flag
        
        Returns:
            Tuple containing:
                - trajectory_reward (float): Total cumulative reward for the trajectory
                - times (list[float]): List of agent action generation times in seconds
                - action_validity (list[int]): List of bools indicating if each action was valid
                - resource_costs (list[ResourceCost]): List of resource costs per action
                - run_id (str): Identifier for this run (e.g., 'run_0')
                - per_turn_reward (list[float]): Reward received at each timestep
                - env_times (list[float]): List of environment step execution times in milliseconds
        
        Raises:
            Exception: Re-raises any exception that occurred during evaluation after logging.
        """
        try:
            return SingleAgentEvaluator._inner_single_eval(arg_tuple)
        except Exception as e:
            start_state, run_idx, get_agent, agent_config_path, port, global_id, difficulty, representation, verbose = arg_tuple
            exp_dir = _get_exp_dir(global_id)
            import traceback
            print('='*60)
            print('='*60)
            print('='*60)
            _multiprocess_safe_log_warning(run_idx, exp_dir, 'WARNING: One of the evaluation processes has failed!')
            _multiprocess_safe_log_warning(run_idx, exp_dir, traceback.format_exc())
            print('='*60)
            print('='*60)
            print('='*60, flush=True)
            raise e

    @staticmethod
    def _inner_single_eval(arg_tuple: Tuple[str, int, Callable[[Optional[str | os.PathLike], EvalConfig], AbstractAgent], Optional[str | os.PathLike], int | str, str, str, str, bool]) -> Tuple[float, list[float], list[int], list[ResourceCost], str, list[float], list[float]]:
        """Execute a single evaluation run of an agent on a specific starting state.
        
        This method creates a game environment, initializes an agent, and runs the agent
        through a complete game trajectory. It tracks rewards, action validity, resource
        costs, and timing information. All trajectory data is logged to a TSV file as the 
        agent runs.
        
        The evaluation continues until the game horizon is reached, the game terminates,
        or an error occurs. Invalid actions are handled gracefully (treated as no-ops),
        and ActionGenerationErrors are caught and replaced with wait() actions.
        
        Args:
            arg_tuple: Tuple containing evaluation parameters:
                - start_state (str): Layout filename for the starting state
                - run_idx (int): Unique index for this evaluation run
                - get_agent (Callable): Function to create the agent
                - agent_config_path (Optional[str | os.PathLike]): Path to agent config
                - port (int | str): Port for game server connection
                - global_id (str): Experiment identifier (used for directory naming)
                - difficulty (str): Game difficulty level ('easy', or 'medium')
                - representation (str): Observation representation type ('pydantic' or 'raw')
                - verbose (bool): If True, shows progress bar and per-step logging
        
        Returns:
            Tuple containing:
                - trajectory_reward (float): Total cumulative reward for the trajectory
                - times (list[float]): List of agent action generation times in seconds
                - action_validity (list[int]): List of 0/1 indicating if each action was valid
                - resource_costs (list[ResourceCost]): List of resource costs per action
                - run_id (str): Identifier for this run (e.g., 'run_0')
                - per_turn_reward (list[float]): Reward received at each timestep
                - env_times (list[float]): List of environment step execution times in milliseconds
        
        Raises:
            ValueError: If the agent does not support the evaluation configuration.
            RuntimeError: If the agent returns None as an action, if the environment
                encounters a fatal error, or if an internal server error occurs.
            NotImplementedError: If an unsupported representation type is specified.
        """
        # Controls tqdm progress bar + output messages on selected actions & final score.

        times = []
        env_times = []
        action_validity = []
        per_turn_reward = []
        resource_costs = []

        # park_id in MiniAmusementPark
        # run_idx is internal refernce to this specific eval run
        # get_agent is the method for creating the agent specified by the user
        start_state, run_idx, get_agent, agent_config_path, port, global_id, difficulty,representation, verbose = arg_tuple
        run_id = f'run_{run_idx}'

        layout_name = start_state
        del start_state

        game = MiniAmusementPark(host="localhost", 
                               port=port, 
                               # randomize_start_state=False, # This should hold be default now
                               return_raw_in_info=True,
                               observation_type=representation,
                               layout=layout_name,
                               difficulty=difficulty)
        game.reset()

        curr_state, raw = game.get_observation_and_raw_state()
        info = {'raw_state': raw}

        # Initial reward is set to zero
        if representation == 'pydantic':
            agent_input = MapPydanticGameResponse(obs=curr_state, info=info, terminated=False, truncated=False, reward=0)
        elif representation == 'raw':
            agent_input = MapRawGameResponse(obs=curr_state, info=info, terminated=False, truncated=False, reward=0)
        else:
            raise NotImplementedError
        curr_raw_state = info['raw_state']

        game_horizon = curr_raw_state['state']['horizon']
        assert game_horizon is not None
        eval_config = EvalConfig(run_idx = run_idx, observation_type=representation, difficulty=difficulty, horizon=game_horizon, logging_id=run_idx)
        agent: AbstractAgent = get_agent(agent_config_path, eval_config)

        if not agent.supports_config(eval_config):
            raise ValueError("Agent does not support the current eval config.")

        # Set up trajectory file
        EXP_DIR = _get_exp_dir(global_id)
        RUN_DIR = os.path.join(EXP_DIR, f"trajectory_{run_idx}")
        os.makedirs(RUN_DIR, exist_ok=True)
        trajectory_file = open(os.path.join(RUN_DIR, "trajectory.tsv"), "w")
        trajectory_writer = csv.writer(trajectory_file, delimiter="\t")
        trajectory_writer.writerow(["step", "duration", "start_budget", "action", "reward", "error", "raw_start_state", "raw_end_state"])


        prev_state = None
        prev_raw_state = None
        trajectory_reward = 0

        action_no = 0

        start_time = time.time()
        with tqdm(total=game_horizon, disable=not verbose) as pbar:
            while(curr_raw_state['state']['step'] < game_horizon):
                error = ""  # Initially, no error
                trunc = False  # Initially, trajectory not truncated

                # 1. Get action from agent
                start_time = time.time()
                try:
                    action = agent.act(agent_input, game.park_id, logging_id=f'action_{action_no}')
                    if action is None:
                        _multiprocess_safe_log_warning(run_idx, EXP_DIR, f"WARNING: Agent returned None as an action at timestep {action_no}.")
                        raise RuntimeError("Agent returned None")
                except ActionGenerationError as e:
                    action = "wait()"
                    import traceback
                    error = "ActionGenerationError; action set by eval script to wait()" + traceback.format_exc()
                    _multiprocess_safe_log_warning(run_idx, EXP_DIR, error)

                    if verbose:
                        print(error)
                except KeyboardInterrupt:
                    raise 
                except Exception as e:
                    import traceback
                    print("")
                    _multiprocess_safe_log_warning(run_idx, EXP_DIR, "WARNING EARLY TERMINATION OF TRAJECTORY DUE TO FATAL ERROR")
                    _multiprocess_safe_log_warning(run_idx, EXP_DIR, traceback.format_exc())
                    trajectory_writer.writerow([action_no, round(time.time() - start_time), None, None, None, f"FATAL ERROR IN AGENT {e} \n{traceback.format_exc()}", json.dumps(curr_raw_state, sort_keys=True), None])
                    trajectory_file.flush()
                    raise

                times.append(time.time() - start_time)
                resource_usage = agent.get_action_resource_usage(reset=True)
                resource_costs.append(resource_usage)
                    
                if verbose:
                    print(f"Run {run_idx}: Step {action_no}: Budget: {curr_state.money:>5}. Park Rating: {curr_state.park_rating:.2f}. "
                        f"Selected action on step {action_no}: {action}", flush=True)

                # 2. Execute action in environment
                reward = 0  # No reward if failed to generate an action
                if action is not None:
                    prev_state = curr_state
                    start_time_env_exec = time.time()
                    try:
                        curr_state, reward, term, trunc, info = game.step(action)
                        if representation == 'pydantic':
                            agent_input = MapPydanticGameResponse(obs=curr_state, info=info, terminated=term, truncated=trunc)
                        elif representation == 'raw':
                            agent_input = MapRawGameResponse(obs=curr_state, info=info, terminated=term, truncated=trunc)
                        else:
                            raise NotImplementedError
                    except Exception:
                        trajectory_writer.writerow([action_no, round(time.time() - start_time),
                                            prev_state.money, 
                                            str(action), None, "Game End (Catastrophic Server Error)", 
                                            json.dumps(curr_raw_state, sort_keys=True), None,
                                            ])
                        raise 

                    env_times.append((time.time() - start_time_env_exec) * 1000) # seconds to ms

                    assert game_horizon is not None
                    assert not term or action_no == game_horizon - 1 

                    if _server_error(info):
                        reward = 0

                    # TPT is configured such that invalid actions are treated as a no-op, advancing time
                    # Either action was success, or no-op was done instead
                    prev_raw_state = curr_raw_state
                    curr_raw_state = info['raw_state'] 
                    if 'error' in info:
                        error = json.dumps(info['error'])
                    assert curr_state.step == action_no + 1
                    pbar.update()  # update progress bar

                    if 'error' in info and _server_error(info):
                        _multiprocess_safe_log_warning(run_idx, EXP_DIR, "WARNING EARLY TERMINATION OF TRAJECTORY DUE TO FATAL INTERNAL SERVER ERROR")
                        trajectory_writer.writerow([action_no, round(time.time() - start_time), None, None, None, f"FATAL ERROR IN ENV \n{info}", json.dumps(curr_raw_state, sort_keys=True), None])
                        trajectory_file.flush()
                        raise RuntimeError(f"TPT server encountered an error: {info}")

                if reward is None:
                    raise RuntimeError("There was an error in the environment that caused the system to crash. Please fix this and restart the evaluation")
                
                # 3. Deal with invalid actions
                if action is not None and 'error' in info:
                    action_validity.append(0)
                    if curr_state.step != action_no + 1:
                        _multiprocess_safe_log_warning(run_idx, EXP_DIR, "WARNING WARNING WARNING: Action {action} in env failed but timestep did not advance, environment state may be compromised")
                elif action is None or 'error' in info or error != '':
                    if verbose:
                        print(f"Invalid action!")
                        if error:
                            print("Error:", error)
                        else:
                            error = f"Indeterminate Error: action={action}"
                    action_validity.append(0)
                    assert curr_state.step == action_no + 1
                else:
                    action_validity.append(1)
                    
                _, raw_end_state = game.get_observation_and_raw_state()

                raw_start_state = copy.deepcopy(prev_raw_state)
                
                # 5. Logging and updating trajectory file
                trajectory_reward += reward
                per_turn_reward.append(reward)
                error = error.replace("\t", "    ")
                assert prev_state is not None
                trajectory_writer.writerow([action_no, round(time.time() - start_time),
                                            prev_state.money, 
                                            str(action), reward, error, 
                                            json.dumps(raw_start_state, sort_keys=True), json.dumps(raw_end_state, sort_keys=True)
                                            ])
                
                # Force flush to aid debugging if the next agent action causes a crash
                trajectory_file.flush()
                
                if trunc:
                    print(f"Game is functionally over at step {action_no}. Ending trajectory early.")
                    trajectory_writer.writerow([action_no, round(time.time() - start_time), prev_state.money, None, 0, "Game End (Early)",None, None ])
                    break


                # Advance counter for either valid or invalid actions
                action_no += 1

                
                # If internal server error
                if _server_error(info):
                    print(f"Internal server error at step {action_no}. Ending trajectory early.")
                    trajectory_writer.writerow([action_no, round(time.time() - start_time), prev_state.money, None, 0, "Game End (Internal Server Error)", None, None ])
                    raise RuntimeError(f"Internal Server Error Occured in {global_id}\n{info}")


        assert prev_state is not None
        trajectory_writer.writerow([action_no, round(time.time() - start_time), prev_state.money, None, 0, "Game End", None, None ])

        trajectory_file.close()
        if verbose:
            print(f"--- Total reward for run {run_idx}: {trajectory_reward} ---", flush=True)

        # Reset the environment to save memory on the map server.
        # In future, we should ideally be destroying the environment entirely.
        game.reset()

        return_val = trajectory_reward, times, action_validity, resource_costs, run_id, per_turn_reward, env_times

        # Record this data for analysis and debugging
        with open(os.path.join(RUN_DIR, 'eval_vals.pkl.tmp'), 'wb') as outfile:
            pickle.dump(return_val, outfile)
        # Atomic operation
        os.replace(os.path.join(RUN_DIR, 'eval_vals.pkl.tmp'), os.path.join(RUN_DIR, 'eval_vals.pkl'))

        return return_val



    def _eval(self) -> Tuple:
        """Execute the full evaluation across all starting states and runs.
        
        This method orchestrates the evaluation process:
        1. Creates the experiment directory
        2. Copies agent configuration for reproducibility
        3. Generates all evaluation tasks (one per layout per run)
        4. Executes tasks in parallel (if max_processes > 0) or sequentially
        5. Aggregates results from all runs
        
        The evaluation proceeds by running the agent num_runs_per_start times for each
        starting state in start_states. Each run is independent and uses a fresh game
        environment.
        
        Returns:
            Tuple containing aggregated results:
                - rewards (tuple[float, ...]): Tuple of total trajectory rewards, one per run
                - times (list[float]): Flattened list of all agent action generation times
                - action_validity (list[int]): Flattened list of action validity (bool) for all actions
                - flat_resource_costs (list[ResourceCost]): Flattened list of resource costs per action
                - run_ids (tuple[str, ...]): Tuple of run identifiers (e.g., ('run_0', 'run_1', ...))
                - resource_costs (tuple[list[ResourceCost], ...]): Tuple of lists, one list of resource costs per run
                - per_turn_rewards (list[float]): Flattened list of rewards per timestep
                - env_times (list[float]): Flattened list of environment execution times in ms
        
        Note:
            The experiment directory must not exist before calling this method. If it
            exists, the evaluation will abort to prevent overwriting previous results.
        """
        tasks = []
        run_idx = 0

        # Create directory for this experiment
        experiment_dir = _get_exp_dir(self.exp_name)
        os.makedirs(experiment_dir, exist_ok=False)

        # Record the agent configuration, and the arguments to the evaluator
        if self.agent_config_path:
            shutil.copy(self.agent_config_path, os.path.join(experiment_dir, f'exp_config_agent.json'))

        # Create a new simulator environment for each run
        # (future proofing against the choice of the size of the processor pool)
        for layout_name in self.start_states:
            for _ in range(self.num_runs_per_start): 
                tasks.append((layout_name, run_idx, self.get_agent, 
                            self.agent_config_path, 
                            self.port, self.exp_name,
                            self.difficulty,
                            self.representation,
                            self.verbose))
                
                run_idx += 1


        # Record the experiments that will be run
        tasks_copy = [[val for val in task if not isinstance(val, Callable)] for task in tasks]
        with open(os.path.join(experiment_dir, f'tasks.json'), 'w') as of:
            json.dump(tasks_copy, of, indent=2)

        # Note: Using multiprocessing for true parallelism given Python GIL
        # Assume that IO (e.g., LLM calls are the main bottleneck)
        # NOTE: Must use spawn or forkserver for the processes, fork will deadlock
        # NOTE: Must use ProcessPoolExecutor and not a multiprocessing.Pool as we need non-daemon workers
        #       so this pool can launch it's own pools if needed.        
        if self.max_processes != 0:
            with ProcessPoolExecutor(max_workers = self.max_processes, 
                                     mp_context = get_context("forkserver")) as p:
                # Use the default map for parallel processing
                results = list(p.map(SingleAgentEvaluator._single_eval, tasks))
        else:
            results = list(SingleAgentEvaluator._single_eval(task) for task in tasks)


        # NOTE: Results are processed in order using the default map
        rewards, times, action_validity, resource_costs, run_ids, per_turn_rewards, env_times = zip(*results)


        # Flatten the nested lists
        times = [item for sublist in times for item in sublist]
        env_times = [item for sublist in env_times for item in sublist]
        action_validity = [item for sublist in action_validity for item in sublist]
        per_turn_rewards = [item for sublist in per_turn_rewards for item in sublist]
        assert len(action_validity) == len(per_turn_rewards)
        flat_resource_costs = [item for sublist in resource_costs for item in sublist]

        return rewards, times, action_validity, flat_resource_costs, run_ids, resource_costs, per_turn_rewards, env_times


def _rc_sum(rc_list: list[ResourceCost]) -> ResourceCost:
    acc = ResourceCost()
    for item in rc_list:
        acc += item 
    return acc 

def evaluate_agent(agent_constructor: Callable[[Optional[str | os.PathLike], EvalConfig], AbstractAgent], 
                    agent_config_path: Optional[str | os.PathLike] = None,
                    samples_per_start: int = 3,
                    max_processes: int = 0,
                    input_layouts: list[str] | None = None, 
                    train: bool = True, exp_name: Optional[str] = None, 
                    port: int = 3000,
                    difficulty: str = 'easy',
                    representation: str = 'pydantic',
                    verbose: bool = False):
    if exp_name is None:
        exp_name = f'exp_{datetime.now()}'

    if difficulty not in ['easy', 'medium']:
        raise ValueError("Difficulty must be one of: 'easy', or 'medium'")

    if os.path.exists(_get_exp_dir(exp_name)):
        print("Output directory already exists, aborting eval.")
        exit(-1)

    # Confirm layouts match train/test mode
    if input_layouts is None and not train:
        input_layouts = [
            layout_filename for 
            layout_filename in TEST_LAYOUTS
        ]
    elif input_layouts is None and train:
        input_layouts = [
            layout_filename for 
            layout_filename in TRAIN_LAYOUTS
        ]
    elif train:
        assert all(x[0] not in TEST_LAYOUTS for x in input_layouts)
    else:
        assert all(x[0] in TEST_LAYOUTS for x in input_layouts)

    assert input_layouts is not None

    driver = SingleAgentEvaluator(port=str(port),
                                  get_agent=agent_constructor, 
                                  start_layouts=input_layouts , 
                                  num_runs_per_start=samples_per_start , 
                                  max_processes=max_processes, 
                                  agent_config_path=agent_config_path, 
                                  exp_name=exp_name, 
                                  difficulty=difficulty,
                                  representation=representation,
                                  verbose=verbose)

    eval_start_time = time.time()
    rewards, times, action_validity, flat_resource_costs, run_ids, resource_costs, per_turn_rewards, env_times = driver._eval()   
    resource_costs_by_run = list(zip(run_ids, resource_costs))
    rewards_by_run = list(zip(run_ids, rewards))
    rewards_by_run.sort(key = lambda x: int(x[0][4:]))

    str_buf = StringIO() 


    print(f"\n==================================\nEvaluation complete, results saved to: {_get_exp_dir(exp_name)}\n")
    print(f"The final average reward (change in park value) is {np.mean(rewards):.1f} ± {np.std(rewards):.1f}", file=str_buf)
    print(f"The final median reward (change in park value) is {np.median(rewards):.1f}", file=str_buf)
    agent_time = f"{np.mean(times):.1f}s ± {np.std(times):.1f}" if f"{np.mean(times):.1f}" != "0.0" else f"{np.mean(times)*1000:.1f}ms ± {np.std(times)*1000:.1f}"
    print(f"The average agent time taken per turn was: {agent_time}", file=str_buf)
    print(f"The average environment time taken per turn was: {np.mean(env_times):.1f}ms ± {np.std(env_times):.1f}", file=str_buf)

    print(f"The total evaluation time was: {(time.time() - eval_start_time)/60:.1f} minutes", file=str_buf)


    accumulator = ResourceCost()
    for cost in flat_resource_costs:
        accumulator += cost 

    # Record the resource costs per run and total costs
    with open(os.path.join(_get_exp_dir(exp_name), f'resource_costs.json'), 'w') as of:
        cost_summary = {name: _rc_sum([cost for cost in costs]).to_dict() for (name, costs) in resource_costs_by_run}
        cost_summary['total'] = accumulator.to_dict()
        json.dump(cost_summary, of, indent=2, sort_keys=True)

    avg_std = ResourceCost.avg_and_dev(flat_resource_costs)
    for (cost, (avg, std)) in avg_std.items():
        print(f"The average {cost} per turn was: {avg:.1f} ± {std:.1f}", file=str_buf)

    for cost_name in accumulator:
        for cost_subtype in accumulator[cost_name]:
            print(f"The total {cost_name} {cost_subtype} was: {accumulator[cost_name][cost_subtype]}", file=str_buf)

    usd_cost = accumulator.to_usd()
    if usd_cost is not None:
        print(f"The total cost was: ${round(usd_cost, 2)} USD", file=str_buf)

    print(f"{np.mean(action_validity)*100:.2f}% of actions were valid", flush=True, file=str_buf)

    valid_action_rewards = [r for (r, val) in zip(per_turn_rewards, action_validity) if val]
    print(f"Considering only valid actions:\n\tmedian per-turn reward is {np.median(valid_action_rewards):.1f}\n\taverage per-turn reward is {np.mean(valid_action_rewards):.1f} ± {np.std(valid_action_rewards):.1f}", file=str_buf)


    with open(os.path.join(_get_exp_dir(exp_name), f'eval_summary.txt'), 'w') as of:
        print(str_buf.getvalue(), file=of)

        # For convenience, save an overview by trajectory
        print('='*40, file=of)
        print('Rewards by Trajectory:', file=of)
        for run_id, reward in rewards_by_run:
            print(f'{run_id+":":8} {reward:.1f}', file=of)

    print(str_buf.getvalue(), flush=True)

    plt.hist(rewards)
    plt.title(f'Trajectory Rewards {exp_name}')
    plt.ylabel('Counts')
    plt.xlabel('Total Trajectory Reward')
    plt.savefig(os.path.join(_get_exp_dir(exp_name), f'rewards.jpg'))

    # For convenience of pasting results into google spreadsheet
    total_cost = accumulator.to_usd()

    if total_cost is not None:
        total_cost = round(total_cost, 2)


if __name__ == '__main__':
    from map_py.human_agent import print_state

    class HumanAgent(AbstractAgent):
        def get_action_resource_usage(self, reset: bool = True) -> ResourceCost:
            return ResourceCost()  # No input or output tokens consumed

        def supports_config(self, eval_config: EvalConfig) -> bool:
            return eval_config.observation_type == 'pydantic'

        def act(self, game_inputs: GameResponse, run_id: int, logging_id: Optional[str] = None) -> str:
            assert isinstance(game_inputs, MapPydanticGameResponse)

            print("Terminated:")
            print(game_inputs.terminated)
            print("Truncated:")
            print(game_inputs.truncated)
            print_state(game_inputs.obs)
            if 'error' in game_inputs.info:
                print(f'Last action produced an error: {game_inputs.info['error']}')
            return input("What action should be taken?\n")

    def human_agent_constructor(agent_config_path: Optional[str | os.PathLike], eval_config: EvalConfig) -> HumanAgent:
        return HumanAgent()

    evaluate_agent(human_agent_constructor, samples_per_start=1, input_layouts=['diagonal_squares'], train=True)
