"""
Stable-Baselines3 training script for Theme Park Tycoon environment.
The environment now accepts ThemeParkActionSpace actions directly.
"""

import os
import sys
import numpy as np
from stable_baselines3 import PPO, A2C, DQN, SAC
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.utils import set_random_seed
from typing import Callable
import logging

# Add the parent directory to the path to import the environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.map import MiniAmusementPark

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_env(host: str, port: str, difficulty: str = "easy", seed: int = 0) -> Callable:
    """
    Create a function that returns the environment directly.
    """
    def _init():
        env = MiniAmusementPark(
            host=host,
            port=port,
            difficulty=difficulty,
            observation_type="gym"  # Use gym observation format
        )
        env = Monitor(env)
        env.reset(seed=seed)
        return env
    return _init

def train_agent(agent_type: str = "PPO", 
                host: str = "localhost", 
                port: str = "8080",
                difficulty: str = "easy",
                total_timesteps: int = 100000,
                n_envs: int = 4,
                save_path: str = "./models"):
    """
    Train an RL agent on the Theme Park Tycoon environment.
    """
    
    # Create save directory
    os.makedirs(save_path, exist_ok=True)
    
    # Set random seed for reproducibility
    set_random_seed(42)
    
    # Create vectorized environment
    if n_envs == 1:
        env = DummyVecEnv([make_env(host, port, difficulty, seed=42)])
    else:
        env = SubprocVecEnv([make_env(host, port, difficulty, seed=42 + i) for i in range(n_envs)])
    
    # Create evaluation environment
    eval_env = DummyVecEnv([make_env(host, port, difficulty, seed=100)])
    
    # Create callbacks
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=f"{save_path}/best_model",
        log_path=f"{save_path}/logs",
        eval_freq=max(1000 // n_envs, 1),
        deterministic=True,
        render=False
    )
    
    checkpoint_callback = CheckpointCallback(
        save_freq=max(5000 // n_envs, 1),
        save_path=f"{save_path}/checkpoints",
        name_prefix=f"{agent_type.lower()}_model"
    )
    
    # Initialize the agent
    if agent_type == "PPO":
        model = PPO(
            "MlpPolicy",
            env,
            verbose=1,
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            tensorboard_log=f"{save_path}/tensorboard_logs"
        )
    elif agent_type == "A2C":
        model = A2C(
            "MlpPolicy",
            env,
            verbose=1,
            learning_rate=7e-4,
            n_steps=5,
            gamma=0.99,
            gae_lambda=1.0,
            ent_coef=0.01,
            tensorboard_log=f"{save_path}/tensorboard_logs"
        )
    elif agent_type == "DQN":
        model = DQN(
            "MlpPolicy",
            env,
            verbose=1,
            learning_rate=1e-4,
            buffer_size=100000,
            learning_starts=1000,
            batch_size=32,
            gamma=0.99,
            train_freq=4,
            gradient_steps=1,
            target_update_interval=1000,
            exploration_fraction=0.1,
            exploration_initial_eps=1.0,
            exploration_final_eps=0.05,
            tensorboard_log=f"{save_path}/tensorboard_logs"
        )
    elif agent_type == "SAC":
        model = SAC(
            "MlpPolicy",
            env,
            verbose=1,
            learning_rate=3e-4,
            buffer_size=100000,
            learning_starts=1000,
            batch_size=256,
            tau=0.005,
            gamma=0.99,
            train_freq=1,
            gradient_steps=1,
            ent_coef="auto",
            tensorboard_log=f"{save_path}/tensorboard_logs"
        )
    else:
        raise ValueError(f"Unsupported agent type: {agent_type}")
    
    # Train the agent
    logger.info(f"Starting training with {agent_type} agent for {total_timesteps} timesteps")
    model.learn(
        total_timesteps=total_timesteps,
        callback=[eval_callback, checkpoint_callback]
    )
    
    # Save the final model
    final_model_path = f"{save_path}/{agent_type.lower()}_final_model"
    model.save(final_model_path)
    logger.info(f"Training completed. Model saved to {final_model_path}")
    
    # Test the trained model
    test_model(model, host, port, difficulty)
    
    return model

def test_model(model, host: str, port: str, difficulty: str = "easy", n_episodes: int = 5):
    """
    Test a trained model on the environment.
    """
    logger.info(f"Testing model for {n_episodes} episodes")
    
    env = DummyVecEnv([make_env(host, port, difficulty, seed=200)])
    
    total_rewards = []
    episode_lengths = []
    
    for episode in range(n_episodes):
        obs, _ = env.reset()
        episode_reward = 0
        episode_length = 0
        
        while True:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward[0]
            episode_length += 1
            
            if terminated[0] or truncated[0]:
                break
        
        total_rewards.append(episode_reward)
        episode_lengths.append(episode_length)
        logger.info(f"Episode {episode + 1}: Reward = {episode_reward:.2f}, Length = {episode_length}")
    
    avg_reward = np.mean(total_rewards)
    avg_length = np.mean(episode_lengths)
    logger.info(f"Average reward: {avg_reward:.2f}")
    logger.info(f"Average episode length: {avg_length:.2f}")

def main():
    """
    Main function to run the training script.
    """
    # Configuration
    config = {
        "host": "localhost",
        "port": "8080",
        "difficulty": "easy",
        "agent_type": "PPO",  # Options: "PPO", "A2C", "DQN", "SAC"
        "total_timesteps": 50000,  # Start with a smaller number for testing
        "n_envs": 2,  # Number of parallel environments
        "save_path": "./trained_models"
    }
    
    # Check if game server is running
    try:
        import requests
        response = requests.get(f"http://{config['host']}:{config['port']}/health", timeout=5)
        if response.status_code != 200:
            logger.warning("Game server might not be running properly")
    except:
        logger.error("Could not connect to game server. Please ensure the server is running.")
        logger.info("You can start the server using: python launch_game.py")
        return
    
    # Train the agent
    model = train_agent(
        agent_type=config["agent_type"],
        host=config["host"],
        port=config["port"],
        difficulty=config["difficulty"],
        total_timesteps=config["total_timesteps"],
        n_envs=config["n_envs"],
        save_path=config["save_path"]
    )
    
    logger.info("Training script completed successfully!")

if __name__ == "__main__":
    main()
