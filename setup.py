#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2025 Laurent Deru.
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


import os
import platformdirs
from setuptools import setup
import sys

from cosmonium.version import version_str


# Add lib/ directory to import path to be able to load the c++ libraries
sys.path.insert(0, 'lib')
# Add third-party/ directory to import path to be able to load the external libraries
sys.path.insert(0, 'third-party')
# CEFPanda and glTF modules aree not at top level
sys.path.insert(0, 'third-party/cefpanda')
sys.path.insert(0, 'third-party/gltf')


app_name = 'cosmonium'
log_filename = os.path.join(platformdirs.user_log_dir(app_name), 'output.log')
requirements_path = None

include_modules = [
    'jinja2.compiler',
    'numpy.core._multiarray_tests',
    ]

for (index, arg) in enumerate(sys.argv):
    if arg == '-p':
        platform = sys.argv[index + 1]
        if platform.startswith('macos'):
            pass
        elif platform.startswith('win'):
            include_modules.append('win32')
            include_modules.append('win32com.gen_py')
            include_modules.append('win32com.shell')
            include_modules.append('win32clipboard')
            include_modules.append('win32con')
        else:
            pass
        break

if '--cosmonium-test' in sys.argv:
    sys.argv.remove('--cosmonium-test')
    log_filename = None

for (index, arg) in enumerate(sys.argv):
    if arg == '-r':
        requirements_path = sys.argv[index + 1]
        sys.argv.pop(index)
        sys.argv.pop(index)
        break

if requirements_path is None:
    print("Missing path for requirements.txt !")
    exit(1)

config = {
    'name': "cosmonium",
    'version': version_str,
    'license': 'GPLv3+',
    'options': {
        'build_apps': {
            'requirements_path': requirements_path,
            'platforms': ['manylinux1_x86_64', 'manylinux1_i686', 'macosx_10_9_x86_64'],
            'prefer_discrete_gpu': True,
            'include_patterns': [
                'config/**',
                'shaders/**',
                'data/**',
                'models/**',
                'doc/**',
                'fonts/**',
                'ralph-data/**',
                'textures/**',
                '*.md',
                'locale/**'
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
            'package_data_dirs':
            {
             'win32': [
                 ('pywin32_system32/*', '', {}),
                 ('win32/*.pyd', '', {}),
             ],
            },
            'include_modules':
            {
                '*': include_modules,
            },
            'gui_apps': {
                'cosmonium': 'main.py',
                #'ralph': 'ralph.py',
            },
            'macos_main_app': 'cosmonium',
            'log_filename': log_filename,
            'log_append': False,
            'plugins': [
                'pandagl',
                'p3ptloader',
                'p3assimp',
                'p3interrogatedb'
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
            'bam_model_extensions': [],
        },
        'bdist_apps': {
            'installers': {
                'manylinux1_x86_64': 'gztar',
                'manylinux1_i686': 'gztar',
                'macosx_10_9_x86_64': 'zip',
                'win_amd64': 'nsis',
                'win32': 'nsis',
            }
        }
    }
}

if __name__ == '__main__':
    setup(**config)
