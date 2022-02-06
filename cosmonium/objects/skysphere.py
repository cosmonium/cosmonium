#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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


from panda3d.core import LQuaternion, LColor, BitMask32

from ..foundation import VisibleObject
from ..shapes.spheres import ScaledSphereShape
from ..astro.rotations import UnknownRotation
from ..shaders.rendering import RenderingShader
from ..shaders.lighting.flat import FlatLightingModel
from .. import settings


class SkySphere(VisibleObject):
    def __init__(self, names, shape=None, appearance=None, shader=None, orientation=None):
        #TODO: should be a ShapeObject instead !
        VisibleObject.__init__(self, names)
        self.appearance = appearance
        if orientation is None:
            orientation = UnknownRotation()
        self.orientation = orientation
        if shape is None:
            shape = ScaledSphereShape(self.context.observer.infinity, inv_texture_u=True)
        self.shape = shape
        self.shape.parent = self
        #TODO: should be done like that or should we have EmisionAppearance ?
        if appearance.emissionColor is None:
            appearance.emissionColor = LColor(1, 1, 1, 1)
        if shader is None:
            shader = RenderingShader(lighting_model=FlatLightingModel())
        self.shader = shader

    def create_instance(self):
        if not self.instance:
            self.instance = self.shape.create_instance()
            if self.instance is None:
                return
        if self.appearance is not None:
            self.appearance.bake()
            self.appearance.apply(self)
        self.instance.setQuat(LQuaternion(*self.orientation))
        self.instance.set_two_sided(True)
        self.instance.setCollideMask(BitMask32.allOff())
        self.instance.reparentTo(self.context.world)
        self.instance.setBin('background', settings.skysphere_depth)
        self.instance.set_depth_write(False)
