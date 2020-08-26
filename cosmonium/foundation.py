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

from panda3d.core import LVecBase3, LQuaternion, NodePath, LColor, DrawMask
from panda3d.core import GeomNode, TextNode, CardMaker

from .bodyclass import bodyClasses
from .fonts import fontsManager, Font
from .parameters import ParametersGroup
from .utils import srgb_to_linear
from .astro import bayer
from .appearances import ModelAppearance
from .shaders import FlatLightingModel, BasicShader
from .utils import TransparencyBlend
from . import settings

from math import log

class BaseObject(object):
    context = None
    default_shown = True
    AllCamerasMask = DrawMask.all_on()
    DefaultCameraMask = DrawMask.bit(0)
    NearCameraMask = DrawMask.bit(1)
    WaterCameraMask = DrawMask.bit(29)
    ShadowCameraMask = DrawMask.bit(30)

    def __init__(self, names=None):
        self.set_names(names)
        self.shown = self.default_shown
        self.visible = False
        self.light = None
        self.parent = None

    def get_names(self):
        return self.names

    def set_names(self, names):
        if names is None:
            self.names = ['']
        elif isinstance(names, (list, tuple)):
            self.names = names
        else:
            self.names = [names]

    def get_friendly_name(self):
        return self.names[0]

    def get_name(self):
        return self.names[0]

    def get_ascii_name(self):
        return self.names[0].encode('ascii', 'replace').decode('ascii').replace('?', 'x').lower()

    def get_exact_name(self, text):
        text = text.upper()
        result = ''
        for name in self.names:
            if name.upper() == text:
                result = name
                break
        return result

    def get_user_parameters(self):
        return None

    def update_user_parameters(self):
        pass

    def apply_func(self, func, near_only=False):
        func(self)

    def set_parent(self, parent):
        self.parent = parent

    def set_light(self, light):
        self.light = light

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

    def check_visibility(self, pixel_size):
        pass

    def check_settings(self):
        pass

    def check_and_update_instance(self, camera_pos, camera_rot, pointset):
        pass

    def remove_instance(self):
        pass

    def update_shader(self):
        pass

    def get_real_pos(self, abs_position, camera_pos, distance_to_obs, vector_to_obs):
        return self.calc_scene_params(abs_position - camera_pos, abs_position, distance_to_obs, vector_to_obs)

    def calc_scene_params(self, rel_position, abs_position, distance_to_obs, vector_to_obs):
        if settings.camera_at_origin:
            obj_position = rel_position
        else:
            obj_position = abs_position
        midPlane = self.context.observer.midPlane
        distance_to_obs /= settings.scale
        if not settings.use_depth_scaling or distance_to_obs <= midPlane:
            position = obj_position / settings.scale
            distance = distance_to_obs
            scale_factor = 1.0 / settings.scale
        elif settings.use_inv_scaling:
            not_scaled = -vector_to_obs * midPlane
            scaled_distance = midPlane * (1 - midPlane / distance_to_obs)
            scaled = -vector_to_obs * scaled_distance
            position = not_scaled + scaled
            distance = midPlane + scaled_distance
            ratio = distance / distance_to_obs
            scale_factor = ratio / settings.scale
        elif settings.use_log_scaling:
            not_scaled = -vector_to_obs * midPlane
            scaled_distance = midPlane * (1 - log(midPlane / distance_to_obs + 1, 2))
            scaled = -vector_to_obs * scaled_distance
            position = not_scaled + scaled
            distance = midPlane + scaled_distance
            ratio = distance / distance_to_obs
            scale_factor = ratio / settings.scale
        return position, distance, scale_factor

    def place_pos_only(self, instance, abs_position, camera_pos, distance_to_obs, vector_to_obs):
        position, distance, scale_factor = self.get_real_pos(abs_position, camera_pos, distance_to_obs, vector_to_obs)
        instance.setPos(*position)

    def place_instance(self, instance, parent):
        instance.setPos(*self.parent.scene_position)
        instance.setScale(*(self.get_scale() * self.parent.scene_scale_factor))
        instance.setQuat(LQuaternion(*self.parent.scene_orientation))

    def place_instance_params(self, instance, scene_position, scene_scale_factor, scene_orientation):
        instance.setPos(*scene_position)
        instance.setScale(self.get_scale() * scene_scale_factor)
        instance.setQuat(LQuaternion(*scene_orientation))

class VisibleObject(BaseObject):
    ignore_light = False
    patchable = False

    def __init__(self, names=None):
        BaseObject.__init__(self, names)
        self.instance = None
        #TODO: Should be handled properly
        self.instance_ready = False
        self.jobs_pending = 0

    def check_and_create_instance(self):
        if not self.instance:
            self.create_instance()
        if self.instance:
            if self.light and not self.ignore_light:
                self.instance.setLight(self.light)

    def create_instance(self):
        pass

    def remove_instance(self):
        if self.instance:
            self.instance.removeNode()
            self.instance = None
            self.instance_ready = False

    def do_show(self):
        if not self.instance:
            self.check_and_create_instance()
        if self.instance:
            self.instance.unstash()
            self.instance.show()

    def do_hide(self):
        if self.instance:
            self.instance.hide()
            self.instance.stash()

    def check_visibility(self, pixel_size):
        if self.parent != None:
            self.visible = self.parent.shown and self.parent.visible

    def get_scale(self):
        return LVecBase3(1.0, 1.0, 1.0)

    def check_and_update_instance(self, camera_pos, camera_rot, pointset):
        if self.shown and self.visible:
            self.do_show()
            self.update_instance(camera_pos, camera_rot)
        else:
            self.do_hide()

    def update_instance(self, camera_pos, camera_rot):
        pass

    def set_light(self, light):
        BaseObject.set_light(self, light)
        if self.instance and not self.ignore_light:
            self.instance.setLight(self.light)

    def get_oid_color(self):
        return LColor()

