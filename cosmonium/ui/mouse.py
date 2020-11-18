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

from panda3d.core import CollisionTraverser, CollisionNode, LPoint2
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import GeomNode, LColor, Texture
from direct.showbase.DirectObject import DirectObject

from direct.task.Task import Task

from .. import settings
from cosmonium.utils import color_to_int
from cosmonium.catalogs import objectsDB

class Mouse(DirectObject):
    def __init__(self, base, oid_texture):
        self.base = base
        self.picking_texture = oid_texture
        self.ui = None
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = self.base.cam.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(CollisionNode.getDefaultCollideMask() | GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
        #self.picker.showCollisions(render)
        self.mouse1_pos = None
        self.mouse3_pos = None
        self.accept('mouse1', self.mouse1_press)
        self.accept('mouse1-up', self.mouse1_release)
        self.accept('mouse3', self.mouse3_press)
        self.accept('mouse3-up', self.mouse3_release)
        if settings.mouse_over:
            taskMgr.add(self.mouse_task, 'mouse-task')
        self.over = None

    def set_ui(self, ui):
        self.ui = ui

    def mouse1_press(self):
        if self.base.mouseWatcherNode.hasMouse():
            self.mouse1_pos = LPoint2(self.base.mouseWatcherNode.get_mouse())

    def mouse1_release(self):
        if self.base.mouseWatcherNode.hasMouse():
            mpos = self.base.mouseWatcherNode.get_mouse()
            if self.mouse1_pos is not None and self.mouse1_pos.get_x() == mpos.get_x() and self.mouse1_pos.get_y() == mpos.get_y():
                self.ui.left_click()
        self.mouse1_pos = None

    def mouse3_press(self):
        if self.base.mouseWatcherNode.hasMouse():
            self.mouse3_pos = LPoint2(self.base.mouseWatcherNode.get_mouse())

    def mouse3_release(self):
        if self.base.mouseWatcherNode.hasMouse():
            mpos = self.base.mouseWatcherNode.get_mouse()
            print(self.mouse3_pos, mpos)
            if self.mouse3_pos is not None and self.mouse3_pos.get_x() == mpos.get_x() and self.mouse3_pos.get_y() == mpos.get_y():
                self.ui.right_click()
        self.mouse3_pos = None

    def find_over_ray(self):
        over = None
        if self.base.mouseWatcherNode.hasMouse():
            mpos = self.base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(self.base.camNode, mpos.getX(), mpos.getY())
            self.picker.traverse(render)
            if self.pq.getNumEntries() > 0:
                self.pq.sortEntries()
                np = self.pq.getEntry(0).getIntoNodePath().findNetPythonTag('owner')
                owner = np.getPythonTag('owner')
                over = owner
                np = self.pq.getEntry(0).getIntoNodePath().findNetPythonTag('patch')
                if np is not None:
                    self.patch = np.getPythonTag('patch')
                else:
                    self.patch = None
        return over

    def find_over_color(self):
        over = None
        if self.base.mouseWatcherNode.hasMouse():
            mpos = self.base.mouseWatcherNode.getMouse()
            self.base.graphicsEngine.extract_texture_data(self.picking_texture, self.base.win.gsg)
            texture_peeker = self.picking_texture.peek()
            if texture_peeker is not None:
                x = (mpos.get_x() + 1) / 2
                y = (mpos.get_y() + 1) / 2
                value = LColor()
                texture_peeker.lookup(value, x, y)
                oid = color_to_int(value)
                if oid != 0:
                    over = objectsDB.get_oid(oid)
                    if over is None:
                        print("Unknown oid", oid, value)
        return over

    def find_over(self):
        if settings.color_picking:
            over_color = self.find_over_color()
        else:
            over_color = None
        over_ray = self.find_over_ray()
        over = over_color
        if over_ray is not None:
            if over is None or over.distance_to_obs > over_ray.distance_to_obs:
                over = over_ray
        if hasattr(over, "primary") and over.primary is not None:
            over = over.primary
        return over

    def get_over(self):
        if settings.mouse_over:
            over = self.over
        else:
            over = self.find_over()
        return over

    def mouse_task(self, task):
        if self.base.mouseWatcherNode.hasMouse():
            self.over = self.find_over()
        return Task.cont

