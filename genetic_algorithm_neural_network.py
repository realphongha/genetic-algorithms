import random
import os

import torch
torch.set_grad_enabled(False)
import numpy as np

from genetic_algorithm import Individual, GeneticAlgorithm


def model_to_chromosome(model):
    chromosome = []
    for params in model.parameters():
        chromosome.append(params.data.cpu().numpy().flatten())
    return torch.tensor(np.concatenate(chromosome))


def chromosome_to_model(chromosome, model):
    chromosome = torch.tensor(chromosome).cuda()
    start = 0
    for param in model.parameters():
        param_size = param.numel()
        param.data = chromosome[start:start+param_size].view(param.shape).float()
        start += param_size


class IndividualNN(Individual):
    def __init__(self, configs, network_class, network=None):
        super().__init__(configs)
        self.network_class = network_class
        self.device = configs["device"]
        self.uniform_a = -1.0
        self.uniform_b = 1.0
        if network is None:
            self.random_init()
        else:
            self.chromosome = network
        self.chromosome.to(self.device)
        self.chromosome.eval()
        self.fitness = self.calc_fitness()

    def load_weights(self, path, calc_fitness=False):
        network = self.network_class(self.configs)
        network.load_state_dict(torch.load(path))
        print("Loaded weights from %s" % path)
        self.chromosome = network
        self.chromosome.to(self.device)
        self.chromosome.eval()
        if calc_fitness:
            self.fitness = self.calc_fitness()

    def random_init(self):
        self.chromosome = self.network_class(self.configs)
        self.chromosome.init_weights(self.uniform_a, self.uniform_b)

    def cross(self, other):
        child_net = self.network_class(self.configs)
        for p1, p2, c in zip(
            self.chromosome.parameters(), other.chromosome.parameters(), child_net.parameters()
        ):
            if random.random() < 0.5:
                c.data = p1.data.clone()
            else:
                c.data = p2.data.clone()
        yield self.__class__(self.configs, self.network_class, child_net)

    def mutate_param(self):
        if random.random() > self.mutation_rate:
            return
        params = random.choice(list(self.chromosome.parameters()))
        flat = params.data.view(-1)
        idx = random.randint(0, flat.shape[0] - 1)
        flat[idx] = random.uniform(self.uniform_a, self.uniform_b)
        # re-calculate fitness after mutation
        self.fitness = self.calc_fitness()


    def mutate_layer(self):
        for p in self.chromosome.parameters():
            if random.random() > self.mutation_rate:
                continue
            sh = p.data.shape
            randn_mask = torch.randn(sh) * self.mutation_strength
            p.data += randn_mask.to(self.device)
        # re-calculate fitness after mutation
        self.fitness = self.calc_fitness()

    def mutate(self):
        if self.configs["mutation_type"] == "layer":
            self.mutate_layer()
        elif self.configs["mutation_type"] == "param":
            self.mutate_param()
        else:
            raise NotImplementedError(
                f"{self.configs['mutation_type']} not implemented!"
            )

    def __hash__(self):
        return hash(model_to_chromosome(self.chromosome))


class GeneticAlgorithmNN(GeneticAlgorithm):
    INDIVIDUAL_CLASS = IndividualNN
    NN_CLASS = None

    def __init__(self, configs: dict):
        super().__init__(configs)
        self.save_path = configs["save_path"]

    def init_population(self):
        for _ in range(self.population_size):
            self.population.append(
                self.INDIVIDUAL_CLASS(self.configs, self.NN_CLASS)
            )

    def selection(self):
        parents = self.population[:self.num_parents]
        return parents

    def crossover(self, population):
        children = []
        while True:
            parent1 = random.choice(population)
            parent2 = random.choice(population)
            for child in parent1.cross(parent2):
                children.append(child)
                if len(children) >= self.population_size:
                    break
            if len(children) >= self.population_size:
                break
        return children

    def mutation(self, population):
        for individual in population:
            individual.mutate()
        return population

    def run(self):
        super().run()
        if self.save_path is not None:
            save_dir = os.path.split(self.save_path)[0]
            os.makedirs(save_dir, exist_ok=True)
            torch.save(self.goat.chromosome.state_dict(), self.save_path)
            print("Saved the GOAT to %s" % self.save_path)

