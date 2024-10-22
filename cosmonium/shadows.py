#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


import builtins
from direct.showbase.ShowBaseGlobal import globalClock
from math import asin, pi
from panda3d.core import WindowProperties, FrameBufferProperties, GraphicsPipe, GraphicsOutput, Camera
from panda3d.core import Texture, OrthographicLens
from panda3d.core import LVector3, LPoint3, LVector3d, LPoint4, Mat4
from panda3d.core import ColorWriteAttrib, LColor, CullFaceAttrib, RenderState
from panda3d.core import LMatrix4, PTA_LMatrix4, LQuaternion
from panda3d._rplight import PSSMCameraRig

from .foundation import BaseObject
from .datasource import DataSource
from .shaders.shadows.pssm import ShaderPSSMShadowMap
from .shaders.shadows.shadowmap import ShaderShadowMap
from .shaders.shadows.rings import ShaderRingsShadow
from .shaders.shadows.ellipsoid import ShaderSphereShadow

from . import settings


class ShadowMapBase:

    def __init__(self):
        self.base = builtins.base

    def create_render_buffer(self, size_x, size_y, depth_bits, depth_tex):
        # Boilerplate code to create a render buffer producing only a depth texture
        window_props = WindowProperties.size(size_x, size_y)
        buffer_props = FrameBufferProperties()

        if False:
            buffer_props.set_rgba_bits(0, 0, 0, 0)
        else:
            buffer_props.set_rgba_bits(8, 8, 8, 8)
        buffer_props.set_accum_bits(0)
        buffer_props.set_stencil_bits(0)
        buffer_props.set_back_buffers(0)
        buffer_props.set_coverage_samples(0)
        buffer_props.set_depth_bits(depth_bits)

        if depth_bits == 32:
            buffer_props.set_float_depth(True)

        buffer_props.set_force_hardware(True)
        buffer_props.set_multisamples(0)
        buffer_props.set_srgb_color(False)
        buffer_props.set_stereo(False)
        buffer_props.set_stencil_bits(0)

        self.win = self.base.win
        self.graphics_engine = self.base.graphics_engine
        buffer = self.graphics_engine.make_output(
            self.win.get_pipe(),
            "pssm_buffer",
            1,
            buffer_props,
            window_props,
            GraphicsPipe.BF_refuse_window,
            self.win.gsg,
            self.win,
        )

        if buffer is None:
            print("Failed to create buffer")
            return

        buffer.add_render_texture(depth_tex, GraphicsOutput.RTM_bind_or_copy, GraphicsOutput.RTP_depth)

        if True:
            color = Texture()
            buffer.add_render_texture(color, GraphicsOutput.RTM_bind_or_copy, GraphicsOutput.RTP_color)
            buffer.setClearColor((1, 1, 1, 1))
            buffer.setClearColorActive(True)

        buffer.set_sort(-1000)
        # buffer.disable_clears()
        buffer.get_display_region(0).disable_clears()
        buffer.get_overlay_display_region().disable_clears()
        buffer.get_overlay_display_region().set_active(False)

        return buffer


