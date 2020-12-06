import hashlib
import logging

import requests
import base64
import random

from datetime import datetime

from storage.AbstractStorage import AbstractStorage
from storage.AbstractStorage import get_content_data

TENDERMINT_URL = 'http://192.168.0.11:26650'

TENDERMINT_CLOUD_URL = 'http://192.168.0.11:26657'
#TENDERMINT_CLUSTER_PORTS = ['26657', '26660', '26662', '26664']


class FogStorage(AbstractStorage):

    @classmethod
    def __init__(self, mode):
        print("Starting Fog server.")

    @classmethod
    def get_tendermint_cloud_url(self):
        return TENDERMINT_CLOUD_URL

    @classmethod
    def get_tendermint_private_url(self):
        return TENDERMINT_URL

    @classmethod
    def get_id_by_name(cls, id_rec):
        return cls.get_abci_query(id_rec)

    @classmethod
    def get_abci_query(cls, id_rec):
        resp = requests.get(cls.get_tendermint_private_url() + '/abci_query?data="%s"' % id_rec)
        if resp.status_code != 200:
            resp = requests.get(cls.get_tendermint_cloud_url() + '/abci_query?data="%s"' % id_rec)

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
        ret = cls.inner_raw_store(id, cc, cls.get_tendermint_private_url(), 'commit')
        cls.store_hash_cloud(id, cc)
        return ret


    @classmethod
    def store_hash_cloud(cls, id, cc):
        hash = hashlib.sha256(cc.encode('utf-8')).hexdigest();
        logging.debug('hash gerado: {0}'.format(hash))
        return cls.inner_raw_store(id, hash, cls.get_tendermint_cloud_url(), 'sync')


    @classmethod
    def raw_store(cls, id, cc):
        cls.inner_raw_store(id, cc, cls.get_tendermint_cloud_url(), 'sync')


    @classmethod
    def inner_raw_store(cls, id, cc, url=TENDERMINT_CLOUD_URL, store_mode='sync'):
        logging.debug('Executando inner_raw_storage para id {0} na url {1} e forma {2}'.format(id, url, store_mode))

        b64body = base64.b64encode('{0}={1}'.format(id, cc).encode('utf-8'))

        data = '{"jsonrpc":"2.0","id":"%s","method":"broadcast_tx_%s","params":{"tx":"%s"}}' % \
               (id, store_mode, b64body.decode('utf-8'))

        logging.debug('Request data: {0}'.format(data))
        headers = {'Content-Type': 'application/json'}

        resp = requests.post(url, data=data, headers=headers)

        if resp.status_code != 200:
            raise Exception("Problem storing the data: %s" % resp.status_code, 400)

        logging.debug('Response data: {0}'.format(resp.text))
        json = resp.json()
        if 'error' in json:
            logging.debug("Retrying")
            resp = requests.post(url, data=data, headers=headers)
            json = resp.json()

        if 'error' in json:
            raise Exception('{"content": { "error": "%s", "error_message": "Problem storing the data: %s- %s" } }' % (
                json['error']['code'], json['error']['message'], json['error']['data']), 500)

        if store_mode == 'commit':
            block = cls.get_block(json['result']['height'], url=url)
            return id, block['result']['block']['header']['time'], block['result']['block']['header']['data_hash'], \
                    json['result']['height']
        else:
            return id, datetime.now().strftime("%Y%m%d%H%M%S"), cc, 0

    @classmethod
    def get_block(cls, height, url=None):
        if url is None:
            url = cls.get_tendermint_cloud_url()
        resp = requests.get(url + '/block?height="%s"' % height)
        if resp.status_code != 200:
            resp = requests.get(cls.get_tendermint_private_url() + '/block?height="%s"' % height)

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
