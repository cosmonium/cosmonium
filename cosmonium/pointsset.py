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


from panda3d.core import GeomNode
from panda3d.core import OmniBoundingVolume, ShaderAttrib

from .foundation import VisibleObject
from .appearances import ModelAppearance
from .shaders.rendering import RenderingShader
from .shaders.lighting.flat import FlatLightingModel
from .shaders.point_control import StaticSizePointControl
from .sprites import SimplePoint, RoundDiskPointSprite
from . import settings

try:
    from cosmonium_engine import EmissivePointsSetShape, ScaledEmissivePointsSetShape, HaloPointsSetShape
except ImportError as e:
    print("WARNING: Could not load PointsSet C implementation, fallback on python implementation")
    print("\t", e)
    from .pyrendering.pointsset import EmissivePointsSetShape, ScaledEmissivePointsSetShape, HaloPointsSetShape

from .pyrendering.pointsset import PassthroughPointsSetShape, RegionsPointsSetShape


class PointsSetShapeObject(VisibleObject):
    default_camera_mask = VisibleObject.DefaultCameraFlag
    tex = None

    def __init__(self, shape, use_sprites=True, use_sizes=True, points_size=2, sprite=None, background=None, shader=None):
        VisibleObject.__init__(self, 'pointsset')
        self.use_sprites = use_sprites
        self.use_sizes = use_sizes
        self.use_oids = True
        self.background = background
        if shader is None:
            if settings.use_hardware_sprites:
                point_control = StaticSizePointControl()
            else:
                point_control = None
            shader = RenderingShader(lighting_model=FlatLightingModel(), vertex_oids=True, point_control=point_control)
        self.shader = shader
        self.shape = shape
        self.shape.reset()

        if self.use_sprites:
            if sprite is None:
                sprite = RoundDiskPointSprite()
            self.sprite = sprite
        else:
            self.sprite = SimplePoint(points_size)
        #TODO: Should not use ModelAppearance !
        self.appearance = ModelAppearance(vertex_color=True)

    def configure(self, scene_manager):
        self.shape.configure(scene_manager, self)

    def configure_shape(self, shape):
        self.sprite.apply(shape.instance)
        shape.instance.setCollideMask(GeomNode.getDefaultCollideMask())
        shape.instance.node().setPythonTag('owner', self)
        # TODO: This is wrong 
        self.appearance.scan_model(shape.instance)
        self.appearance.apply(shape, shape.instance)
        # TODO: Don't recreate shader each time
        self.shader.create(None, self.appearance)
        self.shader.apply(shape.instance)
        if self.use_sprites:
            shape.instance.node().setBounds(OmniBoundingVolume())
            shape.instance.node().setFinal(True)
        if self.background is not None:
            shape.instance.setBin('background', self.background)
        shape.instance.set_depth_write(False)
        shape.instance.hide(self.AllCamerasMask)
        shape.instance.show(self.default_camera_mask)
        if settings.use_hardware_sprites and self.use_sizes:
            attrib = shape.instance.get_attrib(ShaderAttrib)
            shape.instance.setAttrib(attrib.set_flag(ShaderAttrib.F_shader_point_size, True))

    def reset(self):
        self.shape.reset()

    def add_objects(self, scene_manager, scene_anchors):
        self.shape.add_objects(scene_manager, scene_anchors)
        self.shape.reconfigure(scene_manager, self)

    def update(self):
        pass