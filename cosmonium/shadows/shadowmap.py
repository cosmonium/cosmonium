#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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

"""Standard shadow map implementation.

This module provides standard orthographic shadow mapping classes for
directional lights with single shadow maps.
"""

import builtins
from panda3d.core import GraphicsOutput, Camera, NodePath, LQuaterniond
from panda3d.core import Texture, OrthographicLens
from panda3d.core import LPoint3, LPoint3d, LVector3, LVector3d
from panda3d.core import ColorWriteAttrib, CullFaceAttrib, RenderState
from typing import Optional

from ..entities.datasource import DataSource
from ..foundation import BaseObject
from ..shaders.shadows.shadowmap import ShaderShadowMap
from .. import settings

from .base import ShadowCasterBase
from .projector import ShadowProjector
from .buffer_creator import ShadowMapBufferCreator


class ShadowMapBase:
    """Base class for shadow map management.

    This class provides the foundation for shadow mapping by integrating
    with the ShadowMapBufferCreator for buffer creation.

    :ivar base: Reference to the Panda3D base application
    :ivar buffer_creator: ShadowMapBufferCreator instance for buffer creation
    """

    def __init__(self) -> None:
        """Initialize shadow map base with mapper strategy."""
        self.base = builtins.base
        self.buffer_creator = ShadowMapBufferCreator()


class ShadowMap(ShadowMapBase):
    """Standard shadow map implementation.

    Uses ShadowMapper for buffer creation and ShadowProjector for
    camera alignment and projection calculations.

    :ivar size: Resolution of the shadow map
    :ivar buffer: Graphics buffer for shadow rendering
    :ivar depthmap: Depth texture storing shadow data
    :ivar cam: Shadow camera node path
    :ivar node: Shadow camera node
    :ivar snap_cam: Whether to snap camera to texel grid
    :ivar shadow_projector: Projector for frustum calculations
    """

    def __init__(self, size: int) -> None:
        """Initialize shadow map with specified resolution.

        :param size: Size of the square shadow map in pixels
        """
        ShadowMapBase.__init__(self)
        self.size = size
        self.buffer: Optional[GraphicsOutput] = None
        self.depthmap: Optional[Texture] = None
        self.cam: Optional[NodePath] = None
        self.node: Optional[Camera] = None
        self.snap_cam = settings.shadows_snap_cam
        self.debug_shadow_map_texture: bool = settings.debug_shadow_map_texture
        self.shadow_projector = ShadowProjector()

    def create(self, scene_anchor: object) -> None:
        """Create shadow map resources.

        :param scene_anchor: Scene anchor for attaching shadow camera
        """
        self.buffer, self.depthmap = self.buffer_creator.create_simple_shadow_buffer(
            self.size, "shadow-buffer", color_tex=self.debug_shadow_map_texture
        )

        cam = Camera("shadow-cam")
        self.cam = scene_anchor.unshifted_instance.attach_new_node(cam)
        self.node = self.cam.node()
        cam.set_lens(OrthographicLens())
        dr = self.buffer.make_display_region(0, 1, 0, 1)
        dr.disable_clears()
        dr.set_scissor_enabled(False)
        dr.set_camera(self.cam)
        cam.set_scene(scene_anchor.unshifted_instance)

        # TODO: Find a better way to retrieve common render state
        common_state = builtins.base.common_state.get_state()
        if self.debug_shadow_map_texture:
            state = RenderState.make(CullFaceAttrib.make_reverse())
        else:
            state = common_state.make(
                CullFaceAttrib.make_reverse(),
                ColorWriteAttrib.make(ColorWriteAttrib.M_none),
            )
        initial_state = common_state.compose(state)
        self.node.set_initial_state(initial_state)
        if settings.debug_shadow_frustum:
            self.node.show_frustum()

    def align_cam(self) -> None:
        """Align camera to texel grid using shadow projector."""
        self.shadow_projector.align_shadow_camera(self.base.render, self.cam, self.size, self.get_lens())

    def set_lens(self, size: float, near: float, far: float, direction: LVector3d) -> None:
        """Configure shadow camera lens.

        :param size: Film size (frustum size)
        :param near: Near plane distance
        :param far: Far plane distance
        :param direction: View direction
        """
        lens = self.node.get_lens()
        lens.set_film_size(size)
        lens.set_near_far(near, far)
        lens.set_view_vector(LVector3(*direction), LVector3.up())

    def get_lens(self) -> object:
        """Get shadow camera lens.

        :return: Camera lens
        """
        return self.node.get_lens()

    def set_direction(self, direction: LVector3d) -> None:
        """Set shadow camera view direction.

        :param direction: View direction vector
        """
        lens = self.node.get_lens()
        lens.set_view_vector(LVector3(*direction), LVector3.up())

    def get_pos(self) -> LPoint3:
        """Get shadow camera position.

        :return: Camera position
        """
        return self.cam.get_pos()

    def set_pos(self, position: LPoint3d) -> None:
        """Set shadow camera position.

        :param position: Camera position
        """
        self.cam.set_pos(LPoint3(*position))
        if self.snap_cam:
            self.align_cam()

    def remove(self) -> None:
        """Remove and cleanup shadow map resources."""
        self.node = None
        self.cam.remove_node()
        self.cam = None
        self.depthmap = None
        self.buffer.set_active(False)
        self.base.graphics_engine.remove_window(self.buffer)
        self.buffer = None


