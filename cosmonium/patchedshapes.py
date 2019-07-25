from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import BoundingSphere, OmniBoundingVolume, GeomNode
from panda3d.core import LVector3d, LVector4, LPoint3, LPoint3d, LQuaterniond, LQuaternion, LMatrix4
from panda3d.core import NodePath, BoundingBox

from .shapes import Shape
from .textures import TexCoord
from . import geometry
from . import settings

from math import cos, sin, pi, sqrt, copysign, acos, asin

class PatchBase(Shape):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    opposite_face = [SOUTH, WEST, NORTH, EAST]
    text = ['North', 'East', 'South', 'West']
    conv = [WEST, SOUTH, EAST, NORTH]

    coord = None

    def __init__(self, parent, lod, density):
        Shape.__init__(self)
        self.parent = parent
        self.lod = lod
        self.density = density
        self.flat_coord = None
        self.bounds = None
        self.tesselation_inner_level = density
        self.tesselation_outer_level = [density, density, density, density]
        self.neighbours = [[], [], [], []]
        self.children = []
        self.children_bb = []
        self.children_normal = []
        self.children_offset = []
        self.need_split = False
        self.need_merge = False
        self.split_pending = False
        self.merge_pending = False
        self.parent_split_pending = False
        self.instanciate_pending = False
        self.shown = False
        self.apparent_size = None
        self.patch_in_view = False
        self.in_cone = False
        self.last_split = 0
        if self.parent is not None:
            self.parent.add_child(self)
        #TODO: Remove and use enum
        self.cylindrical_map = False
        self.cube_map = False

    def check_settings(self):
        Shape.check_settings(self)
        if self.instance is not None:
            if settings.debug_lod_show_bb:
                self.instance.show_bounds()
            else:
                self.instance.hide_bounds()

    def update_instance(self):
        pass

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def remove_children(self):
        for child in self.children:
            child.parent = None
            child.remove_instance()
            child.shown = False
        self.children = []

    def can_show_children(self):
        for child in self.children:
            if child.visible and not child.instance_ready:
                return False
        return True

    def can_merge_children(self):
        if len(self.children) == 0:
            return False
        for child in self.children:
            if len(child.children) != 0:
                return False
            if not child.need_merge:
                return False
        return True

    def set_neighbours(self, face, neighbours):
        self.neighbours[face] = neighbours

    def get_neighbours(self, face):
        return [] + self.neighbours[face]

    def set_all_neighbours(self, north, east, south, west):
        self.neighbours[PatchBase.NORTH] = north
        self.neighbours[PatchBase.EAST] = east
        self.neighbours[PatchBase.SOUTH] = south
        self.neighbours[PatchBase.WEST] = west

    def get_all_neighbours(self):
        neighbours = []
        for i in range(4):
            neighbours += self.neighbours[i]
        return neighbours

    def get_neighbour_lower_lod(self, face):
        lower_lod = self.lod
        for neighbour in self.neighbours[face]:
            #print(neighbour.lod)
            lower_lod = min(lower_lod, neighbour.lod)
        return lower_lod

    def remove_detached_neighbours(self):
        valid = []
        for neighbour in self.neighbours[PatchBase.NORTH]:
            if neighbour.x1 > self.x0 and neighbour.x0 < self.x1:
                valid.append(neighbour)
        self.neighbours[PatchBase.NORTH] = valid
        valid = []
        for neighbour in self.neighbours[PatchBase.SOUTH]:
            if neighbour.x1 > self.x0 and neighbour.x0 < self.x1:
                valid.append(neighbour)
        self.neighbours[PatchBase.SOUTH] = valid
        valid = []
        for neighbour in self.neighbours[PatchBase.EAST]:
            if neighbour.y1 > self.y0 and neighbour.y0 < self.y1:
                valid.append(neighbour)
        self.neighbours[PatchBase.EAST] = valid
        valid = []
        for neighbour in self.neighbours[PatchBase.WEST]:
            if neighbour.y1 > self.y0 and neighbour.y0 < self.y1:
                valid.append(neighbour)
        self.neighbours[PatchBase.WEST] = valid

    def replace_neighbours(self, face, olds, news):
        opposite = PatchBase.opposite_face[face]
        for neighbour in self.neighbours[face]:
            for old in olds:
                try:
                    neighbour.neighbours[opposite].remove(old)
                except ValueError:
                    pass
            for new in news:
                neighbour.neighbours[opposite].append(new)

    def calc_outer_tesselation_level(self, update):
        for face in range(4):
            #print("Check face", PatchBase.text[face])
            lod = self.get_neighbour_lower_lod(face)
            delta = self.lod - lod
            outer_level = 6 - delta
            new_level = 1 << outer_level
            dest = PatchBase.conv[face]
            if self.tesselation_outer_level[dest] != new_level:
                #print("Change from", self.tesselation_outer_level[dest], "to", new_level)
                if not self in update:
                    update.append(self)
            self.tesselation_outer_level[dest] = new_level
            #print("Level", PatchBase.text[face], ":", delta, 1 << outer_level)

    def in_patch(self, x, y):
        return x >= self.x0 and x <= self.x1 and y >= self.y0 and y <= self.y1

