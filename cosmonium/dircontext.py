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

from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import ExecutionEnvironment

import glob
import os
from copy import deepcopy

class DirContext(object):
    def __init__(self, context=None):
        if context is not None:
            self.category_paths = deepcopy(context.category_paths)
        else:
            self.category_paths={
                                'textures': [],
                                'models': [],
                                'data': [],
                                'scripts': [],
                                'modules': [],
                                'fonts': [],
                                'shaders': [],
                                'doc': [],
                                }

    def add_path(self, category, path):
        if category not in self.category_paths:
            self.category_paths[category] = []
        self.category_paths[category].insert(0, path)

    def add_all_path(self, path):
        for category in self.category_paths.keys():
            self.category_paths[category].insert(0, path)

    def add_all_path_auto(self, path):
        for category in self.category_paths.keys():
            self.category_paths[category].insert(0, os.path.join(path, category))

    def remove_path(self, category, path):
        if category in self.category_paths and path in self.category_paths[category]:
            self.category_paths[category].remove(path)

    def find_file(self, category, pattern):
        if pattern is None: return None
        if os.path.isabs(pattern):
            files = glob.glob(pattern)
            if len(files) > 0:
                return files[0]
        else:
            for res in self.category_paths[category]:
                #print("Looking for", pattern, "in", res)
                full_pattern =  os.path.join(res, pattern)
                files = glob.glob(full_pattern)
                if len(files) > 0:
                    return files[0]
        return None

    def find_texture(self, pattern):
        return self.find_file('textures', pattern)

    def find_model(self, pattern):
        return self.find_file('models', pattern)

    def find_data(self, pattern):
        return self.find_file('data', pattern)

    def find_script(self, pattern):
        return self.find_file('scripts', pattern)

    def find_module(self, pattern):
        return self.find_file('modules', pattern)

    def find_font(self, pattern):
        return self.find_file('fonts', pattern)

    def find_shader(self, pattern):
        return self.find_file('shaders', pattern)

    def find_doc(self, pattern):
        return self.find_file('doc', pattern)

defaultDirContext = DirContext()
main_dir = ExecutionEnvironment.getEnvironmentVariable("MAIN_DIR")
defaultDirContext.add_all_path_auto(main_dir)
defaultDirContext.add_all_path(main_dir)
