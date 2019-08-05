from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import GeomVertexArrayFormat, InternalName, GeomVertexFormat, GeomVertexData, GeomVertexWriter
from panda3d.core import GeomPoints, Geom, GeomNode
from panda3d.core import NodePath, OmniBoundingVolume
from .foundation import VisibleObject
from .appearances import ModelAppearance
from .shaders import BasicShader, FlatLightingModel
from .sprites import SimplePoint, RoundDiskPointSprite

class PointsSet(VisibleObject):
    tex = None
    def __init__(self, use_sprites=True, use_sizes=True, points_size=2, sprite=None, background=None, shader=None):
        self.gnode = GeomNode('starfield')
        self.use_sprites = use_sprites
        self.use_sizes = use_sizes
        self.background = background
        if shader is None:
            shader = BasicShader(lighting_model=FlatLightingModel(), point_shader=False)
        self.shader = shader

        self.reset()

        self.geom = self.makeGeom([], [], [])
        self.gnode.addGeom(self.geom)
        self.instance = NodePath(self.gnode)
        if self.use_sprites:
            if sprite is None:
                sprite = RoundDiskPointSprite()
            self.sprite = sprite
        else:
            self.sprite = SimplePoint(points_size)
        self.min_size = self.sprite.get_min_size()
        self.sprite.apply(self.instance)
        self.instance.setCollideMask(GeomNode.getDefaultCollideMask())
        self.instance.node().setPythonTag('owner', self)
        #TODO: Should not use ModelAppearance !
        self.appearance = ModelAppearance(vertex_color=True)
        if self.appearance is not None:
            self.appearance.bake()
            self.appearance.apply(self, self)
        if self.shader is not None:
            self.shader.apply(self, self.appearance)
        if self.use_sprites:
            self.instance.node().setBounds(OmniBoundingVolume())
            self.instance.node().setFinal(True)
        if self.background is not None:
            self.instance.setBin('background', self.background)
        self.instance.set_depth_write(False)

    def jobs_done_cb(self, patch):
        pass

    def reset(self):
        self.points = []
        self.colors = []
        self.sizes = []

    def add_point_scale(self, position, color, size):
        #Observer is at position (0, 0, 0)
        distance_to_obs = position.length()
        vector_to_obs = -position / distance_to_obs
        point, _, _ = self.get_real_pos_rel(position, distance_to_obs, vector_to_obs)
        self.points.append(point)
        self.colors.append(color)
        self.sizes.append(size)

    def add_point(self, position, color, size):
        self.points.append(position)
        self.colors.append(color)
        self.sizes.append(size)

    def update(self):
        self.update_arrays(self.points, self.colors, self.sizes)

    def makeGeom(self, points, colors, sizes):
        #format = GeomVertexFormat.getV3c4()
        array = GeomVertexArrayFormat()
        array.addColumn(InternalName.make('vertex'), 3, Geom.NTFloat32, Geom.CPoint)
        array.addColumn(InternalName.make('color'), 4, Geom.NTFloat32, Geom.CColor)
        if self.use_sizes:
            array.addColumn(InternalName.make('size'), 1, Geom.NTFloat32, Geom.COther)
        format = GeomVertexFormat()
        format.addArray(array)
        format = GeomVertexFormat.registerFormat(format)
        vdata = GeomVertexData('vdata', format, Geom.UH_static)
        vdata.unclean_set_num_rows(len(points))
        self.vwriter = GeomVertexWriter(vdata, 'vertex')
        self.colorwriter = GeomVertexWriter(vdata, 'color')
        if self.use_sizes:
            self.sizewriter = GeomVertexWriter(vdata, 'size')
        geompoints = GeomPoints(Geom.UH_static)
        geompoints.reserve_num_vertices(len(points))
        index = 0
        for (point, color, size) in zip(points, colors, sizes):
            self.vwriter.addData3f(*point)
            #self.colorwriter.addData3f(color[0], color[1], color[2])
            self.colorwriter.addData4f(*color)
            if self.use_sizes:
                self.sizewriter.addData1f(size)
            geompoints.addVertex(index)
            geompoints.closePrimitive()
            index += 1
        geom = Geom(vdata)
        geom.addPrimitive(geompoints)
        return geom

    def update_arrays(self, points, colors, sizes):
        self.gnode.removeAllGeoms()
        self.geom = self.makeGeom(points, colors, sizes)
        self.gnode.addGeom(self.geom)
