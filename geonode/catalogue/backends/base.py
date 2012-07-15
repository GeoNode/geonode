
class BaseCatalogueBackend(object):

    def remove_record(self, uuid):
        raise NotImplementedError()

    def create_record(self, item):
        raise NotImplementedError()

    def get_record(self, uuid):
        raise NotImplementedError()

    def search_records(self, keywords, start, limit, bbox):
        raise NotImplementedError()
