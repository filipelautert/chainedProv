# encoding=utf8
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from scipy.stats import norm

def main():
    provstore = pd.read_csv("../provstore_result.csv", encoding='utf-8', delimiter=';') #, parse_dates=['completo'])
    #do_charts(provstore, 'ProvStore')

    chainedprov = pd.read_csv("../chainedprov_result.csv", encoding='utf-8', delimiter=';')  # , parse_dates=['completo'])
    #do_charts(chainedprov, 'ChainedProv')

    provstore['type'] = provstore['type'].apply(func_method)

    print(pd.concat([chainedprov, provstore]))
    do_charts(pd.concat([chainedprov, provstore]), 'Comparison')


def func_method(t):
    if t == 'POST':
        return 'POST ProvStore'
    else:
        return 'GET ProvStore'

def do_charts(dt, name):
    #media = dt['diff'].mean()
    #print(media)
    #dt['Zscore'] = dt['diff']
    #dt.Zscore.plot.kde()

    dt.boxplot(column=['diff'], by='type')

    plt.title(name + " - boxplot by operation")
    plt.suptitle(" ")
    plt.show()

    plt.figure()
    #dt.plot(hue='type', x='start', y='diff')
    #dt['index_col'] = dt.index
    print(dt)
    dt = dt.pivot(index='start', columns='type', values='diff')
    dt = dt.interpolate()
    print(dt)

    dt.plot().legend(loc='lower right', fancybox=True, framealpha=1, shadow=True, borderpad=1)
    #fig, ax = plt.subplots()
    #ax.legend()

    plt.title(name + " - request duration over time (seconds)")
    plt.show()


if __name__ == '__main__':
    main()