class ShadowMap(ShadowMapBase):

    def __init__(self, size):
        ShadowMapBase.__init__(self)
        self.size = size
        self.buffer = None
        self.depthmap = None
        self.cam = None
        self.snap_cam = settings.shadows_snap_cam

    def create(self, scene_anchor):
        winprops = WindowProperties.size(self.size, self.size)
        props = FrameBufferProperties()
        props.set_rgb_color(0)
        props.set_alpha_bits(0)
        props.set_depth_bits(1)
        win = self.base.win
        self.buffer = self.base.graphics_engine.make_output(
            win.get_pipe(), "shadows-buffer", -2, props, winprops, GraphicsPipe.BF_refuse_window, win.get_gsg(), win
        )

        if not self.buffer:
            print("Video driver cannot create an offscreen buffer.")
            return
        self.depthmap = Texture()
        self.buffer.add_render_texture(
            self.depthmap, GraphicsOutput.RTM_bind_or_copy, GraphicsOutput.RTP_depth_stencil
        )

        self.depthmap.set_minfilter(Texture.FT_shadow)
        self.depthmap.set_magfilter(Texture.FT_shadow)
        self.depthmap.set_border_color(LColor(1, 1, 1, 1))
        self.depthmap.set_wrap_u(Texture.WM_border_color)
        self.depthmap.set_wrap_v(Texture.WM_border_color)

        cam = Camera("shadow-cam")
        self.cam = scene_anchor.unshifted_instance.attach_new_node(cam)
        cam.set_lens(OrthographicLens())
        dr = self.buffer.make_display_region(0, 1, 0, 1)
        dr.disable_clears()
        dr.set_scissor_enabled(False)
        dr.set_camera(self.cam)
        # Don't use set_scene, the scene of the display region will be the root node of the camera
        # and will be automatically updated

        self.node = self.cam.node()
        self.node.setInitialState(
            RenderState.make(
                CullFaceAttrib.make_reverse(),
                ColorWriteAttrib.make(ColorWriteAttrib.M_none),
            )
        )
        if settings.debug_shadow_frustum:
            self.node.show_frustum()

    def align_cam(self):
        mvp = Mat4(self.base.render.get_transform(self.cam).get_mat() * self.get_lens().get_projection_mat())
        center = mvp.xform(LPoint4(0, 0, 0, 1)) * 0.5 + 0.5
        texel_size = 1.0 / self.size
        offset_x = center.x % texel_size
        offset_y = center.y % texel_size
        mvp.invert_in_place()
        new_center = mvp.xform(
            LPoint4((center.x - offset_x) * 2.0 - 1.0, (center.y - offset_y) * 2.0 - 1.0, (center.z) * 2.0 - 1.0, 1.0)
        )
        self.cam.set_pos(self.cam.get_pos() - LVector3(new_center.x, new_center.y, new_center.z))

    def set_lens(self, size, near, far, direction):
        lens = self.node.get_lens()
        lens.set_film_size(size)
        lens.set_near_far(near, far)
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
        self.base.graphics_engine.remove_window(self.buffer)
        self.buffer = None


class PSSMShadowMap(ShadowMapBase):

    def __init__(self, size):
        ShadowMapBase.__init__(self)
        self.size = size
        self.buffer = None
        self.depthmap = None
        self.camera_rig = None
        self.split_regions = []
        # Basic PSSM configuration
        self.num_splits = 5
        self.border_bias = 0.058
        self.fixed_bias = 0.5
        self.last_cache_reset = globalClock.get_frame_time()

    def create(self, scene_anchor):
        self.create_camera_rig(scene_anchor)
        self.create_pssm_buffer()
        self.attach_pssm_camera_rig()

    def create_camera_rig(self, scene_anchor):
        # Construct the actual PSSM rig
        self.camera_rig = PSSMCameraRig(self.num_splits)
        # Set the max distance from the camera where shadows are rendered
        self.camera_rig.set_pssm_distance(1024)
        # Set the distance between the far plane of the frustum and the sun, objects farther do not cas shadows
        self.camera_rig.set_sun_distance(1024)
        # Set the logarithmic factor that defines the splits
        self.camera_rig.set_logarithmic_factor(2.4)

        self.camera_rig.set_border_bias(self.border_bias)
        # Enable CSM splits snapping to avoid shadows flickering when moving
        self.camera_rig.set_use_stable_csm(True)
        # Keep the film size roughly constant to avoid flickering when moving
        self.camera_rig.set_use_fixed_film_size(True)
        # Set the resolution of each split shadow map
        self.camera_rig.set_resolution(self.size)
        # Attach the camera rig to the root of the current scene
        # TODO: This does not work with RegionSceneManager
        self.camera_rig.reparent_to(self.base.scene_manager.root)

    def attach_pssm_camera_rig(self):
        # Attach the cameras to the shadow stage
        for i in range(self.num_splits):
            camera_np = self.camera_rig.get_camera(i)
            self.split_regions[i].set_camera(camera_np)
            if settings.debug_shadow_frustum:
                camera_np.node().show_frustum()
                camera_np.hide(BaseObject.AllCamerasMask)
                camera_np.show(BaseObject.DefaultCameraFlag)

    def create_pssm_buffer(self):
        # Create the depth buffer
        # The depth buffer is the concatenation of num_splits shadow maps
        self.depthmap = Texture("PSSMShadowMap")
        self.buffer = self.create_render_buffer(self.size * self.num_splits, self.size, 32, self.depthmap)

        # Remove all unused display regions
        self.buffer.remove_all_display_regions()
        self.buffer.get_display_region(0).set_active(False)
        # self.buffer.disable_clears()

        # Set a clear on the buffer instead on all regions
        self.buffer.set_clear_depth(1)
        self.buffer.set_clear_depth_active(True)

        # Prepare the display regions, one for each split
        for i in range(self.num_splits):
            region = self.buffer.make_display_region(
                i / self.num_splits, i / self.num_splits + 1 / self.num_splits, 0, 1
            )
            region.set_sort(25 + i)
            # Clears are done on the buffer
            region.disable_clears()
            region.set_active(True)
            self.split_regions.append(region)

    def update(self, camera_np, light_dir):
        if settings.debug_lod_freeze:
            return
        self.camera_rig.update(camera_np, -light_dir)
        cache_diff = globalClock.get_frame_time() - self.last_cache_reset
        if cache_diff > 5.0:
            self.last_cache_reset = globalClock.get_frame_time()
            self.camera_rig.reset_film_size_cache()

    def remove(self):
        # TODO
        pass


