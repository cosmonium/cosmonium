#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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


import os
import sys

from panda3d.core import ExecutionEnvironment

from .. import settings
from ..parsers.yamlloader import YamlLoader


class CosmoniumConfig:
    def __init__(self):
        base_path = ExecutionEnvironment.getEnvironmentVariable("MAIN_DIR")
        self.main_dir = base_path
        self.common = os.path.join(base_path, 'data/defaults.yaml')
        self.main = os.path.join(base_path, 'data/cosmonium.yaml')
        self.ui = os.path.join(base_path, 'config/ui/celestia/ui.yaml')
        self.catalogs = 'config/catalogs.yaml'
        self.default_home = None
        self.default_target = None
        self.script = None
        self.extra = [os.path.join(base_path, 'data/extra'), settings.data_dir]
        self.celestia = False
        self.celestia_data_list = ["../Celestia", "../CelestiaContent"]
        if sys.platform == "darwin":
            self.celestia_data_list.append("/Applications/Celestia.app/Contents/Resources/CelestiaResources")
        elif sys.platform == "win32":
            self.celestia_data_list.append("C:\\Program Files\\Celestia")
        else:
            self.celestia_data_list.append("/usr/share/celestia")
        self.celestia_support = [
            'data/solar-system/frames.yaml',
            'data/solar-system/ssd.yaml',
            'data/solar-system/manual-orbits.yaml',
            'data/solar-system/celestia.yaml',
        ]
        self.celestia_ssc = [
            "solarsys.ssc",
            "minormoons.ssc",
            "numberedmoons.ssc",
            "asteroids.ssc",
            "outersys.ssc",
            # "extrasolar.ssc",
        ]
        self.celestia_stc = ["nearstars.stc", "revised.stc", "spectbins.stc", "visualbins.stc", "extrasolar.stc"]
        self.celestia_dsc = ["galaxies.dsc"]
        self.celestia_stars_catalog = 'stars.dat'
        self.celestia_stars_names = 'starnames.dat'
        self.celestia_asterisms = 'asterisms.dat'
        self.celestia_boundaries = 'boundaries.dat'
        self.celestia_start_script = 'start.cel'
        self.prc_file = 'config.prc'
        self.test_start = False

    def update_from_args(self, args):
        # TODO: add input checking here
        if args.common is not None:
            self.common = args.common
        if args.main is not None:
            self.main = args.main
        if args.ui is not None:
            self.ui = args.ui
        if args.script is not None:
            self.script = args.script
        if args.home is not None:
            self.default_home = args.home
        if args.default is not None:
            self.default_target = args.default
        if args.extra is not None:
            self.extra += args.extra
        if args.celestia is not None:
            if args.celestia != '':
                self.celestia_data_list = [args.celestia]
            self.celestia = True
        else:
            self.celestia = False
        if self.celestia and self.script is None and self.default_target is None:
            self.script = self.celestia_start_script
        self.test_start = args.test_start


class CosmoniumConfigParser:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = CosmoniumConfig()

    def load(self):
        if os.path.exists(self.config_file):
            print("Loading app config file", self.config_file)
            data = YamlLoader.load_file(self.config_file)
            if data is not None:
                self.decode(data)
        return self.config

    def decode_celestia(self, data):
        self.config.celestia_support = data.get('support', self.config.celestia_support)
        self.config.celestia_ssc = data.get('ssc', self.config.celestia_ssc)
        self.config.celestia_stc = data.get('stc', self.config.celestia_stc)
        self.config.celestia_dsc = data.get('dsc', self.config.celestia_dsc)
        self.config.celestia_stars_catalog = data.get('stars', self.config.celestia_stars_catalog)
        self.config.celestia_stars_names = data.get('names', self.config.celestia_stars_names)
        self.config.celestia_asterisms = data.get('asterisms', self.config.celestia_asterisms)
        self.config.celestia_boundaries = data.get('boundaries', self.config.celestia_boundaries)
        self.config.script = data.get('script', self.config.celestia_start_script)

    def decode(self, data):
        if data is None:
            return
        celestia = data.get('celestia', False)
        celestia_data = data.get('celestia-data', {})
        if isinstance(celestia, bool):
            self.config.celestia = celestia
        else:
            self.config.celestia = True
            self.config.celestia_data_list = [celestia]
        if self.config.celestia:
            self.decode_celestia(celestia_data)
        self.config.common = data.get('common', self.config.common)
        self.config.catalogs = data.get('catalogs', self.config.catalogs)
        self.config.main = data.get('main', self.config.main)
        self.config.script = data.get('script', self.config.script)
        self.config.default_home = data.get('home', self.config.default_home)
        self.config.default_target = data.get('default', self.config.default_target)
        self.config.extra = data.get('extra', self.config.extra)
        if not isinstance(self.config.extra, list):
            self.config.extra = [self.config.extra]
        self.config.prc_file = data.get('prc', self.config.prc_file)
