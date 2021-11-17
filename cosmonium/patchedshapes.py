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


from panda3d.core import OmniBoundingVolume, GeomNode, Texture
from panda3d.core import LVector3d, LVector4, LPoint2d, LPoint3d, LColor, LQuaterniond, LQuaternion, LMatrix3, LMatrix4, LVecBase4i
from panda3d.core import NodePath
from panda3d.core import RenderState, ColorAttrib, RenderModeAttrib, CullFaceAttrib, ShaderAttrib
from direct.task.Task import gather

from .shapes import Shape
from .datasource import DataSource
from .shaders import DataStoreManagerDataSource, ParametersDataStoreDataSource
from .textures import TexCoord
from .pstats import pstat
from . import geometry
from . import settings

from math import cos, sin, pi, sqrt, copysign, log
from collections import deque
import struct

try:
    from cosmonium_engine import QuadTreeNode
    from cosmonium_engine import CullingFrustumBase, CullingFrustum, HorizonCullingFrustum
    from cosmonium_engine import LodResult
    from cosmonium_engine import LodControl, TextureLodControl, TextureOrVertexSizeLodControl, VertexSizeLodControl, VertexSizeMaxDistanceLodControl
except ImportError as e:
    print("WARNING: Could not load Patch C implementation, fallback on python implementation")
    print("\t", e)
    from .pyrendering.quadtree import QuadTreeNode
    from .pyrendering.cullingfrustum import CullingFrustumBase, CullingFrustum, HorizonCullingFrustum
    from .pyrendering.lodresult import LodResult
    from .pyrendering.lodcontrol import LodControl, TextureLodControl, TextureOrVertexSizeLodControl, VertexSizeLodControl, VertexSizeMaxDistanceLodControl

class BoundingBoxShape():
    state = None
    def __init__(self, box):
        self.box = box
        self.instance = None

    def create_instance(self):
        if self.instance is not None: return
        self.instance = geometry.BoundingBoxGeom(self.box)
        if BoundingBoxShape.state is None:
            BoundingBoxShape.state = RenderState.make(ColorAttrib.make_flat(LColor(1, 0, 0, 1)),#0.3, 1.0, 0.5, 1.0)),
                                                      RenderModeAttrib.make(RenderModeAttrib.M_wireframe),
                                                      CullFaceAttrib.make(CullFaceAttrib.M_cull_clockwise),
                                                      ShaderAttrib.make().set_shader_auto(True))
        self.instance.set_state(self.state)
        return self.instance

    def remove_instance(self):
        if self.instance is not None:
            self.instance.remove_node()
            self.instance = None

class PatchLayer:
    def __init__(self):
        self.instance = None

    def check_settings(self):
        pass

    def create_instance(self, patch):
        pass

    def patch_done(self, patch):
        pass

    def update_instance(self, patch):
        pass

    def remove_instance(self):
        if self.instance is not None:
            self.instance.removeNode()
            self.instance = None

class PatchFactory:
    def __init__(self):
        self.heightmap = None
        self.lod_control = None
        self.surface = None
        self.owner = None

    def set_heightmap(self, heightmap):
        self.heightmap = heightmap

    def set_lod_control(self, lod_control):
        self.lod_control = lod_control

    def set_surface(self, surface):
        self.surface = surface

    def set_owner(self, owner):
        self.owner = owner

    #TODO: To move to proper class
    def get_patch_limits(self, patch):
        min_radius = 1.0
        max_radius = 1.0
        mean_radius = 1.0
        if self.heightmap is not None and patch is not None:
            patch_data = self.heightmap.get_patch_data(patch, recurse=True)
            if patch_data is not None:
                #TODO: This should be done inside the heightmap patch
                height_scale = self.heightmap.height_scale
                height_offset = self.heightmap.height_offset
                min_radius = 1.0 + patch_data.min_height * height_scale + height_offset
                max_radius = 1.0 + patch_data.max_height * height_scale + height_offset
                mean_radius = 1.0 + patch_data.mean_height * height_scale + height_offset
            else:
                print("NO PATCH DATA !!!", patch.str_id())
        return (min_radius, max_radius, mean_radius)

    def create_patch(self, parent, lod, x, y):
        pass

class PatchNeighboursBase:
    pass

class PatchNoNeighbours(PatchNeighboursBase):
    def __init__(self, patch):
        self.patch = patch

    def set_neighbours(self, face, neighbours):
        pass

    def add_neighbour(self, face, neighbour):
        pass

    def get_neighbours(self, face):
        return []

    def collect_side_neighbours(self, side):
        return []

    def set_all_neighbours(self, north, east, south, west):
        pass

    def clear_all_neighbours(self):
        pass

    def get_all_neighbours(self):
        return []

    def get_neighbour_lower_lod(self, face):
        return self.patch.lod

    def remove_detached_neighbours(self):
        pass

    def replace_neighbours(self, face, olds, news):
        pass

    def split_neighbours(self, update):
        pass

    def merge_neighbours(self, update):
        pass

    def calc_outer_tessellation_level(self, update):
        pass