class Patch(PatchBase):
    patch_cache = {}
    def __init__(self, parent, lod, density, radius):
        PatchBase.__init__(self, parent, lod, density)
        self.visible = False
        self.radius = radius
        self.geom_scale = 1.0
        self.offset = 0.0
        self.orientation = LQuaterniond()
        self.distance_to_obs = None
        self.sin_max_angle = None
        self.cos_angle = None

    def check_visibility(self, worker, local, model_camera_pos, model_camera_vector, altitude, pixel_size):
        #Testing if we are inside the patch create visual artifacts
        #The change of lod between patches is too noticeable
        if False and self.in_patch(*local):
            within_patch = True
            self.distance = altitude
        else:
            within_patch = False
            self.distance = (self.centre - model_camera_pos).length()
        self.cos_angle = self.normal.dot(model_camera_vector)
        self.patch_in_view = worker.is_patch_in_view(self)
        self.in_cone = True#self.cos_angle < self.sin_max_angle
        self.visible = within_patch or (self.patch_in_view and self.in_cone)
        self.apparent_size = self.get_patch_length() / (self.distance * pixel_size)

    def get_patch_length(self):
        return None

    def get_height_uv(self, u, v):
        return self.radius

class SpherePatch(Patch):
    patch_cache = {}
    coord = TexCoord.Cylindrical

    def __init__(self, parent, lod, density, sector, ring, radius, average_height):
        Patch.__init__(self, parent, lod, density, radius)
        self.face = -1
        self.sector = sector
        self.ring = ring
        self.r_div = 1 << self.lod
        self.s_div = 2 << self.lod
        self.cylindrical_map = True
        if settings.patch_scaling:
            self.geom_scale = float(1 << self.lod)
        self.average_height = average_height
        if settings.shift_patch_origin:
            self.offset = self.average_height
        if self.lod == 0:
            self.sin_max_angle = 1.0
        else:
            self.sin_max_angle = sin(pi/2 / self.s_div + self.parent.owner.owner.context.observer.dfov / 2)
        self.x0 = float(self.sector) / self.s_div
        self.y0 = float(self.ring) / self.r_div
        self.x1 = float(self.sector + 1) / self.s_div
        self.y1 = float(self.ring + 1) / self.r_div
        self.lod_scale_x = 1.0 / self.s_div
        self.lod_scale_y = 1.0 / self.r_div
        self.normal = geometry.UVPatchNormal(self.x0, self.y0, self.x1, self.y1)
        long_scale = 2 * pi * radius * 1000.0
        lat_scale = pi * radius * 1000.0
        long0 = self.x0 * long_scale
        long1 = self.x1 * long_scale
        lat0 = self.y0 * lat_scale
        lat1 = self.y1 * lat_scale
        self.flat_coord = LVector4((long0 % 1000.0),
                                    (lat0 % 1000.0),
                                    (long1 - long0),
                                    (lat1 - lat0))
        offset = self.offset - (self.average_height - 1)
        if self.lod > 0:
            self.bounds = geometry.UVPatchAABB(self.geom_scale,
                                               self.x0, self.y0, self.x1, self.y1,
                                               offset=offset)
        else:
            self.bounds = geometry.halfSphereAABB(self.geom_scale, self.sector == 1, offset)
        self.centre =  geometry.UVPatchPoint(self.geom_scale,
                                             0.5, 0.5,
                                             self.x0, self.y0,
                                             self.x1, self.y1,
                                             offset=-(self.average_height - 1)) * self.radius

    def get_patch_length(self):
        nb_sectors = 2 << self.lod
        return self.radius * self.average_height * 2 * pi / nb_sectors

    def str_id(self):
        return "%d - %d %d" % (self.lod, self.ring, self.sector)

    def create_instance(self):
        if not self.owner in self.patch_cache:
            self.patch_cache[self.owner] = {}
        cache = self.patch_cache[self.owner]
        if settings.software_instancing:
            patch_id = "%d-%d" % (self.lod, self.ring)
            if not patch_id in cache:
                cache[patch_id] = geometry.UVPatch(self.geom_scale,
                                                   self.density, self.density,
                                                   0.0, self.y0,
                                                   1.0 / self.s_div,self.y1,
                                                   offset=self.offset)
            self.instance = NodePath('patch')
            child = self.instance.attach_new_node('instance')
            template = cache[patch_id]
            template.instanceTo(child)
            self.instance.setH(360.0 * self.x0)
        else:
            patch_id = "%d-%d %d" % (self.lod, self.ring, self.sector)
            if not patch_id in cache:
                cache[patch_id] = geometry.UVPatch(self.geom_scale,
                                                   self.density, self.density,
                                                   self.x0, self.y0,
                                                   self.x1, self.y1,
                                                   offset=self.offset)
            self.instance = cache[patch_id]
        self.instance.setPythonTag('patch', self)
        if settings.debug_lod_bb:
            self.instance.node().setBounds(self.bounds)
        else:
            self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(1)

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
        x_tex = (self.sector // x_scale) * x_scale
        y_tex = (self.ring // y_scale) * y_scale
        x_delta = float(self.sector - x_tex) / x_scale
        y_delta = float(self.ring - y_tex) / y_scale
        #Y orientation is the opposite of the texture v axis
        y_delta = 1.0 - y_delta - 1.0 / y_scale
        if y_delta == 1.0: y_delta = 0.0
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
                                       self.x0, self.y0,
                                       self.x1, self.y1)
        tangent = LVector3d(-normal[1], normal[0], 0)
        tangent.normalize()
        binormal = normal.cross(tangent)
        binormal.normalize()
        return (normal, tangent, binormal)

class SquarePatchBase(Patch):
    patch_cache = {}

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

    def __init__(self, face, x, y, parent, lod, density, radius, average_height, user_shader, use_tesselation):
        Patch.__init__(self, parent, lod, density, radius)
        self.face = face
        self.x = x
        self.y = y
        self.cube_map = True
        self.use_shader = user_shader
        self.use_tesselation = use_tesselation
        self.div = 1 << self.lod
        self.x0 = float(self.x) / self.div
        self.y0 = float(self.y) / self.div
        self.x1 = float(self.x + 1) / self.div
        self.y1 = float(self.y + 1) / self.div
        self.lod_scale_x = 1.0 / self.div
        self.lod_scale_y = 1.0 / self.div
        self.sin_max_angle = sin(pi/2/self.div)
        self.source_normal = self.face_normal(x, y)
        self.normal = self.rotations[self.face].xform(self.source_normal)
        if settings.patch_scaling:
            self.geom_scale = float(1 << self.lod)
        else:
            self.geom_scale = 1.0
        self.average_height = average_height
        if settings.shift_patch_origin:
            self.offset = self.average_height
        long_scale = 2 * pi * radius * 1000.0
        lat_scale = pi * radius * 1000.0
        long0 = self.x0 * long_scale / 4
        long1 = self.x1 * long_scale / 4
        lat0 = self.y0 * lat_scale / 4
        lat1 = self.y1 * lat_scale / 4
        self.flat_coord = LVector4((long0 % 1000.0),
                                    (lat0 % 1000.0),
                                    (long1 - long0),
                                    (lat1 - lat0))
        offset = self.offset - (self.average_height - 1)
        self.bounds = self.create_bounding_volume(x, y, offset)
        self.bounds.xform(self.rotations_mat[self.face])
        centre = self.create_centre(x, y, -(self.average_height - 1))
        self.centre = self.rotations[self.face].xform(centre) * self.radius

    def face_normal(self, x, y):
        return None

    def create_bounding_volume(self, x, y, offset):
        return None

    def create_centre(self, x, y, offset):
        return None

    def create_patch_instance(self, x, y):
        return None

    def get_patch_length(self):
        nb_sectors = 4 << self.lod
        return self.radius * 2 * pi / nb_sectors

    def str_id(self):
        return "%d - %d %d %d" % (self.lod, self.face, self.x, self.y)

    def create_instance(self):
        if self.owner.face_unique:
            patch_id = "%d : %d - %d %d" % (self.lod, self.face, self.x, self.y)
        else:
            patch_id = "%d : %d %d" % (self.lod, self.x, self.y)
        if not self.owner in self.patch_cache:
            self.patch_cache[self.owner] = {}
        cache = self.patch_cache[self.owner]
        if not patch_id in cache:
            if self.use_shader:
                if self.use_tesselation:
                    template = geometry.QuadPatch(float(self.x) / self.div,
                                                  float(self.y) / self.div,
                                                  float(self.x + 1) / self.div,
                                                  float(self.y + 1) / self.div)
                else:
                    template = geometry.SquarePatch(self.geom_scale,
                                                  self.density,
                                                  float(self.x) / self.div,
                                                  float(self.y) / self.div,
                                                  float(self.x + 1) / self.div,
                                                  float(self.y + 1) / self.div)
            else:
                template = self.create_patch_instance(self.x, self.y)
            cache[patch_id] = template
        self.instance = NodePath('face')
        cache[patch_id].instanceTo(self.instance)
        self.orientation = self.rotations[self.face]
        self.instance.setQuat(LQuaternion(*self.orientation))
        if settings.debug_lod_bb:
            self.instance.node().setBounds(self.bounds)
        else:
            self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(1)

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
        x_tex = (self.x / x_scale) * x_scale
        y_tex = (self.y / y_scale) * y_scale
        x_delta = float(self.x - x_tex) / x_scale
        y_delta = float(self.y - y_tex) / y_scale
        #Y orientation is the opposite of the texture v axis
        y_delta = 1.0 - y_delta - 1.0 / y_scale
        if y_delta == 1.0: y_delta = 0.0
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

    def face_normal(self, x, y):
        return geometry.NormalizedSquarePatchNormal(float(x) / self.div,
                                                    float(y) / self.div,
                                                    float(x + 1) / self.div,
                                                    float(y + 1) / self.div)

    def create_bounding_volume(self, x, y, offset):
        return geometry.NormalizedSquarePatchAABB(self.geom_scale,
                                                  float(x) / self.div,
                                                  float(y) / self.div,
                                                  float(x + 1) / self.div,
                                                  float(y + 1) / self.div,
                                                  offset)

    def create_centre(self, x, y, offset):
        return geometry.NormalizedSquarePatchPoint(self.geom_scale,
                                                  0.5, 0.5,
                                                  float(x) / self.div,
                                                  float(y) / self.div,
                                                  float(x + 1) / self.div,
                                                  float(y + 1) / self.div,
                                                  offset)
    def create_patch_instance(self, x, y):
        return geometry.NormalizedSquarePatch(self.geom_scale,
                                              self.density,
                                              float(x) / self.div,
                                              float(y) / self.div,
                                              float(x + 1) / self.div,
                                              float(y + 1) / self.div,
                                              offset=self.offset)

    def get_normals_at(self, coord):
        (u, v) = self.coord_to_uv(coord)
        normal = geometry.NormalizedSquarePatchPoint(u, v,
                                                     self.x0, self.y0,
                                                     self.x1, self.y1)
        normal = self.rotations[self.face].xform(normal)
        tangent = LVector3d(-normal[1], normal[0], normal[2])
        tangent.normalize()
        binormal = normal.cross(tangent)
        binormal.normalize()
        return (normal, tangent, binormal)

class SquaredDistanceSquarePatch(SquarePatchBase):
    coord = TexCoord.SqrtCube

    def face_normal(self, x, y):
        return geometry.SquaredDistanceSquarePatchNormal(self.x0, self.y0,
                                                         self.x1, self.y1)

    def create_bounding_volume(self, x, y, offset):
        return geometry.SquaredDistanceSquarePatchAABB(self.geom_scale,
                                                       float(x) / self.div,
                                                       float(y) / self.div,
                                                       float(x + 1) / self.div,
                                                       float(y + 1) / self.div,
                                                       offset=offset)

    def create_centre(self, x, y, offset):
        return geometry.SquaredDistanceSquarePatchPoint(self.geom_scale,
                                                       0.5, 0.5,
                                                       float(x) / self.div,
                                                       float(y) / self.div,
                                                       float(x + 1) / self.div,
                                                       float(y + 1) / self.div,
                                                       offset=offset)

    def create_patch_instance(self, x, y):
        return geometry.SquaredDistanceSquarePatch(self.geom_scale,
                                                   self.density,
                                                   float(x) / self.div,
                                                   float(y) / self.div,
                                                   float(x + 1) / self.div,
                                                   float(y + 1) / self.div,
                                                   offset=self.offset)

    def get_normals_at(self, coord):
        (u, v) = self.coord_to_uv(coord)
        normal = geometry.SquaredDistanceSquarePatchPoint(1.0,
                                                          u, v,
                                                          self.x0, self.y0,
                                                          self.x1, self.y1)
        normal = self.rotations[self.face].xform(normal)
        tangent = LVector3d(-normal[1], normal[0], normal[2])
        tangent.normalize()
        binormal = normal.cross(tangent)
        binormal.normalize()
        return (normal, tangent, binormal)

class PatchedShapeBase(Shape):
    patchable = True
    no_bounds = False
    limit_far = False
    def __init__(self, lod_control=None):
        Shape.__init__(self)
        self.root_patches = []
        self.patches = []
        if lod_control is None:
            lod_control = TexturePatchLodControl()
        self.lod_control = lod_control
        self.max_lod = 0
        self.new_max_lod = 0
        self.frustum = None
        self.lens_bounds = None
        self.to_split = []
        self.to_merge = []
        self.to_show_children = []
        self.to_instanciate = []
        self.to_show = []
        self.to_remove = []

    def check_settings(self):
        for patch in self.patches:
            patch.check_settings()

    def set_lod_control(self, lod_control):
        self.lod_control = lod_control

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

    def remove_patch_instance(self, patch, split=False):
        if patch in self.patches:
            self.patches.remove(patch)
        patch.remove_instance()
        patch.shown = False

    def remove_all_patches_instances(self):
        for patch in self.patches:
            patch.remove_instance()
            patch.shown = False
        self.patches = []

    def create_instance(self):
        if self.instance is None:
            self.instance = NodePath('root')
            self.create_root_patches()
            self.apply_owner()
            if self.use_collision_solid:
                self.create_collision_solid()
                if self.no_bounds:
                    self.instance.node().setBounds(OmniBoundingVolume())
                    self.instance.node().setFinal(1)
        return self.instance

    def remove_instance(self):
        Shape.remove_instance(self)
        if settings.standalone_patches:
            self.remove_all_patches_instances()

    def create_patch_instance(self, patch, hide=False):
        if patch.instance is None:
            patch.create_instance()
            if settings.standalone_patches:
                patch.instance.reparentTo(self.owner.context.world)
            else:
                patch.instance.reparentTo(self.instance)
            if hide:
                patch.instance.hide()
                patch.instance.stash()
            self.patches.append(patch)
            patch.shown = not hide
            if settings.standalone_patches:
                patch.instance.reparentTo(self.owner.context.world)
            else:
                patch.instance.reparentTo(self.instance)
            if settings.debug_lod_show_tb: patch.instance.showTightBounds()
            if settings.debug_lod_show_bb: patch.instance.showBounds()
        else:
            if not hide:
                self.show_patch(patch)
        patch.set_clickable(self.clickable)

    def place_patches(self, owner):
        if self.frustum is not None:
            #Position the frustum relative to the body
            #If lod checking is enabled, the position should be 0, the position of the camera
            #If lod checking is frozen, we use the old relative position
            self.frustum.setPos(*(self.owner.scene_position - self.scene_rel_position * self.owner.scene_scale_factor))

    def split_neighbours(self, patch, update):
        (bl, br, tr, tl) = patch.children
        tl.set_all_neighbours(patch.get_neighbours(PatchBase.NORTH), [tr], [bl], patch.get_neighbours(PatchBase.WEST))
        tr.set_all_neighbours(patch.get_neighbours(PatchBase.NORTH), patch.get_neighbours(PatchBase.EAST), [br], [tl])
        br.set_all_neighbours([tr], patch.get_neighbours(PatchBase.EAST), patch.get_neighbours(PatchBase.SOUTH), [bl])
        bl.set_all_neighbours([tl], [br], patch.get_neighbours(PatchBase.SOUTH), patch.get_neighbours(PatchBase.WEST))
        neighbours = patch.get_all_neighbours()
        patch.replace_neighbours(PatchBase.NORTH, [patch], [tl, tr])
        patch.replace_neighbours(PatchBase.EAST, [patch], [tr, br])
        patch.replace_neighbours(PatchBase.SOUTH, [patch], [bl, br])
        patch.replace_neighbours(PatchBase.WEST,  [patch], [tl, bl])
        for (i, new) in enumerate((tl, tr, br, bl)):
            #text = ['tl', 'tr', 'br', 'bl']
            #print("*** Child", text[i], '***')
            new.remove_detached_neighbours()
            new.calc_outer_tesselation_level(update)
        #print("Neighbours")
        for neighbour in neighbours:
            neighbour.remove_detached_neighbours()
            neighbour.calc_outer_tesselation_level(update)

    def merge_neighbours(self, patch, update):
        (bl, br, tr, tl) = patch.children
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
        patch.set_all_neighbours(north, east, south, west)
        patch.replace_neighbours(PatchBase.NORTH, [patch.children[0], patch.children[1]], [patch])
        patch.replace_neighbours(PatchBase.EAST, [patch.children[1], patch.children[2]], [patch])
        patch.replace_neighbours(PatchBase.SOUTH, [patch.children[2], patch.children[3]], [patch])
        patch.replace_neighbours(PatchBase.WEST,  [patch.children[3], patch.children[0]], [patch])
        patch.calc_outer_tesselation_level(update)
        for neighbour in north + east + south + west:
            neighbour.calc_outer_tesselation_level(update)

    def check_lod(self, patch, local, model_camera_pos, model_camera_vector, altitude, pixel_size, lod_control):
        patch.need_merge = False
        patch.check_visibility(self, local, model_camera_pos, model_camera_vector, altitude, pixel_size)
        self.new_max_lod = max(patch.lod, self.new_max_lod)
        #TODO: Should be checked before calling check_lod
        for child in patch.children:
            self.check_lod(child, local, model_camera_pos, model_camera_vector, altitude, pixel_size, lod_control)
        if len(patch.children) != 0:
            if not patch.merge_pending and patch.can_merge_children():
                self.to_merge.append(patch)
            if patch.split_pending and patch.can_show_children():
                self.to_show_children.append(patch)
            if patch.merge_pending and patch.instanciate_pending and patch.instance_ready:
                self.to_show.append(patch)
            if patch.shown and not patch.split_pending:
                self.to_remove.append(patch)
        else:
            #Split patch only when visible and when the heightmap is available, otherwise offset is wrong
            can_split = patch.visible and (not settings.shift_patch_origin or patch.instance_ready)
            if can_split and lod_control.should_split(patch, patch.apparent_size, patch.distance):
                if self.are_children_visibles(patch):
                    self.to_split.append(patch)
            if not patch.visible or lod_control.should_merge(patch, patch.apparent_size, patch.distance):
                patch.need_merge = True
            if patch.shown and not patch.split_pending and lod_control.should_remove(patch, patch.apparent_size, patch.distance):
                self.to_remove.append(patch)
            if not patch.parent_split_pending:
                if not patch.shown and not patch.instanciate_pending and lod_control.should_instanciate(patch, patch.apparent_size, patch.distance):
                    self.to_instanciate.append(patch)
                if patch.instanciate_pending and patch.instance_ready:
                    self.to_show.append(patch)

    def xform_cam_to_model(self, camera_pos):
        pass

    def create_culling_frustum(self, altitude):
        self.lens = self.owner.context.observer.realCamLens.make_copy()
        if self.limit_far:
            if self.max_lod > 10:
                factor = 2.0 / (1 << ((self.max_lod - 10) // 2))
            else:
                factor = 2.0
            self.limit = sqrt(max(0.0, altitude * (factor * self.owner.height_under + altitude)))
            #print(self.limit)
            far = self.limit / settings.scale
            self.lens.setNearFar(far * 1e-4, far)
        self.lens_bounds = self.lens.makeBounds()
        self.lens_bounds.xform(self.owner.context.observer.cam.getNetTransform().getMat())
        if self.frustum is not None:
            self.frustum.remove_node()
        if settings.debug_lod_frustum:
            geom = self.lens.make_geometry()
            self.frustum = render.attach_new_node('frustum')
            node = GeomNode('frustum_node')
            node.add_geom(geom)
            self.frustum.attach_new_node(node)
            self.scene_rel_position = self.owner.scene_rel_position
            self.frustum.set_quat(base.cam.get_quat())
            #The frustum position is updated in place_patches()
            #Camera lens is not scaled, don't need to set the scale
            #self.frustum.set_scale(base.cam.get_scale())

    def is_bb_in_view(self, bb, patch_normal, patch_offset):
        return True

    def is_patch_in_view(self, patch):
        return True

    def are_children_visibles(self, patch):
        children_visible = len(patch.children_bb) == 0
        for (i, child_bb) in enumerate(patch.children_bb):
            if self.is_bb_in_view(child_bb, patch.children_normal[i], patch.children_offset[i]):
                children_visible = True
                break
        return children_visible

    def update_lod(self, camera_pos, distance_to_obs, pixel_size, appearance):
        if settings.debug_lod_freeze:
            return
        if self.instance is None:
            return False
        if distance_to_obs < self.radius:
            return False
        (model_camera_pos, model_camera_vector, coord) = self.xform_cam_to_model(camera_pos)
        altitude = self.owner.distance_to_obs - self.owner.height_under
        self.create_culling_frustum(altitude)
        self.to_split = []
        self.to_merge = []
        self.to_show_children = []
        self.to_instanciate = []
        self.to_show = []
        self.to_remove = []
        process_nb = 0
        self.new_max_lod = 0
        frame = globalClock.getFrameCount()
        self.lod_control.set_appearance(appearance)
        for patch in self.root_patches:
            self.check_lod(patch, coord, model_camera_pos, model_camera_vector, altitude, pixel_size, self.lod_control)
        self.to_split.sort(key=lambda x: x.distance)
        self.to_merge.sort(key=lambda x: x.distance)
        self.to_show_children.sort(key=lambda x: x.distance)
        self.to_instanciate.sort(key=lambda x: x.distance)
        self.to_show.sort(key=lambda x: x.distance)
        self.to_remove.sort(key=lambda x: x.distance)
        apply_appearance = False
        update = []
        for patch in self.to_show_children:
            if settings.debug_lod_split_merge: print(frame, "Children loaded", patch.str_id())
            for child in patch.children:
                child.parent_split_pending = False
                if child.visible and child.instance is not None and child.instance_ready:
                    if settings.debug_lod_split_merge: print(frame, "Show", child.str_id(), child.instance_ready)
                    child.instanciate_pending = False
                    self.show_patch(child)
            patch.split_pending = False
            patch.instanciate_pending = False
            self.remove_patch_instance(patch, split=True)
            patch.last_split = frame
        for patch in self.to_split:
            process_nb += 1
            if settings.debug_lod_split_merge: print(frame, "Split", patch.str_id())
            self.split_patch(patch)
            self.split_neighbours(patch, update)
            for child in patch.children:
                child.check_visibility(self, coord, model_camera_pos, model_camera_vector, altitude, pixel_size)
                #print(child.str_id(), child.visible)
                if self.lod_control.should_instanciate(child, 0, 0):
                    child.parent_split_pending = True
                    child.instanciate_pending = True
                    self.create_patch_instance(child, hide=True)
                    if settings.debug_lod_split_merge: print(frame, "Instanciate child", child.str_id(), child.instance_ready)
            patch.split_pending = True
            apply_appearance = True
            if process_nb > 2:
                break
        for patch in self.to_instanciate:
            if settings.debug_lod_split_merge: print(frame, "Instanciate", patch.str_id(), patch.patch_in_view, patch.in_cone, patch.instance_ready)
            if patch.lod == 0:
                self.add_root_patches(patch, update)
            self.create_patch_instance(patch, hide=True)
            patch.instanciate_pending = True
            apply_appearance = True
        for patch in self.to_show:
            if settings.debug_lod_split_merge: print(frame, "Show", patch.str_id(), patch.instance_ready, patch.instance_ready)
            if patch.instance is not None:
                #Could happen that the patch has just been removed by the parent in the same batch...
                self.show_patch(patch)
            patch.instanciate_pending = False
            if patch.merge_pending:
                for child in patch.children:
                    self.remove_patch_instance(child)
                    child.parent_split_pending = False
                    child.instanciate_pending = False
                patch.remove_children()
                patch.merge_pending = False
        for patch in self.to_remove:
            if settings.debug_lod_split_merge: print(frame, "Remove", patch.str_id(), patch.patch_in_view, patch.in_cone)
            self.remove_patch_instance(patch)
            patch.split_pending = False
            for child in patch.children:
                child.parent_split_pending = False
            patch.instanciate_pending = False
        for patch in self.to_merge:
            #Dampen high frequency split-merge anomaly
            if frame - patch.last_split < 5: continue
            if settings.debug_lod_split_merge: print(frame, "Merge", patch.str_id(), patch.visible)
            self.merge_neighbours(patch, update)
            if patch.visible:
                self.create_patch_instance(patch, hide=True)
                #TODO: self.merge_neighbours(patch)
                apply_appearance = True
                patch.merge_pending = True
                patch.instanciate_pending = True
            else:
                for child in patch.children:
                    self.remove_patch_instance(child)
                    child.parent_split_pending = False
                    child.instanciate_pending = False
                patch.remove_children()
            patch.split_pending = False
        self.max_lod = self.new_max_lod
        for patch in update:
            patch.update_instance()
        #Return True when new instances have been created
        return apply_appearance

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

    def get_height_at(self, coord):
        patch = self.find_patch_at(coord)
        if patch is not None:
            return patch.get_height_at(coord)
        else:
            print("Patch not found", coord)
            return self.radius

    def get_height_patch(self, patch, u, v):
        return patch.get_height_uv(u, v)

    def get_normals_at(self, coord):
        patch = self.find_patch_at(coord)
        if patch is not None:
            return patch.get_normals_at(coord)
        else:
            print("Patch not found", coord)
            return (LVector3d.up(), LVector3d.forward(), LVector3d.left())

    def dump_patch(self, patch):
        pad = ' ' * (patch.lod * 4)
        print(pad, patch.str_id(), hex(id(patch)))
        print(pad, '  Visible' if patch.visible else '  Not visible', patch.patch_in_view, patch.in_cone)
        if patch.shown: print(pad, '  Shown')
        if patch.need_merge: print(pad, '  Need merge')
        if patch.split_pending: print(pad, '  Split pending')
        if patch.merge_pending: print(pad, '  Merge pending')
        if patch.parent_split_pending: print(pad, '  Parent split pending')
        if patch.instanciate_pending: print(pad, '  Instanciate pending')
        if not patch.instance_ready: print(pad, '  Instance ready')
        if patch.jobs_pending != 0: print(pad, '  Jobs', patch.jobs_pending)
        #print(pad, '  Distance', patch.distance)
        print(pad, "  Tesselation", '-'.join(map(str, patch.tesselation_outer_level)))
        for i in range(4):
            print(pad, "  Neighbours", map(lambda x: hex(id(x)) + ' ' + x.str_id(), patch.neighbours[i]))

    def _dump_tree(self, patch):
        self.dump_patch(patch)
        for child in patch.children:
            self._dump_tree(child)

    def dump_tree(self):
        for patch in self.root_patches:
            self._dump_tree(patch)

    def dump_patches(self):
        for patch in self.patches:
            self.dump_patch(patch)

class PatchedShape(PatchedShapeBase):
    offset = True
    no_bounds = True
    limit_far = True
    def __init__(self, patch_size_from_texture=True, lod_control=None):
        PatchedShapeBase.__init__(self, lod_control)

    def place_patches(self, owner):
        PatchedShapeBase.place_patches(self, owner)
        if settings.standalone_patches:
            for patch in self.patches:
                offset = LVector3d()
                if settings.shift_patch_origin:
                    offset += owner.scene_orientation.xform(patch.normal) * patch.offset * self.owner.get_apparent_radius() * owner.scene_scale_factor
                if settings.offset_body_center:
                    offset += -owner.vector_to_obs * self.owner.height_under * owner.scene_scale_factor
                patch.instance.setPos(*(self.owner.scene_position + offset))
                patch.instance.setScale(self.owner.get_scale() * self.owner.scene_scale_factor / patch.geom_scale)
                patch.instance.setQuat(LQuaternion(*(patch.orientation * owner.scene_orientation)))
        elif settings.offset_body_center or settings.shift_patch_origin:
            offset = LVector3d()
            if settings.offset_body_center:
                offset += owner.model_body_center_offset
            for patch in self.patches:
                if settings.shift_patch_origin:
                    patch_offset = offset + patch.normal * patch.offset
                    patch.instance.setPos(*(patch_offset))
                else:
                    patch.instance.setPos(*(offset))
                if False and self.parent.appearance.tex_transform:
                    for i in range(self.parent.appearance.nb_textures):
                        name = 'texmat_%d' % i
                        shader_input = patch.instance.get_shader_input(name)
                        if shader_input.getValueType() == 0:
                            print("WARNING", self.parent.get_name(), patch.str_id(), ":", name, "not found", patch.shown, patch.instance.isStashed())

    def is_bb_in_view(self, bb, patch_normal, patch_offset):
        offset = LVector3d()
        if settings.offset_body_center:
            offset += self.owner.model_body_center_offset
        if settings.shift_patch_origin:
            offset = offset + patch_normal * patch_offset
        offset = LPoint3(*offset)
        obj_bounds = BoundingBox(bb.get_min() + offset, bb.get_max() + offset)
        if settings.standalone_patches:
            obj_bounds.xform(self.owner.context.world.getMat(render))
        else:
            obj_bounds.xform(self.instance.getMat(render))
        #print(bb, obj_bounds, self.lens_bounds)
        intersect = self.lens_bounds.contains(obj_bounds)
        return (intersect & BoundingBox.IF_some) != 0

    def is_patch_in_view(self, patch):
        return self.is_bb_in_view(patch.bounds, patch.normal, patch.offset)

    def xform_cam_to_model(self, camera_pos):
        position = self.owner.get_local_position()
        orientation = self.owner.get_abs_rotation()
        #TODO: Should receive as parameter !
        camera_vector = self.owner.context.observer.get_camera_rot().xform(LVector3d.forward())
        model_camera_vector = orientation.conjugate().xform(camera_vector)
        model_camera_pos = self.local_to_model(camera_pos, position, orientation, self.owner.get_scale())
        (x, y, distance) = self.owner.spherical_to_longlat(self.owner.cartesian_to_spherical(camera_pos))
        return (model_camera_pos, model_camera_vector, (x, y))

    def local_to_model(self, point, position, orientation, scale):
        model_point = orientation.conjugate().xform(point - position)
        return model_point

class PatchedSphereShape(PatchedShape):
    def create_root_patches(self):
        self.root_patches = [self.create_patch(None, 0, 0, 0),
                             self.create_patch(None, 0, 1, 0)
                            ]

    def create_patch(self, parent, lod, sector, ring, average_height = 1.0):
        density = self.lod_control.get_density_for(lod)
        patch = SpherePatch(parent, lod, density, sector, ring, self.radius, average_height)
        #TODO: Temporary or make right
        patch.owner = self
        return patch

    def split_patch(self, patch):
        for i in range(2):
            for j in range(2):
                average_height = 0.0
                for k in range(2):
                    for l in range(2):
                        average_height += self.owner.surface.get_height_patch(patch, i * 0.5 + k * 0.5, j * 0.5 + l * 0.5)
                average_height = average_height / 4.0 / self.owner.get_apparent_radius()
                self.create_patch(patch, patch.lod + 1, patch.sector * 2 + i, patch.ring * 2 + j, average_height)
        patch.children_bb = []
        patch.children_normal = []
        patch.children_offset = []
        for child in patch.children:
            patch.children_bb.append(child.bounds.make_copy())
            patch.children_normal.append(child.normal)
            patch.children_offset.append(child.offset)

    def global_to_shape_coord(self, x, y):
        return (x, y)

    def find_patch_at(self, coord):
        (x, y) = coord
        for patch in self.root_patches:
            result = self._find_patch_at(patch, x, y)
            if result is not None:
                return result
        return None

class PatchedSquareShapeBase(PatchedShape):
    def __init__(self, patch_size_from_texture=True, lod_control=None, use_shader=False, use_tesselation=False):
        PatchedShape.__init__(self, patch_size_from_texture, lod_control)
        self.use_shader = use_shader
        self.use_tesselation = use_tesselation
        self.face_unique = False

    def create_root_patches(self):
        self.root_patches = [
                             self.create_patch(None, 0, 0, 0, 0),
                             self.create_patch(None, 0, 1, 0, 0),
                             self.create_patch(None, 0, 2, 0, 0),
                             self.create_patch(None, 0, 3, 0, 0),
                             self.create_patch(None, 0, 4, 0, 0),
                             self.create_patch(None, 0, 5, 0, 0)
                             ]

    def create_patch(self, parent, lod, face, x, y, average_heigt=1.0):
        return None

    def split_patch(self, patch):
        for i in range(2):
            for j in range(2):
                average_height = 0.0
                for k in range(2):
                    for l in range(2):
                        average_height += self.owner.surface.get_height_patch(patch, i * 0.5 + k * 0.5, j * 0.5 + l * 0.5)
                average_height = average_height / 4.0 / self.owner.get_apparent_radius()
                self.create_patch(patch, patch.lod + 1, patch.face, patch.x * 2 + i, patch.y * 2 + j, average_height)
        patch.children_bb = []
        patch.children_normal = []
        patch.children_offset = []
        for child in patch.children:
            patch.children_bb.append(child.bounds.make_copy())
            patch.children_normal.append(child.normal)
            patch.children_offset.append(child.offset)

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
        theta = (1.0 - y - 0.5) * pi
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
        return self._find_patch_at(self.root_patches[face], x, y)

class NormalizedSquareShape(PatchedSquareShapeBase):
    def create_patch(self, parent, lod, face, x, y, average_height=1.0):
        density = self.lod_control.get_density_for(lod)
        patch = NormalizedSquarePatch(face, x, y, parent, lod, density, self.radius, average_height, self.use_shader, self.use_tesselation)
        #TODO: Temporary or make right
        patch.owner = self
        return patch

    def xyz_to_xy(self, x, y, z):
        vx = x / z
        vy = y / z

        return (vx, vy)

class SquaredDistanceSquareShape(PatchedSquareShapeBase):
    def create_patch(self, parent, lod, face, x, y, average_height=1.0):
        density = self.lod_control.get_density_for(lod)
        patch = SquaredDistanceSquarePatch(face, x, y, parent, lod, density, self.radius, average_height, self.use_shader, self.use_tesselation)
        #TODO: Temporary or make right
        patch.owner = self
        return patch

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

class PatchLodControl(object):
    def __init__(self, density=32, max_lod=100):
        self.density = density
        self.max_lod = max_lod

    def get_density_for(self, lod):
        return self.density

    def set_appearance(self, appearance):
        pass

    def should_split(self, patch, apparent_patch_size, distance):
        return False

    def should_merge(self, patch, apparent_patch_size, distance):
        return False

    def should_instanciate(self, patch, apparent_patch_size, distance):
        #TODO: Temporary fix for patched shape shadows, keep lod 0 patch visible
        return not patch.shown and (patch.visible or patch.lod == 0) and len(patch.children) == 0

    def should_remove(self, patch, apparent_patch_size, distance):
        #TODO: Temporary fix for patched shape shadows, keep lod 0 patch visible
        return patch.shown and (not patch.visible and patch.lod != 0)

class TexturePatchLodControl(PatchLodControl):
    def __init__(self, min_density=8, density=32, max_lod=100):
        PatchLodControl.__init__(self, density, max_lod)
        self.min_density = min_density

    def get_density_for(self, lod):
        density = self.density // (1 << lod)
        if density < self.min_density:
            density = self.min_density
        return density

    def set_appearance(self, appearance):
        self.appearance = appearance
        if appearance is not None and appearance.texture is not None:
            self.patch_size = appearance.texture.source.texture_size
        else:
            self.patch_size = 0

    def should_split(self, patch, apparent_patch_size, distance):
        if patch.lod >= self.max_lod: return False
        return self.patch_size > 0 and apparent_patch_size > self.patch_size * 1.01 and self.appearance.texture.can_split(patch)

    def should_merge(self, patch, apparent_patch_size, distance):
        return apparent_patch_size < self.patch_size / 1.99

class VertexSizePatchLodControl(PatchLodControl):
    def __init__(self, max_vertex_size, density=32, max_lod=100):
        PatchLodControl.__init__(self, density, max_lod)
        self.max_vertex_size = max_vertex_size

    def should_split(self, patch, apparent_patch_size, distance):
        if patch.lod >= self.max_lod: return False
        apparent_vertex_size = apparent_patch_size / patch.density
        return apparent_vertex_size > self.max_vertex_size

    def should_merge(self, patch, apparent_patch_size, distance):
        apparent_vertex_size = apparent_patch_size / patch.density
        return apparent_vertex_size < self.max_vertex_size / 2.5

class VertexSizeMaxDistancePatchLodControl(VertexSizePatchLodControl):
    def __init__(self, max_distance, max_vertex_size, density=32, max_lod=100):
        VertexSizePatchLodControl.__init__(self, max_vertex_size, density, max_lod)
        self.max_distance = max_distance

    def should_instanciate(self, patch, apparent_patch_size, distance):
        return patch.visible and distance < self.max_distance and patch.instance is None

    def should_remove(self, patch, apparent_patch_size, distance):
        return not patch.visible and patch.instance is not None
