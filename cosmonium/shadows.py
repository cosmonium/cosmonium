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


from panda3d.core import WindowProperties, FrameBufferProperties, GraphicsPipe, GraphicsOutput
from panda3d.core import Texture, OrthographicLens, PandaNode, NodePath
from panda3d.core import LVector3, LPoint3, LVector3d, LPoint4, Mat4
from panda3d.core import ColorWriteAttrib, LColor, CullFaceAttrib, RenderState, DepthOffsetAttrib
from panda3d.core import LMatrix4, PTA_LMatrix4, LQuaternion

from .foundation import BaseObject
from .datasource import DataSource
from .shaders import ShaderShadowMap, ShaderRingShadow, ShaderSphereShadow

from . import settings

from math import asin, pi

class ShadowMap(object):
    def __init__(self, size):
        self.size = size
        self.buffer = None
        self.depthmap = None
        self.cam = None
        self.shadow_caster = None
        self.snap_cam = settings.shadows_snap_cam

    def create(self):
        winprops = WindowProperties.size(self.size, self.size)
        props = FrameBufferProperties()
        props.setRgbColor(0)
        props.setAlphaBits(0)
        props.setDepthBits(1)
        self.buffer = base.graphicsEngine.makeOutput(
            base.pipe, "shadowsBuffer", -2,
            props, winprops,
            GraphicsPipe.BFRefuseWindow,
            base.win.getGsg(), base.win)

        if not self.buffer:
            print("Video driver cannot create an offscreen buffer.")
            return
        self.depthmap = Texture()
        self.buffer.addRenderTexture(self.depthmap, GraphicsOutput.RTMBindOrCopy,
                                 GraphicsOutput.RTPDepthStencil)

        self.depthmap.setMinfilter(Texture.FTShadow)
        self.depthmap.setMagfilter(Texture.FTShadow)
        self.depthmap.setBorderColor(LColor(1, 1, 1, 1))
        self.depthmap.setWrapU(Texture.WMBorderColor)
        self.depthmap.setWrapV(Texture.WMBorderColor)

        self.cam = base.makeCamera(self.buffer, lens=OrthographicLens())
        self.cam.reparent_to(render)
        self.node = self.cam.node()
        self.node.setInitialState(RenderState.make(CullFaceAttrib.make_reverse(),
                                                   ColorWriteAttrib.make(ColorWriteAttrib.M_none),
                                                   ))
        self.node.setScene(render)
        if settings.debug_shadow_frustum:
            self.node.showFrustum()

    def align_cam(self):
        mvp = Mat4(base.render.get_transform(self.cam).get_mat() * self.get_lens().get_projection_mat())
        center = mvp.xform(LPoint4(0, 0, 0, 1)) * 0.5 + 0.5
        texel_size = 1.0 / self.size
        offset_x = center.x % texel_size
        offset_y = center.y % texel_size
        mvp.invert_in_place()
        new_center = mvp.xform(LPoint4((center.x - offset_x) * 2.0 - 1.0,
                                       (center.y - offset_y) * 2.0 - 1.0,
                                       (center.z) * 2.0 - 1.0,
                                       1.0))
        self.cam.set_pos(self.cam.get_pos() - LVector3(new_center.x, new_center.y, new_center.z))

    def set_lens(self, size, near, far, direction):
        lens = self.node.get_lens()
        lens.set_film_size(size)
        lens.setNear(near)
        lens.setFar(far)
        lens.set_view_vector(LVector3(*direction), LVector3.up())
 
    def get_lens(self):
        return self.node.get_lens()

    def set_direction(self, direction):
        lens = self.node.get_lens()
        lens.set_view_vector(LVector3(*direction), LVector3.up())

    def get_pos(self):
        return self.cam.get_pos()

    def set_pos(self, position):
        self.cam.set_pos(LPoint3(*position))
        if self.snap_cam:
            self.align_cam()

    def remove(self):
        self.node = None
        self.cam.remove_node()
        self.cam = None
        self.depthmap = None
        self.buffer.set_active(False)
        base.graphicsEngine.removeWindow(self.buffer)
        self.buffer = None

class ShadowCasterBase(object):
    def __init__(self, light_source):
        self.light_source = light_source

    def create(self):
        pass

    def remove(self):
        pass

    def check_settings(self):
        pass

    def is_valid(self):
        return True

    def add_target(self, shape_object):
        pass

    def update(self):
        pass

