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

from .shapes import ShapeObject
from .shadows import SphereShadowCaster, CustomShadowMapShadowCaster
from .shaders import ShaderSphereSelfShadow

from math import floor, ceil

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
    def __init__(self, name=None, category=None, resolution=None, attribution=None, shape=None, appearance=None, shader=None, clickable=True):
        ShapeObject.__init__(self, name, shape, appearance, shader, clickable)
        self.category = category
        self.resolution = resolution
        self.attribution = attribution
        #TODO: parent is set to None when component is removed, so we use owner until this is done a better way...
        self.owner = None

    def get_component_name(self):
        return _('Surface')

    def create_shadows(self):
        if self.shadow_caster is None:
            if self.shape.is_spherical():
                self.shadow_caster = SphereShadowCaster(self.owner)
                if self.owner.atmosphere is None:
                    self.shader.add_shadows(ShaderSphereSelfShadow())
            else:
                self.shadow_caster = CustomShadowMapShadowCaster(self.owner, None)
                self.owner.visibility_override = True
                self.shadow_caster.add_target(self, self_shadow=True)
        self.shadow_caster.create()

    def remove_shadows(self):
        if self.shadow_caster is not None:
            self.shadow_caster.remove()
            if self.owner.visibility_override:
                self.owner.visibility_override = False
                #Force recheck of visibility or the body will be immediately recreated
                self.owner.check_visibility(self.owner.context.observer.pixel_size)
            self.shadow_caster = None

    def start_shadows_update(self):
        ShapeObject.start_shadows_update(self)
        #Add self-shadowing for non-spherical objects
        #TODO: It's a bit convoluted to do it like that...
        if not self.shape.is_spherical() and self.owner.visible and self.owner.resolved:
            self.shadow_caster.add_target(self, self_shadow=True)

    def get_average_radius(self):
        return self.owner.get_apparent_radius()

    def get_min_radius(self):
        return self.owner.get_apparent_radius()

    def get_max_radius(self):
        return self.owner.get_apparent_radius()

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
        return self.owner.get_apparent_radius()

    def get_height_patch(self, patch, u, v):
        return self.owner.get_apparent_radius()

class MeshSurface(Surface):
    def is_flat(self):
        return False

    def get_height_at(self, x, y, strict=False):
        coord = self.shape.global_to_shape_coord(x, y)
        return self.shape.get_height_at(coord)

    def get_height_patch(self, patch, u, v):
        return self.shape.get_height_patch(patch, u, v)

class ProceduralSurface(FlatSurface):
    JOB_HEIGHTMAP = 0x0002
    def __init__(self, name, shape, heightmap, appearance, shader, clickable=True):
        FlatSurface.__init__(self, name, shape=shape, appearance=appearance, shader=shader, clickable=clickable)
        self.heightmap = heightmap
        self.biome = None

    def set_heightmap(self, heightmap):
        self.heightmap = heightmap

    def heightmap_ready_cb(self, heightmap, patch):
        if self.shape.patchable:
            self.jobs_done_cb(patch)
        else:
            self.jobs_done_cb(None)

    def patch_done(self, patch):
        FlatSurface.patch_done(self, patch)
        self.heightmap.apply(patch)

    def shape_done(self):
        FlatSurface.shape_done(self)
        if not self.shape.patchable:
            self.heightmap.apply(self.shape)

    def schedule_patch_jobs(self, patch):
        if (patch.jobs & ProceduralSurface.JOB_HEIGHTMAP) == 0:
            #print("UPDATE", patch.str_id())
            patch.jobs |= ProceduralSurface.JOB_HEIGHTMAP
            patch.jobs_pending += 1
            if self.biome is not None:
                patch.jobs_pending += 1
            self.heightmap.create_heightmap(patch, self.heightmap_ready_cb, [patch])
            if self.biome is not None:
                self.biome.create_heightmap(patch, self.heightmap_ready_cb, [patch])
        FlatSurface.schedule_patch_jobs(self, patch)

    def schedule_shape_jobs(self, shape):
        if not shape.patchable:
            if (self.shape.jobs & ProceduralSurface.JOB_HEIGHTMAP) == 0:
                #print("UPDATE SHAPE", self.shape.str_id())
                self.shape.jobs |= ProceduralSurface.JOB_HEIGHTMAP
                self.shape.jobs_pending += 1
                if self.biome is not None:
                    self.shape.jobs_pending += 1
                self.heightmap.create_heightmap(self.shape, self.heightmap_ready_cb, [self.shape])
                if self.biome is not None:
                    self.biome.create_heightmap(self.shape, self.heightmap_ready_cb, [self.shape])
        FlatSurface.schedule_shape_jobs(self, shape)

class HeightmapSurface(ProceduralSurface):
    def __init__(self, name, radius, shape, heightmap, biome, appearance, shader, scale = 1.0, clickable=True, displacement=True, follow_mesh=True):
        ProceduralSurface.__init__(self, name, shape, heightmap, appearance, shader, clickable)
        if radius != 0.0:
            self.height_scale = radius
        else:
            self.height_scale = 1.0
        self.min_radius = radius + self.height_scale * self.heightmap.min_height
        self.max_radius = radius + self.height_scale * self.heightmap.max_height
        self.radius = radius
        self.heightmap_base = radius
        self.biome = biome
        self.scale = scale
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
            heightmap_patch = self.heightmap.get_heightmap(patch)
        while patch is not None and (heightmap_patch is None or not heightmap_patch.heightmap_ready):
            patch = patch.parent
            if patch is not None:
                heightmap_patch = self.heightmap.get_heightmap(patch)
        if patch is not None:
            uv = patch.coord_to_uv(coord)
            #print("uv", uv)
            return self.get_height_patch(patch, *uv)
        elif strict:
            return None
        else:
            #print("Patch not found for", x, y)
            return self.radius

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

    def get_height_patch(self, patch, u, v, recursive=False):
        if not self.displacement:
            return self.radius
        heightmap = self.heightmap.get_heightmap(patch)
        while heightmap is None and patch is not None:
            print("Recurse")
            patch = patch.parent
            heightmap = self.heightmap.get_heightmap(patch)
            u /= 2.0
            v /= 2.0
        if heightmap is None:
            print("No heightmap")
            return self.radius
        if self.follow_mesh:
            h = self.get_mesh_height_uv(heightmap, u, v, patch.density)
        else:
            h = heightmap.get_height_uv(u, v)
        height = h * self.height_scale + self.heightmap_base
        return height
