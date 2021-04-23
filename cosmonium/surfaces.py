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
                 radius=None, oblateness=None, scale=None,
                 shape=None, appearance=None, shader=None, clickable=True):
        ShapeObject.__init__(self, name, shape, appearance, shader, clickable)
        self.category = category
        self.resolution = resolution
        self.attribution = attribution
        self.radius = radius
        self.oblateness = oblateness
        self.scale = scale
        #TODO: This is a workaround for patchedshape scale, this should be fixed
        self.height_scale = self.radius
        #TODO: parent is set to None when component is removed, so we use owner until this is done a better way...
        self.owner = None

    def get_component_name(self):
        return _('Surface')

    def configure_shape(self):
        print("CONFIG SHAPE")
        if self.scale is not None:
            scale = self.scale
        elif self.oblateness is not None:
            scale = LVector3(1.0, 1.0, 1.0 - self.oblateness) * self.radius
        else:
            scale = LVector3(self.radius, self.radius, self.radius)
        self.shape.set_scale(scale)

    def unconfigure_shape(self):
        pass

    def create_shadows(self):
        if self.shadow_caster is None:
            if self.shape.is_spherical():
                self.shadow_caster = SphereShadowCaster(self.owner)
                if self.owner.atmosphere is None:
                    self.shader.add_shadows(ShaderSphereSelfShadow())
            else:
                self.shadow_caster = CustomShadowMapShadowCaster(self.owner, None)
                self.shadow_caster.add_target(self, self_shadow=True)
        self.owner.set_visibility_override(True)
        self.shadow_caster.create()

    def remove_shadows(self):
        if self.shadow_caster is not None:
            self.shadow_caster.remove()
            self.owner.set_visibility_override(False)
            self.shadow_caster = None

    def start_shadows_update(self):
        ShapeObject.start_shadows_update(self)
        #Add self-shadowing for non-spherical objects
        #TODO: It's a bit convoluted to do it like that...
        if not self.shape.is_spherical() and self.owner.visible and self.owner.resolved:
            self.shadow_caster.add_target(self, self_shadow=True)

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

class FlatSurface(Surface):
    def get_height_at(self, x, y, strict=False):
        return self.radius

    def get_height_patch(self, patch, u, v):
        return self.radius

class MeshSurface(Surface):
    def is_flat(self):
        return False

    def get_height_at(self, x, y, strict=False):
        coord = self.shape.global_to_shape_coord(x, y)
        return self.shape.get_height_at(coord)

    def get_height_patch(self, patch, u, v):
        return self.shape.get_height_patch(patch, u, v)

class ProceduralSurface(FlatSurface):
    def __init__(self, name,
                 radius, oblateness, scale,
                 shape, heightmap,appearance, shader, clickable=True):
        FlatSurface.__init__(self, name, radius=radius, oblateness=oblateness, scale=scale,
                             shape=shape, appearance=appearance, shader=shader, clickable=clickable)
        self.heightmap = heightmap
        self.biome = None

    def set_heightmap(self, heightmap):
        self.heightmap = heightmap

    def shape_done(self):
        if not self.shape.patchable:
            self.heightmap.apply(self.shape)
        FlatSurface.shape_done(self)

    async def patch_task(self, patch):
        #TODO: We should use gather instead
        self.heightmap.create_patch_data(patch)
        await self.heightmap.load_patch_data(patch)
        if self.biome is not None:
            self.biome.create_patch_data(patch)
            await self.biome.load_patch_data(patch)
        if patch.instance is not None:
            self.heightmap.apply(patch)
            if self.biome is not None:
                self.biome.apply(patch)
        else:
            #print("DISCARDED", patch.str_id())
            pass
        await FlatSurface.patch_task(self, patch)

    def early_apply_patch(self, patch):
        if patch.lod > 0:
            self.heightmap.create_patch_data(patch)
            self.heightmap.apply(patch)
            if self.biome is not None:
                self.biome.create_patch_data(patch)
                self.biome.apply(patch)
        FlatSurface.early_apply_patch(self, patch)

    async def shape_task(self, shape):
        if not shape.patchable:
            self.heightmap.load_heightmap(shape)
            if self.biome is not None:
                self.biome.load_heightmap(shape)
            if shape.instance is not None:
                self.heightmap.apply(shape)
                if self.biome is not None:
                    self.biome.apply(shape)
            else:
                #print("DISCARDED", patch.str_id())
                pass
        await FlatSurface.shape_task(self, shape)

    def remove_instance(self):
        self.heightmap.clear_all()
        if self.biome is not None:
            self.biome.clear_all()
        FlatSurface.remove_instance(self)

class HeightmapSurface(ProceduralSurface):
    def __init__(self, name,
                 radius, oblateness, scale,
                 height_base, height_scale,
                 shape, heightmap, biome, appearance, shader, clickable=True, displacement=True, follow_mesh=True):
        ProceduralSurface.__init__(self, name,radius, oblateness, scale,
                                   shape, heightmap, appearance, shader, clickable)
        self.heightmap_base  = height_base
        self.height_scale = height_scale
        self.min_radius = self.heightmap_base + self.height_scale * self.heightmap.min_height
        self.max_radius = self.heightmap_base + self.height_scale * self.heightmap.max_height
        self.biome = biome
        self.displacement = displacement
        self.follow_mesh = follow_mesh
        #TODO: Make a proper method for this...
        shape.face_unique = True
        shape.set_heightmap(heightmap)

    def is_flat(self):
        return False

    def get_average_radius(self):
        return self.radius

    def get_min_radius(self):
        return self.min_radius

    def get_max_radius(self):
        return self.max_radius

    def global_to_shape_coord(self, x, y):
        return self.shape.global_to_shape_coord(x, y)

    def get_height_at(self, x, y, strict=False):
        #print("get_height_at", x, y)
        if not self.displacement:
            return self.radius
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
        if not self.displacement:
            return self.radius
        patch_data = self.heightmap.get_patch_data(patch)
        if patch_data is not None and patch_data.data_ready:
            if self.follow_mesh:
                h = self.get_mesh_height_uv(patch_data, u, v, patch.density)
            else:
                h = patch_data.get_height_uv(u, v)
            height = h * self.height_scale + self.heightmap_base
        elif strict:
            height = None
        else:
            #print("Patch data not found for", patch.str_id())
            height = self.radius
        return height
