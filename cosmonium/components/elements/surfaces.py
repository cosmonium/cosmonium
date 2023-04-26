#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
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


from math import floor, ceil
from panda3d.core import LVector3, LQuaternion, LVector3d, LPoint3d

from ...shapes.shape_object import ShapeObject
from ...shadows import SphereShadowCaster, CustomShadowMapShadowCaster
from ...shaders.shadows.ellipsoid import ShaderSphereSelfShadow

from ...mathutil.surface_models import SphereModel, SpheroidModel, EllipsoidModel


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

    def get_alt_under(self, position, strict=False):
        raise NotImplementedError()

    def get_height_under(self, position, strict=False):
        raise NotImplementedError()

    def get_point_under(self, position, strict=False):
        raise NotImplementedError()

    def get_tangent_plane_under(self, position):
        raise NotImplementedError()

    def get_height_patch(self, patch, u, v):
        raise NotImplementedError

    def global_to_shape_coord(self, x, y):
        return self.shape.global_to_shape_coord(x, y)

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        ShapeObject.update_instance(self, scene_manager, camera_pos, camera_rot)
        if not self.instance_ready:
            return
        self.instance.set_quat(LQuaternion(*self.body.anchor.get_absolute_orientation()))


class EllipsoidSurface(Surface):
    def __init__(self, name=None, category=None, resolution=None, attribution=None,
                 radius=None, oblateness=None, scale=None,
                 shape=None, appearance=None, shader=None, clickable=True):
        Surface.__init__(self, name, category, resolution, attribution, shape, appearance, shader, clickable)
        self.radius = radius
        self.oblateness = oblateness
        self.scale = scale
        if self.scale is not None:
            self.model = None
        if scale is not None:
            self.model = EllipsoidModel(scale)
        elif self.oblateness is not None:
            #self.model = EllipsoidModel(LVector3d(radius, radius, radius * (1 - oblateness)))
            self.model = SpheroidModel(radius, oblateness)
        elif self.radius is not None:
            #self.model = EllipsoidModel(LVector3d(radius))
            self.model = SphereModel(radius)
        else:
            self.model = None
        #TODO: This is a workaround for patchedshape scale, this should be fixed
        self.height_scale = self.radius

    def configure_shape(self):
        self.shape.set_axes(self.model.get_shape_axes())
        self.shape.set_scale(LVector3(self.radius))

    def get_shape_axes(self):
        return self.model.get_shape_axes()

    def do_create_shadow_caster_for(self, light_source):
        shadow_caster = SphereShadowCaster(light_source, self.body)
        return shadow_caster

    def add_self_shadow(self, light_source):
        if self.body.atmosphere is None and light_source.source not in self.shadow_casters:
            self.create_shadow_caster_for(light_source)
            #TODO: A proper shadow caster should be added
            self.shader.add_shadows(ShaderSphereSelfShadow())

    def get_average_radius(self):
        return self.model.get_average_radius()

    def get_min_radius(self):
        return self.model.get_min_radius()

    def get_max_radius(self):
        return self.model.get_max_radius()

    def geodetic_to_cartesian(self, long, lat, h):
        return self.model.geodetic_to_cartesian(long, lat, h)

    def cartesian_to_geodetic(self, position):
        return self.model.cartesian_to_geodetic(position)

    def parametric_to_cartesian(self, x, y, h):
        return self.model.parametric_to_cartesian(x, y, h)

    def cartesian_to_parametric(self, position):
        return self.model.cartesian_to_parametric(position)

    def get_radius_under(self, position):
        radius_under = self.model.get_radius_under(position)
        return radius_under

    def get_tangent_plane_under(self, position):
        return self.model.get_tangent_plane_under(position)

    def global_to_shape_coord(self, x, y):
        return self.shape.global_to_shape_coord(x, y)


