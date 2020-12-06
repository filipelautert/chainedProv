import logging

import requests
import base64
import random

from storage.AbstractStorage import AbstractStorage
from storage.AbstractStorage import get_content_data

#TENDERMINT_URL = 'http://192.168.99.100:26657'
TENDERMINT_URL = 'http://192.168.0.11:26657'

TENDERMINT_CLUSTER_URL = 'http://192.168.0.11:'
TENDERMINT_CLUSTER_PORTS = ['26657', '26660', '26662', '26664']


class ChainedProvStorage(AbstractStorage):

    mode = None # S ou C
    cluster_port_idx = 0

    @classmethod
    def __init__(self, mode):
        if mode not in ('S', 'C'):
            raise Exception('Mode must be in S ou C')

        self.mode = mode
        print("Starting server in mode %s" % self.mode)

    @classmethod
    def get_tendermint_url(self):
        if self.mode == 'S':
            return TENDERMINT_URL

        url = TENDERMINT_CLUSTER_URL + TENDERMINT_CLUSTER_PORTS[self.cluster_port_idx]
        if (len(TENDERMINT_CLUSTER_PORTS) - 1) > self.cluster_port_idx:
            self.cluster_port_idx = (self.cluster_port_idx + 1)
        else:
            self.cluster_port_idx = 0
        return url


    @classmethod
    def get_id_by_name(cls, id_rec):
        return cls.get_abci_query(id_rec)

    @classmethod
    def get_abci_query(cls, id_rec):
        resp = requests.get(cls.get_tendermint_url() + '/abci_query?data="%s"' % id_rec)
        if resp.status_code != 200:
            raise Exception("Error retrieving key: %s" % resp.status_code, 500)

        json = resp.json()
        if 'error' in json:
            raise Exception('{"content": { "error": "%s", "error_message": "Problem retrieving key: %s- %s" } }' % (
            json['error']['code'], json['error']['message'], json['error']['data']), 500)

        # return json
        return base64.b64decode(json['result']['response']['value'], validate=True).decode('utf-8')

    @classmethod
    def store(cls, rec_id, content):
        id = cls.generate_id(rec_id)
        cc = get_content_data(content)
        return cls.raw_store(id, cc)


    @classmethod
    def raw_store(cls, id, cc):
        url = cls.get_tendermint_url()
        b64body = base64.b64encode('{0}={1}'.format(id, cc).encode('utf-8'))

        data = '{"jsonrpc":"2.0","id":"%s","method":"broadcast_tx_commit","params":{"tx":"%s"}}' % \
               (id, b64body.decode('utf-8'))

        logging.debug('Request data: {0}'.format(data))
        headers = {'Content-Type': 'application/json'}

        resp = requests.post(url, data=data, headers=headers)

        if resp.status_code != 200:
            raise Exception("Problem storing the data: %s" % resp.status_code, 400)

        logging.debug('Response data: {0}'.format(resp.text))
        json = resp.json()
        if 'error' in json:
            url = cls.get_tendermint_url()
            logging.debug("Retrying")
            resp = requests.post(url, data=data, headers=headers)
            json = resp.json()

        if 'error' in json:
            raise Exception('{"content": { "error": "%s", "error_message": "Problem storing the data: %s- %s" } }' % (
                json['error']['code'], json['error']['message'], json['error']['data']), 500)

        block = cls.get_block(json['result']['height'], url=url)

        return id, block['result']['block']['header']['time'], block['result']['block']['header']['data_hash'], \
               json['result']['height']

    @classmethod
    def get_block(cls, height, url=None):
        if url is None:
            url = cls.get_tendermint_url()
        resp = requests.get(url + '/block?height="%s"' % height)
        if resp.status_code != 200:
            raise Exception("Error retrieving block: %s" % resp.status_code, 500)

        json = resp.json()
        if 'error' in json:
            raise Exception('{"content": { "error": "%s", "error_message": "Problem retrieving block: %s- %s" } }' % (
            json['error']['code'], json['error']['message'], json['error']['data']), 500)

        return json

    @classmethod
    def generate_id(cls, rec_id):
        id_gen = random.randint(1000, 100000000)
        for code in map(ord, rec_id):
            id_gen = id_gen + code
        logging.debug("generated id: %d" % id_gen)
        return id_gen
