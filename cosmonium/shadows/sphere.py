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


from math import asin
from panda3d.core import LMatrix4, PTA_LMatrix4, LQuaternion

from ..entities.datasource import DataSource

from .base import ShadowCasterBase


class SphereShadowCaster(ShadowCasterBase):

    def __init__(self, light, occluder):
        ShadowCasterBase.__init__(self, light)
        self.occluder = occluder

    def is_analytic(self):
        return True

    def add_target(self, entity):
        entity.shadows.add_sphere_shadow_caster(self)


class SphereShadowDataSource(DataSource):

    def __init__(self, shadow_casters, max_occluders, far_sun, oblate_occluder):
        DataSource.__init__(self, 'sphere-shadows')
        self.shadow_casters = shadow_casters
        self.max_occluders = max_occluders
        self.far_sun = far_sun
        self.oblate_occluder = oblate_occluder

    def update(self, shape, instance, camera_pos, camera_rot):
        if len(self.shadow_casters.shadow_casters) == 0:
            print("ERROR: No lights for", shape, shape.owner.get_name())
            return
        self.light = self.shadow_casters.shadow_casters[0].light
        scale = shape.owner.scene_anchor.scene_scale_factor
        if self.far_sun:
            vector = shape.owner.anchor.get_local_position() - self.light.source.anchor.get_local_position()
            distance_to_light_source = vector.length()
            instance.set_shader_input(
                'star_ar', asin(self.light.source.get_apparent_radius() / distance_to_light_source)
            )
        star_center = (self.light.source.anchor.get_local_position() - camera_pos) * scale
        star_radius = self.light.source.get_apparent_radius() * scale
        instance.set_shader_input('star_center', star_center)
        instance.set_shader_input('star_radius', star_radius)
        centers = []
        radii = []
        occluder_transform = PTA_LMatrix4()
        if len(self.shadow_casters.shadow_casters) > self.max_occluders:
            print("Too many occluders")
        nb_of_occluders = 0
        for shadow_caster in self.shadow_casters.shadow_casters:
            # TODO: The selection should be done on the angular radius of the shadow.
            if nb_of_occluders >= self.max_occluders:
                break
            nb_of_occluders += 1
            occluder = shadow_caster.occluder
            centers.append((occluder.anchor.get_local_position() - camera_pos) * scale)
            radius = occluder.get_apparent_radius()
            radii.append(radius * scale)
            if self.oblate_occluder:
                # TODO: This should refactored with the code in oneil and moved to the body class
                body_scale = occluder.surface.get_shape_axes()
                descale = LMatrix4.scale_mat(radius / body_scale[0], radius / body_scale[1], radius / body_scale[2])
                rotation_mat = LMatrix4()
                orientation = LQuaternion(*occluder.anchor.get_absolute_orientation())
                orientation.extract_to_matrix(rotation_mat)
                rotation_mat_inv = LMatrix4()
                rotation_mat_inv.invert_from(rotation_mat)
                descale_mat = rotation_mat_inv * descale * rotation_mat
                occluder_transform.push_back(descale_mat)
        instance.set_shader_input('occluder_centers', centers)
        instance.set_shader_input('occluder_radii', radii)
        if self.oblate_occluder:
            instance.set_shader_input('occluder_transform', occluder_transform)
        instance.set_shader_input("nb_of_occluders", nb_of_occluders)
