import gym
from gym import spaces
import numpy as np

class MixEnv(gym.Env):
    def __init__(self):
        super().__init__()
        # obs: [CaO/SiO2, moisture, feed_rate]
        self.observation_space = spaces.Box(
            low=np.array([0.8, 0.0, 50.0]),
            high=np.array([2.0, 25.0, 200.0]),
            dtype=np.float32
        )
        # action: adjust CaO/SiO2 ratio [-0.05,+0.05]
        self.action_space = spaces.Box(
            low=np.array([-0.05]),
            high=np.array([0.05]),
            dtype=np.float32
        )
        self.reset()

    def reset(self):
        self.ratio = 1.5
        self.moisture = 5.0
        self.feed_rate = 100.0
        return np.array([self.ratio, self.moisture, self.feed_rate], dtype=np.float32)

    def step(self, action):
        delta = action[0]
        self.ratio = np.clip(self.ratio + delta, 0.8, 2.0)
        # quality proxy
        deviation = abs(self.ratio - 1.6)
        reward = -deviation * 0.1
        obs = np.array([self.ratio, self.moisture, self.feed_rate], dtype=np.float32)
        done = False
        return obs, float(reward), done, {}