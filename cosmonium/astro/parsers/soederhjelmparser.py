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

from .parser import *

import sys, os

class SoederhejlmAstrometricParser(FixedFieldsParser):
    regex = re.compile('^' + I6 + A1 # HIP, solutions
                       + F4 + PAD + F4 + PAD # Primary magnitude, magnitude difference
                       + F4 + PAD + F3 + PAD # Mass ratio + error
                       + F6 + PAD + F4 + PAD # Parallax + error
                       + F6 + PAD + F4 + PAD # HIP Parallax + error
                       + I3 + PAD + I2 + PAD + I2 + PAD # Mass uncertainty
                       + F4 + PAD + A2 + PAD # Mas sum + flags
                       + F6 + PAD + F7 + PAD # Period, epoch
                       + F5 + PAD + F3 + PAD # SMA, eccentricity
                       + I3 + PAD + I3 + PAD + I3 # Inclination, arg of periapsis, pa of node
                       )
    def __init__(self):
        self.catalogues = {'HIP': {}}
        self.systems = []

    def parse_line(self, line):
        m = self.regex.search(line)
        if m is not None:
            (hip, hip_flags,
             mag, mag_diff,
             mass_ratio, mas_ratio_error,
             parallax, parallax_error,
             hip_parallax, hip_parallax_error,
             total_uncertainty, plx_uncertainty, orbit_uncertainty,
             mass_sum, mass_sum_flags,
             period, epoch,
             sma, eccentricity,
             inclination, arg_of_periapsis, pa_of_node) = m.groups()
            hip = hip.strip()
            system = {'src': 'soederhjelm',
                      'hip': hip,
                      'multiplicity': '',
                      'mag': float(mag),
                      'mag_diff': float(mag_diff),
                      'mass_sum': float(mass_sum),
                      'mass_ratio': float(mass_ratio),
                      'period': float(period) * units.JYear,
                      'epoch': float(epoch) * units.JYear + units.J1BC,
                      'semimajoraxis': float(sma),
                      'eccentricity': float(eccentricity),
                      'inclination': float(inclination),
                      'arg_of_periapsis': float(arg_of_periapsis),
                      'pa_of_node': float(pa_of_node)}
            self.systems.append(system)
            self.catalogues['HIP'][hip] = system
        else:
            print("Soederhjelm-1: Invalid line", line)

class SoederhejlmNonAstrometricParser(FixedFieldsParser):
    regex = re.compile('^' + I6 + A2 + A1 # HIP, multiplicity, solutions
                       + F5 + PAD + A1 + F4 + A1 + PAD # Primary magnitude, limit flag, magnitude difference, uncertainty
                       + F4 + PAD # V-I Color
                       + F5 + PAD + F3 + PAD # Parallax + error
                       + F5 + PAD + F4 + A1 + PAD # HIP Parallax + error + uncertainty
                       + F4 + PAD # Abs magnitude
                       + I2 + PAD + I2 + PAD + I2 + PAD # Mass uncertainty
                       + F5 + PAD + F4 + A1 + PAD + A2 + PAD # Mas sum + mass-ratio + uncertainty + flags
                       + F8 + A1 + F7 + PAD # Period, flags, epoch
                       + F6 + A1 + PAD + F3 + PAD # SMA, flag, eccentricity
                       + I3 + PAD + I3 + PAD + I3 # Inclination, arg of periapsis, pa of node
                       )
    def __init__(self):
        self.catalogues = {'HIP': {}}
        self.systems = []

    def parse_line(self, line):
        m = self.regex.search(line)
        if m is not None:
            (hip, multiplicity, hip_flags,
             mag, limit, mag_diff, uncertainty,
             v_i_color,
             parallax, parallax_error,
             hip_parallax, hip_parallax_error, hip_parallax_uncertainty,
             abs_magnitude,
             total_uncertainty, plx_uncertainty, orbit_uncertainty,
             mass_sum, mass_ratio, mass_uncertainty, mass_sum_flags,
             period, period_flags, epoch,
             sma, sma_flags, eccentricity,
             inclination, arg_of_periapsis, pa_of_node) = m.groups()
            hip = hip.strip()
            mass_ratio = self.to_float(mass_ratio)
            multiplicity = multiplicity.strip()
            if mass_ratio is not None:
                system = {'src': 'soederhjelm',
                          'hip': hip,
                          'multiplicity': multiplicity,
                          'mag': float(mag),
                          'mag_diff': float(mag_diff),
                          'mass_sum': float(mass_sum),
                          'mass_ratio': mass_ratio,
                          'period': float(period) * units.JYear,
                          'epoch': float(epoch) * units.JYear + units.J1BC,
                          'semimajoraxis': float(sma),
                          'eccentricity': float(eccentricity),
                          'inclination': float(inclination),
                          'arg_of_periapsis': float(arg_of_periapsis),
                          'pa_of_node': float(pa_of_node)}
                self.systems.append(system)
                self.catalogues['HIP'][hip] = system
        else:
            print("Soederhjelm-2: Invalid line", line)

class SoederhejlmParser(object):
    def load(self, filepath):
        astrometric = os.path.join(filepath, 'table1.dat')
        non_astrometric = os.path.join(filepath, 'table3.dat')
        non_astrometric_10 = os.path.join(filepath, 'table4.dat')
        astrometricparser = SoederhejlmAstrometricParser()
        astrometricparser.load(astrometric)
        non_astrometricparser = SoederhejlmNonAstrometricParser()
        non_astrometricparser.load(non_astrometric)
        non_astrometricparser.load(non_astrometric_10)
        self.astrometric = astrometricparser.systems
        self.astrometric_catalogues = astrometricparser.catalogues
        self.non_astrometric = non_astrometricparser.systems
        self.non_astrometric_catalogues = non_astrometricparser.catalogues

if __name__ == '__main__':
    if len(sys.argv) == 2:
        parser = SoederhejlmParser()
        parser.load(sys.argv[1])
        #print(parser.astrometric)
        #print(parser.non_astrometric)
    else:
        print("Invalid number of parameters")
