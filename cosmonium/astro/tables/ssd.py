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

from __future__ import absolute_import

from ..orbits import EllipticalOrbit
from ..frame import J2000EclipticReferenceFrame, CelestialReferenceFrame, EquatorialReferenceFrame

from ..elementsdb import orbit_elements_db
from .. import units

import itertools

J1950Jan1 = 2433282.5
J1986Jan19_5 = 2446450.0
J1989Aug18_5 = 2447757.0
J1989Aug25 = 2447763.5
J1997Jan16 = 2450464.5
J2004Jan1 = 2453005.5
J2004Aug25_5 = 2453243.0
J2008May14 = 2454600.5
J2008Sep22 = 2454000.5
J2008Nov30 = 2454800.5
J2019Apr27 = 2458600.5

class JupiterReferenceFrame(CelestialReferenceFrame):
    def __init__(self):
        CelestialReferenceFrame.__init__(self, right_asc=268.057, declination=64.495)

class UranusReferenceFrame(CelestialReferenceFrame):
    def __init__(self):
        CelestialReferenceFrame.__init__(self, right_asc=257.311, declination=-15.175)

charonMeanOrbitFrame = CelestialReferenceFrame(right_asc=133.05142, declination=-6.17674)

def SsdPlanetOrbit(p, a, e, i, w, o, m, epoch=units.J2000):
    return EllipticalOrbit(
             period=p,  period_units=units.JYear,
             semi_major_axis=a, semi_major_axis_units=units.AU,
             eccentricity=e,
             inclination=i,
             long_of_pericenter=w,
             ascending_node=o,
             mean_longitude=m,
             epoch=epoch,
             frame=J2000EclipticReferenceFrame())

def SsdDwarfOrbit(p, a, e, i, w, o, m, epoch):
    return EllipticalOrbit(
             period=p,  period_units=units.JYear,
             semi_major_axis=a, semi_major_axis_units=units.AU,
             eccentricity=e,
             inclination=i,
             arg_of_periapsis=w,
             ascending_node=o,
             mean_anomaly=m,
             epoch=epoch,
             frame=J2000EclipticReferenceFrame())

def SsdMoonOrbit(p, a, e, w, m, i, o, epoch=units.J2000, f=None):
    if f is None:
        f = EquatorialReferenceFrame()
    return EllipticalOrbit(
             period=p,  period_units=units.Day,
             semi_major_axis=a, semi_major_axis_units=units.Km,
             eccentricity=e,
             inclination=i,
             arg_of_periapsis=w,
             ascending_node=o,
             mean_anomaly=m,
             epoch=epoch,
             frame=f)

def SsdLaplaceOrbit(p, a, e, w, m, i, o, ra, d, epoch=units.J2000):
    frame = CelestialReferenceFrame(right_asc=ra, declination=d)
    return EllipticalOrbit(
             period=p,  period_units=units.Day,
             semi_major_axis=a, semi_major_axis_units=units.Km,
             eccentricity=e,
             inclination=i,
             arg_of_periapsis=w,
             ascending_node=o,
             mean_anomaly=m,
             epoch=epoch,
             frame=frame)

def SsdMoon2Orbit(p, a, e, i, o, w, m, epoch=units.J2000, f=None):
    if f is None:
        f = EquatorialReferenceFrame()
    return EllipticalOrbit(
             period=p,  period_units=units.Day,
             semi_major_axis=a, semi_major_axis_units=units.Km,
             eccentricity=e,
             inclination=i,
             long_of_pericenter=w,
             ascending_node=o,
             mean_longitude=m,
             epoch=epoch,
             frame=f)

def SsdCometOrbit(p, a, e, i, w, o, m, epoch):
    return EllipticalOrbit(
             period=p,  period_units=units.Day,
             semi_major_axis=a, semi_major_axis_units=units.AU,
             eccentricity=e,
             inclination=i,
             arg_of_periapsis=w,
             ascending_node=o,
             mean_anomaly=m,
             epoch=epoch,
             frame=J2000EclipticReferenceFrame())

