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


from ..appearances import Appearance
from ..components.elements.surfaces import EllipsoidFlatSurface
from ..shaders.rendering import RenderingShader
from ..shaders.lighting.flat import FlatLightingModel
from ..shapes.spheres import SphereShape


class SurfaceFactory(object):
    def create(self, body):
        return None


class StarTexSurfaceFactory(SurfaceFactory):
    def __init__(self, texture):
        self.texture = texture

    def create(self, body):
        shape = SphereShape()
        appearance = Appearance(emissionColor=body.anchor.point_color, texture=self.texture)
        shader = RenderingShader(lighting_model=FlatLightingModel())
        return EllipsoidFlatSurface(
            'surface',
            radius=body.radius,
            oblateness=body.oblateness,
            scale=body.scale,
            shape=shape,
            appearance=appearance,
            shader=shader,
        )