class ShadowMapShadowCaster(ShadowCasterBase):
    def __init__(self, light_source, occluder):
        ShadowCasterBase.__init__(self, light_source)
        self.occluder = occluder
        self.name = self.occluder.get_ascii_name()
        self.shadow_caster = None
        self.shadow_camera = None

    def create_camera(self):
        pass

    def create(self):
        if self.shadow_caster is not None: return
        self.create_camera()
        self.shadow_camera.set_camera_mask(BaseObject.ShadowCameraMask)

    def remove_camera(self):
        pass

    def remove(self):
        self.remove_camera()

    def check_settings(self):
        if settings.debug_shadow_frustum:
            self.shadow_camera.show_frustum()
        else:
            self.shadow_camera.hide_frustum()

    def is_valid(self):
        return self.shadow_caster is not None

    def update(self):
        radius = self.occluder.get_extend() / settings.scale
        self.shadow_caster.get_lens().set_film_size(radius * 2.1, radius * 2.1)
        #The shadow frustum origin is at the light center which is one radius away from the object
        #So the near plane is 0 to coincide with the boundary of the object
        self.shadow_caster.get_lens().setNear(0)
        self.shadow_caster.get_lens().setFar(radius*2)
        self.shadow_caster.get_lens().set_view_vector(LVector3(*self.light_source.light_direction), LVector3.up())

class ShadowMapDataSource(DataSource):
    def __init__(self, name, caster, use_bias):
        DataSource.__init__(self, 'shadowmap-' + name)
        self.name = name
        self.caster = caster
        self.use_bias = use_bias

    def apply(self, shape, instance):
        shape.instance.setShaderInput('%s_depthmap' % self.name, self.caster.shadow_caster.depthmap)
        shape.instance.setShaderInput("%sLightSource" % self.name, self.caster.shadow_caster.cam)
        if self.caster.occluder is None:
            shape.instance.setShaderInput('%s_shadow_coef' % self.name, 1.0)

    def update(self, shape, instance):
        #TODO: Shadow parameters should not be retrieved like that
        appearance = shape.parent.appearance
        if self.use_bias:
            normal_bias = appearance.shadow_normal_bias / 100.0 * shape.owner.anchor.scene_scale_factor * shape.owner.get_apparent_radius()
            slope_bias = appearance.shadow_slope_bias /100.0 * shape.owner.anchor.scene_scale_factor * shape.owner.get_apparent_radius()
            depth_bias = appearance.shadow_depth_bias / 100.0 * shape.owner.anchor.scene_scale_factor * shape.owner.get_apparent_radius()
            #print(normal_bias, slope_bias, depth_bias, shape.owner.anchor.scene_scale_factor, shape.owner.get_apparent_radius())
            instance.setShaderInput('%s_shadow_normal_bias' % self.name, normal_bias)
            instance.setShaderInput('%s_shadow_slope_bias' % self.name, slope_bias)
            instance.setShaderInput('%s_shadow_depth_bias' % self.name, depth_bias)
        if self.caster.occluder is not None:
            light_source = self.caster.light_source
            occluder = self.caster.occluder
            body = shape.owner
            self_radius = occluder.get_apparent_radius()
            body_radius = body.get_apparent_radius()
            position = occluder.anchor._local_position
            body_position = body.anchor._local_position
            pa = body_position - position
            distance = abs(pa.length() - body_radius)
            if distance != 0:
                self_ar = asin(self_radius / distance) if self_radius < distance else pi / 2
                star_ar = asin(light_source.source.get_apparent_radius() / ((light_source.source.anchor._local_position - body_position).length() - body_radius))
                ar_ratio = self_ar /star_ar
            else:
                ar_ratio = 1.0
            instance.setShaderInput('%s_shadow_coef' % self.name, min(max(ar_ratio * ar_ratio, 0.0), 1.0))

    def clear_shape_data(self, shape, instance):
        instance.clearShaderInput('%s_depthmap' % self.name)
        instance.clearShaderInput("%sLightSource" % self.name)

class PandaShadowCaster(ShadowMapShadowCaster):
    def create_camera(self):
        print("Create Panda3D shadow camera for", self.occluder.get_name())
        self.light.setShadowCaster(True, settings.shadow_size, settings.shadow_size)
        self.shadow_caster = self.directional_light
        self.shadow_camera = self.directional_light

    def remove_camera(self):
        print("Remove Panda3D shadow camera for", self.occluder.get_name())
        self.light.setShadowCaster(False)
        self.shadow_caster = None
        self.shadow_camera = None

class CustomShadowMapShadowCaster(ShadowMapShadowCaster):
    def __init__(self, light_source, occluder):
        ShadowMapShadowCaster.__init__(self, light_source, occluder)
        self.targets = {}

    def create_camera(self):
        print("Create shadow camera for", self.occluder.get_name())
        self.shadow_caster = ShadowMap(settings.shadow_size)
        self.shadow_caster.create()
        self.shadow_camera = self.shadow_caster.node

    def remove_camera(self):
        print("Remove shadow camera for", self.occluder.get_name())
        self.shadow_caster.remove()
        for target in list(self.targets.keys()):
            self.remove_target(target)
        self.shadow_caster = None
        self.shadow_camera = None

    def update(self):
        ShadowMapShadowCaster.update(self)
        self.shadow_caster.set_pos(self.light_source.light_source.getPos())

    def add_target(self, shape_object, self_shadow=False):
        shape_object.shadows.add_generic_occluder(self, self_shadow)

