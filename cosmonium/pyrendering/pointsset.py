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


from panda3d.core import GeomVertexArrayFormat, InternalName, GeomVertexFormat, GeomVertexData, GeomVertexWriter
from panda3d.core import GeomPoints, Geom, GeomNode
from panda3d.core import NodePath, LPoint3
from ..utils import mag_to_scale
from .. import settings


class PointsSetShape:
    def __init__(self, has_size, has_oid):
        self.has_size = has_size
        self.has_oid = has_oid
        self.gnode = GeomNode('starfield')
        self.instance = NodePath(self.gnode)
        self.geom = None
        self.geom_points = None
        self.vdata = None
        self.index = 0

    def make_geom(self):
        array = GeomVertexArrayFormat()
        array.add_column(InternalName.get_vertex(), 3, Geom.NT_float32, Geom.C_point)
        array.add_column(InternalName.get_color(), 4, Geom.NT_float32, Geom.C_color)
        if self.has_size:
            array.add_column(InternalName.get_size(), 1, Geom.NT_float32, Geom.C_other)
        if self.has_oid:
            oids_column_name = InternalName.make('oid')
            array.add_column(oids_column_name, 4, Geom.NT_float32, Geom.C_other)
        source_format = GeomVertexFormat()
        source_format.add_array(array)
        vertex_format = GeomVertexFormat.register_format(source_format)
        self.vdata = GeomVertexData('vdata', vertex_format, Geom.UH_stream)
        self.geom_points = GeomPoints(Geom.UH_stream)
        self.geom = Geom(self.vdata)
        self.geom.add_primitive(self.geom_points)

    def reset(self):
        self.gnode.remove_all_geoms()
        self.make_geom()
        self.gnode.add_geom(self.geom)
        self.index = 0

    def create_writers(self):
        self.vwriter = GeomVertexWriter(self.vdata, InternalName.get_vertex())
        self.colorwriter = GeomVertexWriter(self.vdata, InternalName.get_color())
        if self.has_size:
            self.sizewriter = GeomVertexWriter(self.vdata, InternalName.get_size())
        if self.has_oid:
            oids_column_name = InternalName.make('oid')
            self.oidwriter = GeomVertexWriter(self.vdata, oids_column_name)

    def configure(self, scene_manager, configurator):
        configurator.configure_shape(self)
        self.instance.reparent_to(scene_manager.root)

    def reconfigure(self, scene_manager, configurator):
        pass

    def add_point(self, point, color, size, oid):
        self.vwriter.set_data3(*point)
        self.colorwriter.set_data4(color)
        if self.has_size:
            self.sizewriter.set_data1(size)
        if self.has_oid:
            self.oidwriter.set_data4(oid)
        self.geom_points.add_vertex(self.index)
        self.index += 1

    def add_object(self, scene_anchor):
        raise NotImplementedError()

    def add_objects(self, scene_manager, scene_anchors):
        self.vdata.set_num_rows(len(scene_anchors))
        self.geom_points.reserve_num_vertices(len(scene_anchors))
        self.create_writers()
        for scene_anchor in scene_anchors:
            self.add_object(scene_anchor)


class EmissivePointsSetShape(PointsSetShape):
    def add_object(self, scene_anchor):
        anchor = scene_anchor.anchor
        if anchor.visible_size < settings.min_body_size * 2 and scene_anchor.instance is not None:
            app_magnitude = anchor._app_magnitude
            point_color = anchor.point_color
            scale = mag_to_scale(app_magnitude)
            if scale > 0:
                color = point_color * scale
                size = max(settings.min_point_size, settings.min_point_size + scale * settings.mag_pixel_scale)
                self.add_point(scene_anchor.scene_position, color, size, scene_anchor.oid_color)


class HaloPointsSetShape(PointsSetShape):
    def add_object(self, scene_anchor):
        anchor = scene_anchor.anchor
        app_magnitude = anchor._app_magnitude
        if settings.show_halo and anchor.visible_size < settings.min_body_size * 2 and app_magnitude < settings.smallest_glare_mag:
            point_color = anchor.point_color
            coef = settings.smallest_glare_mag - app_magnitude + 6.0
            radius = max(1.0, anchor.visible_size)
            size = radius * coef * 2.0
            self.add_point(LPoint3(*scene_anchor.scene_position), point_color, size * 2, scene_anchor.oid_color)


class PassthroughPointsSetShape:
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
        if not settings.render_sprite_points: return
        self.shape.add_objects(scene_manager, scene_anchors)


class RegionsPointsSetShape:
    def __init__(self, shape_class, has_size, has_oid):
        self.shape_class = shape_class
        self.has_size = has_size
        self.has_oid = has_oid
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
        if not settings.render_sprite_points: return
        for region in scene_manager.get_regions():
            current_shape = self.shape_class(self.has_size, self.has_oid)
            current_shape.reset()
            self.shapes[region] = current_shape
            current_shape.add_objects(scene_manager, region.get_points_collection())
