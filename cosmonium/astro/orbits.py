from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LPoint3d, LVector3d, LQuaterniond

from . import units
from .frame import J2000EclipticReferenceFrame, J2000EquatorialReferenceFrame
from math import sqrt, pi, cos, sin, acos, asin, atan2
from .zeros import newton

class Orbit(object):
    def __init__(self, frame=None):
        if frame is None:
            frame = J2000EclipticReferenceFrame()
        self.frame = frame
        self.origin = LPoint3d()

    def set_frame(self, frame):
        self.frame = frame

    def getPeriod(self):
        return 0, 0

    def get_global_position_at(self, time):
        return self.origin

    def get_position_at(self, time):
        return None

    def get_rotation_at(self, time):
        return None

    def project(self, time, center, radius):
        return None

    def get_apparent_radius(self):
        return 0.0

class FixedPosition(Orbit):
    #TODO: Rename into something like GlobalFixedPosition
    def __init__(self, position=None,
                 right_asc=0.0, right_asc_unit=units.Deg,
                 declination=0.0, declination_unit=units.Deg,
                 distance=0.0, distance_unit=units.Ly,
                 frame=None):
        Orbit.__init__(self, frame)
        if position is None:
            self.right_asc = right_asc * right_asc_unit
            self.declination = declination * declination_unit
            distance = distance * distance_unit
        else:
            self.right_asc = None
            self.declination = None
            if not isinstance(position, LPoint3d):
                position = LPoint3d(*position)
        if position is None:
            inclination = pi / 2 - self.declination
            ascending_node = self.right_asc + pi / 2
            inclination_quat = LQuaterniond()
            inclination_quat.setFromAxisAngleRad(inclination, LVector3d.unitX())
            ascending_node_quat = LQuaterniond()
            ascending_node_quat.setFromAxisAngleRad(ascending_node, LVector3d.unitZ())
            self.orientation = inclination_quat * ascending_node_quat * J2000EquatorialReferenceFrame.orientation
            position = self.orientation.xform(LVector3d(0, 0, distance))
        self.global_position = position
        self.position=LPoint3d()
        self.rotation=LQuaterniond()

    def calc_asc_decl(self):
        distance = self.global_position.length()
        if distance > 0:
            position = J2000EquatorialReferenceFrame.orientation.conjugate().xform(self.global_position)
            self.declination = asin(position[2] / distance)
            self.right_asc = atan2(position[1], position[0])
        else:
            self.right_asc = 0.0
            self.declination = 0.0

    def get_right_asc(self):
        if self.right_asc is None:
            self.calc_asc_decl()
        return self.right_asc
    
    def get_declination(self):
        if self.declination is None:
            self.calc_asc_decl()
        return self.declination
    
    def project(self, time, center, radius):
        vector = self.global_position - center
        vector /= vector.length()
        vector *= radius
        return vector
    
    def get_global_position_at(self, time):
        return self.global_position

    def get_position_at(self, time):
        return self.position

    def get_rotation_at(self, time):
        return self.rotation
    
class InfinitePosition(Orbit):
    def __init__(self,
                 right_asc=0.0, right_asc_unit=units.Deg,
                 declination=0.0, declination_unit=units.Deg,
                 frame=None):
        Orbit.__init__(self, frame)
        self.right_asc = right_asc * right_asc_unit
        self.declination = declination * declination_unit
        inclination = pi / 2 - self.declination
        ascending_node = self.right_asc + pi / 2
        inclination_quat = LQuaterniond()
        inclination_quat.setFromAxisAngleRad(inclination, LVector3d.unitX())
        ascending_node_quat = LQuaterniond()
        ascending_node_quat.setFromAxisAngleRad(ascending_node, LVector3d.unitZ())
        self.orientation = inclination_quat * ascending_node_quat * J2000EquatorialReferenceFrame.orientation
        self.position=LPoint3d()
        self.rotation=LQuaterniond()

    def project(self, time, center, radius):
        return self.orientation.xform(LVector3d(0, 0, radius))
    
    def get_position_at(self, time):
        return self.position

    def get_rotation_at(self, time):
        return self.rotation
    
class FixedOrbit(Orbit):
    def __init__(self, position=LPoint3d(0, 0, 0), rotation=LQuaterniond(), frame=None):
        Orbit.__init__(self, frame)
        self.position = position
        self.rotation = rotation

    def get_position_at(self, time):
        return self.position

    def get_rotation_at(self, time):
        return self.rotation

