from __future__ import print_function
from __future__ import absolute_import

from .. import units, astro
from .parser import *

import sys, os

class GlieseParser(CsvCatalogueParser):
    ra_de_regex = re.compile('(\d\d) (\d\d) (\d\d) ([-+]\d\d) (\d\d\.[\d ])')
    space_regex = re.compile('\s+')
    NAME = 0
    COMP = 1
    RA_DE = 3
    SPECTRAL_TYPE = 9
    APP_MAG = 11
    PARALLAX = 25
    HD = 34
    skip = 11
    def __init__(self):
        self.stars = []
        self.catalogues = {'GL': {}, 'HD': {}}

    def parse_line(self, fields):
        if len(fields) <= 1: return
        name = fields[self.NAME].strip()
        name = self.space_regex.sub(' ', name)
        comp = fields[self.COMP].strip()
        ra_de = fields[self.RA_DE]
        m = self.ra_de_regex.search(ra_de)
        if m is None:
            print(ra_de)
            print(fields)
        (ra_h, ra_min, ra_sec, de_deg, de_min) = m.groups()
        ra = self.hms_to_deg(ra_h, ra_min, ra_sec)
        de = self.dms_to_deg(de_deg, de_min, '0')
        spectral_type = fields[self.SPECTRAL_TYPE].strip()
        app_mag = float(fields[self.APP_MAG])
        parallax = float(fields[self.PARALLAX]) / 1000.0
        hd = fields[self.HD].strip()
        star = {'src': 'gliese',
                  'gl': name,
                  'comp': comp,
                  'hd': hd,
                  'ra': ra,
                  'de': de,
                  'parallax': parallax,
                  'vmag': app_mag,
                  'spectral_type': spectral_type
                  }
        self.stars.append(star)
        self.catalogues['GL'][name] = star
        self.catalogues['HD'][hd] = star

if __name__ == '__main__':
    if len(sys.argv) == 2:
        parser = GlieseParser()
        parser.load(sys.argv[1])
        print(parser.stars)
    else:
        print("Invalid number of parameters")
