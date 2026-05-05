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


from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import LVector3d, NodePath, OmniBoundingVolume

from .. import settings
from ..foundation import VisibleObject
from ..parameters import ParametersGroup
from ..shaders.base import AutoShader
from ..shaders.lighting.scattering import NoScattering
from ..shadows.manager import MultiShadows
from .datasource import DataSourcesHandler
from .shape_controller import PatchedShapeController
from .tasks_tree import TasksTree


class Entity(VisibleObject):
    """Represents a visible object in Cosmonium with shape, appearance, shader, and shadow management.

    Attributes:
        default_camera_mask: Default camera mask flags.
        sources: Handler for shape-related data sources.
        shape: The geometric shape of the entity.
        shape_controller: Controller for shape patches.
        owner: The owner of the entity.
        appearance: Appearance settings for the entity.
        shader: Shader used for rendering.
        clickable: Whether the entity is clickable.
        instance_ready: If the instance is ready for rendering.
        oid_color: Color used for object ID picking.
        shadows: Shadow manager.
        shadow_casters: Shadow casters for light sources.
        task: Task for instance creation.
        body: Physical body of the entity.
        physics: Physics handler.
    """

    default_camera_mask = (
        VisibleObject.DefaultCameraFlag | VisibleObject.WaterCameraFlag | VisibleObject.ShadowCameraFlag
    )

    def __init__(self, name: str, shape=None, appearance=None, shader=None, clickable: bool = True):
        """Initializes an Entity object.

        Args:
            name: Name of the entity.
            shape: Shape of the entity.
            appearance: Appearance settings.
            shader: Shader for rendering.
            clickable: If the entity is clickable.
        """
        VisibleObject.__init__(self, name)
        self.sources = DataSourcesHandler("shape")
        self.shape = None
        self.shape_controller = None
        self.owner = None
        self.appearance = appearance
        self.set_shape(shape)
        if shader is None:
            shader = AutoShader()
        self.shader = shader
        self.clickable = clickable
        self.instance_ready = False
        self.owner = None
        self.oid_color = None
        self.shadows = MultiShadows(self)
        self.shadow_casters = {}
        self.task = None
        self.body = None
        self.physics = None
        self.lights_source = None
        self.scattering_source = None

    def set_body(self, body) -> None:
        """Sets the body of which this entity is part.

        Args:
            body: The body to set.
        """
        self.body = body

    def check_settings(self) -> None:
        """Checks and updates settings."""
        self.shape.check_settings()
        for shadow_caster in self.shadow_casters.values():
            shadow_caster.check_settings()
        self.update_shader()

    def get_user_parameters(self) -> ParametersGroup:
        """Returns user-editable parameters for the entity.

        Returns:
            Group of user parameters.
        """
        group = ParametersGroup(self.get_component_name())
        if self.shape is not None:
            group.add_parameters(self.shape.get_user_parameters())
        # Commented out as appearance is also a source and so included below
        # if self.appearance is not None:
        # group.add_parameters(self.appearance.get_user_parameters())
        # TODO: DataSourcesHandler should have an iterator interface
        for source in self.sources.sources:
            group.add_parameters(source.get_user_parameters())
        return group

    def update_user_parameters(self) -> None:
        """Updates shape and shader parameters from user input."""
        self.update_shape()
        self.update_shader()

    def get_component_name(self) -> str:
        """Returns the component name for the entity.

        Returns:
            Component name.
        """
        return 'Unknown'

    def set_shape(self, shape) -> None:
        """Sets the shape of the entity and configures data sources and controllers.

        Args:
            shape: Shape to set.
        """
        if self.shape is not None:
            self.shape.parent = None
            self.shape.set_owner(None)
            self.sources.remove_source_by_name('shape')
        self.shape = shape
        if shape is not None:
            self.shape.parent = self
            self.shape.set_owner(self.owner)
            self.sources.add_source(self.shape.get_data_source())
            if shape.patchable:
                self.shape_controller = PatchedShapeController(self)
            if not shape.patchable:
                self.appearance.add_as_source(self.sources)
            if self.shape_controller is not None:
                self.shape_controller.configure_sources(shape, self.appearance)

    def set_owner(self, owner) -> None:
        """
        Sets the owner of the entity.
        Note: To be merged with set_body()

        Args:
            owner: Owner to set.
        """
        self.owner = owner
        self.shape.set_owner(owner)

    @property
    def patch_sources(self) -> None:
        """
        Returns patch sources for patched shapes.
        Note: Temporary workaround.

        Returns:
            Patch sources.
        Raises:
            AttributeError: If patch_sources is unavailable.
        """
        if self.shape_controller is None or not hasattr(self.shape_controller, 'patch_sources'):
            raise AttributeError("patch_sources is only available for patched shapes")
        return self.shape_controller.patch_sources

    def set_lights(self, lights):
        """Sets the lights data source for the entity.

        Args:
            lights: Lights data source.
        """
        if self.lights_source is not None:
            self.sources.remove_source(self.lights_source)
            self.shader.data_source.remove_source('global_lights')
        self.lights_source = lights
        if lights is not None:
            self.sources.add_source(lights)
            self.shader.data_source.add_source(lights.get_data_source())
            self.update_shader()

    def set_oid_color(self, oid_color):
        """Sets the object ID color for picking.

        Args:
            oid_color: Color to set.
        """
        self.oid_color = oid_color

    def get_oid_color(self) -> None:
        """Gets the object ID color.

        Returns:
            The object ID color.
        """
        return self.oid_color

    def set_appearance(self, appearance) -> None:
        """Sets the appearance of the entity.

        Args:
            appearance: Appearance to set.
        """
        self.appearance = appearance

    def set_shader(self, shader) -> None:
        """Sets the shader for the entity.

        Args:
            shader: Shader to set.
        """
        self.shader = shader

    def add_source(self, source) -> None:
        """Adds a data source to the entity.

        Args:
            source: Data source to add.
        """
        self.sources.add_source(source)

    def get_source(self, name: str):
        """Gets a data source by name.

        Args:
            name: Name of the source.
        Returns:
            The data source.
        """
        return self.sources.get_source(name)

    def add_after_effect(self, after_effect) -> None:
        """Adds an after-effect to the shader.

        Args:
            after_effect: After-effect to add.
        """
        if self.shader is not None:
            self.shader.add_after_effect(after_effect)

    def configure_shape(self) -> None:
        """Configures the shape. Placeholder for subclass implementation."""
        pass

    def unconfigure_shape(self) -> None:
        """Unconfigures the shape and removes shadows."""
        self.shadows.clear_shadows()
        self.remove_all_shadows()

    def set_scale(self, scale) -> None:
        """Sets the scale of the shape.

        Args:
            scale: Scale value.
        """
        self.shape.set_scale(scale)

    def get_scale(self) -> LVector3d:
        """Gets the scale of the shape.

        Returns:
            Scale value.
        """
        return self.shape.get_scale()

    def set_scattering(self, scattering_source, scattering_shader) -> None:
        """Sets the scattering source and shader for the entity.

        Args:
            scattering_source: Scattering data source.
            scattering_shader: Scattering shader.
        """
        if self.scattering_source is not None:
            self.sources.remove_source(self.scattering_source)
        self.scattering_source = scattering_source
        self.shader.lighting_model.set_scattering(scattering_shader)
        self.update_shader()
        self.sources.add_source(scattering_source)
        if self.instance is not None and self.instance_ready:
            scattering_source.apply(self.shape, self.instance)

    def remove_scattering(self) -> None:
        """Removes scattering from the shader and sources."""
        self.shader.lighting_model.set_scattering(NoScattering())
        self.update_shader()
        if self.scattering_source is not None:
            self.sources.remove_source(self.scattering_source)
            self.scattering_source = None
        if self.instance is not None:
            # scattering_source.un_apply(self.instance)
            pass

    def is_flat(self) -> bool:
        """Checks if the entity is flat.

        Returns:
            True if flat.
        """
        return True

    def is_spherical(self) -> bool:
        """Checks if the entity is spherical.

        Returns:
            True if spherical.
        """
        return self.shape.is_spherical()

    def task_done(self, task) -> None:
        """Callback for when the shape_task is done.

        Args:
            task: The completed task.
        """
        self.task = None

    def create_instance(self) -> None:
        """Creates the rendering instance for the entity asynchronously."""
        if not self.instance and not self.task:
            if settings.debug_shape_task:
                print(globalClock.get_frame_count(), "CREATE", self)
            self.task = taskMgr.add(
                self.create_instance_task(self.owner.scene_anchor),
                sort=taskMgr.getCurrentTask().sort + 1,
                uponDeath=self.task_done,
            )

    async def create_instance_task(self, scene_anchor) -> None:
        """Asynchronous task to create the entity's rendering instance.

        Args:
            scene_anchor: Anchor for the scene.
        """
        # TODO: Temporarily here until foundation.show() is corrected
        if settings.debug_shape_task:
            print(globalClock.get_frame_count(), "DO CREATE", self)
        if scene_anchor.instance is None:
            print("NO INSTANCE FOR", self, self.owner.get_name())
            return
        self.instance = NodePath('shape')
        if self.shape.patchable:
            self.instance.reparent_to(scene_anchor.shifted_instance)
        else:
            self.instance.reparent_to(scene_anchor.unshifted_instance)
        shape_instance = await self.shape.create_instance()
        if shape_instance is None:
            print("ERROR: Could not create the shape instance")
            return
        # The shape has been removed from the view while the mesh was loaded
        if self.instance is None:
            # TODO: We should probably call shape.remove_instance() here
            return
        shape_instance.reparent_to(self.instance)
        self.shape.set_clickable(self.clickable)
        self.shape.apply_owner()
        self.instance.hide(self.AllCamerasMask)
        self.instance.show(self.default_camera_mask)
        if self.appearance is not None:
            # TODO: should be done somewhere else
            self.appearance.bake()
        # TODO: Should be moved to shape_task
        if self.context.observer.has_scattering:
            self.context.observer.scattering.add_attenuated_object(self)
        self.instance.set_scale(*self.get_scale())
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)
        self.configure_render_order()
        if settings.color_picking and self.get_oid_color() is not None:
            self.instance.set_shader_input("color_picking", self.get_oid_color())
        self.sources.use()
        if self.shape_controller is not None:
            self.shape_controller.use_sources()
        self.schedule_jobs()
        if self.shape.has_lights:
            scene_anchor.add_lights(self.shape.lights)
        if self.physics is not None and self.context.physics:
            if self.physics == 'mesh':
                physics_instances = self.context.physics.build_from_geom(shape_instance, dynamic=False, compress=False)
                # physics_instance.set_scale(self.get_scale())
            self.context.physics.add_objects(self, physics_instances)

    def configure_render_order(self) -> None:
        """Configures the render order. Placeholder for subclass implementation."""
        pass

    def do_create_shadow_caster_for(self, light_source) -> None:
        """Creates a shadow caster for a light source. Placeholder for subclass implementation.

        Args:
            light_source: Light source to create shadow caster for.
        """
        pass

    def create_shadow_caster_for(self, light_source) -> None:
        """Creates and registers a shadow caster for a light source.

        Args:
            light_source: Light source to create shadow caster for.
        """
        if light_source.source not in self.shadow_casters:
            shadow_caster = self.do_create_shadow_caster_for(light_source)
            self.shadow_casters[light_source.source] = shadow_caster
            if not shadow_caster.is_analytic():
                self.owner.set_visibility_override(True)
        self.shadow_casters[light_source.source].create()

    def remove_all_shadows(self) -> None:
        """Removes all shadow casters and clears shadow overrides."""
        for target, shadow_caster in list(self.shadow_casters.items()):
            if not shadow_caster.is_analytic():
                shadow_caster.remove()
                self.owner.set_visibility_override(False)
                del self.shadow_casters[target]

    def start_shadows_update(self) -> None:
        """Starts updating shadows."""
        self.shadows.start_update()

    def end_shadows_update(self) -> None:
        """Ends updating shadows."""
        self.shadows.end_update()

    def add_shadow_target(self, light_source, target) -> None:
        """Adds a shadow target for a light source.

        Args:
            light_source: Light source.
            target: Target to add.
        """
        self.create_shadow_caster_for(light_source)
        self.shadow_casters[light_source.source].add_target(target)

    def add_self_shadow(self, light_source) -> None:
        """Adds self-shadowing for a light source. Placeholder for subclass implementation.

        Args:
            light_source: Light source.
        """
        pass

    async def shape_task(self, shape) -> None:
        """Asynchronous task to load and apply shape data sources.

        Args:
            shape: Shape to process.
        """
        if settings.debug_shape_task:
            print(globalClock.get_frame_count(), "START", shape.str_id(), shape.instance_ready)
        tasks_tree = TasksTree(self.sources.sources)
        self.sources.load(tasks_tree, shape)
        await tasks_tree.run_tasks()
        if shape.instance is not None:
            self.sources.apply(shape)
            shape.instance_ready = True
            self.instance_ready = True
            if self.shader is not None:
                self.shader.create(self.shape, self.appearance)
                self.shader.apply(self.shape.instance)
            shape.shape_done()
        if settings.debug_shape_task:
            print(globalClock.get_frame_count(), "DONE", shape.str_id())

    def schedule_jobs(self) -> None:
        """Schedules shape-related jobs if not already scheduled."""
        if not self.shape.instance_ready and self.shape.task is None:
            if settings.debug_shape_task:
                print(globalClock.get_frame_count(), "SCHEDULE", self.shape.str_id())
            self.shape.task = taskMgr.add(
                self.shape_task(self.shape), sort=taskMgr.getCurrentTask().sort + 1, uponDeath=self.shape.task_done
            )

    def update_shape(self) -> None:
        """Updates the shape if the instance is ready."""
        if self.instance is not None and self.shape is not None and self.instance_ready:
            self.shape.update_shape()

    def update_shader(self) -> None:
        """Updates the shader if the instance is ready."""
        if self.instance is not None and self.shader is not None and self.instance_ready:
            self.shader.create(self.shape, self.appearance)
            self.shader.apply(self.shape.instance)
            self.sources.apply(self.shape)
            if self.shape_controller is not None:
                self.shape_controller.update_shader()

    def update_lod(self, camera_pos, camera_rot) -> None:
        """Updates level of detail (LOD) for appearance and shape controller.

        Args:
            camera_pos: Camera position.
            camera_rot: Camera rotation.
        """
        if not self.instance_ready:
            return
        if self.appearance is not None:
            self.appearance.update_lod(
                self.shape,
                self.owner.get_apparent_radius(),
                self.owner.anchor.distance_to_obs,
                self.context.observer.pixel_size,
            )
        if self.shape_controller is not None:
            self.shape_controller.update_lod(camera_pos, camera_rot)

    def update_instance(self, scene_manager, camera_pos, camera_rot) -> None:
        """Updates the entity instance for rendering and shadow management.

        Args:
            scene_manager: Scene manager.
            camera_pos: Camera position.
            camera_rot: Camera rotation.
        """
        if self.context.observer.apply_scattering > 0:
            self.context.observer.scattering.add_attenuated_object(self)
        if self.shape.instance is not None:
            self.sources.update(self.shape, camera_pos, camera_rot)
        if not self.instance_ready:
            return
        self.shape.update_instance(scene_manager, camera_pos, camera_rot)
        for shadow_caster in self.shadow_casters.values():
            shadow_caster.update(scene_manager)
        if self.shadows.rebuild_needed:
            self.update_shader()
            self.shadows.rebuild_needed = False
        if self.shape_controller is not None:
            self.shape_controller.update_instance()

    def remove_instance(self) -> None:
        """Removes the rendering instance and releases resources."""
        # This method could be called even if the instance does not exist
        if self.instance is None:
            return
        # Remove the shadows data sources as shadows won't be checked anymore
        self.shadows.clear_shadows()
        if self.shape_controller is not None:
            self.shape_controller.remove_instance()
        self.sources.clear(self.shape, self.shape.instance)
        self.sources.release()
        self.shape.remove_instance()
        if self.instance is not None:
            self.instance.remove_node()
            self.instance = None
        self.instance_ready = False
        if self.context.observer.has_scattering:
            self.context.observer.scattering.remove_attenuated_object(self)

    def remove_patch(self, patch) -> None:
        """
        Removes a patch from the shape controller.
        Note: Temporarily in this class

        Args:
            patch: Patch to remove.
        """
        if self.shape_controller is not None:
            self.shape_controller.remove_patch(patch)
