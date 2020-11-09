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

from panda3d.core import TextureStage, Texture, TexGenAttrib, GeomVertexRewriter
from panda3d.core import GeomVertexArrayFormat, InternalName, GeomVertexFormat, GeomVertexData, GeomVertexWriter, OmniBoundingVolume
from panda3d.core import GeomPoints, Geom, GeomNode
from panda3d.core import LVecBase3, LPoint3d, LPoint3, LColor, LVector3d
from panda3d.core import NodePath, StackedPerlinNoise3

from .appearances import AppearanceBase
from .shapes import Shape
from .surfaces import FlatSurface
from .sprites import ExpPointSprite
from .textures import TransparentTexture, DirectTextureSource
from .shaders import PointControl
from .utils import TransparencyBlend
from .parameters import AutoUserParameter, UserParameter

from .bodies import DeepSpaceObject
from .shaders import BasicShader, FlatLightingModel
from .utils import mag_to_scale_nolimit
from .astro import units
from . import settings

from math import cos, sin, pi, log, tan, tanh, sqrt, exp, atan, atanh
from random import random, gauss, choice, seed
from cosmonium.utils import srgb_to_linear

class Galaxy(DeepSpaceObject):
    has_rotation_axis = False
    has_resolved_halo = False
    support_offset_body_center = False

    def __init__(self, names, source_names, radius=None, radius_units=units.Ly,
                 abs_magnitude=None,
                 shape_type=None,
                 shape=None,
                 appearance=None,
                 orbit=None, rotation=None,
                 body_class='galaxy', point_color=None,
                 description=''):
        self.shape_type = shape_type
        shader = None
        if shader is None:
            shader = BasicShader(lighting_model=FlatLightingModel(), point_control=GalaxyPointControl())
        #Disable color picking as it has huge impact on performance
        shader.color_picking = False
        if appearance is None:
            appearance = GalaxyAppearance()
        surface = FlatSurface(radius=radius * radius_units, shape=shape, appearance=appearance, shader=shader)
        DeepSpaceObject.__init__(self, names, source_names, radius, radius_units,
                              surface=surface,
                              orbit=orbit, rotation=rotation,
                              abs_magnitude=abs_magnitude, body_class=body_class)
        self._extend = self.radius

class GalaxyAppearance(AppearanceBase):
    image = None
    texture = None
    sprite = None
    def __init__(self, sprite=None, color_scale=1.0):
        AppearanceBase.__init__(self)
        if sprite is None:
            sprite = ExpPointSprite()
        self.sprite = sprite
        self.color_scale = color_scale
        self.has_vertex_color = True
        self.nb_textures = 1
        self.texture_index = 0
        self.transparency = True
        self.transparency_blend = TransparencyBlend.TB_Additive
        self.background = True
        self.min_coef = 0.2

    def set_magnitude(self, owner, shape, shader, abs_magnitude, app_magnitude, visible_size):
        if shape.instance is not None:
            if shape.is_flat():
                axis = owner.anchor.scene_orientation.xform(LVector3d.up())
                cosa = abs(axis.dot(owner.anchor.vector_to_obs))
                coef = max(self.min_coef, sqrt(cosa))
            else:
                coef = 1.0
            scale = self.color_scale / 255.0 * coef * mag_to_scale_nolimit(app_magnitude)
            size = owner.get_apparent_radius() / owner.anchor.distance_to_obs
            if size > 1.0:
                scale = max(1.0/255, scale / size)
            shape.instance.set_color_scale(LColor(scale, scale, scale, scale))

    def apply(self, shape, owner):
        if self.texture is None:
            if self.image is None:
                self.image = self.sprite.generate()
            texture = Texture()
            texture.load(self.image)
            self.texture = TransparentTexture(DirectTextureSource(texture), blend=TransparencyBlend.TB_PremultipliedAlpha)
            self.texture.set_tex_matrix(False)
        shape.instance.setTexGen(TextureStage.getDefault(), TexGenAttrib.MPointSprite)
        self.texture.apply(shape)
        shape.instance.set_depth_write(False)
        if self.background is not None:
            shape.instance.setBin('background', settings.deep_space_depth)
        owner.shader.apply(shape, self)
        shape.instance_ready = True

    def get_user_parameters(self):
        return [
                AutoUserParameter("Color scale", "color_scale", self, UserParameter.TYPE_FLOAT, [0, 255]),
                ]

