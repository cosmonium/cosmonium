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


from panda3d.core import DrawMask, LColor, LVecBase3

from .parameters import ParametersGroup


class BaseObject(object):
    context = None
    DefaultCameraFlag = DrawMask.bit(0)
    AnnotationCameraFlag = DrawMask.bit(1)
    NearCameraFlag = DrawMask.bit(2)
    WaterCameraFlag = DrawMask.bit(29)
    ShadowCameraFlag = DrawMask.bit(30)
    AllCamerasMask = DrawMask.all_on()

    concrete_object = True

    def __init__(self, name):
        self.name = name
        self.shown = True
        self.visible = False
        self.parent = None
        self.scene_anchor = None
        self.owner = None

    def get_name(self):
        return self.name

    def get_ascii_name(self):
        return self.name.encode('ascii', 'replace').decode('ascii').replace('?', 'x').lower()

    def set_owner(self, owner):
        self.owner = owner

    def set_body(self, body):
        self.body = body

    def get_user_parameters(self):
        return None

    def update_user_parameters(self):
        pass

    def set_parent(self, parent):
        self.parent = parent

    def set_lights(self, lights):
        pass

    def set_scene_anchor(self, scene_anchor):
        self.scene_anchor = scene_anchor

    def show(self):
        self.shown = True
        if self.visible:
            self.do_show()

    def do_show(self):
        pass

    def hide(self):
        self.shown = False
        self.do_hide()

    def do_hide(self):
        pass

    def toggle_shown(self):
        if self.shown:
            self.hide()
        else:
            self.show()

    def set_shown(self, new_shown_status):
        if new_shown_status != self.shown:
            if new_shown_status:
                self.show()
            else:
                self.hide()

    def set_state(self, new_state):
        pass

    def update(self, time, dt):
        pass

    def update_obs(self, observer):
        pass

    def check_visibility(self, frustum, pixel_size):
        pass

    def update_lod(self, camera_pos, camera_rot):
        pass

    def check_settings(self):
        pass

    def check_and_create_instance(self, scene_manager, camera_pos, camera_rot):
        pass

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        pass

    def remove_instance(self):
        pass

    def update_shader(self):
        pass


class VisibleObject(BaseObject):

    def __init__(self, name):
        BaseObject.__init__(self, name)
        self.instance = None
        # TODO: Should be handled properly
        self.instance_ready = False

    def create_instance(self):
        pass

    def remove_instance(self):
        if self.instance:
            self.instance.removeNode()
            self.instance = None
            self.instance_ready = False

    def do_show(self):
        if not self.instance:
            self.create_instance()
        if self.instance:
            self.instance.unstash()
            self.instance.show()

    def do_hide(self):
        if self.instance:
            self.instance.hide()
            self.instance.stash()

    def check_visibility(self, frustum, pixel_size):
        if self.parent is not None:
            self.visible = self.parent.shown and self.parent.visible

    def get_scale(self):
        return LVecBase3(1.0, 1.0, 1.0)

    def check_and_create_instance(self, scene_manager, camera_pos, camera_rot):
        if self.shown and self.visible:
            self.do_show()
        else:
            self.do_hide()

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        if self.shown and self.visible and self.instance is not None:
            self.update_instance(scene_manager, camera_pos, camera_rot)

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        pass

    def set_lights(self, lights):
        pass

    def get_oid_color(self):
        return LColor()


class CompositeObject(BaseObject):
    def __init__(self, name):
        BaseObject.__init__(self, name)
        self.components = []
        self.lights = None

    def set_owner(self, owner):
        BaseObject.set_owner(self, owner)
        for component in self.components:
            component.set_owner(owner)

    def set_lights(self, lights):
        self.lights = lights
        for component in self.components:
            component.set_lights(lights)

    def set_scene_anchor(self, scene_anchor):
        BaseObject.set_scene_anchor(self, scene_anchor)
        for component in self.components:
            component.set_scene_anchor(scene_anchor)

    def add_component(self, component):
        if component is not None:
            self.components.append(component)
            component.set_parent(self)
            component.set_lights(self.lights)
            component.set_scene_anchor(self.scene_anchor)

    def remove_component(self, component):
        if component is None:
            return
        self.components.remove(component)
        if component.instance is not None:
            component.remove_instance()
        component.set_parent(None)

    def get_user_parameters(self):
        params = []
        for component in self.components:
            component_params = component.get_user_parameters()
            if component_params is not None:
                params.append(component_params)
        if len(params) != 0:
            return ParametersGroup(self.get_name(), params)
        else:
            return None

    def update_user_parameters(self):
        for component in self.components:
            component.update_user_parameters()

    def do_show(self):
        for component in self.components:
            component.do_show()

    def do_hide(self):
        for component in self.components:
            component.do_hide()

    def update(self, time, dt):
        for component in self.components:
            component.update(time, dt)

    def update_obs(self, observer):
        for component in self.components:
            component.update_obs(observer)

    def check_visibility(self, frustum, pixel_size):
        if self.parent is not None:
            self.visible = self.parent.shown and self.parent.visible
        for component in self.components:
            component.check_visibility(frustum, pixel_size)

    def update_lod(self, camera_pos, camera_rot):
        for component in self.components:
            component.update_lod(camera_pos, camera_rot)

    def check_settings(self):
        for component in self.components:
            component.check_settings()

    def check_and_create_instance(self, scene_manager, camera_pos, camera_rot):
        for component in self.components:
            component.check_and_create_instance(scene_manager, camera_pos, camera_rot)

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        for component in self.components:
            component.check_and_update_instance(scene_manager, camera_pos, camera_rot)

    def update_shader(self):
        for component in self.components:
            component.update_shader()

    def remove_instance(self):
        for component in self.components:
            component.remove_instance()