ssd_planets = {
    'mercury':      SsdPlanetOrbit(  0.2408467,  0.38709893, 0.20563069, 7.00487,  77.45645,  48.33167, 252.25084),
    'venus':        SsdPlanetOrbit(  0.61519726, 0.72333199, 0.00677323, 3.39471, 131.53298,  76.68069, 181.97973),
    'earth-system': SsdPlanetOrbit(  1.0000174,  1.00000011, 0.01671022, 0.00005, 102.94719, 348.73936, 100.46435),
    'mars':         SsdPlanetOrbit(  1.8808476,  1.52366231, 0.09341233, 1.85061, 336.04084,  49.57854, 355.45332),
    'jupiter':      SsdPlanetOrbit( 11.862615,   5.20336301, 0.04839266, 1.30530,  14.75385, 100.55615,  34.40438),
    'saturn':       SsdPlanetOrbit( 29.447498,   9.53707032, 0.05415060, 2.48446,  92.43194, 113.71504,  49.94432),
    'uranus':       SsdPlanetOrbit( 84.016846,  19.19126393, 0.04716771, 0.76986, 170.96424,  74.22988, 313.23218),
    'neptune':      SsdPlanetOrbit(164.79132,   30.06896348, 0.00858587, 1.76917,  44.97135, 131.72169, 304.88003),
}

ssd_dwarf_planets = {
    'ceres':        SsdDwarfOrbit(  4.607,    2.7667817, 0.07954162, 10.58640,  72.96457,  80.40699, 301.6548490, J2008May14),
    'pluto-system': SsdDwarfOrbit(247.92065, 39.4450697, 0.25024871, 17.08900, 112.59714, 110.37696,  25.2471897, J2008Sep22),
    'eris':         SsdDwarfOrbit(558.75,    67.840,     0.43747,    44.0790,  151.57,     35.9276,  198.490,     J2008May14),
    'makemake':     SsdDwarfOrbit(306.17,    45.426,     0.161,      28.999,   295.154,    79.572,   151.598,     J2008Nov30),
    'haumea':       SsdDwarfOrbit(283.28,    43.133,     0.195,      28.22,    239.184,   122.103,   202.675,     J2008Nov30),

    '2007or10': SsdDwarfOrbit(  553.05, 67.37610770137752,  0.502886641131433,  30.73927683821048,  207.5464021379094,  336.8435936217937, 105.26523287066,   J2019Apr27),
    'quaoar':   SsdDwarfOrbit(  288.81, 43.69157469300723,  0.03955254846935317, 7.988127832822885, 146.4063512588845,  188.8371917258692, 300.7086402479591, J2019Apr27),
    'sedna':    SsdDwarfOrbit(10513.35, 479.9048662568563,  0.8413195848948128, 11.92992424953418,   11.92992424953418, 144.3274552335066, 358.0410177555543, J2019Apr27),
    '2002ms4':  SsdDwarfOrbit(  272.31,  42.0115344245481,  0.1389353283859966, 17.67275515552901,  213.30041324409,    215.9401603424431, 223.0097117806958, J2019Apr27),
    'orcus':    SsdDwarfOrbit(  246.06,  39.26631237879172, 0.2241543633848243, 20.59309162927599,   72.16021189938247, 268.8064721762331, 180.3453764078719, J2019Apr27),
    'salacia':  SsdDwarfOrbit(  272.75,  42.05690689579897, 0.1084607994794708, 23.92151609319524,  310.9787879081173, 279.8932300989333,  122.9873110751723, J2019Apr27),
}