class ShadowMapShadowCaster(ShadowCasterBase):
    """Shadow caster that uses shadow maps for rendering shadows.

    Uses ShadowProjector for computing frustum parameters and managing
    shadow camera projections.

    :ivar occluder: Object casting the shadow
    :ivar entity: Entity owning this caster
    :ivar name: Name of the shadow caster
    :ivar shadow_map: Shadow map instance
    :ivar shadow_camera: Shadow camera node
    :ivar shadow_projector: Projector for frustum calculations
    """

    def __init__(self, light: object, occluder: object, entity: object) -> None:
        """Initialize shadow map shadow caster.

        :param light: Light source
        :param occluder: Object casting shadows
        :param entity: Owner entity
        """
        ShadowCasterBase.__init__(self, light)
        self.occluder = occluder
        self.entity = entity
        self.name = self.occluder.get_ascii_name()
        self.shadow_map: Optional[ShadowMap] = None
        self.shadow_camera: Optional[object] = None
        self.shadow_projector = ShadowProjector()

    def is_analytic(self) -> bool:
        """Check if using analytic shadows.

        :return: False (uses shadow maps)
        """
        return False

    def create_camera(self) -> None:
        """Create shadow camera (to be implemented by subclasses)."""
        pass

    def create(self) -> None:
        """Create shadow resources."""
        if self.shadow_map is not None:
            return
        if not self.entity.instance_ready:
            return
        self.create_camera()
        self.shadow_camera.set_camera_mask(BaseObject.ShadowCameraFlag)
        self.check_settings()

    def remove_camera(self) -> None:
        """Remove shadow camera (to be implemented by subclasses)."""
        pass

    def remove(self) -> None:
        """Remove shadow resources."""
        self.remove_camera()

    def check_settings(self) -> None:
        """Check and apply shadow settings."""
        if self.shadow_map is None:
            return
        if settings.debug_shadow_frustum:
            self.shadow_camera.show_frustum()
        else:
            self.shadow_camera.hide_frustum()

    def is_valid(self) -> bool:
        """Check if shadow caster is valid.

        :return: True if valid
        """
        return self.shadow_map is not None

    def update(self, scene_manager: object) -> None:
        """Update shadow caster for current frame.

        :param scene_manager: Scene manager
        """
        if self.shadow_map is None:
            return
        lens = self.shadow_camera.get_lens()
        radius = self.occluder.get_bounding_radius()
        # Use shadow projector to update lens
        self.shadow_projector.update_lens(lens, radius, LVector3(*self.light.light_direction))


