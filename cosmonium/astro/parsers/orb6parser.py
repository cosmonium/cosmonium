from __future__ import print_function
from __future__ import absolute_import

from .. import units, astro
from .parser import TextCatalogueParser

import sys
import re

class ORB6Parser(TextCatalogueParser):
    skip = 2

    ra_regex = re.compile('(\d\d)(\d\d)(\d\d\.[\d ]{2})')
    de_regex = re.compile('([-+]\d\d)(\d\d)(\d\d\.[\d ])')
    RA_2000 = 0
    DEC_2000 = 1
    WDS = 2
    DD = 3
    ADS = 4
    HD = 5
    HIP = 6
    V1_11 = 7
    V1_11_FLAGS = 8
    V2_22 = 9
    V2_22_FLAGS = 10
    PERIOD = 11
    PERIOD_UNITS = 12
    PERIOD_ERROR = 13
    SEMI_MAJOR_AXIS = 14
    SEMI_MAJOR_AXIS_UNITS = 15
    SEMI_MAJOR_AXIS_ERROR = 16
    INCLINATION = 17
    INCLINATION_ERROR = 18
    NODE = 19
    NODE_FLAGS = 20
    NODE_ERROR = 21
    T0 = 22
    T0_UNITS = 23
    T0_ERROR = 24
    ECCENTRICITY = 25
    ECCENTRICITY_ERROR = 26
    LONGITUDE = 27
    LONGITUDE_FLAGS = 28
    LONGITUDE_ERROR = 29
    EQUINOX = 30
    LAST = 31
    GRADE = 32
    FLAGS = 33
    NOTES = 34
    REFERENCE = 35
    IMAGE = 36
    def __init__(self):
        self.data = []
        self.catalogues = {'HIP': {}, 'WDS': {}, 'HD': {}}

    def parse_line(self, line):
        data = line.split('|')
        m = self.ra_regex.search(data[self.RA_2000])
        (ra_h_2000, ra_min_2000, ra_sec_2000) = m.groups()
        ra_2000 = units.hourMinSec(float(ra_h_2000), float(ra_min_2000), float(ra_sec_2000))
        m = self.de_regex.search(data[self.DEC_2000])
        (de_deg_2000, de_min_2000, de_sec_2000) = m.groups()
        de_2000 = units.degMinSec(float(de_deg_2000), float(de_min_2000), float(de_sec_2000))
        wds = data[self.WDS]
        dd = data[self.DD]
        hd = data[self.HD]
        hip = data[self.HIP]
        if hip != '' and hip != '.':
            hip = hip
        else:
            hip = None
        v1 = data[self.V1_11]
        if v1 != '':
            v1 = float(v1)
        else:
            v1 = None
        v2 = data[self.V2_22]
        if v2 != '':
            v2 = float(v2)
        else:
            v2 = None
        period = data[self.PERIOD]
        if period != '':
            period = float(period)
            period_units = data[self.PERIOD_UNITS]
            if period_units == 'm':
                period_units = units.Min
            elif period_units == 'h':
                period_units = units.Hour
            elif period_units == 'd':
                period_units = units.Day
            elif period_units == 'y':
                period_units = units.JYear
            elif period_units == 'c':
                period_units = units.JCentury
            period *= period_units
        else:
            period= None
        sma = data[self.SEMI_MAJOR_AXIS]
        if sma != '':
            sma = float(sma)
        else:
            sma = None
        inclination = data[self.INCLINATION]
        if inclination != '':
            inclination = float(inclination)
        else:
            inclination = None
        node = data[self.NODE]
        if node != '':
            node = float(node)
        else:
            node = None
        t0 = data[self.T0]
        if t0 != '':
            t0 = float(t0)
            t0_units = data[self.T0_UNITS]
            if t0_units == 'c':
                t0 *= 100
            elif t0_units == 'd':
                t0 += 2400000.0
            elif t0_units == 'm':
                t0 += 2400000.5
            elif t0_units == 'y':
                t0 = units.besselYearToJulian(t0)
        else:
            t0 = None
        longitude = data[self.LONGITUDE]
        if longitude != '':
            longitude = float(longitude)
        else:
            longitude = None
        system = {'src': 'orb6', 'hip': hip, 'hd': hd, 'wds': wds,
                  'v1': v1, 'v2': v2,
                  'period': period,
                  'epoch': t0,
                  'semimajoraxis': sma,
                  #'eccentricity': eccentricity,
                  'inclination': inclination,
                  #'long_of_pericenter': arg_of_periapsis,
                  #'pa_of_node': pa_of_node
                  }
        self.data.append(system)
        if hip is not None:
            self.catalogues['HIP'][hip] = system
        if hd is not None:
            self.catalogues['HD'][hd] = system
        if wds is not None:
            self.catalogues['WDS'][wds] = system

if __name__ == '__main__':
    if len(sys.argv) == 2:
        parser = ORB6Parser()
        output = parser.load(sys.argv[1])
        #with file(sys.argv[2], 'w') as output_file:
        #    output_file.write(output)
        #print(output)
    else:
        print("Invalid number of parameters")
