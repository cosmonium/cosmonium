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


from ...shapes.shape_object import ShapeObject
from ...shadows import SphereShadowCaster, CustomShadowMapShadowCaster
from ...shaders.shadows.ellipsoid import ShaderSphereSelfShadow

from math import floor, ceil
from panda3d.core import LVector3, LQuaternion

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
        self.body = None

    def get_component_name(self):
        return _('Surface')

    def set_body(self, body):
        self.body = body

    def configure_render_order(self):
        self.instance.set_bin("front_to_back", 0)

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
        object_position = self.body.anchor.get_local_position()
        object_orientation = self.body.anchor.get_absolute_orientation()
        shape_position = object_orientation.conjugate().xform(position - object_position) / self.height_scale
        return shape_position

    def local_vector_to_shape(self, vector):
        object_orientation = self.body.anchor.get_absolute_orientation()
        shape_vector = object_orientation.conjugate().xform(vector)
        return shape_vector

    def local_position_to_shape_coord(self, position):
        (x, y, distance) = self.body.spherical_to_xy(self.body.cartesian_to_spherical(position))
        return (x, y)

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        ShapeObject.update_instance(self, scene_manager, camera_pos, camera_rot)
        if not self.instance_ready: return
        self.instance.set_quat(LQuaternion(*self.body.anchor.get_absolute_orientation()))

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

    def configure_shape(self):
        if self.scale is not None:
            scale = self.scale
        elif self.oblateness is not None:
            scale = LVector3(1.0, 1.0, 1.0 - self.oblateness) * self.radius
        else:
            scale = LVector3(self.radius, self.radius, self.radius)
        self.shape.set_scale(scale)

    def do_create_shadow_caster_for(self, light_source):
        shadow_caster = SphereShadowCaster(light_source, self.body)
        return shadow_caster

    def add_self_shadow(self, light_source):
        if self.body.atmosphere is None and not light_source.source in self.shadow_casters:
            self.create_shadow_caster_for(light_source)
            #TODO: A proper shadow caster should be added
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
        object_position = self.body.anchor.get_local_position()
        object_orientation = self.body.anchor.get_absolute_orientation()
        shape_position = object_orientation.conjugate().xform(position - object_position) / self.height_scale
        return shape_position

    def local_vector_to_shape(self, vector):
        object_orientation = self.body.anchor.get_absolute_orientation()
        shape_vector = object_orientation.conjugate().xform(vector)
        return shape_vector

    def local_position_to_shape_coord(self, position):
        (x, y, distance) = self.body.spherical_to_xy(self.body.cartesian_to_spherical(position))
        return (x, y)

class EllipsoidFlatSurface(EllipsoidSurface):
    def get_height_at(self, x, y, strict=False):
        return self.radius

    def get_height_patch(self, patch, u, v):
        return self.radius

class MeshSurface(Surface):
    def is_flat(self):
        return False

    def do_create_shadow_caster_for(self, light_source):
        shadow_caster = CustomShadowMapShadowCaster(light_source, self.body, self)
        shadow_caster.add_target(self, self_shadow=True)
        return shadow_caster

    def add_self_shadow(self, light_source):
        #Add self-shadowing for non-spherical objects
        if self.instance_ready:
            self.create_shadow_caster_for(light_source)
            self.shadow_casters[light_source.source].add_target(self, self_shadow=True)

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
        self.patch_sources.add_source(self.heightmap)
        if biome is not None:
            self.patch_sources.add_source(biome)
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

    def get_patch_at(self, x, y):
        coord = self.shape.global_to_shape_coord(x, y)
        patch = self.shape.find_patch_at(coord)
        return patch

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
    def get_mesh_height_uv(self, heightmap, u, v, patch):
        density = patch.density
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
        h_00 = heightmap.get_height(x0, y0, patch)
        h_01 = heightmap.get_height(x0, y1, patch)
        h_10 = heightmap.get_height(x1, y0, patch)
        h_11 = heightmap.get_height(x1, y1, patch)
        return h_00 + (h_10 - h_00) * dx + (h_01 - h_00) * dy + (h_00 + h_11 - h_01 - h_10) * dx * dy

    def get_height_patch(self, patch, u, v, strict=False):
        patch_data = self.heightmap.get_patch_data(patch, strict=strict)
        if patch_data is not None and patch_data.data_ready:
            h = self.get_mesh_height_uv(patch_data, u, v, patch)
            height = h * self.height_scale + self.heightmap_base
        elif strict:
            height = None
        else:
            #print("Patch data not found for", patch.str_id())
            height = self.radius
        return height

class FlatSurface(Surface):
    @property
    def size(self):
        return self.shape.scale

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
        self.patch_sources.add_source(self.heightmap)
        if biome is not None:
            self.patch_sources.add_source(biome)
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

    def get_patch_at(self, x, y):
        coord = self.shape.global_to_shape_coord(x, y)
        patch = self.shape.find_patch_at(coord)
        return patch

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
        patch_data = self.heightmap.get_patch_data(patch, strict=strict)
        if patch_data is not None and patch_data.data_ready:
            h = self.get_mesh_height_uv(patch_data, u, v, patch.density)
            height = h * self.height_scale + self.heightmap_base
        elif strict:
            height = None
        else:
            #print("Patch data not found for", patch.str_id())
            height = self.heightmap_base
        return height