class CompositeObject(BaseObject):
    def __init__(self, names):
        BaseObject.__init__(self, names)
        self.components = []
        self.init = False

    def create_components(self):
        pass

    def add_component(self, component):
        if component is not None:
            self.components.append(component)
            component.set_parent(self)
            component.set_light(self.light)

    def remove_component(self, component):
        if component is None: return
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

    def apply_func_composite(self, func, near_only=False):
        BaseObject.apply_func(self, func, near_only)
        for component in self.components:
            component.apply_func(func, near_only)

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

    def check_visibility(self, pixel_size):
        for component in self.components:
            component.check_visibility(pixel_size)

    def check_settings(self):
        for component in self.components:
            component.check_settings()

    def check_and_update_instance(self, camera_pos, camera_rot, pointset):
        for component in self.components:
            component.check_and_update_instance(camera_pos, camera_rot, pointset)

    def update_shader(self):
        for component in self.components:
            component.update_shader()

    def remove_instance(self):
        for component in self.components:
            component.remove_instance()

    def set_light(self, light):
        BaseObject.set_light(self, light)
        for component in self.components:
            component.set_light(light)

class ObjectLabel(VisibleObject):
    default_shown = False
    ignore_light = True
    font_init = False
    font = None
    appearance = None
    shader = None

    def __init__(self, names):
        VisibleObject.__init__(self, names)
        self.fade = 1.0

    @classmethod
    def create_shader(cls):
        cls.appearance = ModelAppearance()
        cls.appearance.has_attribute_color = True
        cls.appearance.has_material = False
        cls.appearance.texture = True
        cls.appearance.texture_index = 0
        cls.appearance.nb_textures = 1
        cls.appearance.transparency = True
        cls.appearance.transparency_blend = TransparencyBlend.TB_Alpha
        cls.appearance.alpha_mask = True
        cls.shader = BasicShader(lighting_model=FlatLightingModel())

    def check_settings(self):
        if self.parent.body_class is None:
            print("No class for", self.parent.get_name())
            return
        self.set_shown(bodyClasses.get_show_label(self.parent.body_class))

    @classmethod
    def load_font(cls):
        font = fontsManager.get_font(settings.label_font, Font.STYLE_NORMAL)
        if font is not None:
            cls.font = font.load()
        else:
            cls.font = None
        cls.font_init = True

    def create_instance(self):
        #print("Create label for", self.get_name())
        self.label = TextNode(self.parent.get_ascii_name() + '-label')
        if not self.font_init:
            self.load_font()
        if self.font is not None:
            self.label.set_font(self.font)
        name = bayer.decode_name(self.parent.get_label_text())
        self.label.setText(name)
        self.label.setTextColor(*srgb_to_linear(self.parent.get_label_color()))
        #node=label.generate()
        #self.instance = self.context.annotation.attachNewNode(node)
        #self.instance.setBillboardPointEye()
        #node.setIntoCollideMask(GeomNode.getDefaultCollideMask())
        #node.setPythonTag('owner', self.parent)
        cardMaker = CardMaker(self.get_ascii_name() + '-labelcard')
        cardMaker.setFrame(self.label.getFrameActual())
        cardMaker.setColor(0, 0, 0, 0)
        card_node = cardMaker.generate()
        self.label_instance = NodePath(card_node)
        tnp = self.label_instance.attachNewNode(self.label)
        #self.label_instance.setTransparency(TransparencyAttrib.MAlpha)
        #card.setEffect(DecalEffect.make())
        #Using look_at() instead of billboard effect to also rotate the collision solid
        #card.setBillboardPointEye()
        #Using a card holder as look_at() is changing the hpr parameters
        self.instance = NodePath('label-holder')
        self.label_instance.reparentTo(self.instance)
        self.instance.reparentTo(self.context.annotation)
        self.instance_ready = True

        if self.shader is None:
            self.create_shader()
        self.shader.apply(self, self.appearance)
        self.shader.update(self, self.appearance)
        TransparencyBlend.apply(self.appearance.transparency_blend, self.instance)

        self.instance.setCollideMask(GeomNode.getDefaultCollideMask())
        self.instance.set_depth_write(False)
        self.instance.set_color_scale(LColor(1, 1, 1, 1))
        card_node.setPythonTag('owner', self.parent)
        self.look_at = self.instance.attachNewNode("dummy")

class LabelledObject(CompositeObject):
    def __init__(self, names):
        CompositeObject.__init__(self, names)
        self.label = None

    def create_label_instance(self):
        return ObjectLabel(self.get_ascii_name() + '-label')

    def create_label(self):
        if self.label is None:
            self.label = self.create_label_instance()
            self.add_component(self.label)

    def remove_label(self):
        if self.label is not None:
            self.label.remove_instance()
            self.remove_component(self.label)
            self.label = None

    def show_label(self):
        if self.label:
            self.label.show()

    def hide_label(self):
        if self.label:
            self.label.hide()

    def toggle_label(self):
        if self.label:
            self.label.toggle_shown()