ssd_major_moons = {
    #Earth
    'moon':    SsdMoonOrbit(27.322, 384400, 0.0554, 318.15,  135.27,  5.16,  125.08,  units.J2000, J2000EclipticReferenceFrame()),
    #Mars
    'phobos': SsdLaplaceOrbit(0.319,  9380, 0.0151, 150.247,  92.474, 1.075, 164.931, 317.724, 52.924, J1950Jan1),
    'deimos': SsdLaplaceOrbit(1.262, 23460, 0.0002, 290.496, 296.230, 1.793, 339.600, 316.700, 53.564, J1950Jan1),
    #Jupiter
    'io':       SsdLaplaceOrbit(1.769,  421800, 0.0041,  84.129, 342.021, 0.036,  43.977, 268.057, 64.495, J1997Jan16),
    'europa':   SsdLaplaceOrbit(3.551,  671100, 0.0094,  88.970, 171.016, 0.466, 219.106, 268.084, 64.506, J1997Jan16),
    'ganymede': SsdLaplaceOrbit(7.155, 1070400, 0.0013, 192.417, 317.540, 0.177,  63.552, 268.168, 64.543, J1997Jan16),
    'callisto': SsdLaplaceOrbit(16.69, 1882700, 0.0074,  52.643, 181.408, 0.192, 298.848, 268.639, 64.749, J1997Jan16),
    #Saturn
    'mimas':     SsdLaplaceOrbit(  0.942,  185540, 0.0196,  14.352, 255.312,   1.572, 153.152,  40.590, 83.539, J2004Jan1),
    'enceladus': SsdLaplaceOrbit(  1.370,  238040, 0.0047, 211.923, 197.047,   0.009,  93.204,  40.587, 83.539, J2004Jan1),
    'tethys':    SsdLaplaceOrbit(  1.888,  294670, 0.0001, 262.845, 189.003,   1.091, 330.882,  40.581, 83.539, J2004Jan1),
    'dione':     SsdLaplaceOrbit(  2.737,  377420, 0.0022, 168.820,  65.990,   0.028, 168.909,  40.554, 83.542, J2004Jan1),
    'rhea':      SsdLaplaceOrbit(  4.518,  527070, 0.0010, 256.609, 311.551,   0.331, 311.531,  40.387, 83.556, J2004Jan1),
    'titan':     SsdLaplaceOrbit( 15.95,  1221870, 0.0288, 185.671,  15.154,   0.280,  24.502,  36.470, 83.936, J2004Jan1),
    'hyperion':  SsdLaplaceOrbit( 21.28,  1500880, 0.0274, 324.183, 295.906,   0.630, 264.022,  37.258, 83.819, J2004Jan1),
    'iapetus':   SsdLaplaceOrbit( 79.33,  3560840, 0.0283, 275.921, 356.029,   7.489,  75.831, 288.818, 78.667, J2004Jan1),
    'phoebe':    SsdLaplaceOrbit(550.31, 12947780, 0.1635, 345.582, 287.593, 175.986, 241.570, 277.897, 67.124, J2004Jan1),
    #Uranus
    'miranda': SsdMoonOrbit( 1.413, 129900, 0.0013,  68.312, 311.330, 4.338, 326.438, f=UranusReferenceFrame()),
    'ariel':   SsdMoonOrbit( 2.520, 190900, 0.0012, 115.349,  39.481, 0.041,  22.394, f=UranusReferenceFrame()),
    'umbriel': SsdMoonOrbit( 4.144, 266000, 0.0039,  84.709,  12.469, 0.128,  33.485, f=UranusReferenceFrame()),
    'titania': SsdMoonOrbit( 8.706, 436300, 0.0011, 284.400,  24.614, 0.079,  99.771, f=UranusReferenceFrame()),
    'oberon':  SsdMoonOrbit(13.46,  583500, 0.0014, 104.400, 283.088, 0.068, 279.771, f=UranusReferenceFrame()),
    #Neptune
    'proteus': SsdLaplaceOrbit(  1.122, 117647, 0.0005, 301.706, 117.050,   0.026, 162.690, 299.583, 42.417, J1989Aug18_5),
    'triton':  SsdLaplaceOrbit(  5.877, 354800, 0.0000, 344.046, 264.775, 156.834, 172.431, 299.452, 43.395, J1989Aug25),
    'nereid':  SsdLaplaceOrbit(360.14, 5513400, 0.7512, 280.830, 359.341,   7.232, 334.762, 282.462, 75.854, J1989Aug25),
    #Pluto
    'charon':  SsdMoonOrbit( 6.387,  17536, 0.0022,  71.255, 147.848, 0.001,  85.187, f=charonMeanOrbitFrame),
}

