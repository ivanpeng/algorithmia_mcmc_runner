import json
import random


def generate_samples(nsamples = 300):
    stat_arr = []
    for i in range(nsamples):
        stock_1_dist = random.normalvariate(3, 3)
        stock_2_dist = random.normalvariate(5, 4)
        bond_1_dist = random.expovariate(4.2)
        bond_2_dist = random.expovariate(5)

        day_stat = {
            'returns_stock_1': stock_1_dist,
            'returns_stock_2': stock_2_dist,
            'returns_bond_1': bond_1_dist,
            'returns_bond_2': bond_2_dist
        }
        stat_arr.append(day_stat)
    return stat_arr


if __name__ == "__main__":
    data = generate_samples()
    with open("temp.json", 'w') as f:
        json.dump(data, f)