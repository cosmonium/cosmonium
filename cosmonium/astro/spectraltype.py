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

class SpectralType(object):
    global_class = {'T': [800,    1500],
                    'L': [1500,   2600],
                    'M': [2400,   3700],
                    'K': [3700,   5200],
                    'G': [5200,   6000],
                    'F': [6000,   7500],
                    'A': [7500,  10000],
                    'B': [10000, 30000],
                    'O': [30000, 52000],
                    'W': [30000, 50000],
                    'S': [2000,   3700],
                    'C': [2000,   5560],
                    'R': [3500,   5560],
                    'N': [2000,   3700],}

    spectral_groups = {
        "0": 0, "Ia+": 0, "Ia0": 0, "Ia": 0, "Iab": 0, "Ib":0, "I": 0,
        "II": 1, "III": 1,
        "IV": 2, "V": 2, "VI": 2}
    spectral_temps = {
    "O": [
          [50000, 47600, 45200, 42800, 40400, 38000, 35400, 32800, 30200, 27600, 25000],
          [50000, 47800, 45600, 43400, 41200, 39000, 36800, 34600, 32400, 30200, 28000],
          [50000, 47800, 45600, 43400, 41200, 39000, 36800, 34600, 32400, 30200, 28000],
         ],
    "B": [
          [25000, 23790, 22580, 21370, 20160, 18950, 17140, 15330, 13520, 11710],
          [28000, 26190, 24380, 22570, 20760, 18950, 17140, 13520, 13520, 11710],
          [28000, 26190, 24380, 22570, 20760, 18950, 17140, 13520, 13520, 11710],
         ],
    "A": [
          [9900, 9707, 9513, 9320, 9127, 8933, 8740, 8547, 8353, 8160],
          [9900, 9650, 9400, 9150, 8900, 8650, 8400, 8150, 7900, 7650],
          [9900, 9650, 9400, 9150, 8900, 8650, 8400, 8150, 7900, 7650],
         ],
    "F": [
          [7967, 7773, 7580, 7387, 7193, 7000, 6760, 6520, 6280, 6011],
          [7400, 7260, 7120, 6980, 6840, 6700, 6560, 6420, 6280, 6140],
          [7400, 7260, 7120, 6980, 6840, 6700, 6560, 6420, 6280, 6140],
         ],
    "G": [
          [5743, 5474, 5206, 4937, 4669, 4400, 4343, 4286, 4229, 4171],
          [5743, 5474, 5206, 4937, 4669, 4400, 4343, 4286, 4229, 4171],
          [6000, 5890, 5780, 5670, 5560, 5450, 5340, 5230, 5120, 5010],
         ],
    "K": [
          [4114, 4057, 4000, 3900, 3800, 3700, 3717, 3733, 3750, 3725],
          [4114, 4057, 4000, 3900, 3800, 3700, 3717, 3733, 3750, 3725],
          [4900, 4760, 4620, 4480, 4340, 4200, 4060, 3920, 3780, 3640],
         ],
    "M": [
          [3700, 3510, 3320, 3130, 2940, 2750, 2560, 2370, 2180, 1990],
          [3700, 3510, 3320, 3130, 2940, 2750, 2560, 2370, 2180, 1990],
          [3500, 3333, 3167, 3000, 2833, 2667, 2500, 2333, 2167, 2000],
         ],
    "C": [
          [4669, 4371, 4073, 3776, 3478, 3180, 2883, 2585, 2288, 1990],
          [4669, 4371, 4073, 3776, 3478, 3180, 2883, 2585, 2288, 1990],
          [5560, 5164, 4769, 4373, 3978, 3582, 3187, 2791, 2396, 2000],
         ],
    "L": [
          [2600, 2480, 2355, 2235, 2110, 1990, 1865, 1745, 1620, 1500],
          [2600, 2480, 2355, 2235, 2110, 1990, 1865, 1745, 1620, 1500],
          [2600, 2480, 2355, 2235, 2110, 1990, 1865, 1745, 1620, 1500],
         ],
    "T": [
          [1500, 1420, 1340, 1265, 1185, 1110, 1030, 955, 875, 800],
          [1500, 1420, 1340, 1265, 1185, 1110, 1030, 955, 875, 800],
          [1500, 1420, 1340, 1265, 1185, 1110, 1030, 955, 875, 800],
         ],
    }
    spectral_temps['N'] = spectral_temps['M']
    spectral_temps['S'] = spectral_temps['M']
    spectral_temps['WC'] = spectral_temps['O']
    spectral_temps['WN'] = spectral_temps['O']
    spectral_temps['WO'] = spectral_temps['O']

    def __init__(self):
        self.main = False
        self.white_dwarf = False
        self.wolf_rayet = False
        self.carbon = False
        self.spectral_class = None
        self.subclass = None
        self.second_spectral_class = None
        self.second_subclass = None
        self.abundance = None
        self.luminosity = None
        self.second_luminosity = None
        self.peculiarities = []
        self.temperature = None

    def get_text(self):
        text = ""
        if self.wolf_rayet:
            text += "W"
        if self.white_dwarf:
            text += 'D'
        if self.spectral_class is not None:
            text += self.spectral_class
        if self.subclass is not None:
            text += "%g" % self.subclass
        if self.luminosity is not None:
            text += self.luminosity
        for peculiarity in self.peculiarities:
            text += peculiarity
        return text

    def calc_eff_temperature(self):
        klass = None
        if self.main or self.carbon or self.wolf_rayet:
            if self.wolf_rayet:
                klass = 'W' + self.spectral_class
            else:
                klass = self.spectral_class
            klass_temps = self.spectral_temps.get(klass)
            luminosity = self.luminosity
            if luminosity is None: luminosity = 'V'
            lum_group = self.spectral_groups.get(luminosity)
            if klass_temps is not None and lum_group is not None:
                temps = klass_temps[lum_group]
            else:
                temps = None
            if temps is not None:
                if self.subclass is not None and isinstance(self.subclass, float):
                    self.temperature = temps[int(self.subclass)]
                else:
                    self.temperature = temps[4]
            else:
                self.temperature = 1000.0
        elif self.white_dwarf:
            if self.subclass is not None and isinstance(self.subclass, float):
                if self.subclass != 0:
                    self.temperature = 50400.0 / self.subclass
                else:
                    self.temperature = 100000.0
            else:
                self.temperature = 50400.0
        else:
            self.temperature = 1000.0