class ShadowCasterBase(object):

    def __init__(self, light):
        self.light = light

    def is_analytic(self):
        pass

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

    def update(self, scene_manager):
        pass


class ShadowMapShadowCaster(ShadowCasterBase):

    def __init__(self, light, occluder, shape_object):
        ShadowCasterBase.__init__(self, light)
        self.occluder = occluder
        self.shape_object = shape_object
        self.name = self.occluder.get_ascii_name()
        self.shadow_map = None
        self.shadow_camera = None

    def is_analytic(self):
        return False

    def create_camera(self):
        pass

    def create(self):
        if self.shadow_map is not None:
            return
        if not self.shape_object.instance_ready:
            return
        self.create_camera()
        self.shadow_camera.set_camera_mask(BaseObject.ShadowCameraFlag)
        self.check_settings()

    def remove_camera(self):
        pass

    def remove(self):
        self.remove_camera()

    def check_settings(self):
        if self.shadow_map is None:
            return
        if settings.debug_shadow_frustum:
            self.shadow_camera.show_frustum()
        else:
            self.shadow_camera.hide_frustum()

    def is_valid(self):
        return self.shadow_map is not None

    def update(self, scene_manager):
        if self.shadow_map is None:
            return
        radius = self.occluder.get_bounding_radius()
        self.shadow_camera.get_lens().set_film_size(radius * 2.1, radius * 2.1)
        # The shadow frustum origin is at the light center which is one radius away from the object
        # So the near plane is 0 to coincide with the boundary of the object
        self.shadow_camera.get_lens().set_near(0)
        self.shadow_camera.get_lens().set_far(radius * 2)
        self.shadow_camera.get_lens().set_view_vector(LVector3(*self.light.light_direction), LVector3.up())


