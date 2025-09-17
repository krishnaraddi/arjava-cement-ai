import gym
from gym import spaces
import numpy as np

class KilnEnv(gym.Env):
    def __init__(self, config=None):
        super().__init__()
        self.observation_space = spaces.Box(
            low=np.array([300.0, 0.0, 0.0, 0.0]),
            high=np.array([1500.0, 50.0, 25.0, 200.0]),
            dtype=np.float32
        )
        self.action_space = spaces.Box(
            low=np.array([-5.0, -1.0]),
            high=np.array([5.0, 1.0]),
            dtype=np.float32
        )
        self.target_rate = 150.0
        self.max_steps = 500
        self.reset()

    def reset(self):
        self.current_temp = 900.0 + np.random.randn() * 50.0
        self.fuel_rate = 5.0
        self.moisture = 5.0
        self.clinker_rate = 150.0
        self.step_count = 0
        return np.array([
            self.current_temp,
            self.fuel_rate,
            self.moisture,
            self.clinker_rate
        ], dtype=np.float32)

    def step(self, action):
        temp_delta, fuel_delta = action
        self.current_temp = np.clip(self.current_temp + temp_delta, 300, 1500)
        self.fuel_rate = max(0.0, self.fuel_rate + fuel_delta)
        heat_input = self.fuel_rate * 10.0
        loss = 0.1 * (self.current_temp - 25.0)
        self.current_temp += (heat_input - loss) * 0.01
        self.clinker_rate = self.current_temp * (1 - self.moisture / 100) * 0.001
        reward = self.compute_reward()
        self.step_count += 1
        done = self.step_count >= self.max_steps
        obs = np.array([
            self.current_temp,
            self.fuel_rate,
            self.moisture,
            self.clinker_rate
        ], dtype=np.float32)
        info = {}
        return obs, reward, done, info

    def compute_reward(self):
        fuel_penalty = -0.1 * self.fuel_rate
        quality_bonus = 1.0 * max(0, 1 - abs(self.clinker_rate - self.target_rate) / self.target_rate)
        stability_penalty = -0.05 * abs(self.current_temp - getattr(self, "prev_temp", self.current_temp))
        self.prev_temp = self.current_temp
        return fuel_penalty + quality_bonus + stability_penalty
