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


from math import atan2, cos, sin

from direct.showbase.PythonUtil import clamp
from panda3d.core import (
    Geom,
    GeomLines,
    GeomNode,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexRewriter,
    GeomVertexWriter,
    InternalName,
    LPoint3d,
    LVector3d,
    NodePath,
    OmniBoundingVolume,
)

from ... import settings
from ...appearances import ModelAppearance
from ...astro import units
from ...astro.astro import position_to_equatorial
from ...astro.projection import InfinitePosition
from ...bodyclass import bodyClasses
from ...foundation import CompositeObject, VisibleObject
from ...scene.sceneanchor import SceneAnchor
from ...shaders.lighting.flat import FlatLightingModel
from ...shaders.rendering import RenderingShader
from ...utils import TransparencyBlend, srgb_to_linear
from .background_label import BackgroundLabel


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
        cls.appearance.transparency_blend = TransparencyBlend.TB_Additive
        cls.shader = RenderingShader(lighting_model=FlatLightingModel())
        cls.shader.color_picking = False
        cls.shader.create(None, cls.appearance)

    def set_segments_list(self, segments):
        self.segments = segments
        ra_sin = 0
        ra_cos = 0
        decl = 0
        if len(self.segments) > 0 and len(self.segments[0]) > 0:
            for anchor in self.segments[0]:
                (right_ascension, declination) = position_to_equatorial(anchor.orbit.get_absolute_position_at(0))
                ra_sin += sin(right_ascension)
                ra_cos += cos(right_ascension)
                decl += declination
            ra = atan2(ra_sin, ra_cos)
            decl /= len(self.segments[0])
            self.position = InfinitePosition(ra * units.Rad, decl * units.Rad)

    def update_vertices(self):
        geom = self.node.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vwriter = GeomVertexRewriter(vdata, InternalName.get_vertex())
        for segment in self.segments:
            if len(segment) < 2:
                continue
            for anchor in segment:
                anchor.update(self.context.time.time_full, self.context.update_id)
                anchor.update_observer(self.context.observer.anchor, self.context.update_id)
                position = SceneAnchor.calc_scene_position(
                    self.context.scene_manager,
                    anchor.rel_position,
                    anchor._position,
                    anchor.distance_to_obs,
                    anchor.vector_to_obs,
                )
                vwriter.setData3f(*position)

    def create_instance(self):
        self.vertexData = GeomVertexData('vertexData', GeomVertexFormat.getV3c4(), Geom.UHDynamic)
        self.vertexWriter = GeomVertexWriter(self.vertexData, 'vertex')
        self.colorwriter = GeomVertexWriter(self.vertexData, 'color')
        for segment in self.segments:
            if len(segment) < 2:
                continue
            for _ in segment:
                self.vertexWriter.addData3f(0, 0, 0)
                self.colorwriter.addData4(srgb_to_linear(self.color))
        self.lines = GeomLines(Geom.UHStatic)
        index = 0
        for segment in self.segments:
            if len(segment) < 2:
                continue
            for i in range(len(segment) - 1):
                self.lines.addVertex(index)
                self.lines.addVertex(index + 1)
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
        TransparencyBlend.apply(self.appearance.transparency_blend, self.instance)
        self.update_vertices()

    def check_visibility(self, frustum, pixel_size):
        super().check_visibility(frustum, pixel_size)
        # If asterism fading is enabled, hide the asterism when the observer is farther than 2 times the fade distance
        # This would disable vertex updates.
        if settings.asterism_fade > 0:
            self.visible = (
                LVector3d(self.context.observer.get_absolute_position()).length() < settings.asterism_fade * 2
            )

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        if settings.asterism_fade > 0:
            # Calculate the fade factor based on the observer's distance
            observer_distance = LVector3d(self.context.observer.get_absolute_position()).length()
            # Fade out when the observer is between 1 and 2 times the fade distance
            fade = clamp(1.0 - (observer_distance - settings.asterism_fade) / settings.asterism_fade, 0.0, 1.0)
            self.instance.setColorScale(fade, fade, fade, 1.0)
        self.update_vertices()


class NamedAsterism(CompositeObject):
    background_level = settings.constellations_depth
    body_class = 'constellation'

    def __init__(self, name):
        CompositeObject.__init__(self, name)
        self.create_components()

    def create_components(self):
        self.label = BackgroundLabel(self.get_ascii_name() + '-label', self)
        self.add_component(self.label)
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
