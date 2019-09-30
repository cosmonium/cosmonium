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

from ..bayer import canonize_name
from .. import units, astro

from .parser import *

import sys

class YBSParser(FixedFieldsParser):
    regex = re.compile('^' + I4 + A10 + A11 + I6 + I6 + I4 +  #ID, names, catalogues
                       A1 + A1 + A1 + A5 + A2 + A9 +          # flags
                       I2 + I2 + F4 +                         # RA J1900
                       I3 + I2 + I2 +                         # DE J1900
                       I2 + I2 + F4 +                         # RA J1900
                       I3 + I2 + I2  +                        # DE J1900
                       F6 + F6 +                              # Galactic long lat
                       F5 + A1 + A1 +                         # Magnitude
                       F5 + A1 + F5 + A1 + F5 + A1 +          # UV, BV, RI
                       A20 + A1 +                             # Spectral type
                       F6 + F6 +                              # Proper motion
                       A1E + F5E                              # Parallax
                       )
    name_regex = re.compile('^([ \d]{3})(.{3})([ \d])(.{3})')

    def __init__(self):
        self.stars = []
        self.catalogues = {'HR': {}, 'HD': {}, 'SAO': {}, 'ADS': {}}

    def parse_line(self, line):
        m = self.regex.search(line)
        if m is not None:
            (hr_id, name, dm, hd, sao, fk5,
             ir_flag, rir_flag, multiple, ads, ads_comp, var_id,
             ra_h_1900, ra_min_1900, ra_sec_1900,
             de_deg_1900, de_min_1900, de_sec_1900,
             ra_h_2000, ra_min_2000, ra_sec_2000,
             de_deg_2000, de_min_2000, de_sec_2000,
             glon, glat,
             vmag, vmag_code, vmag_flag, 
             bvcolor, bvcolor_flags, ubcolor, ubcolor_flags, ricolor, ricolor_flags,
             spectral_type, spectral_type_code,
             pm_ra, pm_de,
             parallax_flags, parallax
             ) = m.groups()
            hr_id = hr_id.strip()
            hd = hd.strip()
            sao = sao.strip()
            ads = ads.strip()
            m = self.name_regex.search(name)
            if m:
                (flamsteed, bayer, bayer_num, const) = m.groups()
                flamsteed = flamsteed.strip()
                bayer = bayer.strip().upper()
                bayer_num = bayer_num.strip()
                const = const.strip()
                if bayer != '':
                    if bayer_num != '':
                        bayer = bayer + bayer_num + ' ' + const
                    else:
                        bayer = bayer + ' ' + const
                    bayer = canonize_name(bayer)
                if flamsteed != '':
                    flamsteed = flamsteed + ' ' + const
            else:
                flamsteed = ''
                bayer = ''
            ra_2000 = self.hms_to_deg(ra_h_2000, ra_min_2000, ra_sec_2000)
            de_2000 = self.dms_to_deg(de_deg_2000, de_min_2000, de_sec_2000)
            if ra_2000 is None or de_2000 is None:
                return
            spectral_type = spectral_type.strip()
            parallax = self.to_float(parallax)
            star = {'src': 'ybs',
                    'hr': hr_id,
                    'hd': hd,
                    'sao': sao,
                    'ads': ads,
                    'bayer': bayer,
                    'flamsteed': flamsteed,
                    'ra': ra_2000,
                    'de': de_2000,
                    'parallax': parallax,
                    'vmag': float(vmag),
                    'spectral_type': spectral_type}
            self.catalogues['HR'][hr_id] = star
            self.catalogues['HD'][hd] = star
            self.catalogues['SAO'][sao] = star
            self.catalogues['ADS'][ads] = star
            self.stars.append(star)
        else:
            print("YBS: Invalid line", line)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        parser = YBSParser()
        parser.load(sys.argv[1])
    else:
        print("Invalid number of parameters")
