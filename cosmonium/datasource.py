from __future__ import print_function
from __future__ import absolute_import

class DataSource():
    def __init__(self, name, copyright=None, license=None, url=None):
        self.name = name
        self.copyright = copyright
        self.license = license
        self.url = url

class DataSourceDB():
    def __init__(self):
        self.db = {}

    def add_source(self, source_id, source):
        self.db[source_id] = source

    def get_source(self, source_id):
        if source_id is None: return None
        return self.db.get(source_id, None)

dataSourceDB = DataSourceDB()
