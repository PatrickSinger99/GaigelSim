import gymnasium as gym
from simulation import GaigelSim


class GaigelEnv(gym.Env):
    def __init__(self, num_of_players: int):
        super().__init__()

        # Action Space
        self.action_space = gym.spaces.Discrete(5)

        # Observation space
        trump_obs_space = gym.spaces.Discrete(4)
        hand_obs_space = gym.spaces.MultiDiscrete([25]*5)
        stack_obs_space = gym.spaces.MultiDiscrete([25]*(num_of_players-1))

        self.observation_space = gym.spaces.Dict({
            "trump": trump_obs_space,
            "hand": hand_obs_space,
            "stack": stack_obs_space
        })

        # Simulation
        self.sim = GaigelSim(players=num_of_players)
        self.player = self.sim.players.queue[0]  # Select first player for agent

        self.render_mode = None
        self.num_of_players = num_of_players

        self.total_reward = []
        self.episode_reward = 0

    def _get_obs(self):
        sim_state = self.sim.get_state(self.player)
        return {"trump": sim_state["trump_state"], "hand": sim_state["hand_state"], "stack": sim_state["stack_state"]}

    def _get_info(self):
        return {"points": self.player.points}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.total_reward.append(self.episode_reward)
        self.episode_reward = 0

        # New Simulation
        self.sim = GaigelSim(players=self.num_of_players)
        self.player = self.sim.players.queue[0]  # Select first player for agent
        # Initial actions
        self.sim.shuffle_stack()
        self.sim.select_starting_player()
        self.sim.hand_out_cards()

        observation = self._get_obs()
        info = self._get_info()

        return observation, info

    def step(self, action):

        # TODO TEMP FIX FOR MISSING ACTIONS IN SIM
        action += 1

        # Set action for agents player and step
        self.player.set_next_action(action)
        self.sim.step()

        # Forward simulation till agents player is next in line
        self.sim.step_to_player_turn(self.player)

        # Get rl variables
        observation = self._get_obs()
        terminated = self.sim.game_over
        info = self._get_info()

        # Calculate reward
        reward = 1 if self.sim.last_round_winner == self.player else 0
        self.episode_reward += reward

        return observation, reward, terminated, False, info


if __name__ == "__main__":
    env = GaigelEnv(3)
    print(env.observation_space)
    env = gym.wrappers.FlattenObservation(env)
    print(env.observation_space)