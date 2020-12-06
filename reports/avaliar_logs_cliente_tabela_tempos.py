import operator
import os
import statistics
import sys
from datetime import datetime
from functools import reduce

from reports.report_util import gerar_idx, ordenar

total = {}
mediaUp = {}
mediaDown = {}

def main():
    for r, d, f in os.walk("../executions-logs/"):
        f.sort(key=ordenar)
        for file in f:
            if "CLIENT" in file:
                processar_arquivo(r, file)

    imprimir_csv()


def processar_arquivo(d, f):
    global total, mediaUp, mediaDown

    inicio = None
    fim = None

    idx = gerar_idx(f)
    if idx not in total:
        total[idx] = []
        mediaDown[idx] = []
        mediaUp[idx] = []

    with open(d + f) as fp:
        for line in fp:
            if line.startswith('Load'):
                continue

            try:
                if 'Starting' in line:
                    ls = line.split(":")
                    inicio = datetime.strptime(("%s:%s:%s" % (ls[0], ls[1], ls[2])), '%H:%M:%S')
                    continue

                if 'finalized' in line:
                    ls = line.split(":")
                    fim = datetime.strptime(("%s:%s:%s" % (ls[0], ls[1], ls[2])), '%H:%M:%S')
                    continue

                lq = line.split(";")
                lq2 = lq[0].split(":")
                if len(lq2) >= 3:
                    tipo = lq2[3].strip(" ")
                    if tipo == 'download':
                        mediaDown[idx].append(float(lq[3]))
                    elif tipo == 'upload':
                        mediaUp[idx].append(float(lq[3]))
            except Exception as e:
                print("line having issues: %s" % (line))
                print(e)
                sys.exit(1)

    if fim is not None and inicio is not None:
        total[idx].append(fim - inicio)


def imprimir_csv():
    global total, mediaUp, mediaDown
    print("Type;Requests per second;Total time ( 10 * 1000 requests);Store mean (sec); Retrive mean  (sec)")
    for idx in total:
        print("%s;%s;%f;%f" % (idx, reduce(operator.add, total[idx]), statistics.mean(mediaUp[idx]), statistics.mean(mediaDown[idx])))


if __name__ == '__main__':
    main()
