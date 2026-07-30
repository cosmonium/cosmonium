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


from __future__ import annotations

from abc import ABC, abstractmethod
from itertools import chain
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .patchedshapes import PatchBase


class PatchNeighboursInterface(ABC):
    __slots__ = ()

    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    opposite_side = [SOUTH, WEST, NORTH, EAST]
    text = ['North', 'East', 'South', 'West']
    conv = [WEST, SOUTH, EAST, NORTH]

    @abstractmethod
    def set_neighbours(self, side: int, neighbours: set[PatchBase]) -> None:
        """Set the neighbours for the given side."""
        ...

    @abstractmethod
    def add_neighbour(self, side: int, neighbour) -> None:
        """Add a neighbour in the set of neighbours for the given side."""
        ...

    @abstractmethod
    def get_neighbours(self, side: int) -> set[PatchBase]:
        """Return a copy of neighbours for the given side."""
        ...

    @abstractmethod
    def collect_neighbours(self, side: int) -> set[PatchBase]:
        """Collect the list of leaf patches adjacent to the given side"""
        ...

    @abstractmethod
    def set_all_neighbours(
        self, north: set[PatchBase], east: set[PatchBase], south: set[PatchBase], west: set[PatchBase]
    ) -> None:
        """Set all the neighbours for this patch."""
        ...

    @abstractmethod
    def clear_all_neighbours(self) -> None:
        """Clear all the neighbours of this patch."""
        ...

    @abstractmethod
    def get_all_neighbours(self) -> set[PatchBase]:
        """Return the set of all the neighbours of this patch."""
        ...

    @abstractmethod
    def get_neighbour_lower_lod(self, side: int) -> int:
        """Get the lowest LOD value among neighbours on a face."""
        ...

    @abstractmethod
    def remove_detached_neighbours(self) -> None:
        """Remove neighbours that are not spatially adjacent."""
        ...

    @abstractmethod
    def split_neighbours(self, update: list[PatchBase]) -> None:
        """Split the neighbours of this patch into their respective children."""
        ...

    @abstractmethod
    def merge_neighbours(self, update: list[PatchBase]) -> None:
        """Merge the neighbours of the four children of this patch."""
        ...

    @abstractmethod
    def calc_outer_tessellation_level(self, update: list[PatchBase]) -> None:
        """
        Recalculate the four outer tessellation levels for this patch and
        add it to the update set if any has changed.
        """
        ...


class PatchNoNeighbours(PatchNeighboursInterface):
    """Drop-in PatchNeighbours class to use when no neighbour tracking is wanted"""

    __slots__ = ('patch',)

    def __init__(self, patch: PatchBase):
        self.patch = patch

    def set_neighbours(self, side: int, neighbours: set[PatchBase]) -> None:
        pass

    def add_neighbour(self, side: int, neighbour) -> None:
        pass

    def get_neighbours(self, side: int) -> set[PatchBase]:
        return set()

    def collect_neighbours(self, side: int) -> set[PatchBase]:
        return set()

    def set_all_neighbours(
        self, north: set[PatchBase], east: set[PatchBase], south: set[PatchBase], west: set[PatchBase]
    ) -> None:
        pass

    def clear_all_neighbours(self) -> None:
        pass

    def get_all_neighbours(self) -> set[PatchBase]:
        return set()

    def get_neighbour_lower_lod(self, side: int) -> int:
        return self.patch.lod

    def remove_detached_neighbours(self) -> None:
        pass

    def split_neighbours(self, update: list[PatchBase]) -> None:
        pass

    def merge_neighbours(self, update: list[PatchBase]) -> None:
        pass

    def calc_outer_tessellation_level(self, update: list[PatchBase]) -> None:
        pass


