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


from panda3d.core import loadPrcFileData, LoaderFileTypeRegistry, Filename, get_model_path

import os

from gltf._loader import GltfLoader

from .dircontext import main_dir
from . import cache
from . import settings


def _remove_loader(extension):
    registry = LoaderFileTypeRegistry.get_global_ptr()
    while True:
        ftype = registry.get_type_from_extension(extension)
        if ftype is None:
            break
        registry.unregister_type(ftype)

def init_mesh_loader():
    if settings.use_assimp:
        loadPrcFileData("", "load-file-type p3assimp\n"
                            "assimp-gen-normals #t\n"
                            "assimp-smooth-normal-angle 90\n")
    # Remove any existing GLTF loaders
    _remove_loader('gltf')
    _remove_loader('glb')
    registry = LoaderFileTypeRegistry.get_global_ptr()
    registry.register_type(GltfLoader)
    path = cache.create_path_for("models")
    loadPrcFileData("", "model-cache-dir %s\n" % path)
    get_model_path().prepend_directory(Filename.from_os_specific(os.path.join(main_dir, 'models')))

def load_panda_model_sync(pattern):
    return loader.loadModel(pattern)
