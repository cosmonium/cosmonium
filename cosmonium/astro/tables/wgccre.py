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

from ..frame import J2000EquatorialReferenceFrame

from ..rotations import UniformRotation
from ..elementsdb import rotation_elements_db

from .. import units

def WgccreSimpleRotation(ra, d, w, p):
    return UniformRotation(
             period=360 / p,
             period_units=units.Day,
             right_asc=ra, right_asc_unit=units.Deg,
             declination=d, declination_unit=units.Deg,
             meridian_angle=w,
             epoch=units.J2000,
             frame=J2000EquatorialReferenceFrame())

wgccre_simple = { 'sun':     WgccreSimpleRotation(286.13, 63.87, 84.176, 14.1844000),
                  'mercury': WgccreSimpleRotation(281.0103, 61.4155, 329.5988, 6.1385108),
                  'venus':   WgccreSimpleRotation(272.76, 67.16, 160.20, -1.4813688),
                  #'earth':   WgccreSimpleRotation(),
                  'mars':    WgccreSimpleRotation(317.269202, 54.432516, 176.049863, 350.891982443297),
                  'jupiter': WgccreSimpleRotation(268.056595, 64.495303, 284.95, 870.5360000),
                  'saturn':  WgccreSimpleRotation(40.589, 83.537, 38.90, 810.7939024),
                  'uranus':  WgccreSimpleRotation(257.311, -15.175, 203.81, 501.1600928),
                  'neptune': WgccreSimpleRotation(299.36, 43.46, 249.978, 541.1397757),
                  #Mars
                  'phobos':  WgccreSimpleRotation(317.67071657, 52.88627266, 34.9964842535, 1128.84475928),
                  'deimos':  WgccreSimpleRotation(316.65705808, 53.50992033, 79.39932954, 285.16188899),
                  #Jupiter
                  'metis':    WgccreSimpleRotation(268.05, 64.49, 346.09, 1221.2547301),
                  'adrastea': WgccreSimpleRotation(268.05, 64.49, 33.29, 1206.9986602),
                  'amalthea': WgccreSimpleRotation(268.05, 64.49, 231.67, 722.6314560),
                  'thebe':    WgccreSimpleRotation(268.05, 64.49, 8.56, 533.7004100),
                  'io':       WgccreSimpleRotation(268.05, 64.50, 200.39, 203.4889538),
                  'europa':   WgccreSimpleRotation(268.08, 64.5, 36.022, 101.3747235),
                  'ganymede': WgccreSimpleRotation(268.20, 64.57, 44.064, 50.3176081),
                  'callisto': WgccreSimpleRotation(268.72, 64.83, 259.51, 21.5710715),
                  #Saturn
                  'pan':        WgccreSimpleRotation(40.6, 83.5, 48.8, 626.0440000),
                  'atlas':      WgccreSimpleRotation(40.58, 83.53, 137.88, 598.3060000),
                  'prometheus': WgccreSimpleRotation(40.58, 83.53, 296.14, 587.289000),
                  'pandora':    WgccreSimpleRotation(40.58, 83.53, 162.92, 572.7891000),
                  'epimetheus': WgccreSimpleRotation(40.58, 83.52, 293.87, 518.4907239),
                  'janus':      WgccreSimpleRotation(40.58, 83.52, 58.83, 518.2359876),
                  'mimas':      WgccreSimpleRotation(40.66, 83.52, 333.46, 381.9945550),
                  'enceladus':  WgccreSimpleRotation(40.66, 83.52, 6.32, 262.7318996),
                  'tethys':     WgccreSimpleRotation(40.66, 83.52, 8.95, 190.6979085),
                  'telesto':    WgccreSimpleRotation(50.51, 84.06, 56.88, 190.6979332),
                  'calypso':    WgccreSimpleRotation(36.41, 85.04, 153.51, 190.6742373),
                  'dione':      WgccreSimpleRotation(40.66, 83.52, 357.6, 131.5349316),
                  'helene':     WgccreSimpleRotation(40.85, 83.34, 245.12, 131.6174056),
                  'rhea':       WgccreSimpleRotation(40.38, 83.55, 235.16, 79.6900478),
                  'titan':      WgccreSimpleRotation(39.4827, 83.4279, 186.5855, 22.5769768),
                  'iapetus':    WgccreSimpleRotation(318.16, 75.03, 355.2, 4.5379572),
                  'phoebe':     WgccreSimpleRotation(356.90, 77.80, 178.58, 931.639),
                  #Uranus
                  'cordelio':  WgccreSimpleRotation(257.31, -15.18, 127.69, -1074.5205730),
                  'ophelia':   WgccreSimpleRotation(257.31, -15.18, 130.35, -956.4068150),
                  'bianca':    WgccreSimpleRotation(257.31, -15.18, 105.46, -828.3914760),
                  'cressida':  WgccreSimpleRotation(257.31, -15.18, 59.16, -776.5816320),
                  'desdemona': WgccreSimpleRotation(257.31, -15.18, 95.08, -760.0531690),
                  'juliet':    WgccreSimpleRotation(257.31, -15.18, 302.56, -730.1253660),
                  'portia':    WgccreSimpleRotation(257.31, -15.18, 25.03, -701.4865870),
                  'rosalind':  WgccreSimpleRotation(257.31, -15.18, 314.90, -644.6311260),
                  'belinda':   WgccreSimpleRotation(257.31, -15.18, 297.46, -577.3628170),
                  'puck':      WgccreSimpleRotation(257.31, -15.18, 91.24, -472.5450690),
                  'miranda':   WgccreSimpleRotation(257.43, -15.08, 30.70, -254.6906892),
                  'ariel':     WgccreSimpleRotation(257.43, -15.10, 156.22, -142.8356681),
                  'umbriel':   WgccreSimpleRotation(257.43, -15.10, 108.05, -86.8688923),
                  'titania':   WgccreSimpleRotation(257.43, -15.10, 77.74, -41.3514316),
                  'oberon':    WgccreSimpleRotation(257.43, -15.10, 6.77, -26.7394932),
                  #Neptune
                  'naiad':    WgccreSimpleRotation(299.36, 43.36, 254.06, 1222.8441209),
                  'thalassa': WgccreSimpleRotation(299.36, 43.45, 102.06, 1155.7555612),
                  'despina':  WgccreSimpleRotation(299.36, 43.45, 306.51, 1075.7341562),
                  'galatea':  WgccreSimpleRotation(299.36, 43.43, 258.09, 839.6597686),
                  'larissa':  WgccreSimpleRotation(299.36, 43.41, 179.41, 649.0534470),
                  'proteus':  WgccreSimpleRotation(299.27, 42.91, 93.38, 320.7654228),
                  'triton':   WgccreSimpleRotation(299.36, 41.17, 296.53, -61.2572637),
                  #Dwarf planets / asteroids
                  'ceres':   WgccreSimpleRotation(291.418, 66.764, 170.650, 952.1532),
                  'pallas':  WgccreSimpleRotation(33, -3, 38, 1105.8036),
                  'vesta':   WgccreSimpleRotation(309.031, 42.235, 285.39, 1617.3329428),
                  'lutetia': WgccreSimpleRotation(52, 12, 94, 1057.7515),
                  'europa':  WgccreSimpleRotation(257, 12, 55, 1534.6472187),
                  'ida':     WgccreSimpleRotation(168.76, -87.12, 274.05, 1864.6280070),
                  'eros':    WgccreSimpleRotation(11.35, 17.22, 326.07, 1639.38864745),
                  'davida':  WgccreSimpleRotation(297, 5, 268.1, 1684.4193549),
                  'gaspra':  WgccreSimpleRotation(9.47, 26.70, 83.67, 1226.9114850),
                  'steins':  WgccreSimpleRotation(91, -62, 321.76, 1428.09917),
                  'itokawa': WgccreSimpleRotation(90.53, -66.30, 0, 712.143),
                  'pluto':   WgccreSimpleRotation( 132.993, -6.163, 302.695, 56.3625225),
                  'charon':  WgccreSimpleRotation( 132.993,-6.163, 122.695, 56.3625225),
                  }
rotation_elements_db.register_category('wgccre', 1)

for (element_name, element) in wgccre_simple.items():
    rotation_elements_db.register_element('wgccre', element_name, element)