class GalaxyShapeBase(Shape):
    templates = {}
    def __init__(self, radius=1.0, scale=None):
        Shape.__init__(self)
        self.radius = radius
        self.seed = random()
        if scale is None:
            self.radius = radius
            self.scale = LVecBase3(self.radius, self.radius, self.radius)
        else:
            self.scale = LVecBase3(*scale) * radius
            self.radius = max(scale) * radius
        self.nb_points = 1
        self.size = 1.0
        self.yellow_color = srgb_to_linear((255.0 / 255, 248.0 / 255, 231.0 / 255, 1.0))
        self.blue_color = srgb_to_linear((102.0 / 255, 153.0 / 255, 255.0 / 255, 1.0))

    def shape_id(self):
        return ''

    def get_apparent_radius(self):
        return self.radius

    def get_scale(self):
        return self.scale / self.size

    def is_flat(self):
        return False

    def create_points(self, radius=1.0):
        return None

    def apply(self):
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)

    def create_instance(self):
        shape_id = self.shape_id()
        if shape_id in GalaxyShapeBase.templates:
            template =  GalaxyShapeBase.templates[shape_id]
        else:
            seed(self.seed)
            self.gnode = GeomNode('galaxy')
            self.geom = self.makeGeom(*self.create_points())
            self.gnode.addGeom(self.geom)
            template = NodePath(self.gnode)
            # Disable caching
            #GalaxyShapeBase.templates[shape_id] = template
        self.instance = NodePath('galaxy')
        template.instanceTo(self.instance)
        self.apply()
        self.update_geom(*self.create_points())
        return self.instance

    def update_shape(self):
        seed(self.seed)
        self.update_geom(*self.create_points())

    def makeGeom(self, points, colors, sizes):
        #format = GeomVertexFormat.getV3c4()
        array = GeomVertexArrayFormat()
        array.addColumn(InternalName.get_vertex(), 3, Geom.NTFloat32, Geom.CPoint)
        array.addColumn(InternalName.get_color(), 4, Geom.NTFloat32, Geom.CColor)
        array.addColumn(InternalName.get_size(), 1, Geom.NTFloat32, Geom.COther)
        format = GeomVertexFormat()
        format.addArray(array)
        format = GeomVertexFormat.registerFormat(format)
        vdata = GeomVertexData('vdata', format, Geom.UH_static)
        vdata.unclean_set_num_rows(len(points))
        self.vwriter = GeomVertexWriter(vdata, InternalName.get_vertex())
        self.colorwriter = GeomVertexWriter(vdata, InternalName.get_color())
        self.sizewriter = GeomVertexWriter(vdata, InternalName.get_size())
        geompoints = GeomPoints(Geom.UH_static)
        geompoints.reserve_num_vertices(len(points))
        index = 0
        for (point, color, size) in zip(points, colors, sizes):
            self.vwriter.addData3f(*point)
            self.colorwriter.addData4f(*color)
            self.sizewriter.addData1f(size)
            geompoints.addVertex(index)
            #geompoints.closePrimitive()
            index += 1
        geom = Geom(vdata)
        geom.addPrimitive(geompoints)
        return geom

    def update_geom(self, points, colors, sizes):
        geom = self.instance.children[0].node().modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata.unclean_set_num_rows(len(points))
        vwriter = GeomVertexRewriter(vdata, InternalName.get_vertex())
        colorwriter = GeomVertexWriter(vdata, InternalName.get_color())
        sizewriter = GeomVertexWriter(vdata, InternalName.get_size())
        for (point, color, size) in zip(points, colors, sizes):
            vwriter.addData3f(*point)
            colorwriter.addData4f(*color)
            sizewriter.addData1f(size)

