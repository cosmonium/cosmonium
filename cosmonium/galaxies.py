from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import TextureStage, Texture, TexGenAttrib
from panda3d.core import GeomVertexArrayFormat, InternalName, GeomVertexFormat, GeomVertexData, GeomVertexWriter, OmniBoundingVolume
from panda3d.core import GeomPoints, Geom, GeomNode
from panda3d.core import LVecBase3, LPoint3d, LPoint3, LColor, LVector3d
from panda3d.core import NodePath, StackedPerlinNoise3

from .appearances import AppearanceBase
from .shapes import Shape
from .surfaces import FlatSurface
from .sprites import ExpPointSprite
from .textures import TransparentTexture, DirectTextureSource

from .bodies import DeepSpaceObject
from .shaders import BasicShader, FlatLightingModel
from .astro import units
from . import settings

from math import cos, sin, pi, log, tan, tanh
from random import random, gauss, choice
from cosmonium.utils import mag_to_scale_nolimit

class Galaxy(DeepSpaceObject):
    has_rotation_axis = False
    has_resolved_halo = False
    support_offset_body_center = False

    def __init__(self, name, radius=None, radius_units=units.Ly, 
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
            shader = BasicShader(lighting_model=FlatLightingModel(), point_shader=True, scale_point_static=True)
        if appearance is None:
            appearance = GalaxyAppearance()
        surface = FlatSurface(shape=shape, appearance=appearance, shader=shader)
        DeepSpaceObject.__init__(self, name, radius, radius_units,
                              surface=surface,
                              orbit=orbit, rotation=rotation,
                              abs_magnitude=abs_magnitude, body_class=body_class)
        self.extend = self.radius

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
        self.background = True
        self.correction = 0.4

    def set_magnitude(self, owner, shape, shader, abs_magnitude, app_magnitude, visible_size):
        if shape.instance is not None:
            axis = owner.scene_orientation.xform(LVector3d.up())
            cosa = abs(axis.dot(owner.vector_to_obs))
            coef = cosa * self.correction + (1.0 - self.correction)
            scale = float(self.color_scale) / 255 * coef * mag_to_scale_nolimit(app_magnitude)
            size = owner.get_apparent_radius() / owner.distance_to_obs
            if size > 1.0:
                scale = scale / size
            shape.instance.set_color_scale(LColor(scale, scale, scale, scale))
            shader.set_size_scale(size)

    def apply(self, shape, owner):
        if self.texture is None:
            if self.image is None:
                self.image = self.sprite.generate()
            texture = Texture()
            texture.load(self.image)
            self.texture = TransparentTexture(DirectTextureSource(texture), blend=TransparentTexture.TB_PremultipliedAlpha)
            self.texture.set_tex_matrix(False)
        shape.instance.setTexGen(TextureStage.getDefault(), TexGenAttrib.MPointSprite)
        self.texture.apply(shape)
        shape.instance.set_depth_write(False)
        if self.background is not None:
            shape.instance.setBin('background', settings.deep_space_depth)
        owner.shader.apply(shape, self)
        shape.instance_ready = True
        shape.create_instance_delayed()

class GalaxyShapeBase(Shape):
    templates = {}
    def __init__(self, radius=1.0, scale=None):
        Shape.__init__(self)
        self.radius = radius
        if scale is None:
            self.radius = radius
            self.scale = LVecBase3(self.radius, self.radius, self.radius)
        else:
            self.scale = LVecBase3(*scale) * radius
            self.radius = max(scale) * radius
        self.nb_points = 1
        self.size = 1.0
        self.yellow_color = LColor(255.0 / 255, 248.0 / 255, 231.0 / 255, 1.0)
        self.blue_color = LColor(102.0 / 255, 153.0 / 255, 255.0 / 255, 1.0)

    def shape_id(self):
        return ''

    def get_apparent_radius(self):
        return self.radius

    def get_scale(self):
        return self.scale / self.size

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
            self.gnode = GeomNode('galaxy')
            self.geom = self.makeGeom(*self.create_points())
            self.gnode.addGeom(self.geom)
            template = NodePath(self.gnode)
            GalaxyShapeBase.templates[shape_id] = template
        self.instance = NodePath('galaxy')
        template.instanceTo(self.instance)
        self.apply()
        return self.instance

    def makeGeom(self, points, colors, sizes):
        #format = GeomVertexFormat.getV3c4()
        array = GeomVertexArrayFormat()
        array.addColumn(InternalName.make('vertex'), 3, Geom.NTFloat32, Geom.CPoint)
        array.addColumn(InternalName.make('color'), 4, Geom.NTFloat32, Geom.CColor)
        array.addColumn(InternalName.make('size'), 1, Geom.NTFloat32, Geom.COther)
        format = GeomVertexFormat()
        format.addArray(array)
        format = GeomVertexFormat.registerFormat(format)
        vdata = GeomVertexData('vdata', format, Geom.UH_static)
        vdata.unclean_set_num_rows(len(points))
        self.vwriter = GeomVertexWriter(vdata, 'vertex')
        self.colorwriter = GeomVertexWriter(vdata, 'color')
        self.sizewriter = GeomVertexWriter(vdata, 'size')
        geompoints = GeomPoints(Geom.UH_static)
        geompoints.reserve_num_vertices(len(points))
        index = 0
        for (point, color, size) in zip(points, colors, sizes):
            self.vwriter.addData3f(*point)
            self.colorwriter.addData4f(*color)
            self.sizewriter.addData1f(size)
            geompoints.addVertex(index)
            geompoints.closePrimitive()
            index += 1
        geom = Geom(vdata)
        geom.addPrimitive(geompoints)
        return geom

class EllipticalGalaxyShape(GalaxyShapeBase):
    def __init__(self, factor, radius=1.0, scale=None, nb_points=4000, spread=0.4, zspread=0.2, sprite_size=400):
        GalaxyShapeBase.__init__(self, radius, scale)
        self.factor = factor
        self.nb_points = nb_points
        self.spread = spread
        self.zspread = zspread
        self.sprite_size = sprite_size

    def shape_id(self):
        return 'elliptical-%g' % self.factor

    def create_points(self, radius=1.0):
        points = []
        colors = []
        sizes = []
        nb_points = self.nb_points
        sprite_size = self.sprite_size
        half_sprite_size = self.sprite_size / 2.0
        color = self.yellow_color
        spread = self.spread
        spreadf = self.spread * self.factor
        zspreadf = self.zspread * self.factor
        for i in range(nb_points):
            x = gauss(0.0, spread)
            y = gauss(0.0, spreadf)
            z = gauss(0.0, zspreadf)
            points.append(LPoint3d(x * radius, y * radius, z * radius))
            colors.append(color)
            size = sprite_size + gauss(0, half_sprite_size)
            sizes.append(size)
        return (points, colors, sizes)

class IrregularGalaxyShape(GalaxyShapeBase):
    noise = None
    def __init__(self, radius=1.0, scale=None, nb_points=4000, spread=0.4, zspread=0.2, sprite_size=400):
        GalaxyShapeBase.__init__(self, radius, scale)
        self.nb_points = nb_points
        self.spread = spread
        self.zspread = zspread
        self.sprite_size = sprite_size

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
        half_sprite_size = self.sprite_size / 2.0
        color = [self.yellow_color, self.blue_color]
        spread = self.spread
        zspread = self.zspread
        count = 0
        while count < nb_points:
            p = LPoint3(gauss(0.0, spread), gauss(0.0, spread), gauss(0.0, zspread))
            value = self.noise(p) * 0.5 + 0.5
            if value < 0.5:
                points.append(p * radius)
                colors.append(choice(color))
                size = sprite_size + gauss(0, half_sprite_size)
                sizes.append(size)
                count += 1
        return (points, colors, sizes)

class SpiralGalaxyShapeBase(GalaxyShapeBase):
    def __init__(self, radius=1.0, scale=None, nb_points_bulge=200, nb_points_arms=1000, spread=0.4, zspread=0.01, sprite_size=400):
        GalaxyShapeBase.__init__(self, radius, scale)
        self.nb_points_bulge = nb_points_bulge
        self.nb_points_arms = nb_points_arms
        self.spread = spread
        self.zspread = zspread
        self.sprite_size = sprite_size

    def create_bulge(self, count, radius, spread, zspread, points, colors, sizes):
        sprite_size = self.sprite_size
        half_sprite_size = self.sprite_size / 2.0
        color = self.yellow_color
        for i in range(count):
            x = gauss(0.0, spread)
            y = gauss(0.0, spread)
            z = gauss(0.0, zspread)
            points.append(LPoint3d(x * radius, y * radius, z * radius))
            colors.append(color)
            size = sprite_size + gauss(0, half_sprite_size)
            sizes.append(size)

    def create_spiral(self, count,radius, spread, zspread, points, colors, sizes):
        func = self.shape_func
        sprite_size = self.sprite_size
        half_sprite_size = self.sprite_size / 2.0
        color = self.blue_color
        distance = 0
        for i in (-1.0, 1.0):
            for c in range(count):
                angle = random() * 2.0 * pi
                shape = func(angle)
                x = i * cos(angle) * shape + gauss(0.0, spread)
                y = i * sin(angle) * shape + gauss(0.0, spread)
                z = gauss(0.0, zspread)
                point = LPoint3d(x * radius, y * radius, z * radius)
                points.append(point)
                distance = max(distance, point.length())
                colors.append(color)
                size = sprite_size + gauss(0, half_sprite_size)
                sizes.append(size)
        self.size = distance

    def create_points(self, radius=1.0):
        points = []
        colors = []
        sizes = []
        nb_points_bulge = self.nb_points_bulge
        nb_points_arms = self.nb_points_arms
        spread = self.bulge_size()
        zspread = spread / 2.0
        self.create_bulge(nb_points_bulge, radius, spread, zspread, points, colors, sizes)
        self.create_spiral(nb_points_arms, radius, self.spread, self.zspread, points, colors, sizes)
        self.nb_points = nb_points_bulge + nb_points_arms
        return (points, colors, sizes)

class FullSpiralGalaxyShape(SpiralGalaxyShapeBase):
    def __init__(self, N, B, radius=1.0, scale=None, nb_points_bulge=200, nb_points_arms=1000, spread=0.4, zspread=0.2, point_size=400):
        SpiralGalaxyShapeBase.__init__(self, radius, scale, nb_points_bulge, nb_points_arms, spread, zspread, point_size)
        self.N = N
        self.B = B

    def shape_id(self):
        return 'spiral-%g-%g' % (self.N, self.B)

    def bulge_size(self):
        return 2 * self.shape_func(0)

    def shape_func(self, angle):
        return 1.0 / log(self.B * max(0.00001, tan(angle / (2 * self.N))))

class FullRingGalaxyShape(SpiralGalaxyShapeBase):
    def __init__(self, N, B, radius=1.0, scale=None, nb_points_bulge=200, nb_points_arms=1000, spread=0.4, zspread=0.2, point_size=400):
        SpiralGalaxyShapeBase.__init__(self, radius, scale, nb_points_bulge, nb_points_arms, spread, zspread, point_size)
        self.N = N
        self.B = B

    def shape_id(self):
        return 'ring-%g-%g' % (self.N, self.B)

    def bulge_size(self):
        return 2 * self.shape_func(0)

    def shape_func(self, angle):
        return 1.0 / log(self.B * max(0.00001, tanh(angle / (2 * self.N))))

class SpiralGalaxyShape(SpiralGalaxyShapeBase):
    bar_radius = 0.5
    def __init__(self, pitch, radius=1.0, scale=None, nb_points_bulge=200, nb_points_arms=1000, spread=0.4, zspread=0.2, point_size=400):
        SpiralGalaxyShapeBase.__init__(self, radius, scale, nb_points_bulge, nb_points_arms, spread, zspread, point_size)
        self.pitch = pitch

    def shape_id(self):
        return 'spiral-%g' % self.pitch

    def bulge_size(self):
        return 2 * self.shape_func(0)

    def shape_func(self, angle):
        pitch = self.pitch
        return self.bar_radius / (1 - pitch * tan(pitch) * log(max(0.00001, (angle / pitch))))

class LenticularGalaxyShape(SpiralGalaxyShapeBase):
    bulge_radius = 0.2

    def shape_id(self):
        return 'lenticular'

    def bulge_size(self):
        return self.bulge_radius

    def spread(self):
        return 0.1

    def create_spiral(self, count, radius, spread, zspread, points, colors, sizes):
        sprite_size = self.sprite_size
        half_sprite_size = self.sprite_size / 2.0
        color = self.yellow_color
        for r in range(count * 2):
            distance = self.bulge_radius + abs(gauss(0, (1 - self.bulge_radius)))
            angle = random() * 2.0 * pi
            x = distance * cos(angle) + gauss(0.0, spread)
            y = distance * sin(angle) + gauss(0.0, spread)
            z = gauss(0.0, zspread)
            points.append(LPoint3d(x * radius, y * radius, z * radius))
            colors.append(color)
            size = sprite_size + gauss(0, half_sprite_size)
            sizes.append(size)
