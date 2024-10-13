#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from abc import ABC, abstractmethod
from math import cos, pi


class EasingInterface(ABC):

    @abstractmethod
    def easing(self, t): ...


class NoEasing(EasingInterface):

    def easing(self, t):
        return t


class CubicEasing(EasingInterface):

    def easing(self, t):
        return t * t * (-2.0 * t + 3.0)


class SinEasing(EasingInterface):

    def easing(self, t):
        return -(cos(t * pi) - 1) / 2


class ExpEasing(EasingInterface):

    accel = 2
    speed = 20
    delta = pow(accel, -speed / 2) / 2
    width = 0.5 / (0.5 - delta)

    def easing(self, t):
        if t < 0.5:
            v = pow(self.accel, self.speed * (t - 0.5)) / 2
            return (v - self.delta) * self.width
        else:
            v = (2 - pow(self.accel, -self.speed * (t - 0.5))) / 2
            return 0.5 + (v - 0.5) * self.width
