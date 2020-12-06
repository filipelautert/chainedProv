from abc import ABC, abstractmethod


class AbstractStorage(ABC):

    @abstractmethod
    def get_id_by_name(self, id_rec):
        pass

    @abstractmethod
    def get_abci_query(self, id_rec):
        pass

    @abstractmethod
    def store(self, rec_id, content):
        pass

    @abstractmethod
    def raw_store(self, id, content):
        pass


def get_content_data(content):
    cc = None
    if 'content' in content:
        cc = content['content']
    elif 'url' in content:
        cc = content['url']
    else:
        raise Exception("Attributes content or url not found!", 400)
    return cc
