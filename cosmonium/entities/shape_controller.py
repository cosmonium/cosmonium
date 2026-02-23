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
from direct.task.Task import shield
from direct.task.TaskManagerGlobal import taskMgr

from .. import settings
from .datasource import DataSourcesHandler
from .tasks_tree import TasksTree


class ShapeController:
    """
    Base interface for complex shape lifecycle management.

    Args:
        entity: The entity this controller manages.
    """

    def __init__(self, entity):
        """Initializes the shape controller.

        Args:
            entity: The entity to manage.
        """
        self.entity = entity

    def configure_sources(self, shape, appearance):
        """Configures data sources for the entity.

        Args:
            shape: The shape of the entity.
            appearance: The appearance of the entity.
        """
        pass

    def use_sources(self):
        """Activates the configured data sources."""
        pass

    def schedule_root_job(self):
        """Schedules the root job for shape processing."""
        pass

    def update_instance(self):
        """Updates the scene instance for the shape."""
        pass

    def update_lod(self, camera_pos, camera_rot):
        """Updates level of detail (LOD) for the shape.

        Args:
            camera_pos: Camera position.
            camera_rot: Camera rotation.
        """
        pass

    def update_shader(self):
        """Updates the shader for the shape."""
        pass

    def remove_instance(self):
        """The scene instance is removed."""
        pass

    def remove_patch(self, patch):
        """The given patch is removed from the shape.

        Args:
            patch: Patch to remove.
        """
        pass


class PatchedShapeController(ShapeController):
    """
    Handles patched shapes with LOD, patch scheduling, etc.

    Args:
        entity: The entity this controller manages.
    """

    def __init__(self, entity):
        """Initializes the patched shape controller.

        Args:
            entity: The entity to manage.
        """
        super().__init__(entity)
        self.patch_sources = DataSourcesHandler("patch")
        self.first_patch = True

    def configure_sources(self, shape, appearance):
        """Configures data sources for the entity.

        Args:
            shape: The shape of the entity.
            appearance: The appearance of the entity.
        """
        self.patch_sources.add_source(shape.get_patch_data_source())
        appearance.add_as_source(self.patch_sources)

    def use_sources(self):
        """Activates the patch data sources."""
        self.patch_sources.use()

    async def patch_task(self, patch):
        """Asynchronous task to load and apply patch data.

        Args:
            patch: Patch to process.
        """
        if settings.debug_shape_task:
            print(globalClock.get_frame_count(), "START", patch.str_id(), patch.instance_ready)
        if self.entity.shape.task is not None:
            # The shape task is still running, we need to wait for it to complete
            await shield(self.entity.shape.task)
        tasks_tree = TasksTree(self.patch_sources.sources)
        self.patch_sources.load(tasks_tree, patch)
        patch.create_geometry_instance(tasks_tree)
        patch.set_clickable(self.entity.clickable)
        await tasks_tree.run_tasks()
        if patch.instance is not None:
            self.patch_sources.apply(patch)
            patch.instance_ready = True
            if self.entity.shader is not None:
                if self.first_patch:
                    self.entity.shader.create(self.entity.shape, self.entity.appearance)
                    self.entity.shader.apply(self.entity.shape.instance)
                    self.first_patch = False
            patch.patch_done(early=False)
            self.entity.shape.patch_done(patch, early=False)
        if settings.debug_shape_task:
            print(globalClock.get_frame_count(), "DONE", patch.str_id())

    def schedule_patch_jobs(self, patches):
        """Schedules jobs for new patches to display.

        Args:
            patches: List of patches to schedule.
        """
        for patch in patches:
            if not patch.instance_ready and patch.task is None:
                if settings.debug_shape_task:
                    print(globalClock.get_frame_count(), "SCHEDULE", patch.str_id())
                self.patch_sources.create(patch)
                # Use parent data to display the patch while generation is ongoing
                self.early_apply_patch(patch)
                patch.task = taskMgr.add(
                    self.patch_task(patch),
                    sort=taskMgr.getCurrentTask().sort + 1,
                    uponDeath=patch.task_done,
                )

    def early_apply_patch(self, patch):
        """Applies patch data from lower LOD while full generation is ongoing.

        Args:
            patch: Patch to configure early.
        """
        if patch.lod > 0:
            if settings.debug_shape_task:
                print(globalClock.get_frame_count(), "EARLY", patch.str_id(), patch.instance_ready)
            patch.instance_ready = True
            self.patch_sources.early_apply(patch)
            patch.patch_done(early=True)
            self.entity.shape.patch_done(patch, early=True)

    def update_lod(self, camera_pos, camera_rot):
        """Updates LOD for patches and schedules jobs as needed.

        Args:
            camera_pos: Camera position.
            camera_rot: Camera rotation.
        """
        to_show, to_update = self.entity.shape.update_lod(
            self.entity.context.observer.get_local_position(),
            self.entity.owner.anchor.distance_to_obs,
            self.entity.context.observer.pixel_size,
            self.entity.appearance,
        )
        self.schedule_patch_jobs(to_show)
        for patch in to_update:
            if patch.instance is not None:
                self.patch_sources.apply(patch)

    def update_instance(self):
        """Updates the scene instance for patched shapes."""
        if self.entity.instance_ready:
            self.entity.shape.place_patches(self.entity.owner)

    def remove_instance(self):
        """The scene instance is removed. Notify the data sources to release resources."""
        self.patch_sources.release()
        self.first_patch = True

    def remove_patch(self, patch):
        """The given patch is removed from the shape. Notify the data sources to release resources.

        Args:
            patch: Patch to remove.
        """
        self.patch_sources.clear(patch, patch.instance)
