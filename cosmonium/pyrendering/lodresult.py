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


class LodResult:
    def __init__(self):
        self.to_split = []
        self.to_merge = []
        self.to_show = []
        self.to_remove = []
        self.max_lod = 0

    def add_to_split(self, patch):
        self.to_split.append(patch)

    def add_to_merge(self, patch):
        self.to_merge.append(patch)

    def add_to_show(self, patch):
        self.to_show.append(patch)

    def add_to_remove(self, patch):
        self.to_remove.append(patch)

    def check_max_lod(self, patch):
        self.max_lod = max(self.max_lod, patch.lod)

    def sort_by_distance(self):
        self.to_split.sort(key=lambda x: x.distance)
        self.to_merge.sort(key=lambda x: x.distance)
        self.to_show.sort(key=lambda x: x.distance)
        self.to_remove.sort(key=lambda x: x.distance)
