#!/usr/bin/python3
import numpy as np
import multiprocessing as mp
import copy
from load_data import load_data_form_file
import sys
import time
import random
np.set_printoptions(linewidth=np.inf)


class LegoInformation:
    initial_lego = None
    lego_price = None
    lego_models = None
    nb_models = None
    nb_lego = None

    def __init__(self, initial_lego, lego_price, lego_models):
        self.initial_lego = initial_lego
        self.lego_price = lego_price
        self.lego_models = lego_models
        self.nb_models = len(lego_models)
        self.nb_lego = len(initial_lego)


def is_valid_model(lego_information=LegoInformation, index_model=0, current_lego=[]):
    for i in range(0, lego_information.nb_lego):
        if current_lego[i] > 0 and lego_information.lego_models[index_model][i] > 0:
            return True
    return False


def greedy_algorithm(current_lego, lego_information, solution):
    '''
    This algorithm is intended to run in another process
    '''
    #print(current_lego)
    best_cost = sys.maxsize * -1
    ignore_indexes = []
    while np.min(current_lego) > 0 or len(ignore_indexes) >= lego_information.nb_models:
        costs = np.dot(lego_information.lego_models,np.transpose(lego_information.lego_price/current_lego))
        costs = np.array([costs[i]  if i not in ignore_indexes else float('inf') for i in range(len(costs)) ])
        min_idx = np.argmin(costs)
        print(costs)
        if is_valid_model(lego_information=lego_information, index_model=min_idx, current_lego=current_lego):
            #print(lego_information.lego_models[min_idx])
            updated_lego = np.subtract(current_lego, lego_information.lego_models[min_idx])
            cost = np.dot(current_lego, lego_information.lego_price)
            if cost > best_cost:
                current_lego = updated_lego
                solution[min_idx] += 1
                best_cost = cost
                print("new_best")
            else: 
                ignore_indexes.append(min_idx) 
        else: 
            ignore_indexes.append(min_idx)
    return solution, current_lego


def random_valid_index_model(lego_information=LegoInformation, current_lego=[]):
    valid_index = []
    for i in range(0, lego_information.nb_lego):
        if current_lego[i] > 0:
            for j in range(0, lego_information.nb_models):
                if lego_information.lego_models[j][i] > 0:
                    valid_index.append(j)
    return valid_index[np.random.randint(0, len(valid_index))]


# todo remove duplicate code
def genetic_algorithm(lego_information=LegoInformation, start=time.time()):
    # solution_greedy =mp.Array('i', lego_information.nb_models)
    # start_solution=mp.Array('i', lego_information.nb_models)
    # # Start greedy algorithm 
    # greedy_process = mp.Process(target=greedy_algorithm, args=(start_solution, lego_information, solution_greedy))
    # to compare models

    best_solution_models = np.zeros(lego_information.nb_models)
    best_solution_price = -1 * sys.maxsize
    nb_species_by_iteration = 100
    # crossover
    parent_a = -1
    parent_b = -1
    previous_parent_a_cost = 0
    mutation_probability = 0.01

    population_models = np.zeros((nb_species_by_iteration, lego_information.nb_models))
    population_models_cost = np.zeros(nb_species_by_iteration)

    best_solution_models, current_lego = greedy_algorithm(np.copy(lego_information.initial_lego), lego_information, best_solution_models)
    best_solution_price = np.dot(current_lego, lego_information.lego_price)
    print("{} : {}".format(repr(best_solution_models), best_solution_price))
    print(current_lego)
    while True:
        for j in range(0, nb_species_by_iteration):
            # IMPORTANT : REMOVE THIS FOR FINAL SUBMISSION
            current_time = time.time() - start
            if current_time > 60*3:
                nb_minute = int(current_time/60)
                nb_sec = current_time % 60
                print("Total time {}:{} | best solution : {}".format(nb_minute, nb_sec, best_solution_price))
                return

            models_used_by_generation = np.zeros(lego_information.nb_models).astype("int32")
            if parent_a != -1:
                for h in range(0, lego_information.nb_models):
                    value_to_set = population_models[parent_a][h]
                    if population_models[parent_b][h] < population_models[parent_a][h]:
                        value_to_set = population_models[parent_b][h]
                    if value_to_set > 0:
                        models_used_by_generation[h] = value_to_set

                # mutation
                if np.random.random() < mutation_probability:
                    random_index_for_mutation = random.choice([
                        index for index in range(0, lego_info.nb_models) if models_used_by_generation[index] > 0
                    ])
                    models_used_by_generation[random_index_for_mutation] -= 1

            updated_legos = np.copy(lego_information.initial_lego)
            for model_index in range(0, lego_information.nb_models):
                if models_used_by_generation[model_index] > 0:
                    updated_legos -= lego_information.lego_models[model_index] * models_used_by_generation[model_index]

            while not current_lego_done(updated_legos):
                test_updated_lego = None
                # while True:
                #     random_index = np.random.randint(0, len(lego_information.lego_models) - 1)
                #     test_updated_lego = np.subtract(updated_legos, lego_information.lego_models[random_index])
                #     if change_was_made(updated_legos, test_updated_lego):
                #         models_used_by_generation[random_index] += 1
                #         break
                # updated_legos = np.copy(test_updated_lego)
                # same logic but is less effecient
                model_index = random_valid_index_model(lego_information=lego_information, current_lego=updated_legos)
                updated_legos = np.subtract(updated_legos, lego_information.lego_models[model_index])
                models_used_by_generation[model_index] += 1

            cost_generation = np.dot(updated_legos, lego_information.lego_price)
            if cost_generation > best_solution_price:
                best_solution_price = cost_generation
                best_solution_models = np.copy(models_used_by_generation)
                print("{} : {}".format(repr(best_solution_models), best_solution_price))

            population_models[j] = models_used_by_generation
            population_models_cost[j] = cost_generation

        # todo find a better way to get top 2
        parent_a = np.argmax(population_models_cost)
        if population_models_cost[parent_a] <= previous_parent_a_cost:
            mutation_probability += 0.01 if mutation_probability < 1 else 0
        else:
            mutation_probability -= 0.01 if mutation_probability > 0 else 0
        previous_parent_a_cost = population_models_cost[parent_a]
        population_models_cost[parent_a] = sys.maxsize * -1
        parent_b = np.argmax(population_models_cost)
        # population_models_cost[parent_a] = original_value


def almost_done(current_lego):
    nb_negative_lego = 0
    for i in range(0, len(current_lego)):
        if current_lego[i] < 0:
            nb_negative_lego += 1
    return len(current_lego) - nb_negative_lego <= 1


def change_was_made(current_legos, new_current_legos):
    positive_equals = True
    for i in range(0, len(current_legos)):
        if current_legos[i] > 0 and current_legos[i] != new_current_legos[i]:
            positive_equals = False
    return not positive_equals


def current_lego_done(current_legos):
    for i in range(0, len(current_legos)):
        if current_legos[i] > 0:
            return False
    return True


if __name__ == "__main__":
    start = time.time()
    file_name = "/mnt/c/Users/pinsz/Documents/COURS/Hiver2019/INF8775/TPs/genetic_algorithm/exemplaires/LEGO_50_50_1000"
    lego, price, models = load_data_form_file(file_name)
    lego_info = LegoInformation(lego, price, models)
    genetic_algorithm(lego_information=lego_info, start=start)
