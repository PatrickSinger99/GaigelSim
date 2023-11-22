from environment import GaigelEnv
from stable_baselines3 import PPO
import matplotlib.pyplot as plt

if __name__ == "__main__":
    env = GaigelEnv(num_of_players=3)
    ppo_model = PPO("MultiInputPolicy", env, verbose=1)
    ppo_model.learn(total_timesteps=100000)

    plt.rcParams["figure.figsize"] = (10, 5)
    plt.plot(env.total_reward, color="red")
    plt.title("Learning Curve")
    plt.xlim(0, len(env.total_reward))
    plt.ylabel("Total Reward per Simulation")
    plt.xlabel("Simulation Round")
    plt.show()
    