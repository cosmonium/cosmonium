#!/usr/bin/env python
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

from __future__ import print_function
from __future__ import absolute_import

import sys

# Add source/ directory to import path to be able to load the c++ libraries
sys.path.insert(1, 'source')
# Add third-party/ directory to import path to be able to load the external libraries
sys.path.insert(1, 'third-party')
# CEFPanda and glTF modules aree not at top level
sys.path.insert(1, 'third-party/cefpanda')
sys.path.insert(1, 'third-party/gltf')

from cosmonium.cosmonium import Cosmonium

from cosmonium.parsers.yamlparser import YamlParser
from cosmonium.parsers.objectparser import UniverseYamlParser
from cosmonium.celestia import cel_parser, cel_engine
from cosmonium.celestia import ssc_parser
from cosmonium.celestia import stc_parser
from cosmonium.celestia import star_parser
from cosmonium.celestia import dsc_parser
from cosmonium.celestia import asterisms_parser
from cosmonium.celestia import boundaries_parser
from cosmonium.dircontext import defaultDirContext

#import textures to register celestia texture parser
from cosmonium.celestia import textures
from cosmonium.spaceengine import textures
from cosmonium import settings

import argparse
import os

class CosmoniumConfig(object):
    def __init__(self):
        self.common = 'data/defaults.yaml'
        self.main = 'data/cosmonium.yaml'
        self.default = 'earth'
        self.script = None
        self.extra = [settings.data_dir]
        self.celestia = False
        self.celestia_data_list = ["../Celestia"]
        if sys.platform == "darwin":
            self.celestia_data_list.append("/Applications/Celestia.app/Contents/Resources/CelestiaResources")
        elif sys.platform == "win32":
            self.celestia_data_list.append("C:\\Program Files\\Celestia")
        else:
            self.celestia_data_list.append("/usr/share/celestia")
        self.celestia_support = ['data/solar-system/ssd.yaml', 'data/solar-system/manual-orbits.yaml', 'data/solar-system/celestia.yaml']
        self.celestia_ssc = ["solarsys.ssc", "minormoons.ssc", "numberedmoons.ssc", "asteroids.ssc", "outersys.ssc"]#, "extrasolar.ssc"]
        self.celestia_stc = ["nearstars.stc", "revised.stc", "spectbins.stc", "visualbins.stc", "extrasolar.stc"]
        self.celestia_dsc = ["galaxies.dsc"]
        self.celestia_stars_catalog = 'stars.dat'
        self.celestia_stars_names = 'starnames.dat'
        self.celestia_asterisms = 'asterisms.dat'
        self.celestia_boundaries = 'boundaries.dat'
        self.celestia_start_script = 'start.cel'
        self.prc_file = 'config.prc'

    def update_from_args(self, args):
        #TODO: add input checking here
        if args.common is not None:
            self.common = args.common
        if args.main is not None:
            self.main = args.main
        if args.script is not None:
            self.script = args.script
        if args.default is not None:
            self.default = args.default
        if args.extra is not None:
            self.extra = args.extra
        if args.celestia is not None:
            if args.celestia != '':
                self.celestia_data_list = [args.celestia]
            self.celestia = True
        else:
            self.celestia = False
        if self.celestia and self.script is None and self.default is None:
            self.script = self.celestia_start_script

class CosmoniumConfigParser(YamlParser):
    def __init__(self, config_file):
        YamlParser.__init__(self)
        self.config_file = config_file
        self.config = CosmoniumConfig()

    def load(self):
        if os.path.exists(self.config_file):
            print("Loading app config file", self.config_file)
            self.load_and_parse(self.config_file)
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
        if data is None: return
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
        self.config.main = data.get('main', self.config.main)
        self.config.script = data.get('script', self.config.script)
        self.config.default = data.get('default', self.config.default)
        self.config.extra = data.get('extra', self.config.extra)
        if not isinstance(self.config.extra, list):
            self.config.extra = [self.config.extra]
        self.config.prc_file = data.get('prc', self.config.prc_file)

