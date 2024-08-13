import torch

from genetic_algorithm_neural_network import GeneticAlgorithmNN, IndividualNN
from xor_calculation.xor_nn import XorNN


X_TRAIN = torch.tensor([
    [0, 0],  # 0 xor 0 == 0
    [0, 1],  # 0 xor 1 == 1
    [1, 0],  # 1 xor 0 == 1
    [1, 1],  # 1 xor 1 == 0
]).float()


class XorIndividualNN(IndividualNN):
    def __init__(self, configs, network_class, network=None):
        super().__init__(configs, network_class, network)

    def display(self):
        res = self.chromosome(X_TRAIN.to(self.device)).cpu().detach().numpy()
        print("0 xor 0 =", res[0])
        print("0 xor 1 =", res[1])
        print("1 xor 0 =", res[2])
        print("1 xor 1 =", res[3])

    def calc_fitness(self):
        conf = 0.0
        res = self.chromosome(X_TRAIN.to(self.device)).cpu().detach().numpy()
        conf += res[0][0].item()
        conf += res[1][1].item()
        conf += res[2][1].item()
        conf += res[3][0].item()
        return conf


class XorCalculationGANN(GeneticAlgorithmNN):
    def __init__(self, configs: dict):
        super().__init__(configs)

    def init_population(self):
        for _ in range(self.population_size):
            self.population.append(XorIndividualNN(self.configs, XorNN))

    def can_terminate(self, evolved, gen):
        return gen >= self.max_gen


if __name__ == "__main__":
    configs = {
        "population_size": 500,
        "num_parents": 300,
        "mutation_type": "layer",
        "mutation_rate": 0.01,
        "mutation_strength": 0.1,
        "elitism": 0.05,
        "max_gen": 100,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "save_path": "./weights/xor_calc.pth",
        "debug": True
    }
    xor = XorCalculationGANN(configs)
    xor.run()
    goat = XorIndividualNN(configs, XorNN)
    goat.load_weights("./weights/xor_calc.pth")
    goat.display()

