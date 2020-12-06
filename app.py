import getopt
import logging
import sys
from sys import argv

from flask import Flask, request
#from waitress import serve
from datetime import datetime
import json
import time

from storage.AbstractStorage import get_content_data
from storage.ChainedProvStorage import ChainedProvStorage
from storage.FogStorage import FogStorage
from storage.PostgresqlStorage import PostgresqlStorage

# docker run -p 26657:26657 -it --rm -v "/c/Users/filip/tendermint:/tendermint" tendermint/tendermint node --proxy_app=kvstore
storageEngine = None
app = Flask(__name__)

executions = 2
number_of_threads = 1
mode = 'S'
backend = 'BC'

def main():
    handle_parameters()
    filename = 'executions-logs/B%s-M%s-E%s-T%s-SERVER-%s.log' % (backend, mode, executions, number_of_threads, datetime.now().strftime("%Y%m%d%H%M%S"))
    logging.basicConfig(filename=filename, format="%(asctime)s: %(message)s", level=logging.INFO, datefmt="%H:%M:%S")

    app.run()
    #serve(app, host="0.0.0.0", port=8080)
    # use gevent WSGI server instead of the Flask
    # instead of 5000, you can define whatever port you want.
    #http = WSGIServer(('', 5000), app.wsgi_app)

    # Serve your application
    #http.serve_forever()


@app.route('/')
def welcome_page():
    return 'Welcome to chainedProv. API documentation at https://openprovenance.org/store/help/api/ .'

@app.route('/store/api/v0/documents/', methods=['GET'])
def search():
    #offset, limit, document_name
    document_name = request.args.get('document_name')

    try:
        doc_id = storageEngine.get_id_by_name(document_name)
        return '{"meta": { "limit": 1, "next": null, "offset": 0, "previous": null, "total_count": 1 }, \
                "objects": [ {"created_at": "%s", \
                     "document_name": "%s", \
                     "id": %s, "public": true, "resource_uri": "/store/api/v0/documents/%s/", \
                     "url": "", "views_count": 0 } ] }' % (datetime.now().__str__(), document_name, doc_id, doc_id)

    except Exception as e:
        message, code = e.args
        return message, code
    #content = storageEngine.get_abci_query(doc_id)




@app.route('/store/api/v0/documents/<string:id_rec>', methods=['GET'])
def get_by_id(id_rec):
    json_requested = id_rec.find(".json") != -1
    id_rec = id_rec.replace(".json", "")
    try:
        request_start = time.perf_counter()
        content = storageEngine.get_abci_query(id_rec)
        perf_log("GET_BY_ID", request_start, time.perf_counter())
    except Exception as e:
        message, code = e.args
        return message, code
    if json_requested:
        ret = content
    else:
        ret = prepare_get_json(content, id_rec, datetime.now().__str__(), 'NA')

    return ret


@app.route('/store/api/v0/documents/<string:id_rec>/', methods=['GET'])
def get_data_by_id(id_rec):
    return get_by_id(id_rec)


@app.route('/store/api/v0/documents/', methods=['POST'])
def store():
    logging.debug('Processing POST request...')
    if not request.is_json:
        return "POST should be in application/json format"

    content = request.get_json()
    if len(content) == 0 or "rec_id" not in content:
        return "Attribute rec_id not found!", 400

    rec_id = content['rec_id']

    request_start = time.perf_counter()
    try:
        id, timee, hash, height = storageEngine.store(rec_id, content)
    except Exception as e:
        message, code = e.args
        perf_log("ERROR " + message, request_start, time.perf_counter())
        return message, code

    c = get_content_data(content)

    #stores the full document name associating with the id
    nome = obter_nome_completo(c)
    if nome is not None:
        storageEngine.raw_store(nome, id)
    perf_log("STORE", request_start, time.perf_counter())

    return '{"content": %s, ' \
           '"created_at": "%s", ' \
           '"document_name": "%s", "id": %s, "public": true, "rec_id": "%s", ' \
           '"resource_uri": "/store/api/v0/documents/%s/", "url": null, "views_count": 0,' \
           '"height": "%s"}' \
           % (c, timee, hash, id, rec_id, id, height)


def obter_nome_completo(content):
    doc_recebido = json.loads(content)

    if 'entity' in doc_recebido:
        nome = list(doc_recebido['entity'].keys())[0]
        nome_quebrado = nome.split(":")
        nome = (doc_recebido['prefix'][nome_quebrado[0]]) + nome_quebrado[1]
        return nome
    else:
        return None


def prepare_get_json(content, id, created_at, owner):
    appDict = {
        'document_name': str(id),
        'public': True,
        'owner': owner,
        'created_at': created_at,
        'views_count': 1,
        'content': content
    }
    ret = json.dumps(appDict)
    logging.debug(ret)
    return ret


def perf_log(label, start, end):
    logging.info("%s;%f;%f;%f", label, start, end, end - start)


def handle_parameters():
    global executions, number_of_threads, backend, mode, storageEngine
    help_string = 'app.py -s <BC|BD> -e <# of executions> -t <# of threads> -m <mode>'

    try:
        opts, args = getopt.getopt(argv[1:], "e:t:s:m:h")
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
        elif opt == "-m":
            mode = arg
        elif opt in "-s":
            backend = arg
            if arg in ('BD', 'bd'):
                backend = 'BD'
            elif arg in ('BC', 'bc'):
                backend = 'BC'
            elif arg in ('FOG', 'fog', 'Fog'):
                backend = 'FOG'

    if backend == 'BD':
        storageEngine = PostgresqlStorage(mode)
    elif backend == 'FOG':
        storageEngine = FogStorage(mode)
    else:
        storageEngine = ChainedProvStorage(mode)


if __name__ in ("__main__", "app"):
    main()
else:
    logging.debug(__name__)



## /broadcast_tx_async
## /broadcast_tx_sync
## /broadcast_tx_commit
#These correspond to no-processing, processing through the mempool, and processing through a block, respectively.
#That is, broadcast_tx_async, will return right away without waiting to hear if the transaction is even valid,
#while broadcast_tx_sync will return with the result of running the transaction through CheckTx. Using
#broadcast_tx_commit will wait until the transaction is committed in a block or until some timeout is reached,
#but will return right away if the transaction does not pass CheckTx. The return value for broadcast_tx_commit
#includes two fields, check_tx and deliver_tx, pertaining to the result of running the transaction through those
#ABCI messages.
#The benefit of using broadcast_tx_commit is that the request returns after the transaction is committed (i.e.
#included in a block), but that can take on the order of a second. For a quick result, use broadcast_tx_sync, but
#the transaction will not be committed until later, and by that point its effect on the state may change.

