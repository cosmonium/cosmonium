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


from direct.task.Task import shield
from panda3d.core import NodePath
from panda3d.core import OmniBoundingVolume

from ..foundation import VisibleObject
from ..datasource import DataSourcesHandler
from ..shaders.base import AutoShader
from ..shadows import MultiShadows
from ..parameters import ParametersGroup

from .. import settings


class ShapeObject(VisibleObject):
    default_camera_mask = VisibleObject.DefaultCameraFlag | VisibleObject.WaterCameraFlag | VisibleObject.ShadowCameraFlag
    def __init__(self, name, shape=None, appearance=None, shader=None, clickable=True):
        VisibleObject.__init__(self, name)
        self.sources = DataSourcesHandler("shape")
        self.patch_sources = DataSourcesHandler("patch")
        self.shape = None
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
        self.first_patch = True
        self.task = None

    def check_settings(self):
        self.shape.check_settings()
        for shadow_caster in self.shadow_casters.values():
            shadow_caster.check_settings()
        self.update_shader()

    def get_user_parameters(self):
        group = ParametersGroup(self.get_component_name())
        if self.shape is not None:
            group.add_parameters(self.shape.get_user_parameters())
        if self.appearance is not None:
            group.add_parameters(self.appearance.get_user_parameters())
        #TODO: DataSourcesHandler should have an iterator interface
        for source in self.sources.sources:
            group.add_parameters(source.get_user_parameters())
        return group

    def update_user_parameters(self):
        self.update_shape()
        self.update_shader()

    def get_component_name(self):
        return 'Unknown'

    def set_shape(self, shape):
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
                self.patch_sources.add_source(self.shape.get_patch_data_source())
            #Not using add source as some dependencies of the appearance can also be sources
            if shape.patchable:
                self.appearance.add_as_source(self.patch_sources)
            else:
                self.appearance.add_as_source(self.sources)

    def set_owner(self, owner):
        self.owner = owner
        self.shape.set_owner(owner)

    def set_lights(self, lights):
        self.sources.remove_source_by_name('lights')
        if lights is not None:
            self.sources.add_source(lights)

    def set_oid_color(self, oid_color):
        self.oid_color = oid_color

    def get_oid_color(self):
        return self.oid_color

    def set_appearance(self, appearance):
        self.appearance = appearance

    def set_shader(self, shader):
        self.shader = shader

    def add_source(self, source):
        self.sources.add_source(source)

    def get_source(self, name):
        return self.sources.get_source(name)

    def add_after_effect(self, after_effect):
        if self.shader is not None:
            self.shader.add_after_effect(after_effect)

    def configure_shape(self):
        pass

    def unconfigure_shape(self):
        pass

    def set_scale(self, scale):
        self.shape.set_scale(scale)

    def get_scale(self):
        return self.shape.get_scale()

    def set_scattering(self, scattering_source, scattering_shader):
        self.sources.remove_source_by_name('scattering')
        self.shader.set_scattering(scattering_shader)
        self.update_shader()
        self.sources.add_source(scattering_source)
        if self.instance is not None and self.instance_ready:
            scattering_source.apply(self.shape, self.instance)

    def remove_scattering(self):
        self.shader.remove_scattering()
        self.update_shader()
        self.sources.remove_source_by_name('scattering')
        if self.instance is not None:
            #scattering_source.un_apply(self.instance)
            pass

    def is_flat(self):
        return True

    def is_spherical(self):
        return self.shape.is_spherical()

    def task_done(self, task):
        self.task = None

    #TODO: Temporarily stolen from foundation to be able to spawn task
    def check_and_create_instance(self):
        if not self.instance and not self.task:
            self.task = taskMgr.add(self.create_instance(self.owner.scene_anchor), uponDeath=self.task_done)

    async def create_instance(self, scene_anchor):
        self.instance = NodePath('shape')
        #TODO: Temporarily here until foundation.show() is corrected
        if scene_anchor.instance is None:
            print("NO INSTANCE FOR", self, self.owner.get_name())
            return
        if self.shape.patchable:
            self.instance.reparent_to(scene_anchor.shifted_instance)
        else:
            self.instance.reparent_to(scene_anchor.unshifted_instance)
        shape_instance = await self.shape.create_instance()
        if shape_instance is None:
            print("ERROR: Could not create the shape instance")
            return
        #The shape has been removed from the view while the mesh was loaded
        if self.instance is None:
            #TODO: We should probably call shape.remove_instance() here
            return
        shape_instance.reparent_to(self.instance)
        self.shape.set_clickable(self.clickable)
        self.shape.apply_owner()
        self.instance.hide(self.AllCamerasMask)
        self.instance.show(self.default_camera_mask)
        if self.appearance is not None:
            #TODO: should be done somewhere else
            self.appearance.bake()
        #TODO: Should be moved to shape_task
        if self.context.observer.has_scattering:
            self.context.observer.scattering.add_attenuated_object(self)
        self.instance.set_scale(self.get_scale())
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)
        self.configure_render_order()
        if settings.color_picking and self.get_oid_color() is not None:
            self.instance.set_shader_input("color_picking", self.get_oid_color())
        self.sources.use()
        self.patch_sources.use()
        self.schedule_jobs([])

    def configure_render_order(self):
        pass

    def do_create_shadow_caster_for(self, light_source):
        pass

    def create_shadow_caster_for(self, light_source):
        if not light_source.source in self.shadow_casters:
            shadow_caster = self.do_create_shadow_caster_for(light_source)
            self.shadow_casters[light_source.source] = shadow_caster
            if not shadow_caster.is_analytic():
                self.owner.set_visibility_override(True)
        self.shadow_casters[light_source.source].create()

    def remove_all_shadows(self):
        for shadow_caster in self.shadow_casters.values():
            shadow_caster.remove()
        self.owner.set_visibility_override(False)
        self.shadow_casters = {}

    def start_shadows_update(self):
        self.shadows.start_update()

    def end_shadows_update(self):
        self.shadows.end_update()

    def add_shadow_target(self, light_source, target):
        self.create_shadow_caster_for(light_source)
        self.shadow_casters[light_source.source].add_target(target)

    def add_self_shadow(self, light_source):
        pass

    async def patch_task(self, patch):
        if settings.debug_shape_task:
            print(globalClock.getFrameCount(), "START", patch.str_id(), patch.instance_ready)
        if self.shape.task is not None:
            await shield(self.shape.task)
        await self.patch_sources.load(patch)
        if patch.instance is not None:
            self.patch_sources.apply(patch)
            patch.instance_ready = True
            if self.shader is not None:
                if self.first_patch:
                    self.shader.create(self.shape, self.appearance)
                    self.shader.apply(self.shape.instance)
                    self.first_patch = False
            patch.patch_done()
            self.shape.patch_done(patch)
        if settings.debug_shape_task:
            print(globalClock.getFrameCount(), "DONE", patch.str_id())

    async def shape_task(self, shape):
        if settings.debug_shape_task:
            print(globalClock.getFrameCount(), "START", shape.str_id(), shape.instance_ready)
        await self.sources.load(shape)
        if shape.instance is not None:
            self.sources.apply(shape)
            shape.instance_ready = True
            self.instance_ready = True
            if self.shader is not None:
                self.shader.create(self.shape, self.appearance)
                self.shader.apply(self.shape.instance)
            shape.shape_done()
        if settings.debug_shape_task:
            print(globalClock.getFrameCount(), "DONE", shape.str_id())

    def schedule_jobs(self, patches):
        if self.shape.patchable:
            for patch in patches:
                if not patch.instance_ready and patch.task is None:
                    self.patch_sources.create(patch)
                    # Patch generation is ongoing, use parent data to display the patch in the meantime
                    self.early_apply_patch(patch)
                    patch.task = taskMgr.add(self.patch_task(patch), uponDeath=patch.task_done)
        if not self.shape.instance_ready and self.shape.task is None:
            self.shape.task = taskMgr.add(self.shape_task(self.shape), uponDeath=self.shape.task_done)

    def early_apply_patch(self, patch):
        if patch.lod > 0:
            if settings.debug_shape_task:
                print(globalClock.getFrameCount(), "EARLY", patch.str_id(), patch.instance_ready)
            patch.instance_ready = True
            self.patch_sources.early_apply(patch)
            patch.patch_done()
            self.shape.patch_done(patch)

    def update_shape(self):
        if self.instance is not None and self.shape is not None and self.instance_ready:
            self.shape.update_shape()

    def update_shader(self):
        if self.instance is not None and self.shader is not None and self.instance_ready:
            self.shader.create(self.shape, self.appearance)
            self.shader.apply(self.shape.instance)
            self.sources.apply(self.shape)

    def update_lod(self, camera_pos, camera_rot):
        if not self.instance_ready: return
        to_show, to_update = self.shape.update_lod(self.context.observer.get_local_position(), self.owner.anchor.distance_to_obs, self.context.observer.pixel_size, self.appearance)
        self.schedule_jobs(to_show)
        for patch in to_update:
            if patch.instance is not None:
                self.patch_sources.apply(patch)
        if self.appearance is not None:
            self.appearance.update_lod(self.shape, self.owner.get_apparent_radius(), self.owner.anchor.distance_to_obs, self.context.observer.pixel_size)

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        if self.context.observer.apply_scattering > 0:
            self.context.observer.scattering.add_attenuated_object(self)
        if self.shape.instance is not None:
            self.sources.update(self.shape, camera_pos, camera_rot)
        if not self.instance_ready: return
        self.shape.update_instance(scene_manager, camera_pos, camera_rot)
        if self.shape.patchable:
            self.shape.place_patches(self.owner)
        for shadow_caster in self.shadow_casters.values():
            shadow_caster.update(scene_manager)
        if self.shadows.rebuild_needed:
            self.update_shader()
            self.shadows.rebuild_needed = False

    def remove_instance(self):
        # This method could be called even if the instance does not exist
        if self.instance is None: return
        # Remove the shadows data sources as shadows won't be checked anymore
        self.shadows.clear_shadows()
        self.sources.clear(self.shape, self.shape.instance)
        self.sources.release()
        self.patch_sources.release()
        self.shape.remove_instance()
        if self.instance is not None:
            self.instance.remove_node()
            self.instance = None
        self.instance_ready = False
        if self.context.observer.has_scattering:
            self.context.observer.scattering.remove_attenuated_object(self)
        self.first_patch = True

    def remove_patch(self, patch):
        #TODO: This should be reworked and moved into a dedicated class
        #print("CLEAR", patch.str_id())
        self.patch_sources.clear(patch, patch.instance)
