from __future__ import print_function
from __future__ import absolute_import

from . import settings

import os

def init_cache():
    print("Cache directory:", settings.cache_dir)

def create_path_for(*path):
    final_path = os.path.join(settings.cache_dir, *path)
    if not os.path.isdir(final_path):
        os.makedirs(final_path)
    return final_path