class ShadowMapDataSource(DataSource):

    def __init__(self, name, caster, use_bias, calculate_shadow_coef):
        DataSource.__init__(self, 'shadowmap-' + name)
        self.name = name
        self.caster = caster
        self.use_bias = use_bias
        self.calculate_shadow_coef = calculate_shadow_coef

    def apply(self, shape, instance):
        shape.instance.set_shader_input('%s_depthmap' % self.name, self.caster.shadow_map.depthmap)
        shape.instance.set_shader_input("%sLightSource" % self.name, self.caster.shadow_map.cam)
        if not self.calculate_shadow_coef or self.caster.occluder is None:
            shape.instance.set_shader_input('%s_shadow_coef' % self.name, 1.0)

    def update(self, shape, instance, camera_pos, camera_rot):
        # TODO: Shadow parameters should not be retrieved like that
        appearance = shape.parent.appearance
        if self.use_bias:
            scale = 1.0 / 100.0 * shape.owner.scene_anchor.scene_scale_factor * shape.owner.get_apparent_radius()
            normal_bias = appearance.shadow_normal_bias * scale
            slope_bias = appearance.shadow_slope_bias * scale
            depth_bias = appearance.shadow_depth_bias * scale
            # print(
            #     normal_bias, slope_bias, depth_bias,
            #     shape.owner.anchor.scene_scale_factor, shape.owner.get_apparent_radius())
            instance.set_shader_input('%s_shadow_normal_bias' % self.name, normal_bias)
            instance.set_shader_input('%s_shadow_slope_bias' % self.name, slope_bias)
            instance.set_shader_input('%s_shadow_depth_bias' % self.name, depth_bias)
        if self.calculate_shadow_coef and self.caster.occluder is not None:
            light = self.caster.light
            occluder = self.caster.occluder
            body = shape.owner
            self_radius = occluder.get_apparent_radius()
            body_radius = body.get_apparent_radius()
            position = occluder.anchor.get_local_position()
            body_position = body.anchor.get_local_position()
            pa = body_position - position
            distance = abs(pa.length() - body_radius)
            if distance != 0:
                self_ar = asin(self_radius / distance) if self_radius < distance else pi / 2
                star_ar = asin(
                    light.source.get_apparent_radius()
                    / ((light.source.anchor.get_local_position() - body_position).length() - body_radius)
                )
                ar_ratio = self_ar / star_ar
            else:
                ar_ratio = 1.0
        else:
            ar_ratio = 1.0
        instance.set_shader_input('%s_shadow_coef' % self.name, min(max(ar_ratio * ar_ratio, 0.0), 1.0))

    def clear_shape_data(self, shape, instance):
        instance.clearShaderInput('%s_depthmap' % self.name)
        instance.clearShaderInput("%sLightSource" % self.name)


class PandaShadowMapShadowCaster(ShadowMapShadowCaster):

    def create_camera(self):
        print("Create Panda3D shadow camera for", self.occluder.get_name())
        self.light.setShadowCaster(True, settings.shadow_size, settings.shadow_size)
        self.shadow_map = self.directional_light
        self.shadow_camera = self.directional_light

    def remove_camera(self):
        print("Remove Panda3D shadow camera for", self.occluder.get_name())
        self.light.setShadowCaster(False)
        self.shadow_map = None
        self.shadow_camera = None


class CustomShadowMapShadowCaster(ShadowMapShadowCaster):

    def __init__(self, light, occluder, shape_object):
        ShadowMapShadowCaster.__init__(self, light, occluder, shape_object)
        self.targets = {}

    def create_camera(self):
        print("Create shadow camera for", self.occluder.get_name())
        self.shadow_map = ShadowMap(settings.shadow_size)
        self.shadow_map.create(self.occluder.scene_anchor)
        self.shadow_camera = self.shadow_map.node

    def remove_camera(self):
        print("Remove shadow camera for", self.occluder.get_name())
        if self.shadow_map is not None:
            self.shadow_map.remove()
        else:
            print("Removing already removed shadow camera")
        for target in list(self.targets.keys()):
            self.remove_target(target)
        self.shadow_map = None
        self.shadow_camera = None

    def update(self, scene_manager):
        ShadowMapShadowCaster.update(self, scene_manager)
        if self.shadow_map is not None:
            pos = -self.light.light_direction * self.light.target.get_bounding_radius()
            self.shadow_map.set_pos(pos)

    def create_shader_component(self, self_shadow):
        return ShaderShadowMap(self.name, use_bias=self_shadow)

    def create_data_source(self, self_shadow):
        return ShadowMapDataSource(self.name, self, use_bias=self_shadow, calculate_shadow_coef=True)

    def add_target(self, shape_object, self_shadow=False):
        shape_object.shadows.add_shadow_map_shadow_caster(self, self_shadow)