class SpectralTypeStringDecoder(object):
    main_spectral_classes = ['Y', 'T', 'L', 'M', 'K', 'G', 'F', 'A', 'B', 'O']
    obsolete_main = ['Ma', 'Mb', 'Mc', 'Md', 'Oa', 'Ob', 'Oc', 'Od', 'Oe']
    white_dwarf_prefix = 'D'
    white_dwarf_classes = ['A', 'B', 'C', 'O', 'Q', 'Z', 'X',
                           #Obsolete
                           'G', 'K', 'M', 'F'
                          ]
    # Mount Wilson classes
    mtw_prefix_1 = ['d', 'g', 'c']
    mtw_prefix_2 = ['sd', 'sg']
    mtw_luminosity = {'sd': 'VI', 'd': 'V', 'sg': 'IV', 'g': 'III', 'c': 'Iab'}

    wolf_rayet_prefix = 'W'
    wolf_rayet_classes = ['N', 'C', 'O']
    carbon_classes = ['C', 'S',
                      #Obsolete
                      'R', 'N']

    spectral_lines = ['k', 'm', 'h']

    luminosities = ["0", "Ia+", "Ia0", "Ia", "Iab", "Ib", "I", "II", "III", "IV", "V", "VI", "VII"]
    luminosities.sort(key=len, reverse=True)
    luminosities_first_char = ['I', 'V']
    sub_luminosities = []#'a0', 'a', 'ab', 'b']
    sub_luminosities.sort(key=len, reverse=True)
    peculiarity_types = [
                     #Ambiguous features
                     ':', '...', '!', 'comp', 'p', 'pq',
                     #Emission features
                     'e', '[e]', 'ep', 'eq', 'er', 'ev',
                     'f', 'f*', 'f+', '(f)', '(f+)', '((f))', '((f*))',
                     'ha', 'h',
                     #Absorption features
                     'He wk', 'k', 'm', 'n', 'nn', 'neb',
                     'q', 's', 'ss', 'sh', 'var', 'v', 'w', 'wl', 'wk',
                     #Unknown symbols
                     '+', '(Nova)', '..',
                     'CN', 'MN',
                     'S',
                     '(e)', '(n)', '(ne)', '(m)', '(p)', '(w)',
                     '(R)', '(T)']
    peculiarity_types.sort(key=len, reverse=True)

    cache = {}

    def decode_subclass(self, name, l, i):
        subclass = None
        if i < l and name[i].isdigit():
            subclass = float(name[i])
            i += 1
            if i < l - 1 and name[i] == '.' and name[i+1].isdigit():
                subclass += float(name[i+1]) / 10
                i += 2
        return (subclass, i)

    def decode_main_class(self, name, l, i):
        spectral_class = None
        subclass = None
        if i < l:
            spectral_class = name[i]
            i += 1
            subclass, i = self.decode_subclass(name, l, i)
        return spectral_class, subclass, i
    
    def decode_second_class(self, name, l, i, spectral_class):
        second_spectral_class = None
        second_subclass = None
        if i < l - 1 and (name[i] == '/' or name[i] == '-'):
            i += 1
            if not name[i].isdigit():
                second_spectral_class = name[i]
                i += 1
            else:
                second_spectral_class = spectral_class
            second_subclass, i = self.decode_subclass(name, l, i)
        return (second_spectral_class, second_subclass, i)
    
    def decode_abundance(self, name, l, i):
        abundance = None
        if i < l - 1 and name[i] == ',' and name[i+1].isdigit():
            abundance = float(name[i+1])
            i += 2
        return (abundance, i)

    def decode_luminosity(self, name, l, i):
        luminosity = None
        second_luminosity = None
        while i < l and name[i] == ' ': i+= 1
        if i >= l or name[i] not in self.luminosities_first_char:
            return (luminosity, second_luminosity, i)
        for value in self.luminosities:
            ll = len(value)
            if i < l - ll + 1 and name[i:i+ll] == value:
                luminosity = value
                i += ll
                for sub_luminosity in self.sub_luminosities:
                    lsl = len(sub_luminosity)
                    if i < l - lsl + 1 and name[i:i+lsl] == sub_luminosity:
                        luminosity += sub_luminosity
                        i += lsl
                        break
                if i < l - 1 and (name[i] == '/' or name[i] == '-'):
                    i += 1
                    for value in self.luminosities:
                        ll = len(value)
                        if i < l - ll + 1 and name[i:i+ll] == value:
                            second_luminosity = value
                            i += ll
                            for sub_luminosity in self.sub_luminosities:
                                lsl = len(sub_luminosity)
                                if i < l - lsl + 1 and name[i:i+lsl] == sub_luminosity:
                                    second_luminosity += sub_luminosity
                                    i += lsl
                                    break
                            return (luminosity, second_luminosity, i)
                    for sub_luminosity in self.sub_luminosities:
                        lsl = len(sub_luminosity)
                        if i < l - lsl + 1 and name[i:i+lsl] == sub_luminosity:
                            second_luminosity = luminosity + sub_luminosity
                            i += lsl
                            return (luminosity, second_luminosity, i)
                    i -= 1
                    return (luminosity, second_luminosity, i)
                else:
                    return (luminosity, second_luminosity, i)
        print("Unknown luminosity '%s' : '%s'" % (name, name[i:]))
        return (luminosity, second_luminosity, i)

    def decode_peculiarity(self, name, l, i):
        while i < l and name[i] == ' ': i+= 1
        if i >= l:
            return None, i
        #Disabling peculiarity parsing
        peculiarity = name[i:].strip()
        return name[i:], l
        for peculiarity in self.peculiarity_types:
            lp = len(peculiarity)
            if i < l - lp + 1 and name[i:i+lp] == peculiarity:
                return peculiarity, i + lp
        print("Unknown peculiarity '%s' : '%s'" %( name, name[i:]))
        return None, i

    def do_decode(self, spectral_type, name):
        l = len(name)
        i = 0
        if l == 0:
            return

        if i < l - 1 and name[i:i + 2] in self.obsolete_main:
            spectral_type.main = True
            spectral_type.spectral_class = name[i]
            spectral_type.subclass = name[i + 1]
            i += 2

        elif name[i] == self.white_dwarf_prefix:
            spectral_type.white_dwarf = True
            spectral_type.luminosity = ''
            i += 1
            if i < l:
                if name[i] in self.white_dwarf_classes:
                    spectral_type.spectral_class, spectral_type.subclass, i = self.decode_main_class(name, l, i)
                    spectral_type.peculiarity, i = self.decode_peculiarity(name, l, i)
                else:
                    print("unknown white dwarf type '%s'" % name)

        elif name[i] in self.mtw_prefix_1 or (i < l  - 1 and name[i:i + 2] in self.mtw_prefix_2):
            spectral_type.main = True
            if name[i] in self.mtw_prefix_1:
                spectral_type.luminosity = self.mtw_luminosity[name[i]]
                i += 1
            else:
                spectral_type.luminosity = self.mtw_luminosity[name[i:i + 2]]
                i += 2
            if i < l:
                if name[i] == ':':
                    #TODO: add this to luminosity peculiarity
                    i += 1
            if i < l:
                if name[i] in self.main_spectral_classes:
                    spectral_type.spectral_class, spectral_type.subclass, i = self.decode_main_class(name, l, i)
                    spectral_type.second_spectral_class, spectral_type.second_subclass, i = self.decode_second_class(name, l, i, spectral_type.spectral_class)
                    spectral_type.peculiarity, i = self.decode_peculiarity(name, l, i)
                else:
                    print("unknown class type '%s'" % name)

        elif name[i] == self.wolf_rayet_prefix:
            spectral_type.wolf_rayet = True
            i += 1
            if i < l:
                if name[i] in self.wolf_rayet_classes:
                    spectral_type.spectral_class, spectral_type.subclass, i = self.decode_main_class(name, l, i)
                    spectral_type.peculiarity, i = self.decode_peculiarity(name, l, i)
                else:
                    print("unknown wolf-rayet type '%s'" % name)

        elif name[i] in self.carbon_classes:
            spectral_type.carbon = True
            spectral_type.spectral_class, spectral_type.subclass, i = self.decode_main_class(name, l, i)
            spectral_type.abundance, i = self.decode_abundance(name, l, i)
            spectral_type.luminosity, spectral_type.second_luminosity, i = self.decode_luminosity(name, l, i)
            spectral_type.peculiarity, i = self.decode_peculiarity(name, l, i)

        elif name[i] in self.spectral_lines or name[i] in self.main_spectral_classes:
            if name[i] in self.spectral_lines:
                #TODO: Do something with the spectral lines...
                i += 1
            spectral_type.main = True
            spectral_type.spectral_class, spectral_type.subclass, i = self.decode_main_class(name, l, i)
            spectral_type.second_spectral_class, spectral_type.second_subclass, i = self.decode_second_class(name, l, i, spectral_type.spectral_class)
            spectral_type.luminosity, spectral_type.second_luminosity, i = self.decode_luminosity(name, l, i)
            spectral_type.peculiarity, i = self.decode_peculiarity(name, l, i)
            if spectral_type.luminosity == 'VII':
                # Luminosity class 'VII' is rarely used
                spectral_type.main = False
                spectral_type.white_dwarf = True
                spectral_type.luminosity = ''
        else:
            print("Unknown class '%s'" % name)

    def decode(self, name):
        if not name in self.cache:
            spectral_type = SpectralType()
            self.do_decode(spectral_type, name)
            spectral_type.calc_eff_temperature()
            self.cache[name] = spectral_type
        return self.cache[name]