class RingShadowCaster(ShadowCasterBase):
    def __init__(self, light_source, ring):
        ShadowCasterBase.__init__(self, light_source)
        self.ring = ring

    def add_target(self, shape_object):
        shape_object.shadows.add_ring_occluder(self)


class RingShadowDataSource(DataSource):
    def __init__(self, ring):
        DataSource.__init__(self, 'ring-shadow')
        self.ring = ring

    def update(self, shape, instance):
        (texture, texture_size, texture_lod) = self.ring.appearance.texture.source.get_texture(self.ring.shape)
        if texture is not None:
            instance.setShaderInput('shadow_ring_tex',texture)
        normal = shape.owner.anchor.scene_orientation.xform(LVector3d.up())
        instance.setShaderInput('ring_normal', normal)
        instance.setShaderInput('ring_inner_radius', self.ring.inner_radius * shape.owner.anchor.scene_scale_factor)
        instance.setShaderInput('ring_outer_radius', self.ring.outer_radius * shape.owner.anchor.scene_scale_factor)
        if shape.owner.support_offset_body_center and settings.offset_body_center:
            body_center = shape.owner.anchor.scene_position + shape.owner.projected_world_body_center_offset
        else:
            body_center = shape.owner.anchor.scene_position
        instance.setShaderInput('body_center', body_center)


class SphereShadowCaster(ShadowCasterBase):
    def __init__(self, light_source, occluder):
        ShadowCasterBase.__init__(self, light_source)
        self.occluder = occluder

    def add_target(self, shape_object):
        shape_object.shadows.add_sphere_occluder(self)


class SphereShadowDataSource(DataSource):
    def __init__(self, shadow_casters, max_occluders, far_sun, oblate_occluder):
        DataSource.__init__(self, 'sphere-shadows')
        self.shadow_casters = shadow_casters
        self.max_occluders = max_occluders
        self.far_sun = far_sun
        self.oblate_occluder = oblate_occluder

    def update(self, shape, instance):
        self.light_source = self.shadow_casters.shadow_casters[0].light_source
        observer = shape.owner.context.observer._position
        scale = shape.owner.anchor.scene_scale_factor
        if self.far_sun:
            vector = shape.owner.anchor._local_position - self.light_source.source.anchor._local_position
            distance_to_light_source = vector.length()
            instance.setShaderInput('star_ar', asin(self.light_source.source.get_apparent_radius() / distance_to_light_source))
        star_center = (self.light_source.source.anchor._local_position - observer) * scale
        star_radius = self.light_source.source.get_apparent_radius() * scale
        instance.setShaderInput('star_center', star_center)
        instance.setShaderInput('star_radius', star_radius)
        centers = []
        radii = []
        occluder_transform = PTA_LMatrix4()
        if len(self.shadow_casters.shadow_casters) > self.max_occluders:
            print("Too many occluders")
        nb_of_occluders = 0
        for shadow_caster in self.shadow_casters.shadow_casters:
            #TODO: The selection should be done on the angular radius of the shadow.
            if nb_of_occluders >= self.max_occluders:
                break
            nb_of_occluders += 1
            occluder = shadow_caster.occluder
            centers.append((occluder.anchor._local_position - observer) * scale)
            radius = occluder.get_apparent_radius()
            radii.append(radius * scale)
            if self.oblate_occluder:
                #TODO: This should refactored with the code in oneil and moved to the body class
                planet_scale = occluder.surface.get_scale()
                descale = LMatrix4.scale_mat(radius / planet_scale[0], radius / planet_scale[1], radius / planet_scale[2])
                rotation_mat = LMatrix4()
                orientation = LQuaternion(*occluder.anchor._orientation)
                orientation.extract_to_matrix(rotation_mat)
                rotation_mat_inv = LMatrix4()
                rotation_mat_inv.invert_from(rotation_mat)
                descale_mat = rotation_mat_inv * descale * rotation_mat
                occluder_transform.push_back(descale_mat)
        instance.setShaderInput('occluder_centers', centers)
        instance.setShaderInput('occluder_radii', radii)
        if self.oblate_occluder:
            instance.setShaderInput('occluder_transform', occluder_transform)
        instance.setShaderInput("nb_of_occluders", nb_of_occluders)