class PSSMShadowMapShadowCaster(ShadowCasterBase):

    def __init__(self, light, occluder):
        ShadowCasterBase.__init__(self, light)
        self.occluder = occluder
        self.name = self.occluder.get_ascii_name()
        self.shadow_map = None

    def is_analytic(self):
        return False

    def create(self):
        if self.shadow_map is not None:
            return
        self.shadow_map = PSSMShadowMap(settings.shadow_size)
        self.shadow_map.create(self.occluder.scene_anchor)
        for i in range(self.shadow_map.num_splits):
            camera_np = self.shadow_map.camera_rig.get_camera(i)
            camera_np.node().set_camera_mask(BaseObject.ShadowCameraFlag)

    def remove(self):
        self.shadow_map.remove()
        self.shadow_map = None

    def check_settings(self):
        return
        if settings.debug_shadow_frustum:
            self.shadow_camera.show_frustum()
        else:
            self.shadow_camera.hide_frustum()

    def is_valid(self):
        return self.shadow_map is not None

    def update(self, scene_manager):
        self.shadow_map.update(scene_manager.camera, LVector3(*self.light.light_direction))

    def create_shader_component(self, self_shadow):
        return ShaderPSSMShadowMap(self.name)

    def create_data_source(self, self_shadow):
        return PSSMShadowMapDataSource(self.name, self)

    def add_target(self, shape_object):
        shape_object.shadows.add_shadow_map_shadow_caster(self, self_shadow=False)


class PSSMShadowMapDataSource(DataSource):

    def __init__(self, name, caster):
        DataSource.__init__(self, 'pssmshadowmap-' + name)
        self.name = name
        self.caster = caster

    def apply(self, shape, instance):
        src_mvp_array = self.caster.shadow_map.camera_rig.get_mvp_array()
        mvp_array = PTA_LMatrix4()
        for array in src_mvp_array:
            mvp_array.push_back(array)
        instance.set_shader_inputs(
            PSSMShadowAtlas=self.caster.shadow_map.depthmap,
            pssm_mvps=mvp_array,
            border_bias=self.caster.shadow_map.border_bias,
            fixed_bias=self.caster.shadow_map.fixed_bias,
        )

    def update(self, shape, instance, camera_pos, camera_rot):
        pssm = self.caster.shadow_map
        src_mvp_array = pssm.camera_rig.get_mvp_array()
        mvp_array = PTA_LMatrix4()
        for array in src_mvp_array:
            mvp_array.push_back(array)
        instance.set_shader_inputs(pssm_mvps=mvp_array)

    def clear_shape_data(self, shape, instance):
        instance.clear_shader_input('pssm_mvps')


class RingShadowCaster(ShadowCasterBase):

    def __init__(self, light, ring):
        ShadowCasterBase.__init__(self, light)
        self.ring = ring

    def is_analytic(self):
        # Although ring shadows are analytic, ity still requires the ring texture.
        # So we need to return False here to force the texture loading
        return False

    def add_target(self, shape_object):
        shape_object.shadows.add_ring_shadow_caster(self)


class RingShadowDataSource(DataSource):

    def __init__(self, ring):
        DataSource.__init__(self, 'ring-shadow')
        self.ring = ring

    def update(self, shape, instance, camera_pos, camera_rot):
        (texture, texture_size, texture_lod) = self.ring.appearance.texture.source.get_texture(self.ring.shape)
        if texture is not None:
            instance.set_shader_input('shadow_ring_tex', texture)
        normal = shape.owner.anchor.get_absolute_orientation().xform(LVector3d.up())
        instance.set_shader_input('ring_normal', normal)
        instance.set_shader_input(
            'ring_inner_radius', self.ring.inner_radius * shape.owner.scene_anchor.scene_scale_factor
        )
        instance.set_shader_input(
            'ring_outer_radius', self.ring.outer_radius * shape.owner.scene_anchor.scene_scale_factor
        )
        if shape.owner.support_offset_body_center and settings.offset_body_center:
            body_center = shape.owner.scene_anchor.scene_position + shape.owner.scene_anchor.world_body_center_offset
        else:
            body_center = shape.owner.scene_anchor.scene_position
        instance.set_shader_input('body_center', body_center)


class SphereShadowCaster(ShadowCasterBase):

    def __init__(self, light, occluder):
        ShadowCasterBase.__init__(self, light)
        self.occluder = occluder

    def is_analytic(self):
        return True

    def add_target(self, shape_object):
        shape_object.shadows.add_sphere_shadow_caster(self)