class EllipticalGalaxyShape(GalaxyShapeBase):
    def __init__(self, factor, radius=1.0, scale=None, nb_points=4000, spread=0.4, zspread=0.2, sprite_size=400, sersic=4.0):
        GalaxyShapeBase.__init__(self, radius, scale)
        self.factor = factor
        self.nb_points = nb_points
        self.spread = spread
        self.zspread = zspread
        self.sprite_size = sprite_size
        self.sersic = sersic
        self.color = self.yellow_color

    def shape_id(self):
        return 'elliptical-%g' % self.factor

    def create_points(self, radius=1.0):
        points = []
        colors = []
        sizes = []
        nb_points = self.nb_points
        sprite_size = self.sprite_size
        half_sprite_size = self.sprite_size / 2.0
        color = self.color
        spread = self.spread
        spreadf = self.spread * self.factor
        zspreadf = self.zspread * self.factor
        sersic_inv = 1. / self.sersic
        for i in range(nb_points):
            x = gauss(0.0, spread)
            y = gauss(0.0, spreadf)
            z = gauss(0.0, zspreadf)
            point = LPoint3d(x * radius, y * radius, z * radius)
            points.append(point)
            colors.append(color * (0.9 - pow(point.length(), sersic_inv)))
            size = sprite_size + gauss(0, half_sprite_size)
            sizes.append(size)
        return (points, colors, sizes)

    def get_user_parameters(self):
        return [
                AutoUserParameter("Sersic index", "sersic", self, UserParameter.TYPE_FLOAT, [0.1, 10]),
                AutoUserParameter("Spread", "spread", self, UserParameter.TYPE_FLOAT, [0.001, 1]),
                AutoUserParameter("Z-spread", "zspread", self, UserParameter.TYPE_FLOAT, [0.001, 1]),
                AutoUserParameter("Sprite size", "sprite_size", self, UserParameter.TYPE_FLOAT, [1, 1000]),
                AutoUserParameter("Color", "color", self, UserParameter.TYPE_VEC, [0, 1], nb_components=3)
                ]

class IrregularGalaxyShape(GalaxyShapeBase):
    noise = None
    def __init__(self, radius=1.0, scale=None, nb_points=4000, spread=0.4, zspread=0.2, sprite_size=400, sersic=4.0):
        GalaxyShapeBase.__init__(self, radius, scale)
        self.nb_points = nb_points
        self.spread = spread
        self.zspread = zspread
        self.sprite_size = sprite_size
        self.sersic = sersic
        self.color1 = self.yellow_color
        self.color2 = self.blue_color

    def shape_id(self):
        return 'irregular'

    def create_points(self, radius=1.0):
        if IrregularGalaxyShape.noise is None:
            IrregularGalaxyShape.noise = StackedPerlinNoise3(1, 1, 1, 8, 4, 0.7)
        points = []
        colors = []
        sizes = []
        nb_points = self.nb_points
        sprite_size = self.sprite_size
        colors_list = [self.color1, self.color2]
        spread = self.spread
        zspread = self.zspread
        sersic_inv = 1. / self.sersic
        count = 0
        while count < nb_points:
            p = LPoint3(gauss(0.0, spread), gauss(0.0, spread), gauss(0.0, zspread))
            value = self.noise(p) * 0.5 + 0.5
            if value < 0.5:
                points.append(p * radius)
                color = choice(colors_list)
                color = color * (1 - 0.9 * pow(p.length(), sersic_inv))
                color[3] = 1.0
                colors.append(color)
                size = sprite_size + gauss(0, sprite_size)
                sizes.append(size)
                count += 1
        return (points, colors, sizes)

    def get_user_parameters(self):
        return [
                AutoUserParameter("Sersic index", "sersic", self, UserParameter.TYPE_FLOAT, [0.1, 10]),
                AutoUserParameter("Spread", "spread", self, UserParameter.TYPE_FLOAT, [0.001, 1]),
                AutoUserParameter("Z-spread", "zspread", self, UserParameter.TYPE_FLOAT, [0.001, 1]),
                AutoUserParameter("Sprite size", "sprite_size", self, UserParameter.TYPE_FLOAT, [1, 1000]),
                AutoUserParameter("Color 1", "color1", self, UserParameter.TYPE_VEC, [0, 1], nb_components=3),
                AutoUserParameter("Color 2", "color2", self, UserParameter.TYPE_VEC, [0, 1], nb_components=3)
                ]