class PatchNeighbours(PatchNeighboursBase):
    def __init__(self, patch):
        self.patch = patch
        self.neighbours = [[], [], [], []]

    def set_neighbours(self, face, neighbours):
        self.neighbours[face] = neighbours

    def add_neighbour(self, face, neighbour):
        if neighbour not in self.neighbours[face]:
            self.neighbours[face].append(neighbour)

    def get_neighbours(self, face):
        return [] + self.neighbours[face]

    def _collect_side_neighbours(self, result, side):
        if len(self.patch.children) != 0:
            (bl, br, tr, tl) = self.patch.children
            if side == PatchBase.NORTH:
                tl.neighbours._collect_side_neighbours(result, side)
                tr.neighbours._collect_side_neighbours(result, side)
            elif side == PatchBase.EAST:
                tr.neighbours._collect_side_neighbours(result, side)
                br.neighbours._collect_side_neighbours(result, side)
            elif side == PatchBase.SOUTH:
                bl.neighbours._collect_side_neighbours(result, side)
                br.neighbours._collect_side_neighbours(result, side)
            elif side == PatchBase.WEST:
                tl.neighbours._collect_side_neighbours(result, side)
                bl.neighbours._collect_side_neighbours(result, side)
        else:
            result.append(self.patch)

    def collect_side_neighbours(self, side):
        result = []
        self._collect_side_neighbours(result, side)
        return result

    def set_all_neighbours(self, north, east, south, west):
        self.neighbours[PatchBase.NORTH] = north
        self.neighbours[PatchBase.EAST] = east
        self.neighbours[PatchBase.SOUTH] = south
        self.neighbours[PatchBase.WEST] = west

    def clear_all_neighbours(self):
        self.neighbours = [[], [], [], []]

    def get_all_neighbours(self):
        neighbours = []
        for i in range(4):
            neighbours += self.neighbours[i]
        return neighbours

    def get_neighbour_lower_lod(self, face):
        lower_lod = self.patch.lod
        for neighbour in self.neighbours[face]:
            #print(neighbour.lod)
            lower_lod = min(lower_lod, neighbour.lod)
        return lower_lod

    def remove_detached_neighbours(self):
        valid = []
        patch = self.patch
        for neighbour in self.neighbours[PatchBase.NORTH]:
            if neighbour.x1 > patch.x0 and neighbour.x0 < patch.x1:
                valid.append(neighbour)
        self.neighbours[PatchBase.NORTH] = valid
        valid = []
        for neighbour in self.neighbours[PatchBase.SOUTH]:
            if neighbour.x1 > patch.x0 and neighbour.x0 < patch.x1:
                valid.append(neighbour)
        self.neighbours[PatchBase.SOUTH] = valid
        valid = []
        for neighbour in self.neighbours[PatchBase.EAST]:
            if neighbour.y1 > patch.y0 and neighbour.y0 < patch.y1:
                valid.append(neighbour)
        self.neighbours[PatchBase.EAST] = valid
        valid = []
        for neighbour in self.neighbours[PatchBase.WEST]:
            if neighbour.y1 > patch.y0 and neighbour.y0 < patch.y1:
                valid.append(neighbour)
        self.neighbours[PatchBase.WEST] = valid

    def replace_neighbours(self, face, olds, news):
        opposite = PatchBase.opposite_face[face]
        for neighbour_patch in self.neighbours[face]:
            neighbour_list = neighbour_patch.neighbours.neighbours[opposite]
            for old in olds:
                try:
                    neighbour_list.remove(old)
                except ValueError:
                    pass
            for new in news:
                if not new in neighbour_list:
                    neighbour_list.append(new)

    def split_neighbours(self, update):
        (bl, br, tr, tl) = self.patch.children
        tl.set_all_neighbours(self.get_neighbours(PatchBase.NORTH), [tr], [bl], self.get_neighbours(PatchBase.WEST))
        tr.set_all_neighbours(self.get_neighbours(PatchBase.NORTH), self.get_neighbours(PatchBase.EAST), [br], [tl])
        br.set_all_neighbours([tr], self.get_neighbours(PatchBase.EAST), self.get_neighbours(PatchBase.SOUTH), [bl])
        bl.set_all_neighbours([tl], [br], self.get_neighbours(PatchBase.SOUTH), self.get_neighbours(PatchBase.WEST))
        neighbours = self.get_all_neighbours()
        self.replace_neighbours(PatchBase.NORTH, [self.patch], [tl, tr])
        self.replace_neighbours(PatchBase.EAST, [self.patch], [tr, br])
        self.replace_neighbours(PatchBase.SOUTH, [self.patch], [bl, br])
        self.replace_neighbours(PatchBase.WEST,  [self.patch], [tl, bl])
        for (i, new) in enumerate((tl, tr, br, bl)):
            #text = ['tl', 'tr', 'br', 'bl']
            #print("*** Child", text[i], '***')
            new.remove_detached_neighbours()
            new.calc_outer_tessellation_level(update)
        #print("Neighbours")
        for neighbour in neighbours:
            neighbour.remove_detached_neighbours()
            neighbour.calc_outer_tessellation_level(update)
        self.clear_all_neighbours()

    def merge_neighbours(self, update):
        (bl, br, tr, tl) = self.patch.children
        north = []
        for neighbour in tl.get_neighbours(PatchBase.NORTH) + tr.get_neighbours(PatchBase.NORTH):
            if neighbour not in north:
                north.append(neighbour)
        east = []
        for neighbour in tr.get_neighbours(PatchBase.EAST) + br.get_neighbours(PatchBase.EAST):
            if neighbour not in east:
                east.append(neighbour)
        south = []
        for neighbour in bl.get_neighbours(PatchBase.SOUTH) + br.get_neighbours(PatchBase.SOUTH):
            if neighbour not in south:
                south.append(neighbour)
        west = []
        for neighbour in tl.get_neighbours(PatchBase.WEST) + bl.get_neighbours(PatchBase.WEST):
            if neighbour not in west:
                west.append(neighbour)
        self.set_all_neighbours(north, east, south, west)
        self.replace_neighbours(PatchBase.NORTH, [tl, tr], [self.patch])
        self.replace_neighbours(PatchBase.EAST, [tr, br], [self.patch])
        self.replace_neighbours(PatchBase.SOUTH, [bl, br], [self.patch])
        self.replace_neighbours(PatchBase.WEST,  [tl, bl], [self.patch])
        self.calc_outer_tessellation_level(update)
        for neighbour in north + east + south + west:
            neighbour.calc_outer_tessellation_level(update)

    def calc_outer_tessellation_level(self, update):
        for face in range(4):
            #print("Check face", PatchBase.text[face])
            lod = self.get_neighbour_lower_lod(face)
            delta = self.patch.lod - lod
            outer_level = max(0, self.patch.max_level - delta)
            new_level = 1 << outer_level
            dest = PatchBase.conv[face]
            if self.patch.tessellation_outer_level[dest] != new_level:
                #print("Change from", self.tessellation_outer_level[dest], "to", new_level)
                if not self.patch in update:
                    update.append(self.patch)
            self.patch.tessellation_outer_level[dest] = new_level
            #print("Level", PatchBase.text[face], ":", delta, 1 << outer_level)

class PatchDataStoreManager:
    def __init__(self, max_elem):
        self.max_elem = max_elem
        self.entries = [None] * max_elem
        self.free_entries = deque(range(max_elem))
        self.data_stores = []
        self.parameters = PatchParametersDataStore()
        self.add_data_store(self.parameters)

    def add_data_store(self, data_store):
        self.data_stores.append(data_store)
        data_store.parent = self

    def init(self):
        for data_store in self.data_stores:
            data_store.init()

    def get_shader_data_source(self):
        shader_data_source = DataStoreManagerDataSource()
        for data_store in self.data_stores:
            shader_data_source.add_source(data_store.get_shader_data_source())
        return shader_data_source

    def apply(self, instance):
        for data_store in self.data_stores:
            data_store.apply(instance)

    def clear(self):
        self.entries = [None] * self.max_elem
        self.free_entries = deque(range(self.max_elem))
        for data_store in self.data_stores:
            data_store.clear()

    def apply_patch_data(self, patch, instance):
        if patch.entry_id is None:
            self.add_patch(patch)
        instance.set_shader_input('entry_id', patch.entry_id)

    def add_patch(self, patch):
        if patch.entry_id is None:
            entry_id = self.free_entries.pop()
            patch.entry_id = entry_id

    def remove_patch(self, patch):
        entry_id = patch.entry_id
        if entry_id is not None:
            self.free_entries.append(entry_id)
            patch.entry_id = None

    def update_patch(self, patch):
        if patch.entry_id is None:
            self.add_patch(patch)
        for data_store in self.data_stores:
            data_store.update_patch(patch)