class SpectralTypeIntDecoder(object):
    cache = {}
    def decode(self, value):
        if not value in self.cache:
            spectral_type = SpectralType()
            star_type = value >> 12
            stellar_class = (value >> 8) & 0xf
            sub_class = (value >> 4) & 0xf
            luminosity = (value & 0xf)


            if star_type == 0:
                # Normal star
                stellar_class_map = ["O", "B", "A", "F", "G", "K", "M", "R", "S", "N", "W", "W", "?", "L", "T", "C"]
                luminosity_map = ["I-a0", "I-a", "I-b", "II", "III", "IV", "V", "VI", ""]
                spectral_type.spectral_class = stellar_class_map[stellar_class]
                spectral_type.subclass = float(sub_class)
                spectral_type.luminosity = luminosity_map[luminosity]
                if stellar_class <= 6:
                    spectral_type.main = True
                elif stellar_class <= 9:
                    spectral_type.carbon = True
                elif stellar_class <= 11:
                    spectral_type.wolf_rayet = True
                elif stellar_class == 12:
                    pass
                elif stellar_class <= 14:
                    spectral_type.main = True
                elif stellar_class == 15:
                    spectral_type.carbon = True
                else:
                    pass
            elif star_type == 1:
                #White dwarf
                stellar_class_map = ['A', 'B', 'C', 'O', 'Q', 'Z', '', 'X']
                spectral_type.white_dwarf = True
                spectral_type.spectral_class = stellar_class_map[stellar_class]
                spectral_type.subclass = float(sub_class)
                spectral_type.luminosity = ""
            else:
                spectral_type.spectral_class = "?"
                spectral_type.subclass = 0
                spectral_type.luminosity = ""
            spectral_type.calc_eff_temperature()
            self.cache[value] = spectral_type
        return self.cache[value]

spectralTypeStringDecoder = SpectralTypeStringDecoder()
spectralTypeIntDecoder = SpectralTypeIntDecoder()
