#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#
from .utils import int_to_color

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
                result.append((value.get_exact_name(key), value))
        return result

class GlobalObjectsDB(object):
    def __init__(self):
        self.db = {}
        self.oids = []

    def add(self, body):
        body.oid = len(self.oids)
        body.oid_color = int_to_color(body.oid)
        self.oids.append(body)
        for name in body.names:
            self.db[name.upper()] = body
        for name in body.source_names:
            self.db[name.upper()] = body

    def get(self, name):
        return self.db.get(name.upper(), None)

    def get_oid(self, oid):
        if oid < len(self.oids):
            return self.oids[oid]
        else:
            return None

    def remove(self, body):
        for name in body.names:
            self.db.pop(name.upper(), None)
        self.oids[body.oid] = None

    def startswith(self, text):
        text = text.upper()
        result = []
        for (key, value) in self.db.items():
            if key.startswith(text):
                result.append((value.get_exact_name(key), value))
        return result

objectsDB = GlobalObjectsDB()
