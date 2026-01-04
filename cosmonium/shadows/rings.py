#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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


from panda3d.core import Texture
from panda3d.core import LVector3d
from panda3d.core import LColor

from ..entities.datasource import DataSource
from ..shadows.base import ShadowCasterBase
from ..shaders.shadows.rings import ShaderRingsShadow
from .. import settings


class RingsShadowCaster(ShadowCasterBase):

    def __init__(self, light, ring):
        ShadowCasterBase.__init__(self, light)
        self.ring = ring
        self.name = self.ring.owner.get_ascii_name()

    def is_analytic(self):
        # Although ring shadows are analytic, ity still requires the ring texture.
        # So we need to return False here to force the texture loading
        return False

    def create_shader_component(self):
        return ShaderRingsShadow()

    def create_data_source(self):
        return RingsShadowDataSource(self.ring)

    def add_target(self, entity):
        entity.shadows.add_ring_shadow_caster(self)


class RingsShadowDataSource(DataSource):

    def __init__(self, ring):
        DataSource.__init__(self, 'ring-shadow')
        self.ring = ring

    def update(self, shape, instance, camera_pos, camera_rot):
        (texture, texture_size, texture_lod) = self.ring.appearance.texture.source.get_texture(self.ring.shape)
        if texture is None:
            texture = Texture()
            texture.setup_2d_texture(1, 1, Texture.T_unsigned_byte, Texture.F_rgba8)
            texture.set_clear_color(LColor(0, 0, 0, 0))
        instance.set_shader_input('shadow_ring_tex', texture)
        normal = shape.owner.anchor.get_absolute_orientation().xform(LVector3d.up())
        instance.set_shader_input('ring_normal', normal)
        instance.set_shader_input(
            'ring_inner_radius', self.ring.inner_radius * shape.owner.scene_anchor.scene_scale_factor
        )
        instance.set_shader_input(
            'ring_outer_radius', self.ring.outer_radius * shape.owner.scene_anchor.scene_scale_factor
        )
        if shape.owner.support_offset_body_center and settings.offset_body_center:
            body_center = shape.owner.scene_anchor.scene_position + shape.owner.scene_anchor.world_body_center_offset
        else:
            body_center = shape.owner.scene_anchor.scene_position
        instance.set_shader_input('body_center', body_center)
