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


from panda3d.core import LVecBase3, NodePath, LColor, DrawMask, OmniBoundingVolume
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

class BaseObject(object):
    context = None
    default_shown = True
    DefaultCameraFlag = DrawMask.bit(0)
    AnnotationCameraFlag = DrawMask.bit(1)
    NearCameraFlag = DrawMask.bit(2)
    WaterCameraFlag = DrawMask.bit(29)
    ShadowCameraFlag = DrawMask.bit(30)
    AllCamerasMask = DrawMask.all_on()

    def __init__(self, name):
        self.name =name
        self.shown = self.default_shown
        self.visible = False
        self.parent = None
        self.scene_anchor = None

    def get_name(self):
        return self.name

    def get_user_parameters(self):
        return None

    def update_user_parameters(self):
        pass

    def apply_func(self, func, near_only=False):
        func(self)

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

    def check_settings(self):
        pass

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        pass

    def remove_instance(self):
        pass

    def update_shader(self):
        pass


class VisibleObject(BaseObject):
    ignore_light = False
    patchable = False

    def __init__(self, name):
        BaseObject.__init__(self, name)
        self.instance = None
        #TODO: Should be handled properly
        self.instance_ready = False

    def check_and_create_instance(self):
        if not self.instance:
            self.create_instance()

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

    def check_visibility(self, frustum, pixel_size):
        if self.parent != None:
            self.visible = self.parent.shown and self.parent.visible

    def get_scale(self):
        return LVecBase3(1.0, 1.0, 1.0)

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        if self.shown and self.visible:
            self.do_show()
            self.update_instance(scene_manager, camera_pos, camera_rot)
        else:
            self.do_hide()

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

    def check_visibility(self, frustum, pixel_size):
        for component in self.components:
            component.check_visibility(frustum, pixel_size)

    def check_settings(self):
        for component in self.components:
            component.check_settings()

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        for component in self.components:
            component.check_and_update_instance(scene_manager, camera_pos, camera_rot)

    def update_shader(self):
        for component in self.components:
            component.update_shader()

    def remove_instance(self):
        for component in self.components:
            component.remove_instance()

class ObjectLabel(VisibleObject):
    default_shown = False
    ignore_light = True
    font_init = False
    font = None
    appearance = None
    shader = None
    color_picking = True
    default_camera_mask = VisibleObject.AnnotationCameraFlag

    def __init__(self, name, label_source):
        VisibleObject.__init__(self, name)
        self.fade = 1.0
        self.label_source = label_source

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
        cls.shader.color_picking = settings.color_picking and cls.color_picking

    def check_settings(self):
        if self.label_source.body_class is None:
            print("No class for", self.label_source.get_name())
            return
        self.set_shown(bodyClasses.get_show_label(self.label_source.body_class))

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
        self.label = TextNode(self.label_source.get_ascii_name() + '-label')
        if not self.font_init:
            self.load_font()
        if self.font is not None:
            self.label.set_font(self.font)
        name = bayer.decode_name(self.label_source.get_label_text())
        self.label.setText(name)
        self.label.setTextColor(*srgb_to_linear(self.label_source.get_label_color()))
        #node=label.generate()
        #self.instance.setBillboardPointEye()
        #node.setIntoCollideMask(GeomNode.getDefaultCollideMask())
        #node.setPythonTag('owner', self.label_source)
        cardMaker = CardMaker(self.label_source.get_ascii_name() + '-labelcard')
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
        self.instance.reparent_to(self.scene_anchor.unshifted_instance)
        self.instance_ready = True
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)
        self.instance.hide(self.AllCamerasMask)
        self.instance.show(self.default_camera_mask)

        if self.shader is None:
            self.create_shader()
        self.appearance.apply(self, self.instance)
        self.shader.apply(self, self.appearance, self.instance)
        TransparencyBlend.apply(self.appearance.transparency_blend, self.instance)

        self.instance.setCollideMask(GeomNode.getDefaultCollideMask())
        self.instance.set_depth_write(False)
        self.instance.set_color_scale(LColor(1, 1, 1, 1))
        card_node.setPythonTag('owner', self.label_source)
        self.look_at = self.instance.attachNewNode("dummy")

class LabelledObject(CompositeObject):
    def __init__(self, name):
        CompositeObject.__init__(self, name)
        self.label = None

    def check_settings(self):
        CompositeObject.check_settings(self)
        if self.label is not None: self.label.check_settings()

    def create_label_instance(self):
        return ObjectLabel(self.get_ascii_name() + '-label', self)

    def create_label(self):
        if self.label is None:
            self.label = self.create_label_instance()
            #self.add_component(self.label)

    def remove_label(self):
        if self.label is not None:
            self.label.remove_instance()
            #self.remove_component(self.label)
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
