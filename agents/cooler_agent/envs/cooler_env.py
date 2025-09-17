import gym
from gym import spaces
import numpy as np

class CoolerEnv(gym.Env):
    def __init__(self):
        super().__init__()
        # obs: [exit_temp, fan_speed, throughput]
        self.observation_space = spaces.Box(
            low=np.array([200.0, 0.0, 0.0]),
            high=np.array([800.0, 100.0, 200.0]),
            dtype=np.float32
        )
        # action: adjust fan speed [-5, +5]
        self.action_space = spaces.Box(
            low=np.array([-5.0]),
            high=np.array([5.0]),
            dtype=np.float32
        )
        self.reset()

    def reset(self):
        self.exit_temp = 600.0
        self.fan_speed = 50.0
        self.throughput = 150.0
        return np.array([self.exit_temp, self.fan_speed, self.throughput], dtype=np.float32)

    def step(self, action):
        delta_fan = action[0]
        self.fan_speed = np.clip(self.fan_speed + delta_fan, 0, 100)
        # simple dynamics
        self.exit_temp += -0.2 * delta_fan
        reward = -abs(self.exit_temp - 200.0) * 0.01
        obs = np.array([self.exit_temp, self.fan_speed, self.throughput], dtype=np.float32)
        done = False
        return obs, float(reward), done, {}