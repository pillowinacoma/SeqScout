import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def read_data(filename):
    results = []
    with open(filename) as f:
        _ = f.readline()

        for line in f:
            _, ram, x_time = line.split(' ')
            results.append(float(ram))
    return results

misere_mem = read_data('./mem_misere.dat')
bs_mem = read_data('./mem_bs.dat')
misere_hill_mem = read_data('./mem_misere_hill.dat')

x_axis = [0.1 * i for i in range(len(misere_mem))]

data = {'misere': misere_mem,
            'misereHill': misere_hill_mem,
            'beamSearch-30': bs_mem}

df = pd.DataFrame(data=data, index=x_axis)
ax = sns.lineplot(data=df)

# ax = sns.lineplot(x='x', y=('misereHill', 'misere'), data=df)

ax.set(xlabel='Temps(s)', ylabel='Consommation mémoire (Mo)')

plt.show()