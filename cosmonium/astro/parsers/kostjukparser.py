from __future__ import print_function
from __future__ import absolute_import

from ..bayer import canonize_name
from .. import units

from .parser import *

import sys, os

class KostjukParser(FixedFieldsParser):
    regex = re.compile('^' + I6 + PAD + A12 + PAD + I5 + PAD + #HD, DM, GC
                       I4 + PAD + I6 + PAD +                   #HR, HIP
                       I2 + I2 + F5 + PAD +                    #RA
                       I3 + I2 + F4 + PAD +                    #DE
                       F5 + PAD +                              #Mag
                       I3 + PAD + A5 + PAD + A3)               #Fl, bayer, const
    def __init__(self):
        self.catalogues = {'HD': {}, 'DM': {}, 'GC': {}, 'HR': {}, 'HIP': {}, 'BAYER': {}, 'FLAMSTEED': {}}
        self.stars = []

    def parse_line(self, line):
        m = self.regex.search(line)
        if m is not None:
            (hd, dm, gc, hr, hip,
             ra_h, ra_min, ra_sec,
             de_deg, de_min, de_sec,
             mag,
             fl, bayer, const) = m.groups()
            hd = hd.strip()
            dm = dm.strip()
            gc = gc.strip()
            hr = hr.strip()
            hip = hip.strip()
            fl = fl.strip()
            bayer = bayer.strip().upper()
            const = const.strip()
            if fl != '':
                fl = fl + ' ' + const
            if bayer != '':
                bayer = bayer + ' ' + const
                bayer = canonize_name(bayer)
            star = {'hd': hd, 'dm': dm, 'gc': gc, 'hr': hr, 'hip': hip, 'flamsteed': fl, 'bayer': bayer}
            self.catalogues['HD'][hd] = star
            self.catalogues['DM'][dm] = star
            self.catalogues['GC'][gc] = star
            self.catalogues['HR'][hr] = star
            self.catalogues['HIP'][hip] = star
            self.catalogues['FLAMSTEED'][fl] = star
            self.catalogues['BAYER'][bayer] = star
            self.stars.append(star)
        else:
            print("Kostjuk: Invalid line", line)

    def xref(self, from_cat, from_id, to_cat):
        from_cat = from_cat.upper()
        entry = self.catalogues[from_cat].get(from_id, None)
        if entry is not None:
            return entry.get(to_cat.lower(), None)
        else:
            return None

if __name__ == '__main__':
    if len(sys.argv) == 2:
        parser = KostjukParser()
        parser.load(sys.argv[1])
        print(parser.stars)
    else:
        print("Invalid number of parameters")
