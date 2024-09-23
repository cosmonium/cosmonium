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


from panda3d.core import LColor
from direct.interval.IntervalGlobal import Sequence, Wait

from .textline import TextLine


class FadeTextLine(TextLine):
    def __init__(self, *args, **kwargs):
        TextLine.__init__(self, *args, **kwargs)
        self.fade_sequence = None

    def set(self, text, pos, color, anchor, duration, fade):
        if anchor is None:
            anchor = self.anchor
        TextLine.set_all(self, text, pos, anchor)
        self.instance.setColorScale(LColor(*color))
        if self.fade_sequence is not None:
            self.fade_sequence.pause()
        self.fade_sequence = Sequence(Wait(duration), self.instance.colorScaleInterval(fade, LColor(1, 1, 1, 0)))
        self.fade_sequence.start()
