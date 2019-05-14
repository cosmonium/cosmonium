from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import loadPrcFileData, Filename

from .dircontext import defaultDirContext
from . import cache
from . import settings


def init_mesh_loader():
    if settings.use_assimp:
        loadPrcFileData("", "load-file-type p3assimp\n"
                            "assimp-gen-normals #t\n"
                            "assimp-smooth-normal-angle 90\n")
    path = cache.create_path_for("models")
    loadPrcFileData("", "model-cache-dir %s\n" % path)

def load_model(pattern, callback=None, context=defaultDirContext):
    filename = context.find_model(pattern)
    if filename is not None:
        print("Loading model", filename)
        return loader.loadModel(Filename.from_os_specific(filename).get_fullpath(), callback=callback)
    else:
        print("Model not found", pattern)
        return None

def load_panda_model(pattern, callback=None):
    return loader.loadModel(Filename.from_os_specific(pattern).get_fullpath(), callback=callback)
