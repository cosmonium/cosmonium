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

if sys.version_info[0] < 3:
    excludes = ['cosmonium.support.yaml']
else:
    excludes = ['cosmonium.support.yaml2']

setup(
    name="cosmonium",
    version="0.1.0",
    license='GPLv3+',
    options = {
        'build_apps': {
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
            'exclude_modules': {'*': excludes},
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
        }
    }
)
