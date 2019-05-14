from __future__ import print_function
from __future__ import absolute_import

from ..textures import InvalidTextureSource
from ..dircontext import defaultDirContext
from .textures import CelestiaVirtualTextureSource
from . import config_parser

import sys
import os

def instanciate_vt(filename, context, item_name, item_data):
    image_directory = None
    base_split = 0
    tile_size = 0
    tile_type = 'dds'
    tile_prefix = 'tx_'
    
    for (key, value) in item_data.items():
        if key == 'ImageDirectory':
            image_directory = value
        elif key == 'BaseSplit':
            base_split = value
        elif key == 'TileSize':
            tile_size = value
        elif key == 'TileType':
            tile_type = value
        elif key == 'TilePrefix':
            tile_prefix = value
        else:
            print("Key of VirtualTexture", key, "not supported")
    if base_split != 0:
        print("WARNING: BaseSplit different than 0 not yet supported")
    path = os.path.join(os.path.dirname(filename), image_directory)
    vt = CelestiaVirtualTextureSource(root=path, ext=tile_type, size=tile_size, prefix=tile_prefix, context=context)
    return vt


def instanciate_item(filename, context, disposition, item_type, item_name, item_parent, item_alias, item_data):
    if disposition != 'Add':
        print("Disposition", disposition, "not supported")
        return
    if item_type == 'VirtualTexture':
        return instanciate_vt(filename, context, item_name, item_data)
    else:
        print("Type", item_type, "not supported")
        return

def parse_file(filename, context=defaultDirContext):
    filepath = context.find_data(filename)
    if filepath is None:
        print("Can not find file", filename)
        return InvalidTextureSource()
    try:
        data = open(filepath).read()
    except IOError:
        print("Could not read file", filepath)
        return InvalidTextureSource()
    items = config_parser.parse(data)
    if items and len(items) == 1:
        return instanciate_item(filepath, context, *items[0])
    else:
        print("Invalid file", filepath)
        return InvalidTextureSource()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        parse_file(sys.argv[1])
