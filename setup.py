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
            },
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
