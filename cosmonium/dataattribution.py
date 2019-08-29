from __future__ import print_function
from __future__ import absolute_import

class DataAttribution():
    def __init__(self, name, copyright=None, license=None, url=None):
        self.name = name
        self.copyright = copyright
        self.license = license
        self.url = url

class DataAttributionDB():
    def __init__(self):
        self.db = {}

    def add_attribution(self, attribution_id, attribution):
        self.db[attribution_id] = attribution

    def get_attribution(self, attribution_id):
        if attribution_id is None: return None
        return self.db.get(attribution_id, None)

dataAttributionDB = DataAttributionDB()
