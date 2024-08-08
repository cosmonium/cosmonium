#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
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


class HUDObject(object):
    def __init__(self, id_, owner):
        self.id_ = id_
        self.anchor = None
        self.offset = (0, 0)
        self.owner = owner
        if owner is not None:
            self.skin = owner.skin
        else:
            self.skin = None
        self.shown = True
        self.instance = None

    def set_anchor(self, anchor):
        self.anchor = anchor
        if self.instance is not None:
            self.instance.reparent_to(self.anchor)

    def set_owner(self, owner):
        self.owner = owner
        if owner is not None:
            self.skin = owner.skin
        else:
            self.skin = None

    def hide(self):
        self.instance.stash()
        self.shown = False

    def show(self):
        self.instance.unstash()
        self.shown = True

    def set_scale(self, scale):
        self.scale = scale
        self.update_instance()

    def set_offset(self, offset):
        self.offset = offset
        self.update_instance()

    def create(self):
        raise NotImplementedError()

    def update_instance(self):
        raise NotImplementedError()
