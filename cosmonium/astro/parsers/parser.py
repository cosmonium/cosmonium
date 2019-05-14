from __future__ import print_function
from __future__ import absolute_import

from .. import units, astro

import re
import gzip

I1 = '(\d)'
I2 = '([-+ \d]{2})'
I3 = '([-+ \d]{3})'
I4 = '([-+ \d]{4})'
I5 = '([-+ \d]{5})'
I6 = '([-+ \d]{6})'
F3 = '([-+ \d\.]{3})'
F4 = '([-+ \d\.]{4})'
F5 = '([-+ \d\.]{5})'
F6 = '([-+ \d\.]{6})'
F7 = '([-+ \d\.]{7})'
F8 = '([-+ \d\.]{8})'
F5E = '([-+ \d\.]{5}|$)'
A1 = '(.)'
A1E = '(.|$)'
A2 = '(..)'
A3 = '(.{3})'
A4 = '(.{4})'
A5 = '(.{5})'
A6 = '(.{6})'
A7 = '(.{7})'
A8 = '(.{8})'
A9 = '(.{9})'
A10 = '(.{10})'
A11 = '(.{11})'
A12 = '(.{12})'
A18 = '(.{18})'
A20 = '(.{20})'
PAD = ' '

RA_REGEX = re.compile('(\d\d)(\d\d)(\d\d\.[\d ]+)')
DE_REGEX = re.compile('([-+]\d\d)(\d\d)(\d\d\.[\d ]+)')

class TextCatalogueParser(object):
    skip = 0
    def to_float(self, string):
        string = string.strip()
        if string != '':
            return float(string)
        else:
            return None

    def hms_to_deg(self, h, m, s):
        h = self.to_float(h)
        m = self.to_float(m)
        s = self.to_float(s)
        if h is None or m is None or s is None:
            return None
        else:
            return units.hourMinSec(h, m, s)

    def dms_to_deg(self, d, m, s):
        d = self.to_float(d)
        m = self.to_float(m)
        s = self.to_float(s)
        if d is None or m is None or s is None:
            return None
        else:
            return units.degMinSec(d, m, s)

    def load(self, filepath):
        if filepath.endswith('.gz'):
            with gzip.open(filepath, 'r') as data:
                i = 0
                for line in data.readlines():
                    i += 1
                    if i <= self.skip: continue
                    line = line.decode('utf-8')
                    self.parse_line(line.rstrip('\r\n'))
        else:
            with open(filepath, 'r') as data:
                i = 0
                for line in data.readlines():
                    i += 1
                    if i <= self.skip: continue
                    self.parse_line(line.rstrip('\r\n'))

class FixedFieldsParser(TextCatalogueParser):
    pass

class CsvCatalogueParser(TextCatalogueParser):
    def parse_ra(self, ra):
        m = RA_REGEX.search(ra)
        (ra_hour, ra_min, ra_sec) = m.groups()
        return units.hourMinSec(float(ra_hour), float(ra_min), float(ra_sec))

    def parse_ra_deg(self, ra):
        m = RA_REGEX.search(ra)
        (ra_deg, ra_min, ra_sec) = m.groups()
        return units.degMinSec(float(ra_deg), float(ra_min), float(ra_sec))

    def parse_de(self, de):
        m = DE_REGEX.search(de)
        (de_deg, de_min, de_sec) = m.groups()
        return units.degMinSec(float(de_deg), float(de_min), float(de_sec))

    def load(self, filepath, separator='|'):
        if filepath.endswith('.gz'):
            with gzip.open(filepath, 'r') as data:
                i = 0
                for line in data.readlines():
                    i += 1
                    if i <= self.skip: continue
                    line = line.decode('utf-8')
                    self.parse_line(line.rstrip('\r\n').split(separator))
        else:
            with open(filepath, 'r') as data:
                i = 0
                for line in data.readlines():
                    i += 1
                    if i <= self.skip: continue
                    self.parse_line(line.rstrip('\r\n').split(separator))
