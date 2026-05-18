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

import logging

from panda3d.core import BitMask32, CardMaker, LColor, NodePath, OmniBoundingVolume, TextNode

from ... import settings
from ...appearances import ModelAppearance
from ...astro import bayer
from ...bodyclass import bodyClasses
from ...fonts import Font, fontsManager
from ...foundation import VisibleObject
from ...shaders.lighting.flat import FlatLightingModel
from ...shaders.rendering import RenderingShader
from ...utils import TransparencyBlend, srgb_to_linear

logger = logging.getLogger("annotations")


class ObjectLabel(VisibleObject):
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
        cls.shader = RenderingShader(lighting_model=FlatLightingModel())
        cls.shader.color_picking = settings.color_picking and cls.color_picking
        cls.shader.create(None, cls.appearance)

    def check_settings(self):
        if self.label_source.body_class is None:
            logger.warning("No class for %s", self.label_source.get_name())
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
        self.label = TextNode(self.label_source.get_ascii_name() + '-label')
        if not self.font_init:
            self.load_font()
        if self.font is not None:
            self.label.set_font(self.font)
        name = bayer.decode_name(self.label_source.get_label_text())
        self.label.setText(name)
        self.label.setTextColor(*srgb_to_linear(self.label_source.get_label_color()))
        cardMaker = CardMaker(self.label_source.get_ascii_name() + '-labelcard')
        cardMaker.setFrame(self.label.getFrameActual())
        cardMaker.setColor(0, 0, 0, 0)
        card_node = cardMaker.generate()
        self.label_instance = NodePath(card_node)
        self.label_instance.attachNewNode(self.label)
        # Use a card holder node because look_at() modifies hpr parameters directly,
        # which would otherwise affect label_instance's child nodes
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
        self.shader.apply(self.instance)
        TransparencyBlend.apply(self.appearance.transparency_blend, self.instance)

        self.instance.set_collide_mask(BitMask32.bit(settings.mouse_click_collision_bit))
        self.instance.set_depth_write(False)
        self.instance.set_color_scale(LColor(1, 1, 1, 1))
        card_node.setPythonTag('owner', self.label_source)
        self.look_at = self.instance.attachNewNode("dummy")
