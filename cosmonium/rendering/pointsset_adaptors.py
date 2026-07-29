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


from .. import settings


class PassthroughPointsSetShapeAdaptor:
    def __init__(self, shape):
        self.shape = shape

    def reset(self):
        self.shape.reset()

    def configure(self, scene_manager, configurator):
        configurator.configure_shape(self.shape)
        self.shape.instance.reparent_to(scene_manager.root)

    def reconfigure(self, scene_manager, configurator):
        pass

    def add_objects(self, scene_manager, scene_anchors):
        if not settings.render_sprite_points:
            return
        self.shape.add_objects(scene_manager, scene_anchors)


class RegionsPointsSetShapeAdaptor:
    def __init__(self, shape_class, has_size, has_oid, screen_scale):
        self.shape_class = shape_class
        self.has_size = has_size
        self.has_oid = has_oid
        self.screen_scale = screen_scale
        self.shapes = {}

    def reset(self):
        self.shapes = {}

    def configure(self, scene_manager, configurator):
        pass

    def reconfigure(self, scene_manager, configurator):
        for region, sub_shape in self.shapes.items():
            # sub_shape.configure(region, configurator)
            configurator.configure_shape(sub_shape)
            sub_shape.instance.reparent_to(region.root)

    def add_objects(self, scene_manager, scene_anchors):
        if not settings.render_sprite_points:
            return
        for region in scene_manager.get_regions():
            current_shape = self.shape_class(self.has_size, self.has_oid, self.screen_scale)
            current_shape.reset()
            self.shapes[region] = current_shape
            current_shape.add_objects(scene_manager, region.get_points_collection())