class SphereShadowDataSource(DataSource):

    def __init__(self, shadow_casters, max_occluders, far_sun, oblate_occluder):
        DataSource.__init__(self, 'sphere-shadows')
        self.shadow_casters = shadow_casters
        self.max_occluders = max_occluders
        self.far_sun = far_sun
        self.oblate_occluder = oblate_occluder

    def update(self, shape, instance, camera_pos, camera_rot):
        if len(self.shadow_casters.shadow_casters) == 0:
            print("ERROR: No lights for", shape, shape.owner.get_name())
            return
        self.light = self.shadow_casters.shadow_casters[0].light
        scale = shape.owner.scene_anchor.scene_scale_factor
        if self.far_sun:
            vector = shape.owner.anchor.get_local_position() - self.light.source.anchor.get_local_position()
            distance_to_light_source = vector.length()
            instance.set_shader_input(
                'star_ar', asin(self.light.source.get_apparent_radius() / distance_to_light_source)
            )
        star_center = (self.light.source.anchor.get_local_position() - camera_pos) * scale
        star_radius = self.light.source.get_apparent_radius() * scale
        instance.set_shader_input('star_center', star_center)
        instance.set_shader_input('star_radius', star_radius)
        centers = []
        radii = []
        occluder_transform = PTA_LMatrix4()
        if len(self.shadow_casters.shadow_casters) > self.max_occluders:
            print("Too many occluders")
        nb_of_occluders = 0
        for shadow_caster in self.shadow_casters.shadow_casters:
            # TODO: The selection should be done on the angular radius of the shadow.
            if nb_of_occluders >= self.max_occluders:
                break
            nb_of_occluders += 1
            occluder = shadow_caster.occluder
            centers.append((occluder.anchor.get_local_position() - camera_pos) * scale)
            radius = occluder.get_apparent_radius()
            radii.append(radius * scale)
            if self.oblate_occluder:
                # TODO: This should refactored with the code in oneil and moved to the body class
                body_scale = occluder.surface.get_shape_axes()
                descale = LMatrix4.scale_mat(radius / body_scale[0], radius / body_scale[1], radius / body_scale[2])
                rotation_mat = LMatrix4()
                orientation = LQuaternion(*occluder.anchor.get_absolute_orientation())
                orientation.extract_to_matrix(rotation_mat)
                rotation_mat_inv = LMatrix4()
                rotation_mat_inv.invert_from(rotation_mat)
                descale_mat = rotation_mat_inv * descale * rotation_mat
                occluder_transform.push_back(descale_mat)
        instance.set_shader_input('occluder_centers', centers)
        instance.set_shader_input('occluder_radii', radii)
        if self.oblate_occluder:
            instance.set_shader_input('occluder_transform', occluder_transform)
        instance.set_shader_input("nb_of_occluders", nb_of_occluders)


class ShadowBase(object):
    pass


class SphereShadows(ShadowBase):

    def __init__(self, target):
        self.target = target
        self.shadow_casters = []
        self.max_occluders = 4
        self.far_sun = True
        self.oblate_occluder = True
        self.shader_component = ShaderSphereShadow(self.max_occluders, self.far_sun, self.oblate_occluder)
        self.data_source = SphereShadowDataSource(self, self.max_occluders, self.far_sun, self.oblate_occluder)
        self.nb_updates = 0

    def add_shadow_caster(self, shadow_caster):
        if shadow_caster not in self.shadow_casters:
            self.shadow_casters.append(shadow_caster)

    def empty(self):
        return len(self.shadow_casters) == 0

    def clear_shadows(self):
        if len(self.shadow_casters) > 0:
            self.target.sources.remove_source(self.data_source)
        self.shadow_casters = []

    def start_update(self):
        if self.nb_updates == 0:
            self.had_sphere_occluder = not self.empty()
            self.shadow_casters = []
            self.rebuild_needed = False
        self.nb_updates += 1

    def end_update(self):
        self.nb_updates -= 1
        if self.nb_updates == 0:
            if self.empty() and self.had_sphere_occluder:
                print("Remove sphere shadow component on", self.target.owner.get_friendly_name())
                self.target.shader.remove_shadows(self.target.shape, self.target.appearance, self.shader_component)
                self.target.sources.remove_source(self.data_source)
                self.rebuild_needed = True
            elif not self.had_sphere_occluder and not self.empty():
                self.target.shader.add_shadows(self.shader_component)
                self.target.sources.add_source(self.data_source)
                print("Add sphere shadow component on", self.target.owner.get_friendly_name())
                self.rebuild_needed = True
        return self.rebuild_needed


