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

from ..stage import SceneStage
from ..target import SceneTarget, PasstroughTarget

class RenderStage(SceneStage):
    def __init__(self, name, srgb=True, multisamples=0, inverse_z=False):
        SceneStage.__init__(self, name)
        self.srgb = srgb
        self.multisamples = multisamples
        self.inverse_z = inverse_z

    def provides(self):
        return {'scene': 'color'}

    def can_render_to_screen(self):
        return not self.inverse_z

    def create(self, pipeline):
        if self.screen_stage:
            target = PasstroughTarget("scene")
        else:
            target = SceneTarget("scene")
            target.add_color_target((pipeline.color_bits, pipeline.color_bits, pipeline.color_bits, pipeline.alpha_bits), srgb_colors=self.srgb)
            if self.inverse_z:
                target.add_depth(32, float_depth=True)
            else:
                target.add_depth(24)
            target.set_multisamples(self.multisamples)
        self.add_target(target)
        target.create(pipeline)
        target.dr.set_clear_color_active(True)
        target.dr.set_clear_color(LColor(0, 0, 0, 1))
        target.dr.set_clear_depth_active(True)
        if self.inverse_z:
            target.dr.set_clear_depth(0.0)
            base.common_state.set_attrib(DepthTestAttrib.make(DepthTestAttrib.M_greater))
        else:
            target.dr.set_clear_depth(1.0)
            base.common_state.set_attrib(DepthTestAttrib.make(DepthTestAttrib.M_less_equal))
