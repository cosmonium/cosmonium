#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2021 Laurent Deru.
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

from .shapes import ShapeObject
from .shadows import SphereShadowCaster, CustomShadowMapShadowCaster
from .shaders import ShaderSphereSelfShadow

from math import floor, ceil
from panda3d.core import LVector3

class SurfaceCategory(object):
    def __init__(self, name):
        self.name = name

class SurfaceCategoryDB(object):
    def __init__(self):
        self.categories = {}

    def add(self, category):
        self.categories[category.name] = category

    def get(self, name):
        return self.categories.get(name)

surfaceCategoryDB = SurfaceCategoryDB()

class Surface(ShapeObject):
    def __init__(self, name=None, category=None, resolution=None, attribution=None,
                 shape=None, appearance=None, shader=None, clickable=True):
        ShapeObject.__init__(self, name, shape, appearance, shader, clickable)
        self.category = category
        self.resolution = resolution
        self.attribution = attribution
        #TODO: parent is set to None when component is removed, so we use owner until this is done a better way...
        self.owner = None

    def get_component_name(self):
        return _('Surface')

    def global_to_shape_coord(self, x, y):
        return self.shape.global_to_shape_coord(x, y)

    def get_height_at(self, x, y, strict=False):
        raise NotImplementedError

    def get_height_patch(self, patch, u, v):
        raise NotImplementedError

    def get_normals_at(self, x, y):
        coord = self.shape.global_to_shape_coord(x, y)
        return self.shape.get_normals_at(coord)

    def get_lonlatvert_at(self, x, y):
        coord = self.shape.global_to_shape_coord(x, y)
        return self.shape.get_lonlatvert_at(coord)

    def local_position_to_shape(self, position):
        object_position = self.owner.get_local_position()
        object_orientation = self.owner.get_abs_rotation()
        shape_position = object_orientation.conjugate().xform(position - object_position) / self.height_scale
        return shape_position

    def local_vector_to_shape(self, vector):
        object_orientation = self.owner.get_abs_rotation()
        shape_vector = object_orientation.conjugate().xform(vector)
        return shape_vector

    def local_position_to_shape_coord(self, position):
        (x, y, distance) = self.owner.spherical_to_xy(self.owner.cartesian_to_spherical(position))
        return (x, y)

class EllipsoidSurface(Surface):
    def __init__(self, name=None, category=None, resolution=None, attribution=None,
                 radius=None, oblateness=None, scale=None,
                 shape=None, appearance=None, shader=None, clickable=True):
        Surface.__init__(self, name, category, resolution, attribution, shape, appearance, shader, clickable)
        self.radius = radius
        self.oblateness = oblateness
        self.scale = scale
        #TODO: This is a workaround for patchedshape scale, this should be fixed
        self.height_scale = self.radius
        #TODO: parent is set to None when component is removed, so we use owner until this is done a better way...
        self.owner = None

    def configure_shape(self):
        if self.scale is not None:
            scale = self.scale
        elif self.oblateness is not None:
            scale = LVector3(1.0, 1.0, 1.0 - self.oblateness) * self.radius
        else:
            scale = LVector3(self.radius, self.radius, self.radius)
        self.shape.set_scale(scale)

    def create_shadow_caster(self):
        self.shadow_caster = SphereShadowCaster(self.owner)
        if self.owner.atmosphere is None:
            self.shader.add_shadows(ShaderSphereSelfShadow())

    def get_average_radius(self):
        return self.radius

    def get_min_radius(self):
        return self.radius

    def get_max_radius(self):
        return self.radius

    def global_to_shape_coord(self, x, y):
        return self.shape.global_to_shape_coord(x, y)

    def get_height_at(self, x, y, strict=False):
        raise NotImplementedError

    def get_height_patch(self, patch, u, v):
        raise NotImplementedError

    def get_normals_at(self, x, y):
        coord = self.shape.global_to_shape_coord(x, y)
        return self.shape.get_normals_at(coord)

    def get_lonlatvert_at(self, x, y):
        coord = self.shape.global_to_shape_coord(x, y)
        return self.shape.get_lonlatvert_at(coord)

    def local_position_to_shape(self, position):
        object_position = self.owner.get_local_position()
        object_orientation = self.owner.get_abs_rotation()
        shape_position = object_orientation.conjugate().xform(position - object_position) / self.height_scale
        return shape_position

    def local_vector_to_shape(self, vector):
        object_orientation = self.owner.get_abs_rotation()
        shape_vector = object_orientation.conjugate().xform(vector)
        return shape_vector

    def local_position_to_shape_coord(self, position):
        (x, y, distance) = self.owner.spherical_to_xy(self.owner.cartesian_to_spherical(position))
        return (x, y)

