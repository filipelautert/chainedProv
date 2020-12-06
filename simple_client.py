import getopt
import logging
import sys
import threading
from datetime import datetime
from sys import argv
import os

from prov.model import ProvDocument
import random
from provstore.api import Api
import time

# API key can be found at https://provenance.ecs.soton.ac.uk/store/account/developer/
PROVSTORE_API_KEY = 'ba4f480ed1058743e40b1c50e3c61ba4654eb4b1'
PROVSTORE_URL = 'https://openprovenance.org/store/api/v0'
CHAINEDPROV_URL = 'http://localhost:5000/store/api/v0'

error_count = 0
executions = 2
number_of_threads = 1
mode = 'S'
backend = 'BC'
url = CHAINEDPROV_URL
total_requests = 0
total_request_time = {"upload": 0.0, "download": 0.0}
log_to_file = True


def main():
    handle_parameters()
    filename = 'executions-logs/B%s-M%s-E%s-T%s-CLIENT-%s.log' % (backend, mode, executions, number_of_threads, datetime.now().strftime("%Y%m%d%H%M%S"))
    if log_to_file:
        logging.basicConfig(filename=filename, format="%(asctime)s: %(message)s", level=logging.INFO, datefmt="%H:%M:%S")
    else:
        logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.ERROR, datefmt="%H:%M:%S")

    threads = list()
    logging.info("Starting test with %d executions and %d requests per second", executions, number_of_threads)

    round = 1
    while executions > 0:
        for index in range(number_of_threads):
            logging.debug("Round %d: created and started %d threads per second.", round, index)
            x = threading.Thread(target=run_requests, args=(False,))
            threads.append(x)
            x.start()
        total_threads_running(threads)
        time.sleep(1)
        round += 1

    while total_threads_running(threads) > 1:
        time.sleep(1)

    for index, thread in enumerate(threads):
        logging.debug("Main    : before joining thread %d.", index)
        thread.join()
        logging.debug("Main    : thread %d done", index)

    logging.info("Test finalized. Total requests: %d Errors: %d Download time: %.4f Upload time: %.4f", total_requests,
                 error_count, total_request_time['download'], total_request_time['upload'])


def total_threads_running(threads):
    total = 0
    for thread in threads:
        if thread.is_alive():
            total += 1

    load1, load5, load15 = os.getloadavg()
    logging.info("Load: %s. Threads: %d", load1, total)
    return total


def run_requests(usar_global):
    global executions, error_count, total_requests

    api = Api(base_url=url, username="filipelautert", api_key=PROVSTORE_API_KEY)

    while executions > 0:
        executions -= 1
        total_requests += 1
        try:
            provstore_document = upload(api, 'document_' + str(executions + 1))
            retrieve(api, provstore_document)
        except:
            perf_log("http_error", 0, 0)
            error_count += 1
            executions += 1
            continue

        if not usar_global:
            break
        #validate(d1, retrieved_document)
        #perf_log("validate", end_down, time.perf_counter())


def perf_log(label, start, end):
    total_time = end - start
    if label in total_request_time:
        total_request_time[label] += total_time

    logging.info("%s;%f;%f;%f", label, start, end, total_time)


def upload(api, name):
    document = create_document()
    start_up = time.perf_counter()
    provstore_document = api.document.create(document, name=name, public=True)
    perf_log("upload", start_up, time.perf_counter())
    return provstore_document


def retrieve(api, provstore_document):
    start_down = time.perf_counter()
    retrieved_document = download(api, provstore_document)
    perf_log("download", start_down, time.perf_counter())
    return retrieved_document


def download(api, provstore_document):
    id = provstore_document.id
    return api.document.get(id)


def validate(document, retrieved_document):
    d2 = retrieved_document.prov
    if document != d2:  # Is it the same document we submitted?
        raise Exception('Documents don\'t match: %s != %s' % (document, d2))


def create_document():
    # Create a new provenance document
    document = ProvDocument()  # d1 is now an empty provenance document
    # Before asserting provenance statements, we need to have a way to refer to the "things"
    # we want to describe provenance (e.g. articles, data sets, people). For that purpose,
    # PROV uses qualified names to identify things, which essentially a shortened representation
    # of a URI in the form of prefix:localpart. Valid qualified names require their prefixes defined,
    # which we is going to do next.

    # Declaring namespaces for various prefixes used in the example
    document.add_namespace('now', 'http://www.provbook.org/nownews/')
    document.add_namespace('nowpeople', 'http://www.provbook.org/nownews/people/')
    document.add_namespace('bk', 'http://www.provbook.org/ns/#')

    # Entity: now:employment-article-v1.html
    e1 = document.entity('now:employment-article-v1.html')
    e1.add_attributes({'prov:value': 'Conteudo do HTML'})
    document.agent('nowpeople:Filipe')

    # Attributing the article to the agent
    document.wasAttributedTo(e1, 'nowpeople:Filipe_' + str(random.randint(1000, 1070000000)))

    # add more namespace declarations
    document.add_namespace('govftp', 'ftp://ftp.bls.gov/pub/special.requests/oes/')
    document.add_namespace('void', 'http://vocab.deri.ie/void#')

    # 'now:employment-article-v1.html' was derived from at dataset at govftp
    document.entity('govftp:oesm11st.zip', {'prov:label': 'employment-stats-2011', 'prov:type': 'void:Dataset'})
    document.wasDerivedFrom('now:employment-article-v1.html', 'govftp:oesm11st.zip')

    # Adding an activity
    document.add_namespace('is', 'http://www.provbook.org/nownews/is/#')
    document.activity('is:writeArticle')
    # Usage and Generation
    document.used('is:writeArticle', 'govftp:oesm11st.zip')
    document.wasGeneratedBy('now:employment-article-v1.html', 'is:writeArticle')

    #print("Document prepared.")
    # What we have so far (in PROV-N)
    logging.debug(document.serialize(indent=2))
    # d1.serialize('article-prov.json') # write to file
    return document


def handle_parameters():
    global executions, number_of_threads, backend, mode, log_to_file
    help_string = 'app.py -e <# of executions> -t <# of threads>'
    try:
        opts, args = getopt.getopt(argv[1:], "e:t:m:s:h:l")
    except getopt.GetoptError:
        print(help_string)
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(help_string)
            sys.exit()
        elif opt == "-e":
            executions = int(arg)
        elif opt == "-t":
            number_of_threads = int(arg)
        elif opt == "-s":
            backend = arg
        elif opt == "-m":
            mode = arg
        elif opt == "-l":
            if arg == 'f':
                log_to_file = False


if __name__ == "__main__":
    main()