class SpiralGalaxyShapeBase(GalaxyShapeBase):
    def __init__(self, radius=1.0, scale=None, nb_points_bulge=200, nb_points_arms=1000, spread=0.4, zspread=0.01, sprite_size=400, max_angle=2 * pi, sersic_bulge=4.0, sersic_disk=1.0):
        GalaxyShapeBase.__init__(self, radius, scale)
        self.nb_points_bulge = nb_points_bulge
        self.nb_points_arms = nb_points_arms
        self.spread = spread
        self.zspread = zspread
        self.max_angle = max_angle
        self.sprite_size = sprite_size
        self.sersic_bulge = sersic_bulge
        self.sersic_disk = sersic_disk
        self.bulge_color = self.yellow_color
        self.arms_color = self.blue_color

    def is_flat(self):
        return True

    def create_bulge(self, count, radius, spread, zspread, points, colors, sizes):
        sprite_size = self.sprite_size
        bulge_color = self.bulge_color
        sersic_inv = 1. / self.sersic_bulge
        for i in range(count):
            x = gauss(0.0, spread)
            y = gauss(0.0, spread)
            z = gauss(0.0, zspread)
            point = LPoint3d(x * radius, y * radius, z * radius)
            points.append(point)
            color = bulge_color * (1 - pow(point.length(), sersic_inv)) * 2
            color[3] = 1.0
            colors.append(color)
            size = sprite_size + gauss(0, sprite_size)
            sizes.append(size)

    def create_spiral(self, count,radius, spread, zspread, points, colors, sizes):
        func = self.shape_func
        sprite_size = self.sprite_size
        arm_color = self.arms_color
        sersic_inv = 1. / self.sersic_disk
        distance = 0
        for i in (-1.0, 1.0):
            for c in range(count):
                t = sqrt(random())
                angle = t * self.max_angle
                shape = func(angle)
                x = i * cos(angle) * shape + gauss(0.0, spread)
                y = i * sin(angle) * shape + gauss(0.0, spread)
                z = gauss(0.0, zspread)
                point = LPoint3d(x * radius, y * radius, z * radius)
                points.append(point)
                distance = max(distance, point.length())
                color = arm_color * (1 - 0.9 * pow(distance, sersic_inv))
                color[3] = 1.0
                colors.append(color)
                size = sprite_size + gauss(0, sprite_size)
                sizes.append(size)
        self.size = distance

    def create_spiral_distance(self, count, radius, spread, zspread, points, colors, sizes):
        sprite_size = self.sprite_size
        arm_color = self.arms_color
        disk_color = self.bulge_color
        bulge_size = self.bulge_size()
        sersic_inv = 1. / self.sersic_disk
        distance = 0
        for c in range(count * 2):
            r = sqrt(random() + bulge_size*bulge_size)
            theta = random() * 2 * pi
            x = r * cos(theta)
            y = r * sin(theta)
            z = gauss(0.0, zspread)
            coef = 0.0
            for c in (0, 1.):
                arm_angle = self.inv_shape_func(r) * max(self.max_angle, 0.001) / (2 * pi)
                mtheta = c * pi + theta
                delta = abs(mtheta - arm_angle)
                for i in range(int(self.max_angle / (2 * pi)) + 1):
                    delta = min(delta, abs(mtheta - arm_angle - (i + 1) * 2 * pi), abs(mtheta - arm_angle + (i  + 1) * 2 * pi))
                coef = max(pow(max(1 - delta / pi, 0.0), self.arm_spread), coef)
            point = LPoint3d(x * radius, y * radius, z * radius)
            points.append(point)
            distance = max(distance, point.length())
            color = disk_color * (1 - coef) + arm_color * coef
            color = color * (1 - 0.9 * pow(r, sersic_inv))
            color[3] = 1.0
            colors.append(color)
            size = sprite_size + gauss(0, sprite_size)
            sizes.append(size)
        self.size = distance

    def create_points(self, radius=1.0):
        points = []
        colors = []
        sizes = []
        nb_points_bulge = self.nb_points_bulge
        nb_points_arms = self.nb_points_arms
        spread = self.bulge_size() / 2
        zspread = spread / 2.0
        self.create_bulge(nb_points_bulge, radius, spread, zspread, points, colors, sizes)
        if True:
            self.create_spiral_distance(nb_points_arms, radius, self.spread, self.zspread, points, colors, sizes)
        else:
            self.create_spiral(nb_points_arms, radius, self.spread, self.zspread, points, colors, sizes)
        self.nb_points = nb_points_bulge + nb_points_arms
        return (points, colors, sizes)

    def get_user_parameters(self):
        return [
                AutoUserParameter("Bulge sersic index", "sersic_bulge", self, UserParameter.TYPE_FLOAT, [0.1, 10]),
                AutoUserParameter("Sersic index", "sersic_disk", self, UserParameter.TYPE_FLOAT, [0.1, 10]),
                AutoUserParameter("Spread", "spread", self, UserParameter.TYPE_FLOAT, [0.001, 1]),
                AutoUserParameter("Z-spread", "zspread", self, UserParameter.TYPE_FLOAT, [0.001, 1]),
                AutoUserParameter("Sprite size", "sprite_size", self, UserParameter.TYPE_FLOAT, [1, 1000]),
                AutoUserParameter("Bulge color", "bulge_color", self, UserParameter.TYPE_VEC, [0, 1], nb_components=3),
                AutoUserParameter("Arms color", "arms_color", self, UserParameter.TYPE_VEC, [0, 1], nb_components=3)
                ]