class CustomShadowMapShadowCaster(ShadowMapShadowCaster):
    """Custom shadow map shadow caster with target management.

    :ivar targets: Dictionary of target entities
    """

    def __init__(self, light: object, occluder: object, entity: object) -> None:
        """Initialize custom shadow map shadow caster.

        :param light: Light source
        :param occluder: Object casting shadows
        :param entity: Owner entity
        """
        ShadowMapShadowCaster.__init__(self, light, occluder, entity)
        self.targets = {}

    def create_camera(self) -> None:
        """Create shadow camera and shadow map."""
        print("Create shadow camera for", self.occluder.get_name())
        self.shadow_map = ShadowMap(settings.shadow_size)
        self.shadow_map.create(self.occluder.scene_anchor)
        self.shadow_camera = self.shadow_map.node

    def remove_camera(self) -> None:
        """Remove shadow camera and shadow map."""
        print("Remove shadow camera for", self.occluder.get_name())
        if self.shadow_map is not None:
            self.shadow_map.remove()
        else:
            print("Removing already removed shadow camera")
        for target in list(self.targets.keys()):
            self.remove_target(target)
        self.shadow_map = None
        self.shadow_camera = None

    def update(self, scene_manager: object) -> None:
        """Update shadow caster and position.

        :param scene_manager: Scene manager
        """
        ShadowMapShadowCaster.update(self, scene_manager)
        if self.shadow_map is not None:
            pos = -self.light.light_direction * self.light.target.get_bounding_radius()
            self.shadow_map.set_pos(pos)

    def create_shader_component(self, self_shadow: bool) -> ShaderShadowMap:
        """Create shader component for this shadow caster.

        :param self_shadow: Whether to enable self-shadowing
        :return: Shader shadow map component
        """
        return ShaderShadowMap(self.name, use_bias=self_shadow)

    def create_data_source(self, self_shadow: bool) -> 'ShadowMapDataSource':
        """Create data source for shader uniforms.

        :param self_shadow: Whether to enable self-shadowing
        :return: Shadow map data source
        """
        return ShadowMapDataSource(self.name, self, use_bias=self_shadow, calculate_shadow_coef=True)

    def add_target(self, entity: object, self_shadow: bool = False) -> None:
        """Add target entity to receive shadows.

        :param entity: Target entity
        :param self_shadow: Enable self-shadowing
        """
        entity.shadows.add_shadow_map_shadow_caster(self, self_shadow)


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


class ShadowMapDataSource(DataSource):
    """Data source for shadow map shader uniforms.

    :ivar name: Name of the shadow map
    :ivar caster: Shadow caster instance
    :ivar use_bias: Whether to use shadow bias
    :ivar calculate_shadow_coef: Whether to calculate shadow coefficient
    """

    def __init__(self, name: str, caster: ShadowMapShadowCaster, use_bias: bool, calculate_shadow_coef: bool) -> None:
        """Initialize shadow map data source.

        :param name: Name identifier
        :param caster: Shadow caster
        :param use_bias: Enable shadow bias
        :param calculate_shadow_coef: Enable shadow coefficient calculation
        """
        DataSource.__init__(self, 'shadowmap-' + name)
        self.name = name
        self.caster = caster
        self.use_bias = use_bias
        self.calculate_shadow_coef = calculate_shadow_coef

    def apply(self, shape: object, instance: NodePath) -> None:
        """Apply shadow map to shape instance.

        :param shape: Shape to apply shadows to
        :param instance: Instance node
        """
        instance.set_shader_input('%s_depthmap' % self.name, self.caster.shadow_map.depthmap)
        instance.set_shader_input("%sLightSource" % self.name, self.caster.shadow_map.cam)
        if not self.calculate_shadow_coef or self.caster.occluder is None:
            instance.set_shader_input('%s_shadow_coef' % self.name, 1.0)

    def update(self, shape: object, instance: NodePath, camera_pos: LPoint3d, camera_rot: LQuaterniond) -> None:
        """Update shadow parameters for current frame.

        :param shape: Shape receiving shadows
        :param instance: Instance node
        :param camera_pos: Camera position
        :param camera_rot: Camera rotation
        """
        from math import asin, pi

        appearance = shape.parent.appearance
        if self.use_bias:
            scale = 1.0 / 100.0 * shape.owner.scene_anchor.scene_scale_factor * shape.owner.get_apparent_radius()
            normal_bias = appearance.shadow_normal_bias * scale
            slope_bias = appearance.shadow_slope_bias * scale
            depth_bias = appearance.shadow_depth_bias * scale
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

    def clear_shape_data(self, shape: object, instance: NodePath) -> None:
        """Clear shadow data from shape instance.

        :param shape: Shape to clear
        :param instance: Instance node
        """
        instance.clearShaderInput('%s_depthmap' % self.name)
        instance.clearShaderInput("%sLightSource" % self.name)