class EllipsoidFlatSurface(EllipsoidSurface):

    def get_alt_under(self, position, strict=False):
        return 0

    def get_height_under(self, position, strict=False):
        return self.model.get_radius_under(position)

    def get_point_under(self, position, strict=False):
        return self.model.get_point_under(position)

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

    def get_alt_under(self, position, strict=False):
        return 0

    def get_height_under(self, frame_position, strict=False):
        # TODO: This should be properly implemented
        return self.shape.radius

    def get_point_under(self, position, strict=False):
        return LPoint3d()

    def get_tangent_plane_under(self, position):
        normal = position.normalized()
        if normal.dot(LVector3d.right()) != 0:
            tangent = LVector3d.right() * normal.dot(LVector3d.right())
            tangent.normalize()
            binormal = tangent.cross(normal)
        else:
            tangent = LVector3d.forward() * normal.dot(LVector3d.forward())
            tangent.normalize()
            binormal = tangent.cross(normal)
        return (tangent, binormal, normal)

    def get_height_patch(self, patch, u, v):
        return self.shape.get_height_patch(patch, u, v)


class HeightmapSurface(EllipsoidSurface):
    def __init__(self, name,
                 radius, oblateness, scale,
                 height_scale,
                 shape, heightmap, biome, appearance, shader, clickable=True):
        EllipsoidSurface.__init__(self, name, radius=radius, oblateness=oblateness, scale=scale,
                                  shape=shape, appearance=appearance, shader=shader, clickable=clickable)
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

    def get_average_radius(self):
        return self.radius

    def get_min_radius(self):
        return self.model.get_min_radius() + self.height_scale * self.heightmap.min_height

    def get_max_radius(self):
        return self.model.get_max_radius() + self.height_scale * self.heightmap.max_height

    def get_point_under(self, position, strict=False):
        point_under = self.model.get_point_under(position)
        height = self.get_alt_under(point_under, strict)
        (tangent, binormal, normal) = self.get_tangent_plane_under(point_under)
        if height is not None:
            point_under += normal * height
        elif strict:
            point_under = None
        else:
            #print("Patch not found for", x, y)
            pass
        return point_under

    def get_height_under(self, position, strict=False):
        height = self.get_alt_under(position, strict)
        radius_under = self.model.get_radius_under(position)
        if height is not None:
            height = radius_under + height
        elif strict:
            height = None
        else:
            #print("Patch not found for", x, y)
            height = radius_under
        return height

    def get_alt_under(self, position, strict=False):
        (x, y, _h) = self.model.cartesian_to_parametric(position)
        coord = self.shape.global_to_shape_coord(x, y)
        patch = self.shape.find_patch_at(coord)
        if patch is not None:
            u, v = patch.coord_to_uv(coord)
            height = self.get_height_patch(patch, u, v, strict)
        elif strict:
            height = None
        else:
            #print("Patch not found for", x, y)
            height = 0
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
            height = h * self.height_scale
        elif strict:
            height = None
        else:
            #print("Patch data not found for", patch.str_id())
            height = 0
        return height


class FlatSurface(Surface):
    def __init__(self, name, shape, appearance, shader, clickable=True):
        Surface.__init__(self, name,  shape=shape, appearance=appearance, shader=shader, clickable=clickable)
        self.height_scale = 1.0

    @property
    def size(self):
        return self.shape.scale

    def get_alt_under(self, position, strict=False):
        return 0

    def get_height_under(self, position):
        return 0

    def get_min_radius(self):
        return 0

    def get_point_under(self, position):
        return LPoint3d(position[0], position[1], 0)

    def get_tangent_plane_under(self, position):
        return (LVector3d.right(), LVector3d.forward(), LVector3d.up())


class HeightmapFlatSurface(FlatSurface):
    def __init__(self, name,
                 height_scale,
                 shape, heightmap, biome, appearance, shader, clickable=True):
        FlatSurface.__init__(self, name,
                             shape=shape, appearance=appearance, shader=shader, clickable=clickable)
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
        return self.height_scale * self.heightmap.min_height

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
            height = h * self.height_scale
        elif strict:
            height = None
        else:
            #print("Patch data not found for", patch.str_id())
            height = 0
        return height

    def get_alt_under(self, position, strict=False):
        #print("get_height_at", x, y)
        coord = self.shape.global_to_shape_coord(position[0], position[1])
        patch = self.shape.find_patch_at(coord)
        if patch is not None:
            u, v = patch.coord_to_uv(coord)
            height = self.get_height_patch(patch, u, v, strict)
        elif strict:
            height = None
        else:
            #print("Patch not found for", x, y)
            height = 0
        return height

    def get_height_under(self, position, strict=False):
        return self.get_alt_under(position, strict)
