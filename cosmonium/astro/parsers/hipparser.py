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

from .. import units, astro
from .parser import *

import sys, os

class HipMainParser(CsvCatalogueParser):
    HIP = 0
    COMP = 1
    CLASSES = 2
    GROUPS = 3
    RA = 4
    DE = 5
    PARALLAX = 6
    SPECTRAL_TYPE = 27
    def __init__(self):
        self.systems = []
        self.catalogues = {'HIP': {}}

    def parse_line(self, fields):
        hip = fields[self.HIP].strip()
        ra = float(fields[self.RA])
        de = float(fields[self.DE])
        parallax = float(fields[self.PARALLAX]) / 1000.0
        spectral_type = fields[self.SPECTRAL_TYPE].strip()
        system = {'src': 'hip',
                  'hip': hip,
                  'ra': ra,
                  'de': de,
                  'parallax': parallax,
                  'spectral_type': spectral_type,
                  'vmag': None #TODO: Read from HipPhoto
                  }
        self.systems.append(system)
        self.catalogues['HIP'][hip] = system

class HipPhotoParser(CsvCatalogueParser):
    HIP = 0
    def __init__(self, systems, catalogues):
        self.systems = systems
        self.catalogues = catalogues

    def parse_line(self, fields):
        hip = fields[self.HIP].strip()
        system = self.catalogues['HIP'].get(hip, None)
        if system is not None:
            system[0] = ''
        else:
            print("Unknown HIP photo entry", hip)

class HipBiblioParser(CsvCatalogueParser):
    HIP = 0
    HD = 1

    skip = 5
    def __init__(self, systems, catalogues):
        self.systems = systems
        self.catalogues = catalogues
        catalogues['HD'] = {}

    def parse_line(self, fields):
        if len(fields) <= 1: return
        hip = fields[self.HIP].strip()
        hd = fields[self.HD].strip()
        system = self.catalogues['HIP'].get(hip, None)
        if system is not None:
            if hd != '':
                system['hd'] = hd
                self.catalogues['HD'][hd] = system
        else:
            print("Unknown HIP biblio entry", hip)

class HipParser(object):
    def load(self, filepath):
        main = os.path.join(filepath, 'main.dat.gz')
        photo = os.path.join(filepath, 'photo.dat.gz')
        biblio = os.path.join(filepath, 'biblio.dat.gz')
        main_parser = HipMainParser()
        main_parser.load(main)
        #photo_parser = HipPhotoParser(main_parser.systems)
        #photo_parser.load(photo)
        biblio_parser = HipBiblioParser(main_parser.systems, main_parser.catalogues)
        biblio_parser.load(biblio)
        self.systems = main_parser.systems
        self.catalogues = main_parser.catalogues

if __name__ == '__main__':
    if len(sys.argv) == 2:
        parser = HipParser()
        parser.load(sys.argv[1])
        #print(parser.systems)
    else:
        print("Invalid number of parameters")
