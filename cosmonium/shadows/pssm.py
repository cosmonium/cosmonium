#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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

"""Parallel Split Shadow Maps (PSSM) implementation.

This module provides classes for implementing Parallel Split Shadow Maps,
a technique for rendering high-quality shadows over large distances by
dividing the view frustum into multiple splits.
"""


from direct.showbase.ShowBaseGlobal import globalClock
from panda3d._rplight import PSSMCameraRig
from panda3d.core import LVector3, PTA_LMatrix4, Texture

from .. import settings
from ..entities.datasource import DataSource
from ..foundation import BaseObject
from ..shaders.shadows.pssm import ShaderPSSMShadowMap
from .base import ShadowCasterBase
from .shadowmap import ShadowMapBase


class PSSMShadowMap(ShadowMapBase):
    """Parallel Split Shadow Map implementation.

    Manages the creation and updating of PSSM shadow maps using multiple splits
    for better shadow quality over varying distances.
    """

    def __init__(self, size):
        """Initialize PSSM shadow map.

        Args:
            size: Resolution of each shadow map split.
        """
        ShadowMapBase.__init__(self)
        self.size = size
        self.buffer = None
        self.depthmap = None
        self.debug_texture = None
        self.camera_rig = None
        self.split_regions = []
        # Basic PSSM configuration
        self.num_splits = 5
        self.border_bias = 0.058
        self.fixed_bias = 0.5
        self.last_cache_reset = globalClock.get_frame_time()

    def create(self, scene_anchor):
        """Create PSSM shadow map resources.

        Args:
            scene_anchor: Scene anchor for attaching the camera rig.
        """
        self.create_camera_rig(scene_anchor)
        self.create_pssm_buffer()
        self.attach_pssm_camera_rig()

    def create_camera_rig(self, scene_anchor):
        """Create and configure the PSSM camera rig.

        Args:
            scene_anchor: Scene anchor for attaching the camera rig.
        """
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
        """Attach cameras to the shadow buffer regions."""
        # Attach the cameras to the shadow stage
        for i in range(self.num_splits):
            camera_np = self.camera_rig.get_camera(i)
            self.split_regions[i].set_camera(camera_np)
            if settings.debug_shadow_frustum:
                camera_np.node().show_frustum()
                camera_np.hide(BaseObject.AllCamerasMask)
                camera_np.show(BaseObject.DefaultCameraFlag)

    def create_pssm_buffer(self):
        """Create the PSSM shadow buffer and depth texture."""
        # Create the depth buffer
        # The depth buffer is the concatenation of num_splits shadow maps
        self.depthmap = Texture("PSSMShadowMap")
        if settings.debug_shadow_map_texture:
            self.debug_texture = Texture("PSSMShadowMapDebug")
        self.buffer = self.buffer_creator.create_render_buffer(
            self.size * self.num_splits, self.size, 32, self.depthmap, self.debug_texture
        )

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
        """Update the PSSM camera rig for the current frame.

        Args:
            camera_np: Main camera node path.
            light_dir: Light direction vector.
        """
        if settings.debug_lod_freeze:
            return
        self.camera_rig.update(camera_np, -light_dir)
        cache_diff = globalClock.get_frame_time() - self.last_cache_reset
        if cache_diff > 5.0:
            self.last_cache_reset = globalClock.get_frame_time()
            self.camera_rig.reset_film_size_cache()

    def remove(self):
        """Remove PSSM shadow map resources."""
        # TODO
        pass


class PSSMShadowMapShadowCaster(ShadowCasterBase):
    """Shadow caster using PSSM shadow maps.

    Handles the creation and management of PSSM shadow maps for a given light
    and occluder.
    """

    def __init__(self, light, occluder):
        """Initialize PSSM shadow caster.

        Args:
            light: Light source for casting shadows.
            occluder: Object casting the shadows.
        """
        ShadowCasterBase.__init__(self, light)
        self.occluder = occluder
        self.name = self.occluder.get_ascii_name()
        self.shadow_map = None

    def is_analytic(self):
        """Check if this shadow caster uses analytic shadows.

        Returns:
            False, as PSSM uses shadow maps.
        """
        return False

    def create(self):
        """Create PSSM shadow map resources."""
        if self.shadow_map is not None:
            return
        self.shadow_map = PSSMShadowMap(settings.shadow_size)
        self.shadow_map.create(self.occluder.scene_anchor)
        for i in range(self.shadow_map.num_splits):
            camera_np = self.shadow_map.camera_rig.get_camera(i)
            camera_np.node().set_camera_mask(BaseObject.ShadowCameraFlag)

    def remove(self):
        """Remove PSSM shadow map resources."""
        self.shadow_map.remove()
        self.shadow_map = None

    def check_settings(self):
        """Check and apply shadow settings."""
        return
        if settings.debug_shadow_frustum:
            self.shadow_camera.show_frustum()
        else:
            self.shadow_camera.hide_frustum()

    def is_valid(self):
        """Check if the shadow caster is valid.

        Returns:
            True if shadow map is created, False otherwise.
        """
        return self.shadow_map is not None

    def update(self, scene_manager):
        """Update the shadow caster for the current frame.

        Args:
            scene_manager: Scene manager instance.
        """
        self.shadow_map.update(scene_manager.camera, LVector3(*self.light.light_direction))

    def create_shader_component(self, self_shadow):
        """Create shader component for PSSM shadows.

        Args:
            self_shadow: Whether to enable self-shadowing.

        Returns:
            ShaderPSSMShadowMap instance.
        """
        return ShaderPSSMShadowMap(self.name)

    def create_data_source(self, self_shadow):
        """Create data source for PSSM shader uniforms.

        Args:
            self_shadow: Whether to enable self-shadowing.

        Returns:
            PSSMShadowMapDataSource instance.
        """
        return PSSMShadowMapDataSource(self.name, self)

    def add_target(self, entity):
        """Add target entity to receive PSSM shadows.

        Args:
            entity: Entity to receive shadows.
        """
        entity.shadows.add_shadow_map_shadow_caster(self, self_shadow=False)


class PSSMShadowMapDataSource(DataSource):
    """Data source for PSSM shadow map shader uniforms.

    Provides the necessary uniforms for PSSM shadow mapping in shaders.
    """

    def __init__(self, name, caster):
        """Initialize PSSM data source.

        Args:
            name: Name identifier for the shadow map.
            caster: PSSM shadow caster instance.
        """
        DataSource.__init__(self, 'pssmshadowmap-' + name)
        self.name = name
        self.caster = caster

    def apply(self, shape, instance):
        """Apply PSSM shadow uniforms to the shape instance.

        Args:
            shape: Shape to apply shadows to.
            instance: Node path instance.
        """
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
        """Update PSSM uniforms for the current frame.

        Args:
            shape: Shape receiving shadows.
            instance: Node path instance.
            camera_pos: Camera position.
            camera_rot: Camera rotation.
        """
        pssm = self.caster.shadow_map
        src_mvp_array = pssm.camera_rig.get_mvp_array()
        mvp_array = PTA_LMatrix4()
        for array in src_mvp_array:
            mvp_array.push_back(array)
        instance.set_shader_inputs(pssm_mvps=mvp_array)

    def clear_shape_data(self, shape, instance):
        """Clear PSSM shadow data from the shape instance.

        Args:
            shape: Shape to clear.
            instance: Node path instance.
        """
        instance.clear_shader_input('pssm_mvps')
