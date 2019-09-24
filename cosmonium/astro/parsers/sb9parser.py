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

from .. import units

from .parser import *

import sys, os
import re

class SB9MainParser(CsvCatalogueParser):
    ra_regex = re.compile('(\d\d)(\d\d)(\d\d\.[\d ]{2})')
    de_regex = re.compile('([-+]\d\d)(\d\d)(\d\d\.[\d ])')
    float_interval_regex = re.compile('(\d*\.\d*)\-(\d*\.\d*)')
    SYSTEM_ID   = 0 #           System Number (SB8: <=1469)
    J1900_COORD = 1 #           1900.0 coordinates (for backward compatibility with SB8)
    J2000_COORD = 2 #           2000.0 coordinates
    COMPONENT   = 3 #           Component
    APP_MAG_1   = 4 #           Magnitude of component 1
    FILTER_1    = 5 #           Filter component 1
    APP_MAG_2   = 6 #           Magnitude of component 2
    FILTER_2    = 7 #           Filter component 2
    SPECTRAL_1  = 8 #           Spectral type component 1
    SPECTRAL_2  = 9 #           Spectral type component 2

    def __init__(self):
        self.data = {}

    def to_float(self, value):
        if value != '':
            value = float(value)
        else:
            value = None
        return value

    def to_float_inter(self, value):
        if value != '':
            try:
                value = float(value)
            except ValueError:
                m = self.float_interval_regex.search(value)
                if m is not None:
                    (v1, v2) = m.groups()
                    v1 = float(v1)
                    v2 = float(v2)
                    value = (v1 + v2) / 2
                else:
                    value = None
        else:
            value = None
        return value

    def parse_line(self, data):
        system_id = data[self.SYSTEM_ID]
        component = data[self.COMPONENT]
        app_mag_1 = self.to_float_inter(data[self.APP_MAG_1])
        filter_1 = data[self.FILTER_1]
        app_mag_2 = self.to_float_inter(data[self.APP_MAG_2])
        filter_2 = data[self.FILTER_2]
        spectral_type_1 = data[self.SPECTRAL_1]
        spectral_type_2 = data[self.SPECTRAL_2]
        self.data[system_id] = {'src': 'sb9',
                                'app_mag_1': app_mag_1,
                                'app_mag_2': app_mag_2,
                                'spectral_type_1': spectral_type_1,
                                'spectral_type_2': spectral_type_2}
    
class SB9AliasParser(CsvCatalogueParser):
    SYSTEM_ID = 0 #           System number
    CAT_NAME  = 1 #           Catalog name
    CAT_ID    = 2 #           ID in that catalog

    def __init__(self, main):
        self.main = main
        self.catalogues = {}

    def parse_line(self, data):
        system_id = data[self.SYSTEM_ID]
        catalogue = data[self.CAT_NAME]
        catalogue_low = catalogue.lower()
        cat_id = data[self.CAT_ID]
        if system_id in self.main:
            if not catalogue in self.catalogues:
                self.catalogues[catalogue] = {}
            self.catalogues[catalogue][cat_id] = self.main[system_id]
            if catalogue_low in self.main[system_id]:
                #print("Duplicate entry for", system_id, 'for catalogue', catalogue, cat_id, self.main[system_id][catalogue_low])
                if not isinstance(self.main[system_id][catalogue_low], list):
                    self.main[system_id][catalogue_low] = [self.main[system_id][catalogue_low]]
                self.main[system_id][catalogue_low].append(cat_id)
            else:
                self.main[system_id][catalogue_low] = cat_id

class SB9Parser(object):
    def load(self, filepath):
        main = os.path.join(filepath, 'Main.dta')
        alias = os.path.join(filepath, 'Alias.dta')
        mainparser = SB9MainParser()
        mainparser.load(main)
        aliasparer = SB9AliasParser(mainparser.data)
        aliasparer.load(alias)
        self.catalogues = aliasparer.catalogues

if __name__ == '__main__':
    if len(sys.argv) == 2:
        parser = SB9Parser()
        parser.load(sys.argv[1])
        #with file(sys.argv[2], 'w') as output_file:
        #    output_file.write(output)
        #print(output)
        print(parser.catalogues['HIP']['32349'])
    else:
        print("Invalid number of parameters")