ssd_inner_moons = {
    # Jupiter
    'metis':    SsdMoonOrbit(0.295, 128000, 0.0012, 297.177, 276.047, 0.019, 146.912, J1997Jan16, JupiterReferenceFrame()),
    'adrastea': SsdMoonOrbit(0.298, 129000, 0.0018, 328.047, 135.673, 0.054, 228.378, J1997Jan16, JupiterReferenceFrame()),
    'amalthea': SsdMoonOrbit(0.498, 181400, 0.0032, 155.873, 185.194, 0.380, 108.946, J1997Jan16, JupiterReferenceFrame()),
    'thebe':    SsdMoonOrbit(0.675, 221900, 0.0176, 234.269, 135.956, 1.080, 108.946, J1997Jan16, JupiterReferenceFrame()),
    # Saturn
    'pan':        SsdMoon2Orbit(0.57505, 133584, 0.000035, 0.001,  20,     176,     146.59, units.J2000),
    'daphnis':    SsdMoon2Orbit(0.59408, 136504, 0,        0,       0,       0,     222.952, 2453491.9),
    'atlas':      SsdMoon2Orbit(0.60169, 137670, 0.0012,   0.003,   0.500, 332.021, 129.760, J2004Jan1),
    'prometheus': SsdMoon2Orbit(0.61299, 139380, 0.0022,   0.008, 259.504,  63.893, 306.117, J2004Jan1),
    'pandora':    SsdMoon2Orbit(0.62850, 141720, 0.0042,   0.050, 327.215,  50.676, 253.373, J2004Jan1),
    'janus':      SsdMoon2Orbit(0.69466, 151460, 0.0068,   0.163,  46.899, 288.678, 171.432, J2004Jan1),
    'epimetheus': SsdMoon2Orbit(0.69433, 151410, 0.0098,   0.351,  85.244,  37.847, 346.196, J2004Jan1),
    # Uranus
    'cordelia':  SsdMoonOrbit(0.335, 49800, 0.0003, 136.827, 254.805, 0.085,  38.374, J1986Jan19_5),
    'ophelia':   SsdMoonOrbit(0.376, 53800, 0.0099,  17.761, 116.259, 0.104, 164.048, J1986Jan19_5),
    'bianca':    SsdMoonOrbit(0.435, 59200, 0.0009,   8.293, 138.486, 0.193,  93.220, J1986Jan19_5),
    'cressida':  SsdMoonOrbit(0.464, 61800, 0.0004,  44.236, 233.795, 0.006,  99.403, J1986Jan19_5),
    'desdemona': SsdMoonOrbit(0.474, 62700, 0.0001, 183.285, 184.627, 0.113, 306.089, J1986Jan19_5),
    'juliet':    SsdMoonOrbit(0.493, 64400, 0.0007, 223.819, 244.696, 0.065, 200.155, J1986Jan19_5),
    'portia':    SsdMoonOrbit(0.513, 66100, 0.0001, 222.433, 218.312, 0.059, 260.067, J1986Jan19_5),
    'rosalind':  SsdMoonOrbit(0.558, 69900, 0.0001, 140.477, 136.181, 0.279,  12.847, J1986Jan19_5),
    'cupid':     SsdMoonOrbit(0.613, 74392, 0.0013, 247.608, 163.830, 0.099, 182.793, J2004Aug25_5),
    'belinda':   SsdMoonOrbit(0.624, 75300, 0.0001,  42.406, 357.224, 0.031, 279.337, J1986Jan19_5),
    'perdita':   SsdMoonOrbit(0.638, 76417, 0.0116, 253.925, 192.405, 0.470, 309.376, J2004Aug25_5),
    'puck':      SsdMoonOrbit(0.762, 86000, 0.0001, 177.094, 245.796, 0.319, 268.734, J1986Jan19_5),
    'mab':       SsdMoonOrbit(0.923, 97736, 0.0025, 249.565, 273.769, 0.134, 350.737, J1986Jan19_5),
    # Neptune
    'naiad':    SsdLaplaceOrbit(0.294, 48227, 0.0004, 0, 0, 4.746, 0, 299.431, 42.940, J1989Aug18_5),
    'thalassa': SsdLaplaceOrbit(0.311, 50075, 0.0002, 0, 0, 0.209, 0, 299.431, 42.939, J1989Aug18_5),
    'despina':  SsdLaplaceOrbit(0.335, 52526, 0.0002, 0, 0, 0.064, 0, 299.431, 42.937, J1989Aug18_5),
    'galatea':  SsdLaplaceOrbit(0.429, 61953, 0.0000, 0, 0, 0.062, 0, 299.430, 42.925, J1989Aug18_5),
    'larissa':  SsdLaplaceOrbit(0.555, 73548, 0.0014, 0, 0, 0.205, 0, 299.429, 42.897, J1989Aug18_5),
    # Pluto
    'styx':    SsdMoonOrbit(20.16, 42393, 0.0006, 330.244, 194.546, 0.080,  26.956, f=charonMeanOrbitFrame),
    'nix':     SsdMoonOrbit(24.85, 48671, 0.0000, 324.463, 284.405, 0.000, 203.400, f=charonMeanOrbitFrame),
    'kerebos': SsdMoonOrbit(32.17, 57729, 0.0000, 160.629, 161.061, 0.426, 305.871, f=charonMeanOrbitFrame),
    'hydra':   SsdMoonOrbit(38.20, 64698, 0.0056, 153.307, 326.678, 0.304, 113.173, f=charonMeanOrbitFrame),
    # Eris
    'dysnomia': SsdMoonOrbit(15.774, 37350, 0, 0, 0, 0, 0),
    # Haumea
    'namaka': SsdMoonOrbit(18.3, 25660, 0.25, 0, 0, 113.013, 0),
    'hiiaka': SsdMoonOrbit(49.4, 49880, 0.05, 0, 0, 126.356, 0),
    # 2007 OR10
    's2007or101': SsdMoonOrbit(6, 15000, 0.31, 0, 0, 0, 0),
    # Quaoar
    'weywot': SsdMoonOrbit(12.438, 14500, 0.14, 0, 0, 0.14, 0),
    # Orcus
    'vanth': SsdMoonOrbit(9.5406, 9030, 0.007, 0, 0, 21, 0),
    # Salacia
    'actaea': SsdMoonOrbit(5.49380, 5619, 0.0084, 0, 0, 0, 0),
}

