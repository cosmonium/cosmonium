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
from panda3d.core import NodePath, OmniBoundingVolume, DrawMask, ShaderAttrib, LPoint3
from .foundation import VisibleObject
from .appearances import ModelAppearance
from .shaders.rendering import RenderingShader
from .shaders.lighting.flat import FlatLightingModel
from .shaders.point_control import StaticSizePointControl
from .sprites import SimplePoint, RoundDiskPointSprite
from .utils import mag_to_scale
from . import settings


class PointsSetShape:
    def __init__(self, has_size, has_oid):
        self.has_size = has_size
        self.has_oid = has_oid
        self.gnode = GeomNode('starfield')
        self.instance = NodePath(self.gnode)
        self.geom = None
        self.geom_points = None
        self.index = 0

    def make_geom(self):
        array = GeomVertexArrayFormat()
        array.add_column(InternalName.get_vertex(), 3, Geom.NT_float32, Geom.C_point)
        array.addColumn(InternalName.get_color(), 4, Geom.NT_float32, Geom.C_color)
        if self.has_size:
            array.add_column(InternalName.get_size(), 1, Geom.NT_float32, Geom.C_other)
        if self.has_oid:
            oids_column_name = InternalName.make('oid')
            array.add_column(oids_column_name, 4, Geom.NT_float32, Geom.C_other)
        vertex_format = GeomVertexFormat()
        vertex_format.add_array(array)
        vertex_format = GeomVertexFormat.register_format(vertex_format)
        vdata = GeomVertexData('vdata', vertex_format, Geom.UH_static)
        self.vwriter = GeomVertexWriter(vdata, InternalName.get_vertex())
        self.colorwriter = GeomVertexWriter(vdata, InternalName.get_color())
        if self.has_size:
            self.sizewriter = GeomVertexWriter(vdata, InternalName.get_size())
        if self.has_oid:
            self.oidwriter = GeomVertexWriter(vdata, oids_column_name)
        self.geom_points = GeomPoints(Geom.UH_static)
        self.geom = Geom(vdata)
        self.geom.add_primitive(self.geom_points)

    def reset(self):
        self.gnode.remove_all_geoms()
        self.make_geom()
        self.gnode.add_geom(self.geom)
        self.index = 0

    def configure(self, scene_manager, configurator):
        configurator.configure_shape(self)
        self.instance.reparent_to(scene_manager.root)

    def reconfigure(self, scene_manager, configurator):
        pass

    def add_point(self, point, color, size, oid):
        self.vwriter.add_data3(*point)
        self.colorwriter.add_data4(color)
        if self.has_size:
            self.sizewriter.add_data1(size)
        if self.has_oid:
            self.oidwriter.add_data4(oid)
        self.geom_points.add_vertex(self.index)
        self.index += 1

    def add_object(self, scene_anchor):
        raise NotImplementedError()

    def add_objects(self, scene_manager, scene_anchors):
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
            sub_shape.configure(region, configurator)

    def add_objects(self, scene_manager, scene_anchors):
        if not settings.render_sprite_points: return
        for region in scene_manager.get_regions():
            current_shape = self.shape_class(self.has_size, self.has_oid)
            current_shape.reset()
            self.shapes[region] = current_shape
            current_shape.add_objects(scene_manager, region.points)


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
            shader = RenderingShader(lighting_model=FlatLightingModel(), vertex_oids=True, point_control=StaticSizePointControl())
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
        if self.use_sizes:
            attrib = shape.instance.get_attrib(ShaderAttrib)
            shape.instance.setAttrib(attrib.set_flag(ShaderAttrib.F_shader_point_size, True))

    def reset(self):
        self.shape.reset()

    def add_objects(self, scene_manager, scene_anchors):
        self.shape.add_objects(scene_manager, scene_anchors)
        self.shape.reconfigure(scene_manager, self)

    def update(self):
        pass