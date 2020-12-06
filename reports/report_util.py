from io import StringIO

import pandas as pd
import matplotlib.pyplot as plt

import seaborn as sns

def ordenar(f):
    nome_s = f.split("-")
    if nome_s[1] == 'MS':  # single deve vir primeiro
        nome_s[1] = "MA"

    return '-'.join(nome_s)


def gerar_idx(nome_arquivo):
    nome_s = nome_arquivo.split("-")
    return "%s;%s" % \
          (('BC1' if nome_s[1] == 'MS' else ('CLOUD' if nome_s[1] == 'MC' else ('FOG' if nome_s[1] == 'MF' else nome_s[1]))),
           nome_s[3].replace("T", ""))


def do_boxplot(file, colx, coly, name):
    sns.set(rc={'figure.figsize': (11.7, 8.27)})
    sns.set(style="ticks", palette="pastel")
    #print("plotting")
    dt = pd.read_csv(StringIO(file), sep=';')
    #print(dt.head())
    sns.boxplot(x=colx, y=coly, data=dt, showmeans=True)
    #sns.despine(offset=10, trim=True)

    plt.savefig('../img/' + name)
    plt.show()
