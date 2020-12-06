import os
import statistics
from scipy import stats

from reports.report_util import *

mediaDown = {}
mediaUp = {}

col1 = 'Type/Requests per sec'
col2 = 'Retrieve time (sec)'
col2_up = 'Store time (sec)'
csv_down = col1 + ';' + col2 + '\n'
csv_up = col1 + ';' + col2_up + '\n'


def main():
    for r, d, f in os.walk("../executions-logs/"):
        f.sort(key=ordenar)
        for file in f:
            if "SERVER" in file:
                processar_arquivo(r, file)

    imprimir_csv()
    do_boxplot(csv_up, col1, col2_up, 'server_up.pdf')
    do_boxplot(csv_down, col1, col2, 'server_down.pdf')


def processar_arquivo(d, f):
    global mediaUp, mediaDown, csv_up, csv_down
    idx = gerar_idx(f)
    label = idx.replace(";", "/")

    if idx not in mediaUp:
        mediaUp[idx] = []
        mediaDown[idx] = []

    with open(d + f) as fp:
        for line in fp:
            try:
                if 'psycopg2' in line:
                    continue

                lq = line.split(";")
                lq2 = lq[0].split(":")
                if len(lq2) >= 3:
                    tipo = lq2[3].strip(" ")
                    if tipo == 'GET_BY_ID':
                        v = float(lq[3])
                        if v < 10:
                            mediaDown[idx].append(v)
                        else:
                            print("Ignorando valor " + lq[3])
                    elif tipo == 'STORE':
                        v = float(lq[3])
                        if v < 20:
                            mediaUp[idx].append(v)
                        else:
                            print("Ignorando valor " + lq[3])
            except Exception as e:
                print("Linha com defeito: %s" % (line))
                print(e)

    csv_down += ''.join((label + ";" + str(item) + '\n') for item in mediaDown[idx])
    csv_up += ''.join((label + ";" + str(item) + '\n') for item in mediaUp[idx])


def imprimir_csv():

    print("Type;Requests per second; "
          "Retrieve mean (sec); Retrieve median (sec); Retrieve Standard deviation; Retrieve confidence interval;"
          "Store mean (sec); Store median (sec) ; Store Standard deviation; Store confidence interval")
    for idx in mediaUp:
        mediaD = statistics.mean(mediaDown[idx])
        mediaU = statistics.mean(mediaUp[idx])
        medianaD = statistics.median(mediaDown[idx])
        medianaU = statistics.median(mediaUp[idx])

        desvioPadraoD = statistics.pstdev(mediaDown[idx])
        intConfD = stats.norm.interval(0.95, loc=mediaD, scale=desvioPadraoD)

        desvioPadraoU = statistics.pstdev(mediaDown[idx])
        intConfU = stats.norm.interval(0.95, loc=mediaU, scale=desvioPadraoU)


        print("%s;%f;%f;%f;%s;%f;%f;%f;%s"
              % (idx, mediaD, medianaD, desvioPadraoD, intConfD, mediaU,
                  medianaU, desvioPadraoU, intConfU))


if __name__ == '__main__':
    main()