class ShadowBase(object):
    pass

class SphereShadows(ShadowBase):
    def __init__(self):
        self.shadow_casters = []
        self.max_occluders = 4
        self.far_sun = True
        self.oblate_occluder = True
        self.shader_component = ShaderSphereShadow(self.max_occluders, self.far_sun, self.oblate_occluder)
        self.data_source = SphereShadowDataSource(self, self.max_occluders, self.far_sun, self.oblate_occluder)

    def add_shadow_caster(self, shadow_caster):
        if not shadow_caster in self.shadow_casters:
            self.shadow_casters.append(shadow_caster)

    def empty(self):
        return len(self.shadow_casters) == 0

    def clear(self):
        self.shadow_casters = []

class GenericShadows(ShadowBase):
    def __init__(self, target):
        self.target = target
        self.casters = []
        self.old_casters = []
        self.shader_components = {}
        self.data_sources = {}
        self.rebuild_needed = False
        self.nb_updates = 0

    def add_occluder(self, caster, self_shadow):
        if not caster.is_valid(): return
        self.casters.append(caster)
        if not caster in self.old_casters:
            print("Add shadow caster", caster.name, "on", self.target.owner.get_name())
            shadow_shader =  ShaderShadowMap(caster.name, caster.occluder, caster.shadow_caster, use_bias=self_shadow)
            self.shader_components[caster] = shadow_shader
            data_source = ShadowMapDataSource(caster.name, caster, use_bias=self_shadow)
            self.target.sources.add_source(data_source)
            self.data_sources[caster] = data_source
            self.target.shader.add_shadows(shadow_shader)
            self.rebuild_needed = True
        else:
            self.old_casters.remove(caster)

    def start_update(self):
        if self.nb_updates == 0:
            self.old_casters = self.casters
            self.casters = []
            self.rebuild_needed = False
        self.nb_updates += 1

    def end_update(self):
        self.nb_updates -= 1
        if self.nb_updates == 0:
            for caster in self.old_casters:
                print("Remove shadow caster", caster.name, "on", self.target.owner.get_name())
                shadow_shader = self.shader_components[caster]
                self.target.shader.remove_shadows(self.target.shape, self.target.appearance, shadow_shader)
                del self.shader_components[caster]
                data_source = self.data_sources[caster]
                self.target.sources.remove_source(data_source)
                self.rebuild_needed = True
            self.old_casters = []
        return self.rebuild_needed

class MultiShadows(ShadowBase):
    def __init__(self, target):
        self.target = target
        self.ring_shadow = None
        self.sphere_shadows = SphereShadows()
        self.generic_shadows = GenericShadows(target)
        self.rebuild_needed = False
        self.had_sphere_occluder = False
        self.nb_updates = 0

    def clear_shadows(self):
        self.ring_shadow = None
        self.sphere_shadows.clear()
        self.shadow_map = None
        self.target.shader.remove_all_shadows(self.target.shape, self.target.appearance)
        self.rebuild_needed = True
        self.had_sphere_occluder = False

    def start_update(self):
        if self.nb_updates == 0:
            self.had_sphere_occluder = not self.sphere_shadows.empty()
            self.sphere_shadows.clear()
            self.generic_shadows.start_update()
        self.nb_updates += 1

    def end_update(self):
        self.nb_updates -= 1
        if self.nb_updates == 0:
            if self.sphere_shadows.empty() and self.had_sphere_occluder:
                print("Remove sphere shadow component")
                self.target.shader.remove_shadows(self.target.shape, self.target.appearance, self.sphere_shadows.shader_component)
                self.target.sources.remove_source(self.sphere_shadows.data_source)
                self.rebuild_needed = True
            elif not self.had_sphere_occluder and not self.sphere_shadows.empty():
                self.target.shader.add_shadows(self.sphere_shadows.shader_component)
                self.target.sources.add_source(self.sphere_shadows.data_source)
                print("Add sphere shadow component")
                self.rebuild_needed = True
            self.rebuild_needed = self.generic_shadows.end_update() or self.rebuild_needed

    def add_ring_occluder(self, shadow_caster):
        if self.ring_shadow is None:
            print("Add ring shadow component")
            self.ring_shadow = shadow_caster
            self.target.shader.add_shadows(ShaderRingShadow())
            self.target.sources.add_source(RingShadowDataSource(self.ring_shadow.ring))
            self.rebuild_needed = True
        elif self.ring_shadow != shadow_caster:
            print("Can not switch ring shadow caster")

    def add_sphere_occluder(self, shadow_caster):
        self.sphere_shadows.add_shadow_caster(shadow_caster)

    def add_generic_occluder(self, occluder, self_shadow):
        self.generic_shadows.add_occluder(occluder, self_shadow)
