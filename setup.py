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

from setuptools import setup
import sys

# Add source/ directory to import path to be able to load the c++ libraries
sys.path.insert(0, 'source')
# Add third-party/ directory to import path to be able to load the external libraries
sys.path.insert(0, 'third-party')
# CEFPanda and glTF modules aree not at top level
sys.path.insert(0, 'third-party/cefpanda')
sys.path.insert(0, 'third-party/gltf')

version = '0.1.2.dev0'

config = {
    'name': "cosmonium",
    'version': version,
    'license': 'GPLv3+',
    'options': {
        'build_apps': {
            'platforms': ['manylinux1_x86_64', 'macosx_10_9_x86_64'],
            'include_patterns': [
                'shaders/**',
                'data/**',
                'doc/**',
                'fonts/**',
                'ralph-data/**',
                'textures/**',
                '*.md',
            ],
            'exclude_patterns': [
                'data/**/level1/**',
                'data/**/level2/**',
                'data/**/level3/**',
                'data/**/level4/**',
                'data/**/level5/**',
                'data/**/level6/**',
                'data/**/level7/**',
                'data/**/level8/**',
                'data/**/level9/**',
                'data/tools/**',
                'data/data/**',
            ],
            'gui_apps': {
                'cosmonium': 'main.py',
                'ralph': 'ralph.py',
            },
            'macos_main_app': 'cosmonium',
            'log_filename': '$USER_APPDATA/cosmonium/output.log',
            'log_append': False,
            'plugins': [
                'pandagl',
                'p3ptloader',
                'p3assimp'
            ],
            'icons' : {
                "cosmonium" : [
                    "textures/cosmonium-512.png",
                    "textures/cosmonium-256.png",
                    "textures/cosmonium-128.png",
                    "textures/cosmonium-64.png",
                    "textures/cosmonium-48.png",
                    "textures/cosmonium-32.png",
                    "textures/cosmonium-16.png",
                ],
            },
       }
    }
}

if __name__ == '__main__':
    setup(**config)
