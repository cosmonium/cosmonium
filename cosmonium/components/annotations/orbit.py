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


from panda3d.core import LColor, OmniBoundingVolume
from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomVertexRewriter, InternalName
from panda3d.core import Geom, GeomNode, GeomLines
from panda3d.core import NodePath

from ...foundation import VisibleObject
from ...astro.orbits import FixedPosition
from ...bodyclass import bodyClasses
from ...shaders.rendering import RenderingShader
from ...shaders.lighting.flat import FlatLightingModel
from ...shaders.lighting.smoothline import SmoothLineLightingModel
from ...shaders.vertex_control.spread_object import LargeObjectVertexControl
from ...appearances import ModelAppearance
from ...utils import TransparencyBlend, srgb_to_linear
from ... import settings


class Orbit(VisibleObject):
    ignore_light = True
    default_shown = False
    selected_color = LColor(1.0, 0.0, 0.0, 1.0)
    appearance = None
    shader = None
    default_camera_mask = VisibleObject.AnnotationCameraFlag

    def __init__(self, body):
        VisibleObject.__init__(self, body.get_ascii_name() + '-orbit')
        self.body = body
        self.nbOfPoints = 360
        self.orbit = self.find_orbit(self.body)
        self.color = None
        self.fade = 0.0
        if not self.orbit:
            print("No orbit for", self.get_name())
            self.visible = False

    def get_oid_color(self):
        if self.body is not None:
            return self.body.oid_color
        else:
            return LColor()

    @classmethod
    def create_shader(cls):
        cls.appearance = ModelAppearance(attribute_color=True)
        cls.appearance.transparency = True
        cls.appearance.transparency_blend = TransparencyBlend.TB_Additive
        cls.appearance.transparency_level = 0
        if settings.use_depth_scaling:
            vertex_control = LargeObjectVertexControl()
        else:
            vertex_control = None
        if settings.use_smooth_lines:
            lighting_model=SmoothLineLightingModel()
        else:
            lighting_model = FlatLightingModel()
        cls.shader = RenderingShader(lighting_model=lighting_model, vertex_control=vertex_control)
        cls.shader.create(None, cls.appearance)

    def check_settings(self):
        if self.body.body_class is None:
            print("No class for", self.body.get_name())
            return
        self.set_shown(settings.show_orbits and bodyClasses.get_show_orbit(self.body.body_class))

    def find_orbit(self, body):
        if body != None:
            if not isinstance(body.anchor.orbit, FixedPosition):
                return body.anchor.orbit
            else:
                return None, None
        else:
            return None, None

    def set_selected(self, selected):
        if selected:
            self.color = self.selected_color
        else:
            self.color = self.body.get_orbit_color()
        if self.instance:
            self.instance.setColor(srgb_to_linear(self.color * self.fade))

    def create_instance(self):
        self.vertexData = GeomVertexData('vertexData', GeomVertexFormat.getV3(), Geom.UHStatic)
        self.vertexWriter = GeomVertexWriter(self.vertexData, 'vertex')
        delta = self.body.parent.anchor.get_local_position()
        if self.orbit.is_periodic():
            epoch = self.context.time.time_full - self.orbit.period / 2
            step = self.orbit.period / (self.nbOfPoints - 1)
        else:
            #TODO: Properly calculate orbit start and end time
            epoch = self.orbit.get_time_of_perihelion() - self.orbit.period * 5.0
            step = self.orbit.period * 10.0 / (self.nbOfPoints - 1)
        for i in range(self.nbOfPoints):
            time = epoch + step * i
            pos = self.orbit.get_local_position_at(time) - delta
            self.vertexWriter.addData3f(*pos)
        self.lines = GeomLines(Geom.UHStatic)
        for i in range(self.nbOfPoints-1):
            self.lines.addVertex(i)
            self.lines.addVertex(i+1)
        if self.orbit.is_periodic() and self.orbit.is_closed():
            self.lines.addVertex(self.nbOfPoints-1)
            self.lines.addVertex(0)
        self.geom = Geom(self.vertexData)
        self.geom.addPrimitive(self.lines)
        self.node = GeomNode(self.body.get_ascii_name() + '-orbit')
        self.node.addGeom(self.geom)
        self.instance = NodePath(self.node)
        self.instance.setCollideMask(GeomNode.getDefaultCollideMask())
        if settings.use_smooth_lines:
            self.instance.setRenderModeThickness(settings.orbit_smooth_thickness)
            self.instance.set_shader_input("line_parameters", (settings.orbit_smooth_width, settings.orbit_smooth_blend))
            self.instance.set_depth_write(False)
            self.instance.set_transparency(True)
        else:
            self.instance.setRenderModeThickness(settings.orbit_thickness)
        self.instance.node().setPythonTag('owner', self.body)
        if settings.color_picking and self.body.oid_color is not None:
            self.instance.set_shader_input("color_picking", self.body.oid_color)
        self.instance.reparentTo(self.body.parent.scene_anchor.unshifted_instance)
        if self.color is None:
            self.color = self.body.get_orbit_color()
        self.instance.setColor(srgb_to_linear(self.color * self.fade))
        self.instance_ready = True
        if self.shader is None:
            self.create_shader()
        self.shader.apply(self.instance)
        self.appearance.apply(self, self.instance)
        TransparencyBlend.apply(self.appearance.transparency_blend, self.instance)
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)
        self.instance.hide(self.AllCamerasMask)
        self.instance.show(self.default_camera_mask)

    def update_geom(self):
        geom = self.node.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vwriter = GeomVertexRewriter(vdata, InternalName.get_vertex())
        #TODO: refactor with above code !!!
        delta = self.body.parent.get_local_position()
        if self.orbit.is_periodic():
            epoch = self.context.time.time_full - self.orbit.period
            step = self.orbit.period / (self.nbOfPoints - 1)
        else:
            #TODO: Properly calculate orbit start and end time
            epoch = self.orbit.get_time_of_perihelion() - self.orbit.period * 5.0
            step = self.orbit.period * 10.0 / (self.nbOfPoints - 1)
        for i in range(self.nbOfPoints):
            time = epoch + step * i
            pos = self.orbit.get_local_position_at(time) - delta
            vwriter.setData3f(*pos)

    def check_visibility(self, frustum, pixel_size):
        if self.body.parent.anchor.visible and self.body.parent.scene_anchor.instance is not None and self.body.shown and self.orbit:
            distance_to_obs = self.body.anchor.distance_to_obs
            if distance_to_obs > 0.0:
                size = self.orbit.get_bounding_radius() / (distance_to_obs * pixel_size)
            else:
                size = 0.0
            self.visible = size > settings.orbit_fade
            self.fade = min(1.0, max(0.0, (size - settings.orbit_fade) / settings.orbit_fade))
            if self.color is not None and self.instance is not None:
                self.instance.setColor(srgb_to_linear(self.color * self.fade))
        else:
            self.visible = False

    def update_user_parameters(self):
        if self.instance is not None:
            self.update_geom()
