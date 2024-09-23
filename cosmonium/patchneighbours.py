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


from itertools import chain


class PatchNeighboursBase:
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    opposite_face = [SOUTH, WEST, NORTH, EAST]
    text = ['North', 'East', 'South', 'West']
    conv = [WEST, SOUTH, EAST, NORTH]


class PatchNoNeighbours(PatchNeighboursBase):
    def __init__(self, patch):
        self.patch = patch

    def set_neighbours(self, face, neighbours):
        pass

    def add_neighbour(self, face, neighbour):
        pass

    def get_neighbours(self, face):
        return []

    def collect_side_patches(self, side):
        return []

    def set_all_neighbours(self, north, east, south, west):
        pass

    def clear_all_neighbours(self):
        pass

    def get_all_neighbours(self):
        return []

    def get_neighbour_lower_lod(self, face):
        return self.patch.lod

    def remove_detached_neighbours(self):
        pass

    def replace_neighbours(self, face, olds, news):
        pass

    def split_neighbours(self, update):
        pass

    def merge_neighbours(self, update):
        pass

    def calc_outer_tessellation_level(self, update):
        pass


class PatchNeighbours(PatchNeighboursBase):
    def __init__(self, patch):
        self.patch = patch
        self.neighbours = [set(), set(), set(), set()]

    def set_neighbours(self, face, neighbours):
        self.neighbours[face] = neighbours

    def add_neighbour(self, face, neighbour):
        if neighbour not in self.neighbours[face]:
            self.neighbours[face].add(neighbour)

    def get_neighbours(self, face):
        return set(self.neighbours[face])

    # TODO: This should be moved to QuadTreeNode
    def _collect_side_patches(self, result, side):
        if len(self.patch.children) != 0:
            (bl, br, tr, tl) = self.patch.children
            if side == self.NORTH:
                tl.neighbours._collect_side_neighbours(result, side)
                tr.neighbours._collect_side_neighbours(result, side)
            elif side == self.EAST:
                tr.neighbours._collect_side_neighbours(result, side)
                br.neighbours._collect_side_neighbours(result, side)
            elif side == self.SOUTH:
                bl.neighbours._collect_side_neighbours(result, side)
                br.neighbours._collect_side_neighbours(result, side)
            elif side == self.WEST:
                tl.neighbours._collect_side_neighbours(result, side)
                bl.neighbours._collect_side_neighbours(result, side)
        else:
            result.add(self.patch)

    def collect_side_patches(self, side):
        result = set()
        self._collect_side_patches(result, side)
        return result

    def _collect_neighbours(self, result, side):
        if len(self.patch.children) != 0:
            (bl, br, tr, tl) = self.patch.children
            if side == self.NORTH:
                tl.neighbours._collect_neighbours(result, side)
                tr.neighbours._collect_neighbours(result, side)
            elif side == self.EAST:
                tr.neighbours._collect_neighbours(result, side)
                br.neighbours._collect_neighbours(result, side)
            elif side == self.SOUTH:
                bl.neighbours._collect_neighbours(result, side)
                br.neighbours._collect_neighbours(result, side)
            elif side == self.WEST:
                tl.neighbours._collect_neighbours(result, side)
                bl.neighbours._collect_neighbours(result, side)
        else:
            result |= self.neighbours[side]

    def collect_neighbours(self, side):
        result = set()
        self._collect_neighbours(result, side)
        return result

    def set_all_neighbours(self, north, east, south, west):
        self.neighbours[self.NORTH] = north
        self.neighbours[self.EAST] = east
        self.neighbours[self.SOUTH] = south
        self.neighbours[self.WEST] = west

    def clear_all_neighbours(self):
        self.neighbours = [set(), set(), set(), set()]

    def get_all_neighbours(self):
        neighbours = set()
        for i in range(4):
            neighbours |= self.neighbours[i]
        return neighbours

    def get_neighbour_lower_lod(self, face):
        lower_lod = self.patch.lod
        for neighbour in self.neighbours[face]:
            # print(neighbour.lod)
            lower_lod = min(lower_lod, neighbour.lod)
        return lower_lod

    def remove_detached_neighbours(self):
        valid = set()
        patch = self.patch
        for neighbour in self.neighbours[self.NORTH]:
            if neighbour.x1 > patch.x0 and neighbour.x0 < patch.x1:
                valid.add(neighbour)
        self.neighbours[self.NORTH] = valid
        valid = set()
        for neighbour in self.neighbours[self.SOUTH]:
            if neighbour.x1 > patch.x0 and neighbour.x0 < patch.x1:
                valid.add(neighbour)
        self.neighbours[self.SOUTH] = valid
        valid = set()
        for neighbour in self.neighbours[self.EAST]:
            if neighbour.y1 > patch.y0 and neighbour.y0 < patch.y1:
                valid.add(neighbour)
        self.neighbours[self.EAST] = valid
        valid = set()
        for neighbour in self.neighbours[self.WEST]:
            if neighbour.y1 > patch.y0 and neighbour.y0 < patch.y1:
                valid.add(neighbour)
        self.neighbours[self.WEST] = valid

    def split_opposite_neighbours(self, face, news):
        opposite = self.opposite_face[face]
        for neighbour_patch in self.neighbours[face]:
            neighbours = neighbour_patch.neighbours.neighbours[opposite]
            # print(f"Replace {self.patch} with {news} in {neighbours} of {neighbour_patch}")
            try:
                neighbours.remove(self.patch)
                for new in news:
                    neighbours.add(new)
            except KeyError:
                pass
            # print("Result", neighbours)

    def merge_opposite_neighbours(self, face, olds):
        opposite = self.opposite_face[face]
        for neighbour_patch in self.neighbours[face]:
            neighbours = neighbour_patch.neighbours.neighbours[opposite]
            # print(f"Replace {olds} with {self.patch} in {neighbours} of {neighbour_patch}")
            found = False
            for old in olds:
                try:
                    neighbours.remove(old)
                    found = True
                except KeyError:
                    pass
            if found and self.patch not in neighbours:
                neighbours.add(self.patch)
            # print("Result", neighbours)

    # TODO: This should be moved to QuadTreeNode
    def _do_collect_children(self, result, side):
        if len(self.patch.children) != 0:
            (bl, br, tr, tl) = self.patch.children
            if side == self.NORTH:
                result.add(tl)
                result.add(tr)
                tl.neighbours._do_collect_children(result, side)
                tr.neighbours._do_collect_children(result, side)
            elif side == self.EAST:
                result.add(tr)
                result.add(br)
                tr.neighbours._do_collect_children(result, side)
                br.neighbours._do_collect_children(result, side)
            elif side == self.SOUTH:
                result.add(bl)
                result.add(br)
                bl.neighbours._do_collect_children(result, side)
                br.neighbours._do_collect_children(result, side)
            elif side == self.WEST:
                result.add(tl)
                result.add(bl)
                tl.neighbours._do_collect_children(result, side)
                bl.neighbours._do_collect_children(result, side)

    def collect_children(self, side):
        result = set()
        self._do_collect_children(result, side)
        return result

    def split_neighbours(self, update):
        (bl, br, tr, tl) = self.patch.children
        tl.set_all_neighbours(self.get_neighbours(self.NORTH), set([tr]), set([bl]), self.get_neighbours(self.WEST))
        tr.set_all_neighbours(self.get_neighbours(self.NORTH), self.get_neighbours(self.EAST), set([br]), set([tl]))
        br.set_all_neighbours(set([tr]), self.get_neighbours(self.EAST), self.get_neighbours(self.SOUTH), set([bl]))
        bl.set_all_neighbours(set([tl]), set([br]), self.get_neighbours(self.SOUTH), self.get_neighbours(self.WEST))
        neighbours = self.get_all_neighbours()
        self.split_opposite_neighbours(self.NORTH, [tl, tr])
        self.split_opposite_neighbours(self.EAST, [tr, br])
        self.split_opposite_neighbours(self.SOUTH, [bl, br])
        self.split_opposite_neighbours(self.WEST, [tl, bl])
        for i, new in enumerate((tl, tr, br, bl)):
            # text = ['tl', 'tr', 'br', 'bl']
            # print("*** Child", text[i], '***')
            new.remove_detached_neighbours()
            new.calc_outer_tessellation_level(update)
        # print("Neighbours")
        for neighbour in neighbours:
            neighbour.remove_detached_neighbours()
            neighbour.calc_outer_tessellation_level(update)
        self.clear_all_neighbours()

    def merge_neighbours(self, update):
        north = self.collect_neighbours(self.NORTH)
        north_children = self.collect_children(self.NORTH)
        east = self.collect_neighbours(self.EAST)
        east_children = self.collect_children(self.EAST)
        south = self.collect_neighbours(self.SOUTH)
        south_children = self.collect_children(self.SOUTH)
        west = self.collect_neighbours(self.WEST)
        west_children = self.collect_children(self.WEST)
        self.set_all_neighbours(north, east, south, west)
        self.merge_opposite_neighbours(self.NORTH, north_children)
        self.merge_opposite_neighbours(self.EAST, east_children)
        self.merge_opposite_neighbours(self.SOUTH, south_children)
        self.merge_opposite_neighbours(self.WEST, west_children)
        self.calc_outer_tessellation_level(update)
        for neighbour in chain(north, east, south, west):
            neighbour.calc_outer_tessellation_level(update)

    def calc_outer_tessellation_level(self, update):
        for face in range(4):
            # print("Check face", self.text[face])
            lod = self.get_neighbour_lower_lod(face)
            delta = self.patch.lod - lod
            outer_level = max(0, self.patch.max_level - delta)
            new_level = 1 << outer_level
            dest = self.conv[face]
            if self.patch.tessellation_outer_level[dest] != new_level:
                # print("Change from", self.tessellation_outer_level[dest], "to", new_level)
                if self.patch not in update:
                    update.append(self.patch)
            self.patch.tessellation_outer_level[dest] = new_level
            # print("Level", self.text[face], ":", delta, 1 << outer_level)