class ShadowMapShadows(ShadowBase):

    def __init__(self, target):
        self.target = target
        self.casters = []
        self.old_casters = []
        self.shader_components = {}
        self.data_sources = {}
        self.rebuild_needed = False
        self.nb_updates = 0

    def add_shadow_caster(self, caster, self_shadow):
        if not caster.is_valid():
            return
        self.casters.append(caster)
        if caster not in self.old_casters:
            print("Add shadow caster", caster.name, "on", self.target.owner.get_friendly_name())
            shadow_shader = caster.create_shader_component(self_shadow)
            self.shader_components[caster] = shadow_shader
            data_source = caster.create_data_source(self_shadow)
            self.target.sources.add_source(data_source)
            self.data_sources[caster] = data_source
            self.target.shader.add_shadows(shadow_shader)
            self.rebuild_needed = True
        else:
            self.old_casters.remove(caster)

    def clear_shadows(self):
        for caster in self.casters:
            data_source = self.data_sources[caster]
            self.target.sources.remove_source(data_source)
        self.casters = []
        self.shader_components = {}
        self.data_sources = {}

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
                print(
                    "Remove shadow caster",
                    caster.name,
                    "on",
                    self.target.owner.get_name(),
                    self.target.get_name() or '',
                )
                shadow_shader = self.shader_components[caster]
                self.target.shader.remove_shadows(self.target.shape, self.target.appearance, shadow_shader)
                del self.shader_components[caster]
                data_source = self.data_sources[caster]
                self.target.sources.remove_source(data_source)
                del self.data_sources[caster]
                self.rebuild_needed = True
            self.old_casters = []
        return self.rebuild_needed


class MultiShadows(ShadowBase):

    def __init__(self, target):
        self.target = target
        self.ring_shadow = None
        self.sphere_shadows = SphereShadows(target)
        self.shadow_map_shadows = ShadowMapShadows(target)
        self.rebuild_needed = False
        self.had_sphere_occluder = False
        self.nb_updates = 0

    def clear_shadows(self):
        self.sphere_shadows.clear_shadows()
        self.shadow_map_shadows.clear_shadows()
        self.target.sources.remove_source_by_name('ring-shadow')
        self.ring_shadow = None
        self.shadow_map = None
        self.target.shader.remove_all_shadows(self.target.shape, self.target.appearance)
        self.rebuild_needed = True
        self.had_sphere_occluder = False

    def start_update(self):
        if self.nb_updates == 0:
            self.had_sphere_occluder = not self.sphere_shadows.empty()
            self.sphere_shadows.start_update()
            self.shadow_map_shadows.start_update()
        self.nb_updates += 1

    def end_update(self):
        self.nb_updates -= 1
        if self.nb_updates == 0:
            shadow_map_rebuild_needed = self.shadow_map_shadows.end_update()
            sphere_shadows_rebuild_needed = self.sphere_shadows.end_update()
            self.rebuild_needed = shadow_map_rebuild_needed or sphere_shadows_rebuild_needed

    def add_ring_shadow_caster(self, shadow_caster):
        if self.ring_shadow is None:
            print("Add ring shadow component")
            self.ring_shadow = shadow_caster
            self.target.shader.add_shadows(ShaderRingsShadow())
            self.target.sources.add_source(RingShadowDataSource(self.ring_shadow.ring))
            self.rebuild_needed = True
        elif self.ring_shadow != shadow_caster:
            print("Can not switch ring shadow caster")

    def add_sphere_shadow_caster(self, shadow_caster):
        self.sphere_shadows.add_shadow_caster(shadow_caster)

    def add_shadow_map_shadow_caster(self, shadow_caster, self_shadow):
        self.shadow_map_shadows.add_shadow_caster(shadow_caster, self_shadow)
