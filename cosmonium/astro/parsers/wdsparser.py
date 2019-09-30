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

class HdsParser(FixedFieldsParser):
    regex = re.compile('^' + A10 + A7 + A5 + PAD +      #2000 Coordinate , discoverer, components
                       I5                               #Hipparos ID
                       )
    def __init__(self, systems):
        self.catalogues = {'WDS': {}, 'HIP': {}}
        self.systems = systems

    def parse_line(self, line):
        m = self.regex.search(line)
        if m is not None:
            (coord, disc, components,
             hip) = m.groups()
            hip = hip.strip()
            if coord in self.systems:
                system = self.systems[coord]
                self.catalogues['WDS'][coord] = system
                self.catalogues['HIP'][hip] = system
                system['hip'] = hip
            else:
                print("System missing for", coord)

class WdsMainParser(FixedFieldsParser):
    skip = 5
    regex = re.compile('^' + A10 + A7 + A5 + PAD +      #2000 Coordinate , discoverer, components
                       I4 + PAD + I4 + PAD + I4 + PAD + # First data, last data, number of obs
                       I3 + PAD + I3 + PAD +            # First position angle, last position angle
                       F5 + PAD + F5 + PAD +            # First separation, last sep
                       F5 + PAD + F6 +                  # First magnitude, second magnitude
                       A10 +                            # Spectral type
                       I4 + I4 + PAD +                  # Primary proper motion ra/decl
                       I4 + I4 + PAD +                  # Secondary proper motion ra/decl
                       A8 + A5 + PAD + A18              # Durchmusterung, notes, coord (arcsec)
                       )
    def __init__(self):
        self.systems = {}

    def parse_line(self, line):
        m = self.regex.search(line)
        if m is not None:
            (coord, disc, components,
             first_date, last_date, nb_of_obs,
             first_angle, last_angle,
             first_sep, last_sep,
             first_mag, second_mag,
             spectral,
             prim_pm_ra, prim_pm_de,
             sec_pm_ra, sec_pm_de,
             durch, notes, coord_arcsec
             ) = m.groups()
            spectral = spectral.strip()
            first_mag = first_mag.strip()
            if first_mag != '.' and first_mag != '':
                first_mag = float(first_mag)
            else:
                first_mag = None
            second_mag = second_mag.strip()
            if second_mag != '.' and second_mag != '':
                second_mag = float(second_mag)
            else:
                second_mag = None
            system = {'src': 'wds',
                      'coord': coord,
                      'app_mag_1': first_mag,
                      'app_mag_2': second_mag,
                      'spectral_type': spectral
                      }
            self.systems[coord] = system
        else:
            print("WDS: Invalid line", line)

class WdsParser(object):
    def load(self, filepath):
        main = os.path.join(filepath, 'wdsweb_summ2.txt')
        alias = os.path.join(filepath, 'hds.txt')
        main_parser = WdsMainParser()
        main_parser.load(main)
        alias_parser = HdsParser(main_parser.systems)
        alias_parser.load(alias)
        self.systems = main_parser.systems
        self.catalogues = alias_parser.catalogues

if __name__ == '__main__':
    if len(sys.argv) == 3:
        parser = WdsMainParser()
        parser.load(sys.argv[1])
        alias = HdsParser(parser.systems)
        alias.load(sys.argv[2])
        #print(parser.systems)
    else:
        print("Invalid number of parameters")
