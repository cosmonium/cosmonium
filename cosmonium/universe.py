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

from panda3d.core import LPoint3d, LQuaterniond

from .astro.orbits import FixedOrbit
from .astro.rotations import FixedRotation
from .astro.astro import app_to_abs_mag
from .astro.frame import AbsoluteReferenceFrame
from .astro import units

from .foundation import CompositeObject
from .systems import StellarSystem
from .octree import OctreeNode, OctreeLeaf, InfiniteFrustum, VisibleObjectsTraverser, hasOctreeLeaf
from .pstats import pstat

from math import sqrt
from time import time

class Universe(StellarSystem):
    def __init__(self, context):
        StellarSystem.__init__(self, 'Universe',
                               orbit=FixedOrbit(frame=AbsoluteReferenceFrame()),
                               rotation=FixedRotation(LQuaterniond(), frame=AbsoluteReferenceFrame()),
                               description='Universe')
        self.visible = True
        self.octree_width = 100000.0 * units.Ly
        abs_mag = app_to_abs_mag(6.0, self.octree_width * sqrt(3))
        self.octree = OctreeNode(0,
                             LPoint3d(10 * units.Ly, 10 * units.Ly, 10 * units.Ly),
                             self.octree_width,
                             abs_mag)
        self.update_id = 0
        self.previous_leaves = []
        self.to_update_leaves = []
        self.to_update = []
        self.to_update_extra = []
        self.to_remove = []
        self.nb_cells = 0
        self.nb_leaves = 0
        self.nb_leaves_in_cells = 0
        self.dump_octree = False
        self.dump_octree_stats = False

    def get_fullname(self, separator='/'):
        return ''

    def dumpOctree(self):
        self.octree.dump_octree()

    def log_octree(self):
        self.dump_octree = True

    def dumpOctreeStats(self):
        self.dump_octree_stats = not self.dump_octree_stats

    def create_octree(self):
        print("Creating octree...")
        start = time()
        for child in self.children:
            self.octree.add(OctreeLeaf(child, child.get_global_position(), child.get_abs_magnitude(), child.get_extend()))
        end = time()
        print("Creation time:", end - start)

    def build_octree_cells_list(self, limit):
        self.update_id += 1
        self.previous_leaves = self.to_update_leaves
        pos = self.context.observer.get_position()
        mat = self.context.cam.getMat()
        bh = self.context.observer.realCamLens.make_bounds()
        f = InfiniteFrustum(bh, mat, pos)
        t = VisibleObjectsTraverser(f, 6.0, self.update_id)
        self.octree.traverse(t)
        self.to_update_leaves = t.get_leaves()
        self.to_remove = []
        if hasOctreeLeaf:
            self.to_update = list(map(lambda x: x.get_object(), self.to_update_leaves))
            for old in self.previous_leaves:
                if old.get_update_id() != self.update_id:
                    self.to_remove.append(old.get_object())
        else:
            self.to_update = self.to_update_leaves
            for old in self.previous_leaves:
                if old.update_id != self.update_id:
                    self.to_remove.append(old)
        self.octree_cells_to_clean = []
        self.to_update_extra = []
#         cells = pstats.levelpstat('cells')
#         leaves = pstats.levelpstat('leaves')
#         cleans = pstats.levelpstat('cleans')
#         visibles = pstats.levelpstat('visibles')
#         in_cells = pstats.levelpstat('in_cells')
#         in_view = pstats.levelpstat('in_view')
#         cells.set_level(self.nb_cells)
#         leaves.set_level(self.nb_leaves_in_cells)
#         cleans.set_level(len(self.octree_cells_to_clean))
#         visibles.set_level(len(self.to_update))
#         in_cells.set_level(self.in_cells)
#         in_view.set_level(self.in_view)

    def first_update(self):
        for child in self.children:
            child.first_update(self.context.time.time_full)

    def first_update_obs(self, observer):
        for child in self.children:
            child.first_update_obs(observer)

    def add_extra_to_list(self, *elems):
        for extra in elems:
            if extra is not None:
                self.to_update_extra.append(extra)

    def update(self, time, dt):
        CompositeObject.update(self, time, dt)
        for leaf in self.to_update:
            if isinstance(leaf, StellarSystem):
                #print("Update system", leaf.get_name())
                leaf.update(time, dt)
            elif not leaf.update_frozen:
                #print("Update", leaf.get_name())
                leaf.update(time, dt)
        for extra in self.to_update_extra:
            #print("Update", extra.get_name())
            extra.update(time, dt)

    def update_obs(self, observer):
        CompositeObject.update_obs(self, observer)
        self.nearest_system = None
        for leaf in self.to_update:
            leaf.update_obs(observer)
            if self.nearest_system is None or leaf.distance_to_obs < self.nearest_system.distance_to_obs:
                self.nearest_system = leaf
        for extra in self.to_update_extra:
            extra.update_obs(observer)

    def check_visibility(self, pixel_size):
        CompositeObject.check_visibility(self, pixel_size)
        for leaf in self.to_update:
            leaf.check_visibility(pixel_size)
        for extra in self.to_update_extra:
            pass#extra.check_visibility(pixel_size)

    def check_settings(self):
        CompositeObject.check_settings(self)
        for leaf in self.to_update:
            leaf.check_settings()
        for extra in self.to_update_extra:
            pass#extra.check_settings()
        for component in self.components:
            component.check_settings()

    def check_and_update_instance(self, camera_pos, orientation, pointset):
        CompositeObject.check_and_update_instance(self, camera_pos, orientation, pointset)
        for leaf in self.to_update:
            leaf.check_and_update_instance(camera_pos, orientation, pointset)
        for leaf in self.to_remove:
            leaf.remove_instance()

    def get_distance(self, time):
        return 0

    def get_global_position(self):
        return LPoint3d()
    
    def get_abs_rotation(self):
        return self._orientation
