import os
import statistics

from reports.report_util import *



col1 = 'Type/Requests per sec'
col2 = '# of requests blocked'
col2_load = "System load"
csv_thread = col1 + ';' + col2 + '\n'
csv_load = col1 + ';' + col2_load + '\n'

mediaLoad = {}
mediaThreads = {}


def main():
    for root, dire, files in os.walk("../executions-logs/"):
        files.sort(key=ordenar)
        for file in files:
            if "CLIENT" in file:
                processar_arquivo(root, file)

    imprimir_csv()
    do_boxplot(csv_thread, col1, col2, 'client_threads.pdf')
    do_boxplot(csv_load, col1, col2_load, 'client_load.pdf')

def processar_arquivo(d, f):
    global csv_thread, csv_load, mediaLoad, mediaThreads
    idx = gerar_idx(f)
    label = idx.replace(";", "/")

    if idx not in mediaLoad:
        mediaLoad[idx] = []
        mediaThreads[idx] = []

    with open(d + f) as fp:
        for line in fp:
            lq = line.split(":")
            if len(lq) >= 5:
                tipo = lq[3].strip(" ")
                if tipo == 'Load':
                    mediaLoad[idx].append(float(lq[4].split(" ")[1].rstrip(".")))
                    mediaThreads[idx].append(float(lq[5]))
                #print("line %s" % (line))

    if len(mediaLoad[idx]) != 0 and len(mediaThreads[idx]) != 0:
        csv_thread += ''.join((label + ";" + str(item) + '\n') for item in mediaThreads[idx])
        csv_load += ''.join((label + ";" + str(item) + '\n') for item in mediaLoad[idx])


def imprimir_csv():
    print("Type;Requests per second;System Load mean (1 min);mean of requests blocked")
    for idx in mediaThreads:
        print("%s;%f;%f" % (idx, statistics.mean(mediaLoad[idx]), statistics.mean(mediaThreads[idx])))



if __name__ == '__main__':
    main()