class PatchParametersDataStore:
    def __init__(self):
        self.texture_data = None
        self.data_sources = []
        self.data_size = 0
        self.texture_size = 0
        self.pack_format = ''

    def get_shader_data_source(self):
        return ParametersDataStoreDataSource()

    def add_data_source(self, data_source):
        if self.texture_data is not None:
            print("ERROR, can not add data source")
            return
        self.data_sources.append(data_source)
        self.data_size += data_source.get_nb_shader_data()
        self.texture_size = self.parent.max_elem * ((self.data_size * 4 + 15) // 16)
        self.pack_format = 'f' * self.data_size

    def init(self):
        if self.texture_size == 0: return
        self.texture_data = Texture()
        self.texture_data.setup_1d_texture(self.texture_size, Texture.T_float, Texture.F_rgba32)
        self.texture_data.set_clear_color(0.0)

    def apply(self, instance):
        if self.texture_size == 0: return
        instance.set_shader_input("data_store", self.texture_data)

    def clear(self):
        self.texture_data = None

    def update_patch(self, patch):
        if self.texture_size == 0: return
        data = []
        for data_source in self.data_sources:
            data_source.collect_shader_data(data, patch)
        data_buffer = memoryview(self.texture_data.modify_ram_image())
        offset = patch.entry_id * self.data_size * 4
        packed_data = struct.pack(self.pack_format, *data)
        data_buffer[offset : offset + self.data_size * 4] = packed_data

class PatchBase(Shape):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    opposite_face = [SOUTH, WEST, NORTH, EAST]
    text = ['North', 'East', 'South', 'West']
    conv = [WEST, SOUTH, EAST, NORTH]

    coord = None

    def __init__(self, parent, lod, density, surface_scale):
        Shape.__init__(self)
        self.parent = parent
        self.lod = lod
        self.density = density
        self.owner = None
        self.quadtree_node = None
        self.entry_id = None
        self.tessellation_inner_level = density
        self.tessellation_outer_level = LVecBase4i(density, density, density, density)
        self.neighbours = PatchNeighbours(self)
        self.layers = []
        self.max_level = int(log(density, 2)) #TODO: should be done properly with checks
        self.flat_coord = None
        self.bounds_shape = None
        self.children = []
        self.shown = False
        self.last_split = 0

    def check_settings(self):
        Shape.check_settings(self)
        for layer in self.layers:
            layer.check_settings()
        if self.instance is not None:
            if settings.debug_lod_show_bb:
                if self.bounds_shape.instance is None:
                    self.bounds_shape.create_instance()
                    #TODO: This is more that ugly...
                    self.bounds_shape.instance.reparent_to(self.owner.instance)
            else:
                self.bounds_shape.remove_instance()

    def add_layer(self, layer):
        self.layers.append(layer)

    def remove_layer(self, layer):
        self.layers.remove(layer)

    def add_neighbour(self, face, neighbour):
        return self.neighbours.add_neighbour(face, neighbour)

    def set_all_neighbours(self, north, east, south, west):
        return self.neighbours.set_all_neighbours(north, east, south, west)

    def get_neighbours(self, face):
        return self.neighbours.get_all_neighbours()

    def collect_side_neighbours(self, side):
        return self.neighbours.collect_side_neighbours(side)

    def remove_detached_neighbours(self):
        return self.neighbours.remove_detached_neighbours()

    def split_neighbours(self, update):
        return self.neighbours.split_neighbours(update)

    def merge_neighbours(self, update):
        return self.neighbours.merge_neighbours(update)

    def calc_outer_tessellation_level(self, update):
        self.neighbours.calc_outer_tessellation_level(update)

    def patch_done(self):
        self.quadtree_node.set_instance_ready(self.instance_ready)
        if self.instance is not None:
            self.instance.unstash()
        for layer in self.layers:
            layer.patch_done(self)

    def create_geometry_instance(self):
        for layer in self.layers:
            layer.create_instance(self)

    def remove_geometry_instance(self):
        for layer in self.layers:
            layer.remove_instance()

    def create_instance(self):
        self.instance = NodePath('patch')
        self.instance.setPythonTag('patch', self)
        self.create_geometry_instance()
        if settings.debug_lod_show_bb:
            self.bounds_shape = BoundingBoxShape(self.quadtree_node.bounds)
            self.bounds_shape.create_instance()
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(1)
        self.quadtree_node.set_shown(True)

    def update_instance(self, shape):
        if self.instance is None: return
        #print("Update", self.str_id())
        for layer in self.layers:
            layer.update_instance(self)

    def remove_instance(self):
        self.quadtree_node.set_shown(False)
        self.quadtree_node.set_instance_ready(False)
        Shape.remove_instance(self)
        if self.bounds_shape is not None:
            self.bounds_shape.remove_instance()
        self.remove_geometry_instance()

    def add_child(self, child):
        child.parent = self
        child.owner = self.owner
        self.children.append(child)
        self.quadtree_node.add_child(child.quadtree_node)

    def remove_children(self):
        for child in self.children:
            child.parent = None
            child.remove_instance()
            child.shown = False
        self.children = []
        self.quadtree_node.remove_children()

class SpherePatch(PatchBase):
    coord = TexCoord.Cylindrical

    def __init__(self, parent, lod, density, x, y, surface_scale, min_radius, max_radius, mean_radius):
        PatchBase.__init__(self, parent, lod, density, surface_scale)
        self.face = -1
        self.x = x
        self.y = y
        r_div = 1 << self.lod
        s_div = 2 << self.lod
        if settings.shift_patch_origin:
            self.offset = mean_radius
        self.x0 = float(self.x) / s_div
        self.y0 = float(self.y) / r_div
        self.x1 = float(self.x + 1) / s_div
        self.y1 = float(self.y + 1) / r_div
        long_scale = 2 * pi * surface_scale * 1000.0
        lat_scale = pi * surface_scale * 1000.0
        long0 = self.x0 * long_scale
        long1 = self.x1 * long_scale
        lat0 = self.y1 * lat_scale
        lat1 = self.y0 * lat_scale
        self.flat_coord = LVector4((long0 % 1000.0),
                                    (lat0 % 1000.0),
                                    (long1 - long0),
                                    (lat1 - lat0))
        self.create_quadtree_node(min_radius, max_radius, mean_radius)
        self.bounds_shape = BoundingBoxShape(self.quadtree_node.bounds)

    def create_quadtree_node(self, min_radius, max_radius, mean_radius):
        nb_sectors = 2 << self.lod
        length = mean_radius * 2 * pi / nb_sectors
        normal = geometry.UVPatchNormal(self.x0, self.y0, self.x1, self.y1)
        if self.lod > 0:
            bounds = geometry.UVPatchAABB(min_radius, max_radius,
                                          self.x0, self.y0, self.x1, self.y1,
                                          offset=self.offset)
        else:
            bounds = geometry.halfSphereAABB(mean_radius, self.x == 1, self.offset)
        centre =  geometry.UVPatchPoint(mean_radius,
                                        0.5, 0.5,
                                        self.x0, self.y0,
                                        self.x1, self.y1)
        self.quadtree_node = QuadTreeNode(self, self.lod, self.density, centre, length, normal, self.offset, bounds)

    def str_id(self):
        return "%d - %d %d" % (self.lod, self.y, self.x)

    def set_texture_to_lod(self, texture, texture_stage, texture_lod, patched):
        if texture_lod == self.lod and patched:
            return
        delta = self.lod - texture_lod
        if delta < 0:
            print(self.str_id(), self.lod, texture_lod, texture_stage)
        scale = 1 << delta
        if patched:
            x_scale = scale
            y_scale = scale
        else:
            x_scale = 2 * scale
            y_scale = scale
        self.instance.setTexScale(texture_stage, 1.0 / x_scale, 1.0 / y_scale)
        x_tex = (self.x // x_scale) * x_scale
        y_tex = (self.y // y_scale) * y_scale
        x_delta = float(self.x - x_tex) / x_scale
        y_delta = float(self.y - y_tex) / y_scale
        if not patched and texture.offset != 0:
            x_delta += texture.offset / 360.0
        self.instance.setTexOffset(texture_stage, x_delta, y_delta)

    def coord_to_uv(self, coord):
        (x, y) = coord
        dx = self.x1 - self.x0
        dy = self.y1 - self.y0
        u = (x - self.x0) / dx
        v = (y - self.y0) / dy
        return (u, v)

    def get_normals_at(self, coord):
        (u, v) = self.coord_to_uv(coord)
        normal = geometry.UVPatchPoint(1.0,
                                       u, v,
                                       self.x0, self.y0, self.x1, self.y1)
        tangent = LVector3d(-normal[1], normal[0], 0)
        tangent.normalize()
        binormal = normal.cross(tangent)
        binormal.normalize()
        return (normal, tangent, binormal)

    def get_lonlatvert_at(self, coord):
        (u, v) = self.coord_to_uv(coord)
        normal = geometry.UVPatchPoint(1.0,
                                       u, v,
                                       self.x0, self.y0, self.x1, self.y1)
        tangent = LVector3d(-normal[1], normal[0], 0)
        tangent.normalize()
        binormal = normal.cross(tangent)
        binormal.normalize()
        return (tangent, binormal, normal)

class SpherePatchLayer(PatchLayer):
    def create_instance(self, patch):
        self.instance = geometry.UVPatch(1.0,
                                         patch.density, patch.density,
                                         patch.x0, patch.y0, patch.x1, patch.y1,
                                         has_offset=patch.offset is not None,
                                         offset=patch.offset)
        self.instance.reparent_to(patch.instance)

    def update_instance(self, patch):
        if self.instance is not None and patch.shown:
                self.remove_instance()
                self.create_instance(patch)

class SquarePatchBase(PatchBase):

    RIGHT = 0
    LEFT = 1
    BACK = 2
    FRONT = 3
    TOP = 4
    BOTTOM = 5

    rotations = [LQuaterniond(), LQuaterniond(), LQuaterniond(), LQuaterniond(), LQuaterniond(), LQuaterniond()]
    rotations_mat = [LMatrix4(), LMatrix4(),LMatrix4(), LMatrix4(), LMatrix4(), LMatrix4()]
    rotations[0].setHpr(LVector3d(0, 0, 90)) #right
    rotations[1].setHpr(LVector3d(0, 0, -90)) #left
    rotations[2].setHpr(LVector3d(0, 90, 0)) #back
    rotations[3].setHpr(LVector3d(0, -90, 0)) #face
    rotations[4].setHpr(LVector3d(180, 0, 0)) #top
    rotations[5].setHpr(LVector3d(180, 180, 0)) #bottom
    for i in range(6):
        LQuaternion(*rotations[i]).extractToMatrix(rotations_mat[i])

    def __init__(self, face, x, y, parent, lod, density, surface_scale, min_radius, max_radius, mean_radius):
        PatchBase.__init__(self, parent, lod, density, surface_scale)
        self.face = face
        self.x = x
        self.y = y
        div = 1 << self.lod
        self.x0 = float(self.x) / div
        self.y0 = float(self.y) / div
        self.x1 = float(self.x + 1) / div
        self.y1 = float(self.y + 1) / div
        if settings.shift_patch_origin:
            self.offset = mean_radius
        long_scale = 2 * pi * surface_scale * 1000.0
        lat_scale = pi * surface_scale * 1000.0
        long0 = self.x0 * long_scale / 4
        long1 = self.x1 * long_scale / 4
        lat0 = self.y1 * lat_scale / 4
        lat1 = self.y0 * lat_scale / 4
        self.flat_coord = LVector4((long0 % 1000.0),
                                    (lat0 % 1000.0),
                                    (long1 - long0),
                                    (lat1 - lat0))
        self.create_quadtree_node(min_radius, max_radius, mean_radius)
        self.bounds_shape = BoundingBoxShape(self.quadtree_node.bounds)

    def create_quadtree_node(self,min_radius, max_radius, mean_radius):
        nb_sectors = 4 << self.lod
        length = mean_radius * 2 * pi / nb_sectors
        bounds = self.create_bounding_volume(min_radius, max_radius)
        bounds.xform(self.rotations_mat[self.face])
        centre = self.create_centre(mean_radius)
        centre = self.rotations[self.face].xform(centre)
        source_normal = self.face_normal()
        normal = self.rotations[self.face].xform(source_normal)
        self.quadtree_node = QuadTreeNode(self, self.lod, self.density, centre, length, normal, self.offset, bounds)

    def face_normal(self, x, y):
        return None

    def create_bounding_volume(self, x, y, min_radius, max_radius):
        return None

    def create_centre(self, x, y):
        return None

    def create_patch_instance(self, x, y):
        return None

    def str_id(self):
        return "%d - %d %d %d" % (self.lod, self.face, self.x, self.y)

    def set_texture_to_lod(self, texture, texture_stage, texture_lod, patched):
        #TODO: Refactor into Patch
        if texture_lod == self.lod and patched:
            return
        delta = self.lod - texture_lod
        if delta < 0:
            print(self.str_id(), self.lod, texture_lod, texture_stage)
        scale = 1 << delta
        if patched:
            x_scale = scale
            y_scale = scale
        else:
            x_scale = 2 * scale
            y_scale = scale
        self.instance.setTexScale(texture_stage, 1.0 / x_scale, 1.0 / y_scale)
        x_tex = (self.x // x_scale) * x_scale
        y_tex = (self.y // y_scale) * y_scale
        x_delta = float(self.x - x_tex) / x_scale
        y_delta = float(self.y - y_tex) / y_scale
        self.instance.setTexOffset(texture_stage, x_delta, y_delta)

    def coord_to_uv(self, coord):
        (face, x, y) = coord
        dx = self.x1 - self.x0
        dy = self.y1 - self.y0
        u = (x - self.x0) / dx
        v = (y - self.y0) / dy
        return (u, v)

class NormalizedSquarePatch(SquarePatchBase):
    coord = TexCoord.NormalizedCube

    def face_normal(self):
        return geometry.NormalizedSquarePatchNormal(self.x0, self.y0, self.x1, self.y1)

    def create_bounding_volume(self, min_radius, max_radius):
        return geometry.NormalizedSquarePatchAABB(min_radius, max_radius,
                                                  self.x0, self.y0, self.x1, self.y1,
                                                  offset=self.offset)

    def create_centre(self, radius):
        return geometry.NormalizedSquarePatchPoint(radius,
                                                  0.5, 0.5,
                                                  self.x0, self.y0, self.x1, self.y1)
    def get_normals_at(self, coord):
        (u, v) = self.coord_to_uv(coord)
        normal = geometry.NormalizedSquarePatchPoint(1.0,
                                                     u, v,
                                                     self.x0, self.y0, self.x1, self.y1)
        normal = self.rotations[self.face].xform(normal)
        tangent = LVector3d(-normal[1], normal[0], normal[2])
        tangent.normalize()
        binormal = normal.cross(tangent)
        binormal.normalize()
        return (normal, tangent, binormal)

    def get_lonlatvert_at(self, coord):
        (u, v) = self.coord_to_uv(coord)
        normal = geometry.NormalizedSquarePatchPoint(1.0,
                                                     u, v,
                                                     self.x0, self.y0, self.x1, self.y1)
        normal = self.rotations[self.face].xform(normal)
        tangent = LVector3d(-normal[1], normal[0], 0)
        tangent.normalize()
        binormal = normal.cross(tangent)
        binormal.normalize()
        return (tangent, binormal, normal)

class NormalizedSquarePatchLayer(PatchLayer):
    def create_instance(self, patch):
        self.instance = geometry.NormalizedSquarePatch(1.0,
                                                       geometry.TesselationInfo(patch.density, patch.tessellation_outer_level),
                                                       patch.x0, patch.y0, patch.x1, patch.y1,
                                                       has_offset=patch.offset is not None,
                                                       offset=patch.offset,
                                                       use_patch_adaptation=settings.use_patch_adaptation,
                                                       use_patch_skirts=settings.use_patch_skirts)
        self.instance.reparent_to(patch.instance)
        orientation = patch.rotations[patch.face]
        self.instance.set_quat(LQuaternion(*orientation))

    def update_instance(self, patch):
        if self.instance is not None and patch.shown:
                self.remove_instance()
                self.create_instance(patch)

class SquaredDistanceSquarePatch(SquarePatchBase):
    coord = TexCoord.SqrtCube

    def face_normal(self):
        return geometry.SquaredDistanceSquarePatchNormal(self.x0, self.y0, self.x1, self.y1)

    def create_bounding_volume(self, min_radius, max_radius):
        return geometry.SquaredDistanceSquarePatchAABB(min_radius, max_radius,
                                                       self.x0, self.y0, self.x1, self.y1,
                                                       offset=self.offset)

    def create_centre(self, radius):
        return geometry.SquaredDistanceSquarePatchPoint(radius,
                                                       0.5, 0.5,
                                                       self.x0, self.y0, self.x1, self.y1)

    def get_normals_at(self, coord):
        (u, v) = self.coord_to_uv(coord)
        normal = geometry.SquaredDistanceSquarePatchPoint(1.0,
                                                          u, v,
                                                          self.x0, self.y0, self.x1, self.y1)
        normal = self.rotations[self.face].xform(normal)
        tangent = LVector3d(-normal[1], normal[0], normal[2])
        tangent.normalize()
        binormal = normal.cross(tangent)
        binormal.normalize()
        return (normal, tangent, binormal)

    def get_lonlatvert_at(self, coord):
        (u, v) = self.coord_to_uv(coord)
        normal = geometry.SquaredDistanceSquarePatchPoint(1.0,
                                                          u, v,
                                                          self.x0, self.y0, self.x1, self.y1)
        normal = self.rotations[self.face].xform(normal)
        tangent = LVector3d(-normal[1], normal[0], 0)
        tangent.normalize()
        binormal = normal.cross(tangent)
        binormal.normalize()
        return (tangent, binormal, normal)

class SquaredDistanceSquarePatchLayer(PatchLayer):
    def create_instance(self, patch):
        self.instance = geometry.SquaredDistanceSquarePatch(1.0,
                                                            geometry.TesselationInfo(patch.density, patch.tessellation_outer_level),
                                                            patch.x0, patch.y0, patch.x1, patch.y1,
                                                            has_offset=patch.offset is not None,
                                                            offset=patch.offset,
                                                            use_patch_adaptation=settings.use_patch_adaptation,
                                                            use_patch_skirts=settings.use_patch_skirts)

        self.instance.reparent_to(patch.instance)
        orientation = patch.rotations[patch.face]
        self.instance.set_quat(LQuaternion(*orientation))

    def update_instance(self, patch):
        if self.instance is not None and patch.shown:
                self.remove_instance()
                self.create_instance(patch)


class PatchedShapeBase(Shape):
    patchable = True
    no_bounds = False
    def __init__(self, factory, heightmap=None, lod_control=None):
        Shape.__init__(self)
        self.factory = factory
        #TODO: Should not be done here
        self.factory.set_lod_control(lod_control)
        self.factory.set_heightmap(heightmap)
        self.factory.set_owner(self)
        self.data_store = None
        if settings.patch_data_store:
            self.data_store = PatchDataStoreManager(max_elem=settings.patch_data_store_max_elems)
            if settings.patch_parameters_data_store:
                if heightmap is not None:
                    self.data_store.parameters.add_data_source(heightmap)
        self.root_patches = []
        self.patches = []
        self.linked_objects = []
        self.lod_control = lod_control
        self.max_lod = 0
        self.culling_frustum = None
        self.frustum_node = None
        self.frustum_rel_position = None

    #TODO: Ugly workaround until we get rid of surface in PatchFactory
    def set_owner(self, owner):
        Shape.set_owner(self, owner)
        self.factory.set_surface(self.parent)

    def check_settings(self):
        for patch in self.patches:
            patch.check_settings()
        if self.frustum_node is not None and not settings.debug_lod_frustum:
            self.frustum_node.remove_node()
            self.frustum_node = None

    def get_data_source(self):
        return PatchedShapeDataSource(self)

    def set_heightmap(self, heightmap):
        self.factory.set_heightmap(heightmap)
        if self.data_store is not None and settings.patch_parameters_data_store:
            self.data_store.parameters.add_data_source(heightmap)

    def set_lod_control(self, lod_control):
        self.lod_control = lod_control
        self.factory.set_lod_control(lod_control)

    def add_linked_object(self, linked_object):
        self.linked_objects.append(linked_object)

    def remove_linked_object(self, linked_object):
        self.linked_objects.remove(linked_object)

    def create_patch(self, parent, lod, face, x, y):
        patch = self.factory.create_patch(parent, lod, face, x, y)
        if parent is not None:
            parent.add_child(patch)
        return patch

    def create_root_patches(self):
        pass

    def add_root_patches(self, patch, update):
        pass

    def split_patch(self, patch):
        return []

    def merge_patch(self, patch):
        pass

    def hide_patch(self, patch):
        if patch.instance is not None:
            patch.instance.hide()
            patch.instance.stash()
        patch.shown = False

    def show_patch(self, patch):
        patch.instance.unstash()
        patch.instance.show()
        patch.shown = True

    def create_patch_instance(self, patch):
        patch.visible = True
        if patch.instance is None:
            patch.create_instance()
            patch.instance.reparent_to(self.instance)
            self.patches.append(patch)
            if patch.lod > 0:
                patch.shown = True
                if patch.bounds_shape.instance is not None:
                    patch.bounds_shape.instance.reparent_to(self.instance)
            else:
                patch.shown = False
                patch.instance.stash()
        else:
            self.show_patch(patch)
        patch.set_clickable(self.clickable)

    def remove_patch_instance(self, patch):
        if patch in self.patches:
            self.patches.remove(patch)
        patch.remove_instance()
        patch.shown = False
        if len(patch.children) == 0:
            # Only remove a patch if it has no children, its data might be used by one of the child.
            self.parent.remove_patch(patch)
        if self.data_store is not None:
            self.data_store.remove_patch(patch)

    def update_patch_instances(self, update):
        for patch in update:
            patch.update_instance(self)

    def remove_all_patches_instances(self):
        patch = None
        for patch in self.patches:
            patch.remove_instance()
            patch.shown = False
        self.patches = []

    async def create_instance(self):
        if self.instance is None:
            self.instance = NodePath('root')
            if self.data_store is not None:
                self.data_store.init()
            self.create_root_patches()
            self.apply_owner()
            if self.use_collision_solid:
                self.create_collision_solid()
                if self.no_bounds:
                    self.instance.node().setBounds(OmniBoundingVolume())
                    self.instance.node().setFinal(1)
            tasks = []
            for linked_object in self.linked_objects:
                tasks.append(linked_object.create_instance())
            if len(tasks) > 0:
                gather(*tasks)
        return self.instance

    def remove_instance(self):
        self.remove_all_patches_instances()
        if self.data_store is not None:
            self.data_store.clear()
        Shape.remove_instance(self)

    def patch_done(self, patch):
        for linked_object in self.linked_objects:
            linked_object.patch_done(patch)
        if self.data_store is not None:
            self.data_store.update_patch(patch)

    def place_patches(self, owner):
        if self.frustum_node is not None:
            #Position the frustum relative to the body
            #If lod checking is enabled, the position should be 0, the position of the camera
            #If lod checking is frozen, we use the old relative position
            self.frustum_node.set_pos(*(self.parent.body.scene_position + self.frustum_rel_position * self.owner.scene_scale_factor))
            #TODO: The frustum is not correctly placed when lod is frozen and scale is changing

    def xform_cam_to_model(self, camera_pos):
        pass

    def create_culling_frustum(self, scene_manager, camera):
        pass

    def create_frustum_node(self):
        if self.frustum_node is not None:
            self.frustum_node.remove_node()
        if settings.debug_lod_frustum:
            geom = self.culling_frustum.lens.make_geometry()
            self.frustum_node = render.attach_new_node('frustum')
            node = GeomNode('frustum_node')
            node.add_geom(geom)
            self.frustum_node.attach_new_node(node)
            self.frustum_rel_position = -self.owner.scene_rel_position
            self.frustum_node.set_quat(self.owner.context.observer.get_camera_rot())
            #The frustum position is updated in place_patches()

    @pstat
    def update_lod(self, camera_pos, distance_to_obs, pixel_size, appearance):
        if settings.debug_lod_freeze:
            return
        if self.instance is None:
            return False
        min_radius = self.parent.body.surface.get_min_radius()
        if distance_to_obs < min_radius:
            print("Too low !")
            return False
        (model_camera_pos, model_camera_vector, coord) = self.xform_cam_to_model(camera_pos)
        altitude_to_ground = (self.parent.body.anchor.distance_to_obs - self.parent.body.anchor._height_under) / self.parent.height_scale
        self.create_culling_frustum(self.owner.context.scene_manager, self.owner.context.observer)
        self.create_frustum_node()
        self.to_split = []
        self.to_merge = []
        self.to_show = []
        self.to_remove = []
        process_nb = 0
        self.new_max_lod = 0
        frame = globalClock.getFrameCount()
        if appearance is not None and appearance.texture is not None:
            self.lod_control.set_texture_size(appearance.texture.source.texture_size)
        else:
            self.lod_control.set_texture_size(0)
        lod_result = LodResult()
        for patch in self.root_patches:
            patch.quadtree_node.check_lod(lod_result, self.culling_frustum, LPoint2d(*coord), LPoint3d(model_camera_pos), LVector3d(model_camera_vector), altitude_to_ground, pixel_size, self.lod_control)
        lod_result.sort_by_distance()
        apply_appearance = False
        update = []
        for node in lod_result.to_split:
            patch = node.patch
            process_nb += 1
            if settings.debug_lod_split_merge: print(frame, "Split", patch.str_id())
            self.split_patch(patch)
            patch.split_neighbours(update)
            for linked_object in self.linked_objects:
                linked_object.split_patch(patch)
                linked_object.remove_patch_instance(patch)
            for child in patch.children:
                child.quadtree_node.check_visibility(self.culling_frustum, coord, model_camera_pos, model_camera_vector, altitude_to_ground, pixel_size)
                #print(child.str_id(), child.visible)
                if self.lod_control.should_instanciate(child.quadtree_node, 0, 0):
                    self.create_patch_instance(child)
                    if settings.debug_lod_split_merge: print(frame, "Show child", child.str_id(), child.instance_ready)
                    for linked_object in self.linked_objects:
                        linked_object.create_patch_instance(child)
            self.remove_patch_instance(patch)
            apply_appearance = True
            patch.last_split = frame
            if process_nb > 2:
                break
        for node in lod_result.to_show:
            patch = node.patch
            if settings.debug_lod_split_merge: print(frame, "Show", patch.str_id(), patch.quadtree_node.patch_in_view, patch.instance_ready)
            if patch.lod == 0:
                self.add_root_patches(patch, update)
            self.create_patch_instance(patch)
            apply_appearance = True
            for linked_object in self.linked_objects:
                linked_object.create_patch_instance(patch)
        for node in lod_result.to_remove:
            patch = node.patch
            if settings.debug_lod_split_merge: print(frame, "Remove", patch.str_id(), patch.quadtree_node.patch_in_view)
            for linked_object in self.linked_objects:
                linked_object.remove_patch_instance(patch)
            self.remove_patch_instance(patch)
        for node in lod_result.to_merge:
            patch = node.patch
            #Dampen high frequency split-merge anomaly
            if frame - patch.last_split < 5: continue
            if settings.debug_lod_split_merge: print(frame, "Merge", patch.str_id(), patch.quadtree_node.visible)
            self.merge_patch(patch)
            patch.merge_neighbours(update)
            if patch.quadtree_node.visible:
                self.create_patch_instance(patch)
                apply_appearance = True
            for linked_object in self.linked_objects:
                linked_object.merge_patch(patch)
            for child in patch.children:
                for linked_object in self.linked_objects:
                    linked_object.remove_patch_instance(child)
                self.remove_patch_instance(child)
            patch.remove_children()
        self.max_lod = self.new_max_lod
        self.update_patch_instances(update)
        #Return True when new instances have been created
        return apply_appearance or len(update) > 0

    def _find_patch_at(self, patch, x, y):
        if x >= patch.x0 and x <= patch.x1 and y >= patch.y0 and y <= patch.y1:
            #print("In", patch, patch.x0, patch.x1, patch.y0, patch.y1)
            if len(patch.children) == 0:
                return patch
            for child in patch.children:
                result = self._find_patch_at(child, x, y)
                if result is not None: return result
            return patch
        return None

    def find_patch_at(self, coord):
        return None

    def get_normals_at(self, coord):
        patch = self.find_patch_at(coord)
        if patch is not None:
            return patch.get_normals_at(coord)
        else:
            print("Patch not found", coord)
            return (LVector3d.up(), LVector3d.forward(), LVector3d.left())

    def get_lonlatvert_at(self, coord):
        patch = self.find_patch_at(coord)
        if patch is not None:
            return patch.get_lonlatvert_at(coord)
        else:
            print("Patch not found", coord)
            return (LVector3d.right(), LVector3d.forward(), LVector3d.up())

    def dump_patch(self, patch, padding=True):
        if padding:
            pad = ' ' * (patch.lod * 4)
        else:
            pad = ''
        print(pad, patch.str_id(), hex(id(patch)))
        print(pad, '  Visible' if patch.visible else '  Not visible', patch.patch_in_view)
        if patch.shown: print(pad, '  Shown')
        if not patch.instance_ready: print(pad, '  Instance not ready')
        if patch.task is not None: print(pad, '  Task running')
        #print(pad, '  Distance', patch.distance)
        print(pad, "  Tessellation", '-'.join(map(str, patch.tessellation_outer_level)))
        for i in range(4):
            print(pad, "  Neighbours", list(map(lambda x: hex(id(x)) + ' ' + x.str_id(), patch.neighbours.neighbours[i])))

    def _dump_tree(self, patch):
        self.dump_patch(patch)
        for child in patch.children:
            self._dump_tree(child)

    def dump_tree(self):
        for patch in self.root_patches:
            self._dump_tree(patch)

    def dump_patches(self):
        for patch in self.patches:
            self.dump_patch(patch, padding=False)

    def _dump_stats(self, stats_array, patch):
        stats_array[0] += patch.visible
        stats_array[1] += patch.shown
        stats_array[7] += (patch.visible and not patch.instance_ready)
        if patch.task is not None: stats_array[8] += 1
        stats_array[9] += 1
        for child in patch.children:
            self._dump_stats(stats_array, child)

    def dump_stats(self):
        stats_array = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for patch in self.root_patches:
            self._dump_stats(stats_array, patch)
        print("Nb patches:          ", stats_array[9])
        print("Max lod:             ", self.max_lod)
        print("Visible:             ", stats_array[0])
        print("Shown:               ", stats_array[1])
        print("Instance not ready:  ", stats_array[7])
        print("Tasks running:       ", stats_array[8])

class EllipsoidPatchedShape(PatchedShapeBase):
    offset = True
    no_bounds = True

    def create_culling_frustum(self, scene_manager, camera):
        min_radius = self.parent.body.surface.get_min_radius() / self.parent.height_scale
        altitude_to_min_radius = (self.parent.body.anchor.distance_to_obs - self.parent.height_scale) / self.parent.height_scale
        cam_transform_mat = camera.cam.getNetTransform().getMat()
        if False:
            upper = LMatrix3()
            scale = self.parent.body.surface.get_scale() * self.parent.body.scene_scale_factor
            inv_scale = LVector3d(1.0 / scale[0], 1.0 / scale[1], 1.0 / scale[2])
            upper.set_scale_mat(inv_scale)
            rot_mat = LMatrix3()
            self.parent.body.anchor._orientation.conjugate().extract_to_matrix(rot_mat)
            upper *= rot_mat
            transform_mat = LMatrix4(upper, upper.xform(-self.parent.body.scene_position))
        else:
            transform_mat = LMatrix4()
            transform_mat.invert_from(self.instance.getNetTransform().getMat())
        transform_mat = cam_transform_mat * transform_mat
        if self.parent.body.support_offset_body_center and settings.offset_body_center:
            self.model_body_center_offset = self.parent.body.anchor._orientation.conjugate().xform(-self.parent.body.anchor.vector_to_obs) * self.parent.body.anchor._height_under
            scale = self.parent.body.surface.get_scale()
            self.model_body_center_offset[0] /= scale[0]
            self.model_body_center_offset[1] /= scale[1]
            self.model_body_center_offset[2] /= scale[2]
        else:
            self.model_body_center_offset = LVector3d()
        self.culling_frustum = HorizonCullingFrustum(camera.realCamLens, self.parent.height_scale / scene_manager.scale, transform_mat, min_radius, altitude_to_min_radius,
                                                     self.max_lod, settings.offset_body_center, self.model_body_center_offset, settings.shift_patch_origin,
                                                     settings.cull_far_patches, settings.cull_far_patches_threshold)

    def place_patches(self, owner):
        PatchedShapeBase.place_patches(self, owner)
        if settings.offset_body_center or settings.shift_patch_origin:
            body_offset = self.model_body_center_offset
            for patch in self.patches:
                if settings.shift_patch_origin:
                    patch_offset = body_offset + patch.quadtree_node.normal * patch.offset
                else:
                    patch_offset = body_offset
                patch.instance.setPos(*patch_offset)
                if patch.bounds_shape.instance is not None:
                    patch.bounds_shape.instance.setPos(*patch_offset)

    def xform_cam_to_model(self, camera_pos):
        position = self.parent.body.get_local_position()
        orientation = self.parent.body.get_abs_rotation()
        #TODO: Should receive as parameter !
        camera_vector = self.owner.context.observer.get_camera_vector()
        model_camera_vector = orientation.conjugate().xform(camera_vector)
        model_camera_pos = self.local_to_model(camera_pos, position, orientation, self.parent.height_scale)
        (x, y, distance) = self.parent.body.spherical_to_xy(self.parent.body.cartesian_to_spherical(camera_pos))
        return (model_camera_pos, model_camera_vector, (x, y))

    def local_to_model(self, point, position, orientation, scale):
        model_point = orientation.conjugate().xform(point - position) / scale
        return model_point

class PatchedSpherePatchFactory(PatchFactory):
    def create_patch(self, parent, lod, face, x, y):
        density = self.lod_control.get_density_for(lod)
        (min_radius, max_radius, mean_radius) = self.get_patch_limits(parent)
        patch = SpherePatch(parent, lod, density, x, y, self.surface.height_scale, min_radius, max_radius, mean_radius)
        patch.add_layer(SpherePatchLayer())
        #TODO: Temporary or make right
        patch.owner = self.owner
        return patch

class PatchedSphereShape(EllipsoidPatchedShape):
    def create_root_patches(self):
        self.root_patches = [self.create_patch(None, 0, -1, 0, 0),
                             self.create_patch(None, 0, -1, 1, 0)
                            ]
        for patch in self.root_patches:
            for linked_object in self.linked_objects:
                linked_object.create_root_patch(patch)

    def create_child_patch(self, patch, i, j):
        child = self.create_patch(patch, patch.lod + 1, -1, patch.x * 2 + i, patch.y * 2 + j)
        return child

    def split_patch(self, patch):
        #bl, br, tr, tl
        self.create_child_patch(patch, 0, 0)
        self.create_child_patch(patch, 1, 0)
        self.create_child_patch(patch, 1, 1)
        self.create_child_patch(patch, 0, 1)

    def global_to_shape_coord(self, x, y):
        return (x, y)

    def find_patch_at(self, coord):
        (x, y) = coord
        for patch in self.root_patches:
            result = self._find_patch_at(patch, x, y)
            if result is not None:
                return result
        return None

class PatchedSquareShapeBase(EllipsoidPatchedShape):
    def __init__(self, factory, heightmap=None, lod_control=None):
        EllipsoidPatchedShape.__init__(self, factory, heightmap, lod_control)
        self.face_unique = False

    def create_root_patches(self):
        right = self.create_patch(None, 0, SquarePatchBase.RIGHT, 0, 0)
        left = self.create_patch(None, 0, SquarePatchBase.LEFT, 0, 0)
        back = self.create_patch(None, 0, SquarePatchBase.BACK, 0, 0)
        front = self.create_patch(None, 0, SquarePatchBase.FRONT, 0, 0)
        top = self.create_patch(None, 0, SquarePatchBase.TOP, 0, 0)
        bottom = self.create_patch(None, 0, SquarePatchBase.BOTTOM, 0, 0)
        self.root_patches = [ right, left, back, front, top, bottom ]
        #north, east, south, west
#         right.set_all_neighbours([front], [bottom], [back], [top])
#         left.set_all_neighbours([], [], [], [])
#         back.set_all_neighbours([], [], [top], [])
#         front.set_all_neighbours([bottom], [right], [top], [left])
#         top.set_all_neighbours([back], [left], [front], [right])
#         bottom.set_all_neighbours([front], [right], [back], [left])
        for patch in self.root_patches:
            for linked_object in self.linked_objects:
                linked_object.create_root_patch(patch)

    def create_child_patch(self, patch, i, j):
        child = self.create_patch(patch, patch.lod + 1, patch.face, patch.x * 2 + i, patch.y * 2 + j)
        return child

    def split_patch(self, patch):
        #bl, br, tr, tl
        self.create_child_patch(patch, 0, 0)
        self.create_child_patch(patch, 1, 0)
        self.create_child_patch(patch, 1, 1)
        self.create_child_patch(patch, 0, 1)

    def xyz_to_xy(self, x, y, z):
        return None

    def xyz_to_uv(self, x, y, z):
        (u, v) = self.xyz_to_xy(x, y, z)
        u = u * 0.5 + 0.5
        v = v * 0.5 + 0.5
        return (u, v)

    def xyz_to_face_xy(self, x, y, z):
        ax = abs(x)
        ay = abs(y)
        az = abs(z)
        if ax >= ay and ax >= az:
            if x >= 0.0:
                face = SquarePatchBase.RIGHT
                (u, v) = self.xyz_to_uv(-z, y, x)
                (u, v) = (u, v)
            else:
                face = SquarePatchBase.LEFT
                (u, v) = self.xyz_to_uv(z, y, -x)
                (u, v) = (u, v)
        elif ay >= x and ay >= az:
            if y >= 0.0:
                face = SquarePatchBase.FRONT
                (u, v) = self.xyz_to_uv(x, z, -y)
                (u, v) = (u, 1.0 - v)
            else:
                face = SquarePatchBase.BACK
                (u, v) = self.xyz_to_uv(x, -z, y)
                (u, v) = (u, 1.0 - v)
        elif az >= ax and az >= ay:
            if z >= 0.0:
                face = SquarePatchBase.TOP
                (u, v) = self.xyz_to_uv(x, y, z)
                (u, v) = (1.0 - u, 1.0 - v)
            else:
                face = SquarePatchBase.BOTTOM
                (u, v) = self.xyz_to_uv(x, -y, -z)
                (u, v) = (1.0 - u, 1.0 - v)
        return (face, u, v)

    def global_to_shape_coord(self, x, y):
        theta = (y - 0.5) * pi
        phi = (x - 0.5) * 2 * pi
        xp = cos(theta) * cos(phi)
        yp = cos(theta) * sin(phi)
        zp = sin(theta)
        (face, x, y) = self.xyz_to_face_xy(xp, yp, zp)
        #print(face, x, y)
        return (face, x, y)

    def find_patch_at(self, coord):
        if self.instance is None:
            return None
        (face, x, y) = coord
        if face < len(self.root_patches):
            return self._find_patch_at(self.root_patches[face], x, y)
        else:
            print("Unknown face", face)
            return None

class NormalizedSquarePatchFactory(PatchFactory):
    def __init__(self):
        PatchFactory.__init__(self)
        self.use_shader = False
        self.use_tessellation = False

    def create_patch(self, parent, lod, face, x, y):
        density = self.lod_control.get_density_for(lod)
        (min_radius, max_radius, mean_radius) = self.get_patch_limits(parent)
        patch = NormalizedSquarePatch(face, x, y, parent, lod, density, self.surface.height_scale, min_radius, max_radius, mean_radius)
        patch.add_layer(NormalizedSquarePatchLayer())
        #TODO: Temporary or make right
        patch.owner = self.owner
        return patch

class NormalizedSquareShape(PatchedSquareShapeBase):
    def xyz_to_xy(self, x, y, z):
        vx = x / z
        vy = y / z

        return (copysign(vx, x), copysign(vy, y))

class SquaredDistanceSquarePatchFactory(PatchFactory):
    def __init__(self):
        PatchFactory.__init__(self)
        self.use_shader = False
        self.use_tessellation = False

    def create_patch(self, parent, lod, face, x, y):
        density = self.lod_control.get_density_for(lod)
        (min_radius, max_radius, mean_radius) = self.get_patch_limits(parent)
        patch = SquaredDistanceSquarePatch(face, x, y, parent, lod, density, self.surface.height_scale, min_radius, max_radius, mean_radius)
        patch.add_layer(SquaredDistanceSquarePatchLayer())
        #TODO: Temporary or make right
        patch.owner = self.owner
        return patch

class SquaredDistanceSquareShape(PatchedSquareShapeBase):
    def xyz_to_xy(self, x, y, z):
        x2 = x * x * 2.0
        y2 = y * y * 2.0
        vx = x2 - y2
        vy = y2 - x2

        ii = vy - 3.0
        ii *= ii

        isqrt = -sqrt(ii - 12.0 * x2) + 3.0

        vx = sqrt(abs(0.5 * (vx + isqrt)))
        vy = sqrt(abs(0.5 * (vy + isqrt)))

        return (copysign(vx, x), copysign(vy, y))

class PatchedShapeDataSource(DataSource):
    def __init__(self, shape):
        DataSource.__init__(self, 'shape')
        self.shape = shape

    def apply_patch_data(self, patch, instance):
        if self.shape.data_store is not None:
            self.shape.data_store.apply_patch_data(patch, instance)
        instance.set_shader_input("flat_coord", patch.flat_coord)
        instance.set_shader_input('TessLevelInner', patch.tessellation_inner_level)
        instance.set_shader_input('TessLevelOuter', *patch.tessellation_outer_level)

    def apply(self, shape, instance):
        if self.shape.data_store is not None:
            self.shape.data_store.apply(instance)