class EllipsoidFlatSurface(EllipsoidSurface):
    def get_height_at(self, x, y, strict=False):
        return self.radius

    def get_height_patch(self, patch, u, v):
        return self.radius

class MeshSurface(Surface):
    def is_flat(self):
        return False

    def create_shadow_caster(self):
        self.shadow_caster = CustomShadowMapShadowCaster(self.owner, None)
        self.shadow_caster.add_target(self, self_shadow=True)

    def start_shadows_update(self):
        ShapeObject.start_shadows_update(self)
        #Add self-shadowing for non-spherical objects
        #TODO: It's a bit convoluted to do it like that...
        if self.owner.visible and self.owner.resolved:
            self.shadow_caster.add_target(self, self_shadow=True)

    def get_height_at(self, x, y, strict=False):
        coord = self.shape.global_to_shape_coord(x, y)
        return self.shape.get_height_at(coord)

    def get_height_patch(self, patch, u, v):
        return self.shape.get_height_patch(patch, u, v)

class HeightmapSurface(EllipsoidSurface):
    def __init__(self, name,
                 radius, oblateness, scale,
                 height_base, height_scale,
                 shape, heightmap, biome, appearance, shader, clickable=True):
        EllipsoidSurface.__init__(self, name, radius=radius, oblateness=oblateness, scale=scale,
                                  shape=shape, appearance=appearance, shader=shader, clickable=clickable)
        self.heightmap_base  = height_base
        self.height_scale = height_scale
        self.heightmap = heightmap
        self.biome = biome
        self.sources.append(self.heightmap)
        if biome is not None:
            self.sources.append(biome)
        self.min_radius = self.heightmap_base + self.height_scale * self.heightmap.min_height
        self.max_radius = self.heightmap_base + self.height_scale * self.heightmap.max_height
        #TODO: Make a proper method for this...
        shape.face_unique = True
        shape.set_heightmap(heightmap)

    def set_heightmap(self, heightmap):
        self.heightmap = heightmap

    def is_flat(self):
        return False

    def get_average_radius(self):
        return self.radius

    def get_min_radius(self):
        return self.min_radius

    def get_max_radius(self):
        return self.max_radius

    def remove_instance(self):
        self.heightmap.clear_all()
        if self.biome is not None:
            self.biome.clear_all()
        EllipsoidSurface.remove_instance(self)

    def get_height_at(self, x, y, strict=False):
        #print("get_height_at", x, y)
        coord = self.shape.global_to_shape_coord(x, y)
        patch = self.shape.find_patch_at(coord)
        if patch is not None:
            u, v = patch.coord_to_uv(coord)
            height = self.get_height_patch(patch, u, v, strict)
        elif strict:
            height = None
        else:
            #print("Patch not found for", x, y)
            height = self.radius
        return height

    #TODO: Should be based on how the patch is tesselated !
    def get_mesh_height_uv(self, heightmap, u, v, density):
        x = u * density
        y = v * density
        x0 = floor(x) / density * heightmap.width
        y0 = floor(y) / density * heightmap.height
        x1 = ceil(x) / density * heightmap.width
        y1 = ceil(y) / density * heightmap.height
        dx = u * heightmap.width - x0
        if x1 != x0:
            dx /= x1 - x0
        dy = v * heightmap.height - y0
        if y1 != y0:
            dy /= y1 - y0
        h_00 = heightmap.get_height(x0, y0)
        h_01 = heightmap.get_height(x0, y1)
        h_10 = heightmap.get_height(x1, y0)
        h_11 = heightmap.get_height(x1, y1)
        return h_00 + (h_10 - h_00) * dx + (h_01 - h_00) * dy + (h_00 + h_11 - h_01 - h_10) * dx * dy

    def get_height_patch(self, patch, u, v, strict=False):
        patch_data = self.heightmap.get_patch_data(patch)
        if patch_data is not None and patch_data.data_ready:
            h = self.get_mesh_height_uv(patch_data, u, v, patch.density)
            height = h * self.height_scale + self.heightmap_base
        elif strict:
            height = None
        else:
            #print("Patch data not found for", patch.str_id())
            height = self.radius
        return height

