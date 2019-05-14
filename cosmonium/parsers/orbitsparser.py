from __future__ import print_function
from __future__ import absolute_import

from ..astro.elementsdb import orbit_elements_db
from ..astro.orbits import FixedPosition, FixedOrbit, EllipticalOrbit
from ..astro import units

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .utilsparser import DistanceUnitsYamlParser, TimeUnitsYamlParser, AngleUnitsYamlParser
from .utilsparser import FrameYamlParser

class EllipticOrbitYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        semi_major_axis = data.get('semi-major-axis', None)
        semi_major_axis_units = DistanceUnitsYamlParser.decode(data.get('semi-major-axis-units', 'AU'))
        pericenter_distance = data.get('pericenter-distance', None)
        pericenter_distance_units = DistanceUnitsYamlParser.decode(data.get('pericenter-distance-units', 'AU'))
        period = data.get('period', None)
        period_units = TimeUnitsYamlParser.decode(data.get('period-units', 'Year'))
        radial_speed = data.get('radial-speed', None)
        eccentricity = data.get('eccentricity', 0.0)
        inclination = data.get('inclination', 0.0)
        ascending_node = data.get('ascending-node', 0.0)
        arg_of_periapsis = data.get('arg-of-periapsis', None)
        long_of_pericenter = data.get('long-of-pericenter', None)
        mean_anomaly = data.get('mean-anomaly', None)
        mean_longitude = data.get('mean-longitude', 0.0)
        epoch = data.get('epoch', units.J2000)
        frame = FrameYamlParser.decode(data.get('frame', 'J2000Ecliptic'))
        return EllipticalOrbit(semi_major_axis,
                              semi_major_axis_units,
                              pericenter_distance,
                              pericenter_distance_units,
                              radial_speed,
                              period,
                              period_units,
                              eccentricity,
                              inclination,
                              ascending_node,
                              arg_of_periapsis,
                              long_of_pericenter,
                              mean_anomaly,
                              mean_longitude,
                              epoch,
                              frame)

class FixedPositionYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        ra = data.get('ra', 0.0)
        ra_units = AngleUnitsYamlParser.decode(data.get('ra-units', 'Deg'))
        decl = data.get('de', 0.0)
        decl_units = AngleUnitsYamlParser.decode(data.get('de-units', 'Deg'))
        distance = data.get('distance', 0.0)
        distance_units = DistanceUnitsYamlParser.decode(data.get('distance-units', 'pc'))
        frame = FrameYamlParser.decode(data.get('frame', 'J2000Equatorial'))
        return FixedPosition(right_asc=ra,
                             right_asc_unit=ra_units,
                             declination=decl,
                             declination_unit=decl_units,
                             distance=distance,
                             distance_unit=distance_units,
                             frame=frame)

class OrbitYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        if data is None: return FixedOrbit()
        (object_type, parameters) = cls.get_type_and_data(data)
        if object_type == 'elliptic':
            orbit = EllipticOrbitYamlParser.decode(parameters)
        elif object_type == 'fixed':
            orbit = FixedPositionYamlParser.decode(parameters)
        else:
            orbit = orbit_elements_db.get(data)
        return orbit

class NamedOrbitYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        name = data.get('name')
        category = data.get('category')
        if name is None or category is None: return None
        orbit = OrbitYamlParser.decode(data)
        orbit_elements_db.register_element(category, name, orbit)
        return None

ObjectYamlParser.register_object_parser('orbit', NamedOrbitYamlParser())