ssd_asteroids = {
    'pallas': SsdCometOrbit(1686.155999342055, 2.772465922815752, 0.2303368122519394, 34.83623460557907,  310.0488584525203, 173.0800618276949, 59.69913098405375, J2019Apr27),
    'juno':   SsdCometOrbit(1592.787284087904, 2.669149515649107, 0.2569423149737984, 12.98891943923851,  248.1386297217077, 169.8527548037533, 34.92501898650092, J2019Apr27),
    'vesta':  SsdCometOrbit(1325.432764736216, 2.361417895877277, 0.08872145950956178, 7.141770811873426, 150.7285412870121, 103.810804427096,  95.86193620017683, J2019Apr27),
}

ssd_comets = {
    'halley': SsdCometOrbit(27509.1290731861, 17.8341442925537,   0.967142908462304, 162.262690579161,   111.3324851045177,  58.42008097656843,  38.3842644764388,   2449400.5),
    '9p':     SsdCometOrbit(2037.951672378393, 3.145794166571019, 0.5096459803932888, 10.4737498480644,  179.202032429995,   68.75013903945421, 345.2364494836611,   2457519.5),
    '67p':    SsdCometOrbit(2355.612450811296, 3.46473701803964,  0.6405847372930017,  7.043698689343029, 12.69446404906225, 50.18000114437616,  92.07346224536946,  2455493.5),
    '81p':    SsdCometOrbit(2342.495969932252, 3.451863526325708, 0.5370707300610902,  3.237247549683569, 41.75623208556019, 136.0976855407395,  85.97576116427592,  2455809.5),
    '103p':   SsdCometOrbit(2360.898405736858, 3.46991828939617,  0.6948983400864248, 13.61932727050992, 181.2096850329413, 219.7584952349638,    4.229104992556878, 2455525.5),
}
#Slightly higher priority than kepler orbits
orbit_elements_db.register_category('ssd', 1)

for (element_name, element) in itertools.chain(ssd_planets.items(),
                                               ssd_dwarf_planets.items(),
                                               ssd_major_moons.items(),
                                               ssd_inner_moons.items(),
                                               ssd_asteroids.items(),
                                               ssd_comets.items()):
    orbit_elements_db.register_element('ssd', element_name, element)
