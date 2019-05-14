class ObjectsDB(object):
    def __init__(self):
        self.db = {}

    def add(self, body):
        for name in body.names:
            self.db[name.upper()] = body

    def get(self, name):
        return self.db.get(name.upper(), None)

    def remove(self, body):
        for name in body.names:
            self.db.pop(name.upper(), None)

    def startswith(self, text):
        text = text.upper()
        result = []
        for (key, value) in self.db.items():
            if key.startswith(text):
                result.append(value)
        return result
objectsDB = ObjectsDB()
