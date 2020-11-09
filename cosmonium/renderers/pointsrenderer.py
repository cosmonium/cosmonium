#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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

from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LPoint3

from ..pointsset import PointsSet
from ..sprites import RoundDiskPointSprite, GaussianPointSprite, ExpPointSprite, MergeSprite
from ..utils import mag_to_scale

from .. import settings

class PointsRenderer(object):
    def __init__(self, context):
        self.context = context
        self.pointset = PointsSet(use_sprites=True, sprite=GaussianPointSprite(size=16, fwhm=8))
        if settings.render_sprite_points:
            self.pointset.instance.reparentTo(self.context.world)
        
        self.haloset = PointsSet(use_sprites=True, sprite=ExpPointSprite(size=256, max_value=0.6), background=settings.halo_depth)
        if settings.render_sprite_points:
            self.haloset.instance.reparentTo(self.context.world)

    def reset(self):
        self.pointset.reset()
        self.haloset.reset()

    def update(self, observer):
        self.pointset.update()
        self.haloset.update()
        
    def add_point(self, point_color, scene_position, visible_size, app_magnitude, oid_color):
        if visible_size < settings.min_body_size * 2:
            scale = mag_to_scale(app_magnitude)
            if scale > 0:
                color = point_color * scale
                size = max(settings.min_point_size, settings.min_point_size + scale * settings.mag_pixel_scale)
                self.pointset.add_point(scene_position, color, size, oid_color)

    def add_halo(self, point_color, scene_position, visible_size, app_magnitude, oid_color):
        if settings.show_halo and app_magnitude < settings.smallest_glare_mag:
            coef = settings.smallest_glare_mag - app_magnitude + 6.0
            radius = max(1.0, visible_size)
            size = radius * coef * 2.0
            self.haloset.add_point(LPoint3(*scene_position), point_color, size * 2, oid_color)
