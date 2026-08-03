#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


import builtins
import os

from gltf import GltfSettings
from gltf._loader import GltfLoader
from panda3d.core import Filename, LoaderFileTypeRegistry, get_model_path, loadPrcFileData

from . import cache, settings
from .cmod.cmod_loader import CmodLoader


def _remove_loader(extension):
    registry = LoaderFileTypeRegistry.get_global_ptr()
    while True:
        ftype = registry.get_type_from_extension(extension)
        if ftype is None:
            break
        registry.unregister_type(ftype)


def set_physics_engine(engine_name):
    GltfSettings.collision_shapes = engine_name


def init_mesh_loader(main_dir):
    if settings.use_assimp:
        loadPrcFileData("", "load-file-type p3assimp\n" "assimp-gen-normals #t\n" "assimp-smooth-normal-angle 90\n")

    registry = LoaderFileTypeRegistry.get_global_ptr()

    # Remove any existing GLTF loaders
    _remove_loader('gltf')
    _remove_loader('glb')
    # Register GLTF loader
    registry.register_type(GltfLoader)

    # Remove any existing CMOD loaders
    _remove_loader('cmod')
    # Register CMOD loader
    registry.register_type(CmodLoader())

    path = cache.create_path_for("models")
    loadPrcFileData("", "model-cache-dir %s\n" % path)
    get_model_path().prepend_directory(Filename.from_os_specific(os.path.join(main_dir, 'models')))


def load_panda_model_sync(pattern):
    return builtins.base.loader.loadModel(pattern)
