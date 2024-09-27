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


from panda3d.core import NodePath, CardMaker, OmniBoundingVolume

from ...astro.astro import radiance_to_mag
from ...foundation import VisibleObject
from ...sprites import ExpPointSprite

from ... import settings


class Halo(VisibleObject):
    default_shown = True
    ignore_light = True
    default_camera_mask = VisibleObject.DefaultCameraFlag
    halo_sprite = None

    def __init__(self, body):
        VisibleObject.__init__(self, body.get_ascii_name() + '-halo')
        self.body = body

    @classmethod
    def create_halo_sprite(cls):
        cls.halo_sprite = ExpPointSprite(size=256, max_value=0.6)

    def create_instance(self):
        if self.halo_sprite is None:
            self.create_halo_sprite()
        self.instance = NodePath("halo")
        card_maker = CardMaker("card")
        card_maker.set_frame(-1, 1, -1, 1)
        node = card_maker.generate()
        self.card_instance = self.instance.attach_new_node(node)
        self.card_instance.setBillboardPointEye()
        self.halo_sprite.apply(self.instance)
        self.instance.setColor(self.body.anchor.point_color)
        self.instance.reparent_to(self.scene_anchor.unshifted_instance)
        self.instance.set_light_off(1)
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)
        self.instance.hide(self.AllCamerasMask)
        self.instance.show(self.default_camera_mask)

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        if self.instance is not None:
            self.instance.set_scale(*self.get_scale())

    def get_scale(self):
        coef = settings.smallest_glare_mag - radiance_to_mag(self.body.anchor._point_radiance) + 6.0
        return self.body.surface.get_scale() * coef
