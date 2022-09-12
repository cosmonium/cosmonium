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


from panda3d.core import DepthTestAttrib
from panda3d.core import LColor

from ..stage import RenderSceneStage
from ..target import SceneTarget, PasstroughTarget

class AnnotationsRenderStage(RenderSceneStage):
    def __init__(self, name, camera_mask, colors, srgb=True, inverse_z=False):
        RenderSceneStage.__init__(self, name, camera_mask)
        self.colors = colors
        self.srgb = srgb
        self.inverse_z = inverse_z

    def requires(self):
        return ['scene', 'depth']

    def provides(self):
        return {'scene': 'color',
                'depth': 'depth'}

    def can_render_to_screen(self):
        return False

    def create(self, pipeline):
        target = SceneTarget("annotations")
        scene = self.get_source('scene')
        target.add_color_target(self.colors, srgb_colors=self.srgb, texture=scene)
        depth = self.get_source('depth')
        if self.inverse_z:
            target.add_depth_target(32, float_depth=True, texture=depth)
        else:
            target.add_depth_target(24, texture=depth)
        self.add_target(target)
        target.create(pipeline)
        if self.inverse_z:
            target.dr.set_clear_depth(0.0)
            base.common_state.set_attrib(DepthTestAttrib.make(DepthTestAttrib.M_greater))
        else:
            target.dr.set_clear_depth(1.0)
            base.common_state.set_attrib(DepthTestAttrib.make(DepthTestAttrib.M_less_equal))
