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

from panda3d.core import loadPrcFileData, Filename, get_model_path

import sys
import os

if sys.version_info[0] >= 3:
    import gltf

from .dircontext import defaultDirContext, main_dir
from . import cache
from . import settings


def init_mesh_loader():
    if settings.use_assimp:
        loadPrcFileData("", "load-file-type p3assimp\n"
                            "assimp-gen-normals #t\n"
                            "assimp-smooth-normal-angle 90\n")
    if sys.version_info[0] >= 3:
        gltf.patch_loader(None)
    path = cache.create_path_for("models")
    loadPrcFileData("", "model-cache-dir %s\n" % path)
    get_model_path().prepend_directory(Filename.from_os_specific(os.path.join(main_dir, 'models')))

def load_model(pattern, callback=None, context=defaultDirContext):
    filename = context.find_model(pattern)
    if filename is not None:
        print("Loading model", filename)
        return loader.loadModel(Filename.from_os_specific(filename).get_fullpath(), callback=callback)
    else:
        print("Model not found", pattern)
        return None

def load_panda_model(pattern, callback=None):
    return loader.loadModel(pattern, callback=callback)
