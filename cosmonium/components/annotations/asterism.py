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


from panda3d.core import LPoint3d,OmniBoundingVolume
from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexWriter
from panda3d.core import Geom, GeomNode, GeomLines
from panda3d.core import NodePath

from ...foundation import VisibleObject, LabelledObject
from ...scene.sceneanchor import SceneAnchor
from ...astro.projection import InfinitePosition
from ...astro.astro import position_to_equatorial
from ...astro import units
from ...bodyclass import bodyClasses
from ...shaders.rendering import RenderingShader
from ...shaders.lighting.flat import FlatLightingModel
from ...appearances import ModelAppearance
from ...utils import srgb_to_linear
from ... import settings

from .background_label import BackgroundLabel

from math import sin, cos, atan2


class Asterism(VisibleObject):
    shader = None

    def __init__(self, name):
        VisibleObject.__init__(self, name)
        self.color = bodyClasses.get_orbit_color('constellation')
        self.position = LPoint3d(0, 0, 0)
        self.segments = []
        self.position = None

    def check_settings(self):
        self.set_shown(settings.show_asterisms)

    @classmethod
    def create_shader(cls):
        cls.appearance = ModelAppearance()
        cls.appearance.has_vertex_color = True
        cls.appearance.has_material = False
        cls.shader = RenderingShader(lighting_model=FlatLightingModel())
        cls.shader.color_picking = False
        cls.shader.create(None, cls.appearance)

    def set_segments_list(self, segments):
        self.segments = segments
        ra_sin = 0
        ra_cos = 0
        decl = 0
        if len(self.segments) > 0 and len(self.segments[0]) > 0:
            for star in self.segments[0]:
                (right_ascension, declination) = position_to_equatorial(star.anchor.orbit.get_absolute_position_at(0))
                ra_sin += sin(right_ascension)
                ra_cos += cos(right_ascension)
                decl += declination
            ra = atan2(ra_sin, ra_cos)
            decl /= len(self.segments[0])
            self.position = InfinitePosition(ra * units.Rad, decl * units.Rad)

    def create_instance(self):
        self.vertexData = GeomVertexData('vertexData', GeomVertexFormat.getV3c4(), Geom.UHStatic)
        self.vertexWriter = GeomVertexWriter(self.vertexData, 'vertex')
        self.colorwriter = GeomVertexWriter(self.vertexData, 'color')
        #TODO: Ugly hack to calculate star position from the sun...
        old_global_position = self.context.observer.anchor.get_absolute_reference_point()
        old_local_position = self.context.observer.anchor.get_local_position()
        self.context.observer.anchor.set_absolute_reference_point(LPoint3d())
        self.context.observer.anchor.set_local_position(LPoint3d())
        self.context.update_id += 1
        for segment in self.segments:
            if len(segment) < 2: continue
            for star in segment:
                #TODO: Temporary workaround to have star pos
                star.anchor.update_and_update_observer(0, self.context.observer.anchor, self.context.update_id)
                position = SceneAnchor.calc_scene_position(self.context.scene_manager, star.anchor.rel_position, star.anchor._position, star.anchor.distance_to_obs, star.anchor.vector_to_obs)
                self.vertexWriter.addData3f(*position)
                self.colorwriter.addData4(srgb_to_linear(self.color))
        self.context.observer.anchor.set_absolute_reference_point(old_global_position)
        self.context.observer.anchor.set_local_position(old_local_position)
        self.lines = GeomLines(Geom.UHStatic)
        index = 0
        for segment in self.segments:
            if len(segment) < 2: continue
            for i in range(len(segment)-1):
                self.lines.addVertex(index)
                self.lines.addVertex(index+1)
                self.lines.closePrimitive()
                index += 1
            index += 1
        self.geom = Geom(self.vertexData)
        self.geom.addPrimitive(self.lines)
        self.node = GeomNode("asterism")
        self.node.addGeom(self.geom)
        self.instance = NodePath(self.node)
        if self.shader is None:
            self.create_shader()
        self.appearance.apply(self, self.instance)
        self.shader.apply(self.instance)
        self.instance.setRenderModeThickness(settings.asterism_thickness)
        self.instance.reparentTo(self.scene_anchor.unshifted_instance)
        self.instance.setBin('background', settings.asterisms_depth)
        self.instance.set_depth_write(False)
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)

class NamedAsterism(LabelledObject):
    ignore_light = True
    default_shown = True
    background_level = settings.constellations_depth
    body_class = 'constellation'

    def __init__(self, name):
        LabelledObject.__init__(self, name)
        self.create_components()

    def create_label_instance(self):
        return BackgroundLabel(self.get_ascii_name() + '-label', self)

    def create_components(self):
        self.create_label()
        self.asterism = Asterism(self.get_name())
        self.add_component(self.asterism)

    def set_segments_list(self, segments):
        self.asterism.set_segments_list(segments)

    def project(self, time, center, distance):
        return self.asterism.position.project(time, center, distance)

    def get_label_text(self):
        return self.get_name()

    def get_label_color(self):
        return bodyClasses.get_label_color(self.body_class)

    def get_label_size(self):
        return settings.constellations_label_size