class CircularOrbit(Orbit):
    def __init__(self,
                 radius,
                 radius_units=units.AU,
                 radial_speed=None,
                 period=None,
                 period_units=units.JYear,
                 inclination=0,
                 ascending_node=0.0,
                 arg_of_periapsis=None,
                 long_of_pericenter=None,
                 mean_anomaly=None,
                 mean_longitude=0.0,
                 epoch=units.J2000,
                 frame=None):
        Orbit.__init__(self, frame)
        self.radius = radius * radius_units
        if radial_speed is None:
            if period is None:
                self.mean_motion = 0.0
                self.period = 0.0
            else:
                self.period = period * period_units
                self.mean_motion = 2*pi/self.period
        else:
            self.mean_motion = radial_speed
            self.period = 2*pi/self.mean_motion/period_units
        if arg_of_periapsis is None:
            if long_of_pericenter is None:
                arg_of_periapsis = 0.0
            else:
                arg_of_periapsis = long_of_pericenter - ascending_node
        if inclination == 0.0:
            #Ascending node is undefined if there is no inclination
            ascending_node = 0.0
        if mean_anomaly is None:
            mean_anomaly = mean_longitude - (arg_of_periapsis + ascending_node)
        self.inclination = inclination * pi / 180
        self.ascending_node = ascending_node * pi / 180
        self.arg_of_periapsis = arg_of_periapsis * pi / 180
        self.mean_anomaly = mean_anomaly * pi / 180
        self.epoch = epoch
        inclination_quat = LQuaterniond()
        inclination_quat.setFromAxisAngleRad(self.inclination, LVector3d.unitX())
        arg_of_periapsis_quat = LQuaterniond()
        arg_of_periapsis_quat.setFromAxisAngleRad(self.arg_of_periapsis, LVector3d.unitZ())
        ascending_node_quat = LQuaterniond()
        ascending_node_quat.setFromAxisAngleRad(self.ascending_node, LVector3d.unitZ())
        #self.rotation = ascending_node_quat * inclination_quat * arg_of_periapsis_quat
        self.rotation = arg_of_periapsis_quat * inclination_quat * ascending_node_quat
        
    def getPeriod(self):
        return self.period, self.mean_motion

    def get_position_at(self, time):
        angle = (time - self.epoch) * self.mean_motion + self.mean_anomaly
        x=cos(angle) * self.radius
        y=sin(angle) * self.radius
        return LPoint3d(x, y, 0.0)

    def get_rotation_at(self, time):
        return self.rotation

    def get_apparent_radius(self):
        return self.radius

class EllipticalOrbit(CircularOrbit):
    def __init__(self,
             semi_major_axis=None,
             semi_major_axis_units=units.AU,
             pericenter_distance=None,
             pericenter_distance_units=units.AU,
             radial_speed=None,
             period=None,
             period_units=units.JYear,
             eccentricity=0.0,
             inclination=0,
             ascending_node=0.0,
             arg_of_periapsis=None,
             long_of_pericenter=None,
             mean_anomaly=None,
             mean_longitude=0.0,
             epoch = units.J2000,
             frame=None):
        CircularOrbit.__init__(self, 0, 0, radial_speed, period, period_units, inclination, ascending_node, arg_of_periapsis, long_of_pericenter, mean_anomaly, mean_longitude, epoch, frame)
        self.eccentricity = eccentricity
        if pericenter_distance is None:
            if semi_major_axis is None:
                self.pericenter_distance = 1
            else:
                self.pericenter_distance = semi_major_axis  * semi_major_axis_units * (1.0 - self.eccentricity)
        else:
            self.pericenter_distance = pericenter_distance * pericenter_distance_units
        self.apocenter_distance = self.pericenter_distance * (1.0 + self.eccentricity) / (1.0 - self.eccentricity)

    def get_apparent_radius(self):
        return self.apocenter_distance

    def get_position_at(self, time):
        mean_anomaly = (time - self.epoch) * self.mean_motion + self.mean_anomaly
        def kepler_func(x):
            return mean_anomaly + self.eccentricity * sin(x) - x
        def kepler_func_prime(x):
            return  self.eccentricity * cos(x) - 1
        def solve_fixed(f, x0, maxiter):
            x=0
            res=x0
            for i in range(0, maxiter):
                x = res
                res = f(x)
            return res
        try:
            #eccentric_anomaly=solve_fixed(kepler_func, mean_anomaly, maxiter=5)
            eccentric_anomaly=newton(kepler_func, mean_anomaly, kepler_func_prime, maxiter=10)
        except RuntimeError:
            print("Could not converge", self.body.get_name())
            eccentric_anomaly = mean_anomaly
        a = self.pericenter_distance / (1.0 - self.eccentricity)
        x = a * (cos(eccentric_anomaly) - self.eccentricity)
        y = a * sqrt(1 - self.eccentricity * self.eccentricity) * sin(eccentric_anomaly)
        return LPoint3d(x, y, 0.0)
