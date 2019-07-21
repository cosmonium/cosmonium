from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import CollisionPlane, CollisionNode
from panda3d.core import LPoint3d, LColor, LPlaned, LPlane

from .astro.orbits import FixedOrbit
from .astro.rotations import FixedRotation
from .astro.astro import app_to_abs_mag, abs_to_app_mag
from .astro.frame import AbsoluteReferenceFrame
from .astro import units

from .foundation import CompositeObject
from .systems import StellarSystem
from .bodies import StellarObject
from .octree import Octree
from .pointsset import PointsSet
from . import pstats
from . import settings
from .pstats import pstat

from time import time

class Universe(StellarSystem):
    def __init__(self, context):
        StellarSystem.__init__(self, 'Universe',
                               orbit=FixedOrbit(frame=AbsoluteReferenceFrame()),
                               rotation=FixedRotation(frame=AbsoluteReferenceFrame()),
                               description='Universe')
        self.visible = True
        self.octree_width = 100000.0 * units.Ly
        abs_mag = app_to_abs_mag(6.0, self.octree_width * Octree.coef)
        self.octree = Octree(0,
                             LPoint3d(10 * units.Ly, 10 * units.Ly, 10 * units.Ly),
                             self.octree_width,
                             abs_mag)
        self.octree_cells = []
        self.octree_old_cells = None
        self.octree_cells_to_clean = None
        self.update_id = 0
        self.to_update = []
        self.to_update_extra = []
        self.nb_cells = 0
        self.nb_leaves = 0
        self.nb_leaves_in_cells = 0
        self.dump_octree = False
        self.dump_octree_stats = False
        self.octree_points = PointsSet(use_sprites=False, use_sizes=False, points_size=20)
        self.octree_points.instance.reparentTo(self.context.annotation)

    def dumpOctree(self):
        self.dump_octree = True

    def dumpOctreeStats(self):
        self.dump_octree_stats = not self.dump_octree_stats

    def addPlanes(self):
        for plane in self.planes:
            colPlane = CollisionPlane(LPlane(*plane))
            planeNode = CollisionNode('planeNode')
            planeNode.addSolid(colPlane)
            planeNP = render.attachNewNode(planeNode)
            planeNP.show()

    def create_octree(self):
        print("Creating octree...")
        start = time()
        for child in self.children:
            self.octree.add(child, child.get_global_position(), child.get_abs_magnitude())
        end = time()
        print("Creation time:", end - start)

    def show_cell(self, cell):
        print(cell.center, cell.width)
        position = cell.center - self.context.observer.get_position()
        self.octree_points.add_point_scale(position, LColor(1, 1, 1, 1), 5)

        self.octree_points.add_point_scale(position + LPoint3d(-cell.width, -cell.width, -cell.width), LColor(1, 0, 1, 1), 5)
        self.octree_points.add_point_scale(position + LPoint3d(cell.width, -cell.width, -cell.width), LColor(1, 0, 1, 1), 5)
        self.octree_points.add_point_scale(position + LPoint3d(cell.width, -cell.width, cell.width), LColor(1, 0, 1, 1), 5)
        self.octree_points.add_point_scale(position + LPoint3d(-cell.width, -cell.width, cell.width), LColor(1, 0, 1, 1), 5)

        self.octree_points.add_point_scale(position + LPoint3d(cell.width, cell.width, -cell.width), LColor(1, 1, 0, 1), 5)
        self.octree_points.add_point_scale(position + LPoint3d(-cell.width, cell.width, -cell.width), LColor(0, 1, 0, 1), 5)
        self.octree_points.add_point_scale(position + LPoint3d(-cell.width, cell.width, cell.width), LColor(0, 1, 0, 1), 5)
        self.octree_points.add_point_scale(position + LPoint3d(cell.width, cell.width, cell.width), LColor(1, 1, 0, 1), 5)

    def _build_octree_leaves_list(self, octree, visible_leaf, invisible_leaf, limit, camera_pos):
        scale = settings.scale
        distance = (octree.center - camera_pos).length() - octree.radius
        if distance > 0.0:
            dimmest = app_to_abs_mag(limit, distance)
        else:
            dimmest = 99.0
        self.nb_leaves_in_cells += len(octree.leaves)
        for leaf in octree.leaves:
            skip = False
            abs_mag = leaf.abs_magnitude
            if abs_mag > dimmest:
                skip = True
            else:
                vector = leaf.global_position - camera_pos
                distance = vector.length()
                app_magnitude = abs_to_app_mag(abs_mag, distance)
                if app_magnitude > limit:
                    skip = True
                else:
                    for plane in self.planes:
                        plane_dist = plane.distToPlane(vector / scale)
                        if plane_dist > leaf.extend / scale:
                            skip = True
                            break
            if not skip:
                #if self.dump_octree: print("In view", leaf.names, app_magnitude, distance)
                visible_leaf(leaf)
            elif leaf.init_annotations:
                #TODO: Should make a better test than just checking annotations...
                invisible_leaf(leaf)

    @pstat
    def build_octree_leaves_list(self, visible_leaf, invisible_leaf, limit, camera_pos):
        for octree in self.octree_cells:
            if len(octree.leaves) > 0:
                self._build_octree_leaves_list(octree, visible_leaf, invisible_leaf, limit, camera_pos)

    def _build_octree_cells_list(self, octree, limit, camera_pos):
        octree.update_id = self.update_id
        self.octree_cells.append(octree)
        for child in octree.children:
            if child is not None:
                self.nb_cells += 1
                #if self.dump_octree: print("Checking", child.level, child.center)
                #if self.dump_octree and len(child.leaves) > 0: self.show_cell(child)
                vector = child.center - camera_pos
                length = vector.length()
                distance = length - child.radius
                if distance <= 0.0:
                    self.in_cells += 1
                    self._build_octree_cells_list(child, limit, camera_pos)
                else:
                    vector /= length
                    cosA = vector.dot(self.camera_vector)
                    if cosA > 0.0:
                        self.in_view += 1
                        skip = False
                        if True:
                            rel_position = (child.center - camera_pos) / settings.scale
                            radius = child.radius / settings.scale
                            for plane in self.planes:
                                plane_dist = plane.distToPlane(rel_position)
                                if plane_dist > radius:
                                    skip = True
                                    #if self.dump_octree: print("skip", plane.getNormal(), plane_dist, child.center, child.width / settings.scale)
                                    break
                        if not skip and abs_to_app_mag(child.max_magnitude, distance) < limit:
                            self._build_octree_cells_list(child, limit, camera_pos)

    @pstat
    def do_build_octree_cells_list(self, limit, camera_pos):
        self._build_octree_cells_list(self.octree, limit, camera_pos)

    def build_octree_cells_list(self, limit):
        if self.dump_octree: self.octree_points.reset()
        camera_pos = self.context.observer.get_position()
        frustum = self.context.observer.realCamLens.make_bounds()
        self.planes = []
        for i in range(1, 6):
            plane = LPlaned(*(frustum.getPlane(i) * self.context.cam.getMat()))
            self.planes.append(plane)
        self.camera_vector = self.context.observer.get_camera_vector()
        self.octree_old_cells = self.octree_cells
        self.octree_cells = []
        self.to_update = []
        self.to_update_extra = []
        self.to_remove = []
        self.update_id += 1
        self.nb_cells = 1
        self.nb_leaves = 0
        self.nb_leaves_in_cells = 0
        self.in_cells = 0
        self.in_view = 0
        cells_list_start = time()
        self.do_build_octree_cells_list(limit, camera_pos)
        self.octree_cells_to_clean = []
        for cell in self.octree_old_cells:
            if cell.update_id != self.update_id:
                self.octree_cells_to_clean.append(cell)
        cells_list_end = time()
        leaves_list_start = time()
        self.build_octree_leaves_list(self.to_update.append, self.to_remove.append, limit, camera_pos)
        leaves_list_end = time()
        if self.dump_octree_stats:
            print(len(self.to_update), '(', self.nb_leaves, ',', self.nb_leaves_in_cells, ')', len(self.octree_cells), '(', self.nb_cells, ')')
            print("Cells :", (cells_list_end - cells_list_start) * 1000, 'ms (',  (cells_list_end - cells_list_start) / self.nb_cells * 1000 * 1000, 'us)')
            if self.nb_leaves > 0:
                print("Leaves :", (leaves_list_end - leaves_list_start) * 1000, 'ms (', (leaves_list_end - leaves_list_start) / self.nb_leaves * 1000 * 1000, 'us)')
            print("To clean", len(self.octree_cells_to_clean))
            print()
        cells = pstats.levelpstat('cells')
        leaves = pstats.levelpstat('leaves')
        cleans = pstats.levelpstat('cleans')
        visibles = pstats.levelpstat('visibles')
        in_cells = pstats.levelpstat('in_cells')
        in_view = pstats.levelpstat('in_view')
        cells.set_level(self.nb_cells)
        leaves.set_level(self.nb_leaves_in_cells)
        cleans.set_level(len(self.octree_cells_to_clean))
        visibles.set_level(len(self.to_update))
        in_cells.set_level(self.in_cells)
        in_view.set_level(self.in_view)
        if self.dump_octree:
            self.octree_points.update()
            print(self.octree_points.points)
        self.dump_octree = False

    def _first_update(self, octree):
        for child in octree.children:
            if child is not None:
                self._first_update(child)
                for leaf in child.leaves:
                    leaf.update(0)

    def first_update(self):
        self._first_update(self.octree)

    def add_extra_to_list(self, *elems):
        for extra in elems:
            if extra is not None:
                self.to_update_extra.append(extra)

    def update(self, time):
        CompositeObject.update(self, time)
        for leaf in self.to_update:
            if not leaf.update_frozen:
                #print("Update", leaf.get_name())
                leaf.update(time)
        for extra in self.to_update_extra:
            #print("Update", extra.get_name())
            extra.update(time)

    def update_obs(self, camera_pos):
        CompositeObject.update_obs(self, camera_pos)
        self.nearest_system = None
        for leaf in self.to_update:
            leaf.update_obs(camera_pos)
            if self.nearest_system is None or leaf.distance_to_obs < self.nearest_system.distance_to_obs:
                self.nearest_system = leaf
        for extra in self.to_update_extra:
            extra.update_obs(camera_pos)

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

    def clean_octree_cells(self):
        for cell in self.octree_cells_to_clean:
            for leaf in cell.leaves:
                leaf.remove_instance()

    def get_distance(self, time):
        return 0

    def get_global_position(self):
        return LPoint3d()

    def get_local_position(self):
        return self.orbit_position
    
    def get_abs_rotation(self):
        return self.orientation
