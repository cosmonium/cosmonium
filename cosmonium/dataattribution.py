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