class FullSpiralGalaxyShape(SpiralGalaxyShapeBase):
    def __init__(self, N, B, radius=1.0, scale=None, nb_points_bulge=200, nb_points_arms=1000, spread=0.4, zspread=0.2, point_size=400, max_angle=2 * pi, sersic_bulge=4.0, sersic_disk=1.0):
        SpiralGalaxyShapeBase.__init__(self, radius, scale, nb_points_bulge, nb_points_arms, spread, zspread, point_size, max_angle, sersic_bulge, sersic_disk)
        self.N = N
        self.B = B

    def shape_id(self):
        return 'spiral-%g-%g' % (self.N, self.B)

    def bulge_size(self):
        return 2 * self.shape_func(0)

    def shape_func(self, angle):
        return 1.0 / log(self.B * max(0.00001, tan(angle / (2 * self.N))))

    def inv_shape_func(self, distance):
        return atan(exp(1.0 / distance) / self.B) * 2 * self.N

    def get_user_parameters(self):
        params = SpiralGalaxyShapeBase.get_user_parameters(self)
        params += [AutoUserParameter("N", "N", self, UserParameter.TYPE_FLOAT, [0, 10]),
                   AutoUserParameter("B", "B", self, UserParameter.TYPE_FLOAT, [0, 10]),
                   ]
        return params

class FullRingGalaxyShape(SpiralGalaxyShapeBase):
    def __init__(self, N, B, radius=1.0, scale=None, nb_points_bulge=200, nb_points_arms=1000, spread=0.4, zspread=0.2, point_size=400, max_angle=2 * pi, sersic_bulge=4.0, sersic_disk=1.0):
        SpiralGalaxyShapeBase.__init__(self, radius, scale, nb_points_bulge, nb_points_arms, spread, zspread, point_size, max_angle, sersic_bulge, sersic_disk)
        self.N = N
        self.B = B

    def shape_id(self):
        return 'ring-%g-%g' % (self.N, self.B)

    def bulge_size(self):
        return 2 * self.shape_func(0)

    def shape_func(self, angle):
        return 1.0 / log(self.B * max(0.00001, tanh(angle / (2 * self.N))))

    def inv_shape_func(self, distance):
        return atanh(exp(1.0 / distance) / self.B) * 2 * self.N

    def get_user_parameters(self):
        params = SpiralGalaxyShapeBase.get_user_parameters(self)
        params += [AutoUserParameter("N", "N", self, UserParameter.TYPE_FLOAT, [0, 10]),
                   AutoUserParameter("B", "B", self, UserParameter.TYPE_FLOAT, [0, 10]),
                   ]
        return params

