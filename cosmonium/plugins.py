#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2020 Laurent Deru.
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

import importlib
import os

class ModuleLoader():
    def __init__(self):
        self.cache = {}

    def load_module(self, module_path):
        if not module_path in self.cache:
            print("Loading", module_path)
            module_name, _ = os.path.splitext(os.path.basename(module_path))
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.cache[module_path] = module
        return self.cache[module_path]

moduleLoader = ModuleLoader()
