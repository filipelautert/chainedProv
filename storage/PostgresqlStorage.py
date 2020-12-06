import hashlib
from configparser import ConfigParser
from contextlib import contextmanager
from datetime import datetime

from psycopg2.pool import SimpleConnectionPool
from storage.AbstractStorage import AbstractStorage, get_content_data


class PostgresqlStorage(AbstractStorage):

    connectionpool = None

    def __init__(self, mode):
        print("Ignoring server mode requested: %s" % mode)
        # pool define with 100 live connections
        self.connectionpool = SimpleConnectionPool(1, 100, dsn=self.config())

    def get_id_by_name(self, id_rec):
        return self.get_data(id_rec, 'select data from provenance where rec_id = %s')

    def get_abci_query(self, id_rec):
        return self.get_data(id_rec, 'select data from provenance where id = %s')

    def get_data(self, id_rec, sql):
        # deve retornar o conteúdo json
        with self.getConn() as conn:
            cur = conn.cursor()
            cur.execute(sql, (id_rec,))
            # display the PostgreSQL database server version
            return cur.fetchone()[0]

    def store(self, rec_id, content):
        # deve retornar: id gerado, time da operação, hash do dado, height do bloco
        cc_content = get_content_data(content)
        with self.getConn() as conn:
            cur = conn.cursor()
            data = datetime.now()
            data_hash = hashlib.sha256(cc_content.encode('utf-8')).hexdigest();
            cur.execute('insert into provenance(rec_id, data, date, hash) values (%s, %s, %s, %s) RETURNING id',
                        (rec_id, cc_content, data, data_hash))
            gen_id = cur.fetchone()[0]
            conn.commit()
            return gen_id, data.__str__(), data_hash, gen_id

    def raw_store(self, id, content):
        pass

    def config(self, filename='database.ini', section='postgresql'):
        parser = ConfigParser()
        parser.read(filename)

        # get section, default to postgresql
        db = ""
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db += "%s='%s' " % (param[0], param[1])
        else:
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))

        return db

    @contextmanager
    def getConn(self):
        con = self.connectionpool.getconn()
        try:
            yield con
        finally:
            self.connectionpool.putconn(con)


# function for testing purpose
def main():
    storage = PostgresqlStorage()
    id, time, hash, height = storage.store('Salada', {'content': '{ "author": "filipe" }'})
    print('Hash: {0}'.format(hash))
    print(storage.get_abci_query(id))


if __name__ == '__main__':
    main()