class SpiralGalaxyShape(SpiralGalaxyShapeBase):
    bar_radius = 0.5
    def __init__(self, pitch, radius=1.0, scale=None, nb_points_bulge=200, nb_points_arms=1000, spread=0.4, zspread=0.2, point_size=400, max_angle=2 * pi, sersic_bulge=4.0, sersic_disk=1.0):
        SpiralGalaxyShapeBase.__init__(self, radius, scale, nb_points_bulge, nb_points_arms, spread, zspread, point_size, max_angle, sersic_bulge, sersic_disk)
        self.pitch = pitch
        self.arm_spread = 5

    def set_pitch(self, pitch):
        self.pitch = pitch / 180 * pi

    def get_pitch(self):
        return self.pitch * 180 / pi

    def set_max_angle(self, max_angle):
        self.max_angle = max_angle / 180 * pi

    def get_max_angle(self):
        return self.max_angle * 180 / pi

    def shape_id(self):
        return 'spiral-%g' % self.pitch

    def bulge_size(self):
        return 2 * self.shape_func(0)

    def shape_func(self, angle):
        pitch = self.pitch
        return self.bar_radius / (1 - pitch * tan(pitch) * log(max(0.00001, (angle / pitch))))

    def inv_shape_func(self, distance):
        pitch = self.pitch
        return pitch * exp((1 - self.bar_radius / distance) / (pitch * tan(pitch)))

    def get_user_parameters(self):
        params = SpiralGalaxyShapeBase.get_user_parameters(self)
        params += [UserParameter("Pitch", self.set_pitch, self.get_pitch, UserParameter.TYPE_FLOAT, [20, 35]),
                   UserParameter("Winding", self.set_max_angle, self.get_max_angle, UserParameter.TYPE_FLOAT, [0, 720]),
                   AutoUserParameter("Spread", 'arm_spread', self, UserParameter.TYPE_FLOAT, [0, 20]),
                   ]
        return params

class LenticularGalaxyShape(SpiralGalaxyShapeBase):
    bulge_radius = 0.2

    def shape_id(self):
        return 'lenticular'

    def bulge_size(self):
        return self.bulge_radius

    def create_spiral(self, count, radius, spread, zspread, points, colors, sizes):
        sprite_size = self.sprite_size
        disk_color = self.yellow_color
        sersic_inv = 1. / self.sersic_disk
        for r in range(count * 2):
            distance = self.bulge_radius + abs(gauss(0, (1 - self.bulge_radius)))
            angle = random() * 2.0 * pi
            x = distance * cos(angle) + gauss(0.0, spread)
            y = distance * sin(angle) + gauss(0.0, spread)
            z = gauss(0.0, zspread)
            point = LPoint3d(x * radius, y * radius, z * radius)
            points.append(point)
            color = disk_color * (1 - 0.9 * pow(point, sersic_inv))
            color[3] = 1.0
            colors.append(color)
            size = sprite_size + gauss(0, sprite_size)
            sizes.append(size)

class GalaxyPointControl(PointControl):
    use_vertex = True
    world_vertex = True
    def get_id(self):
        return "pt-galaxy"

    def vertex_uniforms(self, code):
        code.append("uniform float max_sprite_size;")
        code.append("uniform float scale_factor;")
        code.append("uniform float apparent_radius;")
        code.append("uniform float pixel_size;")

    def vertex_inputs(self, code):
        code.append("in float size;")

    def vertex_outputs(self, code):
        code.append("out float attenuation;")

    def fragment_inputs(self, code):
        code.append("in float attenuation;")

    def vertex_shader(self, code):
        code.append("float distance = length(world_vertex) / scale_factor;")
        code.append("gl_PointSize = size / 1000. * apparent_radius / (distance * pixel_size);")
        code.append("attenuation = (max_sprite_size - gl_PointSize) / max_sprite_size;")
        code.append("if (gl_PointSize > max_sprite_size) gl_PointSize = 0;")

    def fragment_shader(self, code):
        code.append("total_emission_color *= attenuation;")

    def update_shader_shape_static(self, shape, appearance):
        PointControl.update_shader_shape_static(self, shape, appearance)
        shape.instance.setShaderInput("apparent_radius", shape.owner.get_apparent_radius())
        shape.instance.setShaderInput("max_sprite_size", settings.max_sprite_size)

    def update_shader_shape(self, shape, appearance):
        shape.instance.setShaderInput("scale_factor", shape.owner.anchor.scene_scale_factor)
