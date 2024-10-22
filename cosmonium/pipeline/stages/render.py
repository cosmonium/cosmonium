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


import builtins
from panda3d.core import DepthTestAttrib
from panda3d.core import Texture, LColor

from ...textures import TextureConfiguration

from ..stage import RenderSceneStage
from ..target import SceneTarget, PasstroughTarget


class RenderStage(RenderSceneStage):

    def __init__(self, name, camera_mask, colors, srgb=True, multisamples=0, inverse_z=False, create_mimap=False):
        RenderSceneStage.__init__(self, name, camera_mask)
        self.colors = colors
        self.srgb = srgb
        self.multisamples = multisamples
        self.inverse_z = inverse_z
        self.create_mipmap = create_mimap

    def provides(self):
        return {'scene': 'color', 'depth': 'depth'}

    def can_render_to_screen(self):
        return not self.inverse_z

    def create(self, pipeline):
        if self.screen_stage:
            target = PasstroughTarget("scene")
        else:
            target = SceneTarget("scene")
            if self.create_mipmap:
                config = TextureConfiguration(
                    wrap_u=Texture.WM_border_color,
                    wrap_v=Texture.WM_border_color,
                    minfilter=Texture.FT_linear_mipmap_linear,
                )
            else:
                config = TextureConfiguration()
            target.add_color_target(self.colors, srgb_colors=self.srgb, config=config)
            if self.inverse_z:
                target.add_depth_target(32, float_depth=True)
            else:
                target.add_depth_target(24)
            target.set_multisamples(self.multisamples)
        self.add_target(target)
        target.create(pipeline)
        target.dr.set_clear_color_active(True)
        target.dr.set_clear_color(LColor(0, 0, 0, 1))
        target.dr.set_clear_depth_active(True)
        if self.inverse_z:
            target.dr.set_clear_depth(0.0)
            builtins.base.common_state.set_attrib(DepthTestAttrib.make(DepthTestAttrib.M_greater))
        else:
            target.dr.set_clear_depth(1.0)
            builtins.base.common_state.set_attrib(DepthTestAttrib.make(DepthTestAttrib.M_less_equal))