class CosmoniumApp(Cosmonium):
    def __init__(self, args):
        parser = CosmoniumConfigParser(os.path.join(settings.config_dir, 'cosmonium.yaml'))
        self.app_config = parser.load()
        self.app_config.update_from_args(args)
        settings.prc_file = self.app_config.prc_file
        Cosmonium.__init__(self)

    def find_celestia_data(self):
        self.celestia_data = None
        for path in self.app_config.celestia_data_list:
            if os.path.isdir(path):
                self.celestia_data = path
                break
        if self.celestia_data is None:
            print("Could not find Celestia installation")
            sys.exit(1)
        else:
            print("Celestia data found at", self.celestia_data)
        defaultDirContext.add_path('textures', self.celestia_data + '/textures/lores')
        defaultDirContext.add_path('textures', self.celestia_data + '/textures/medres')
        defaultDirContext.add_path('textures', self.celestia_data + '/textures/hires')
        defaultDirContext.add_path('models', self.celestia_data + '/models')
        defaultDirContext.add_path('data', self.celestia_data + '/data')
        defaultDirContext.add_path('scripts', self.celestia_data + '/scripts')
        defaultDirContext.add_path('scripts', self.celestia_data)

    def load_universe_celestia(self):
        self.find_celestia_data()
        if len(self.app_config.celestia_support) > 0:
            parser = UniverseYamlParser(self.universe)
            for support in self.app_config.celestia_support:
                self.load_file(parser, support)
        names = star_parser.load_names(self.app_config.celestia_stars_names)
        if self.app_config.celestia_stars_catalog is not None:
            if self.app_config.celestia_stars_catalog.endswith('.dat'):
                star_parser.load_bin(self.app_config.celestia_stars_catalog, names, self.universe)
            else:
                star_parser.load_text(self.app_config.celestia_stars_catalog, names, self.universe)
        stc_parser.load(self.app_config.celestia_stc, self.universe)
        ssc_parser.load(self.app_config.celestia_ssc, self.universe)
        asterisms_parser.load(self.app_config.celestia_asterisms, self.universe)
        boundaries_parser.load(self.app_config.celestia_boundaries, self.universe)
        #dsc_parser.load(self.celestia_dsc, self.universe)

    def load_file(self, parser, path):
        lower = path.lower()
        if lower.endswith('.yaml') or lower.endswith('.yml'):
            parser.load_and_parse(path)
        elif lower.endswith('.ssc'):
            ssc_parser.load(path, self.universe)
        elif lower.endswith('.stc'):
            stc_parser.load(path, self.universe)
        elif lower.endswith('.dsc'):
            dsc_parser.load(path, self.universe)

    def load_dir(self, parser, path):
        for entry in os.listdir(path):
            self.load_file(parser, os.path.join(path, entry))

    def load_universe_cosmonium(self):
        parser = UniverseYamlParser(self.universe)
        parser.load_and_parse(self.app_config.common)
        parser.load_and_parse(self.app_config.main)
        for extra in self.app_config.extra:
            if os.path.isdir(extra):
                self.load_dir(parser, extra)
            else:
                self.load_file(parser, extra)

    def load_universe(self):
        if self.app_config.celestia:
            self.load_universe_celestia()
        else:
            self.load_universe_cosmonium()

    def start_universe(self):
        running = False
        if self.app_config.script is not None:
            if self.app_config.script.startswith('cel://'):
                self.load_cel_url(self.app_config.script)
                running = True
            else:
                settings.debug_jump = False
                print("Running", self.app_config.script)
                script = cel_parser.load(self.app_config.script)
                running = self.run_script(cel_engine.build_sequence(self, script))
        if not running:
            self.select_body(self.universe.find_by_name(self.app_config.default))
            self.autopilot.go_to_front(duration=0.0)
            self.gui.update_info("Welcome to Cosmonium!")

parser = argparse.ArgumentParser()
parser.add_argument("script",
                    help="CEL script to run at start up",
                    nargs='?',
                    default=None)
parser.add_argument("--celestia",
                    help="Load data from Celestia",
                    nargs='?',
                    const='',
                    default=None)
parser.add_argument("--common",
                    help="Path to the file with the basic common configuration",
                    default=None)
parser.add_argument("--main",
                    help="Path to the file with the universe configuration",
                    default=None)
parser.add_argument("--default",
                    help="Default body to show when there is no start up script",
                    default=None)
parser.add_argument("--extra",
                    help="Extra configuration files or directories to load",
                    nargs='+',
                    default=None)
if sys.platform == "darwin":
    #Ignore -psn_<app_id> from MacOS
    parser.add_argument('-p', help=argparse.SUPPRESS)
args = parser.parse_args()

app = CosmoniumApp(args)
app.run()