class PatchNeighbours(PatchNeighboursInterface):
    __slots__ = ('patch', 'neighbours')

    def __init__(self, patch: PatchBase):
        self.patch = patch
        self.neighbours: list[set[PatchBase]] = [set(), set(), set(), set()]

    def set_neighbours(self, side: int, neighbours: set[PatchBase]) -> None:
        self.neighbours[side] = neighbours

    def add_neighbour(self, side: int, neighbour) -> None:
        if neighbour not in self.neighbours[side]:
            self.neighbours[side].add(neighbour)

    def get_neighbours(self, side: int) -> set[PatchBase]:
        return set(self.neighbours[side])

    def _collect_neighbours(self, result: set[PatchBase], side: int) -> None:
        if len(self.patch.children) != 0:
            bl, br, tr, tl = self.patch.children
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

    def collect_neighbours(self, side: int) -> set[PatchBase]:
        result: set[PatchBase] = set()
        self._collect_neighbours(result, side)
        return result

    def set_all_neighbours(
        self, north: set[PatchBase], east: set[PatchBase], south: set[PatchBase], west: set[PatchBase]
    ) -> None:
        self.neighbours[self.NORTH] = north
        self.neighbours[self.EAST] = east
        self.neighbours[self.SOUTH] = south
        self.neighbours[self.WEST] = west

    def clear_all_neighbours(self) -> None:
        self.neighbours = [set(), set(), set(), set()]

    def get_all_neighbours(self) -> set[PatchBase]:
        result: set[PatchBase] = set()
        for neighbour in self.neighbours:
            result |= neighbour
        return result

    def get_neighbour_lower_lod(self, side: int) -> int:
        lower_lod = self.patch.lod
        for neighbour in self.neighbours[side]:
            # print(neighbour.lod)
            lower_lod = min(lower_lod, neighbour.lod)
        return lower_lod

    def remove_detached_neighbours(self) -> None:
        patch = self.patch

        self.neighbours[self.NORTH] = {n for n in self.neighbours[self.NORTH] if n.x1 > patch.x0 and n.x0 < patch.x1}
        self.neighbours[self.SOUTH] = {n for n in self.neighbours[self.SOUTH] if n.x1 > patch.x0 and n.x0 < patch.x1}
        self.neighbours[self.EAST] = {n for n in self.neighbours[self.EAST] if n.y1 > patch.y0 and n.y0 < patch.y1}
        self.neighbours[self.WEST] = {n for n in self.neighbours[self.WEST] if n.y1 > patch.y0 and n.y0 < patch.y1}

    def split_opposite_neighbours(self, side: int, news: list[PatchBase]) -> None:
        """Update opposite neighbours when splitting."""
        opposite = self.opposite_side[side]
        for neighbour_patch in self.neighbours[side]:
            neighbours = neighbour_patch.neighbours.neighbours[opposite]
            try:
                neighbours.remove(self.patch)
                for new in news:
                    neighbours.add(new)
            except KeyError:
                # Patch was not in the neighbour list of the opposite patch
                pass

    def merge_opposite_neighbours(self, side: int, olds: set[PatchBase]) -> None:
        """Update opposite neighbours when merging."""
        opposite = self.opposite_side[side]
        for neighbour_patch in self.neighbours[side]:
            neighbours = neighbour_patch.neighbours.neighbours[opposite]
            found = False
            for old in olds:
                try:
                    neighbours.remove(old)
                    found = True
                except KeyError:
                    pass
            if found and self.patch not in neighbours:
                neighbours.add(self.patch)

    # TODO: This should be moved to QuadTreeNode
    def _do_collect_children(self, result: set[PatchBase], side: int) -> None:
        if len(self.patch.children) != 0:
            bl, br, tr, tl = self.patch.children
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

    def collect_children(self, side: int) -> set[PatchBase]:
        """Collect all the child patches of this patch for the given side for all levels."""
        result: set[PatchBase] = set()
        self._do_collect_children(result, side)
        return result

    def split_neighbours(self, update: list[PatchBase]) -> None:
        bl, br, tr, tl = self.patch.children

        north_neighbours = self.get_neighbours(self.NORTH)
        east_neighbours = self.get_neighbours(self.EAST)
        south_neighbours = self.get_neighbours(self.SOUTH)
        west_neighbours = self.get_neighbours(self.WEST)

        tl.neighbours.set_all_neighbours(north_neighbours, {tr}, {bl}, west_neighbours)
        tr.neighbours.set_all_neighbours(north_neighbours, east_neighbours, {br}, {tl})
        br.neighbours.set_all_neighbours({tr}, east_neighbours, south_neighbours, {bl})
        bl.neighbours.set_all_neighbours({tl}, {br}, south_neighbours, west_neighbours)

        old_neighbours = north_neighbours | east_neighbours | south_neighbours | west_neighbours

        self.split_opposite_neighbours(self.NORTH, [tl, tr])
        self.split_opposite_neighbours(self.EAST, [tr, br])
        self.split_opposite_neighbours(self.SOUTH, [bl, br])
        self.split_opposite_neighbours(self.WEST, [tl, bl])
        for child in (tl, tr, br, bl):
            child.neighbours.remove_detached_neighbours()
            child.neighbours.calc_outer_tessellation_level(update)
        for patch in old_neighbours:
            patch.neighbours.remove_detached_neighbours()
            patch.neighbours.calc_outer_tessellation_level(update)
        self.clear_all_neighbours()

    def merge_neighbours(self, update: list[PatchBase]) -> None:
        # We collect all the child patches for all sub level to support multi-level merging
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
        for patch in chain(north, east, south, west):
            patch.neighbours.calc_outer_tessellation_level(update)

    def calc_outer_tessellation_level(self, update: list[PatchBase]) -> None:
        for side in range(4):
            lod = self.get_neighbour_lower_lod(side)
            delta = self.patch.lod - lod
            outer_level = max(0, self.patch.max_level - delta)
            new_level = 1 << outer_level
            dest = self.conv[side]
            if self.patch.tessellation_outer_level[dest] != new_level:
                if self.patch not in update:
                    update.append(self.patch)
            self.patch.tessellation_outer_level[dest] = new_level
