#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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

"""Ring shadow implementation.

This module provides classes for implementing ring shadows, which are shadows
cast by planetary rings onto surfaces below them.
"""


from panda3d.core import LColor, LVector3d, Texture

from .. import settings
from ..entities.datasource import DataSource
from ..shaders.shadows.rings import ShaderRingsShadow
from ..shadows.base import ShadowCasterBase


class RingsShadowCaster(ShadowCasterBase):
    """Shadow caster for planetary ring shadows.

    Handles the creation and management of shadows cast by planetary rings
    onto surfaces below them.
    """

    def __init__(self, light, ring):
        """Initialize ring shadow caster.

        Args:
            light: Light source for casting shadows.
            ring: Ring object casting the shadows.
        """
        ShadowCasterBase.__init__(self, light)
        self.ring = ring
        self.name = self.ring.owner.get_ascii_name()

    def is_analytic(self):
        """Check if this shadow caster uses analytic shadows.

        Returns:
            False, as ring shadows require texture loading.
        """
        # Although ring shadows are analytic, ity still requires the ring texture.
        # So we need to return False here to force the texture loading
        return False

    def create_shader_component(self):
        """Create shader component for ring shadows.

        Returns:
            ShaderRingsShadow instance.
        """
        return ShaderRingsShadow()

    def create_data_source(self):
        """Create data source for ring shadow uniforms.

        Returns:
            RingsShadowDataSource instance.
        """
        return RingsShadowDataSource(self.ring)

    def add_target(self, entity):
        """Add target entity to receive ring shadows.

        Args:
            entity: Entity to receive shadows.
        """
        entity.shadows.add_ring_shadow_caster(self)


class RingsShadowDataSource(DataSource):
    """Data source for ring shadow shader uniforms.

    Provides the necessary uniforms for ring shadow rendering in shaders.
    """

    def __init__(self, ring):
        """Initialize ring shadow data source.

        Args:
            ring: Ring object providing shadow data.
        """
        DataSource.__init__(self, 'ring-shadow')
        self.ring = ring

    def update(self, shape, instance, camera_pos, camera_rot):
        """Update ring shadow uniforms for the current frame.

        Args:
            shape: Shape receiving shadows.
            instance: Node path instance.
            camera_pos: Camera position.
            camera_rot: Camera rotation.
        """
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