class FlatSurface(Surface):
    pass

class HeightmapFlatSurface(FlatSurface):
    def __init__(self, name,
                 height_base, height_scale,
                 shape, heightmap, biome, appearance, shader, clickable=True):
        FlatSurface.__init__(self, name,
                             shape=shape, appearance=appearance, shader=shader, clickable=clickable)
        self.heightmap_base  = height_base
        self.height_scale = height_scale
        self.heightmap = heightmap
        self.biome = biome
        self.sources.append(self.heightmap)
        if biome is not None:
            self.sources.append(biome)
        #TODO: Make a proper method for this...
        shape.face_unique = True
        shape.set_heightmap(heightmap)

    def set_heightmap(self, heightmap):
        self.heightmap = heightmap

    def is_flat(self):
        return False

    def get_min_radius(self):
        return self.heightmap_base + self.height_scale * self.heightmap.min_height

    def remove_instance(self):
        self.heightmap.clear_all()
        if self.biome is not None:
            self.biome.clear_all()
        FlatSurface.remove_instance(self)

    def get_height_at(self, x, y, strict=False):
        #print("get_height_at", x, y)
        coord = self.shape.global_to_shape_coord(x, y)
        patch = self.shape.find_patch_at(coord)
        if patch is not None:
            u, v = patch.coord_to_uv(coord)
            height = self.get_height_patch(patch, u, v, strict)
        elif strict:
            height = None
        else:
            #print("Patch not found for", x, y)
            height = self.heightmap_base
        return height

    #TODO: Should be based on how the patch is tesselated !
    def get_mesh_height_uv(self, heightmap, u, v, density):
        x = u * density
        y = v * density
        x0 = floor(x) / density * heightmap.width
        y0 = floor(y) / density * heightmap.height
        x1 = ceil(x) / density * heightmap.width
        y1 = ceil(y) / density * heightmap.height
        dx = u * heightmap.width - x0
        if x1 != x0:
            dx /= x1 - x0
        dy = v * heightmap.height - y0
        if y1 != y0:
            dy /= y1 - y0
        h_00 = heightmap.get_height(x0, y0)
        h_01 = heightmap.get_height(x0, y1)
        h_10 = heightmap.get_height(x1, y0)
        h_11 = heightmap.get_height(x1, y1)
        return h_00 + (h_10 - h_00) * dx + (h_01 - h_00) * dy + (h_00 + h_11 - h_01 - h_10) * dx * dy

    def get_height_patch(self, patch, u, v, strict=False):
        patch_data = self.heightmap.get_patch_data(patch)
        if patch_data is not None and patch_data.data_ready:
            h = self.get_mesh_height_uv(patch_data, u, v, patch.density)
            height = h * self.height_scale + self.heightmap_base
        elif strict:
            height = None
        else:
            #print("Patch data not found for", patch.str_id())
            height = self.heightmap_base
        return height
