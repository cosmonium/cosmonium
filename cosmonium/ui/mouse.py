from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import GeomNode

from direct.task.Task import Task

from .. import settings

class Mouse(object):
    def __init__(self, base):
        self.base = base
        if settings.mouse_over:
            taskMgr.add(self.mouse_task, 'mouse-task')
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = self.base.cam.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(CollisionNode.getDefaultCollideMask() | GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
        #self.picker.showCollisions(render)
        self.over = None

    def find_over(self):
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

    def get_over(self):
        if settings.mouse_over:
            over = self.over
        else:
            over = self.find_over()
        return over

    def mouse_task(self, task):
        if self.mouseWatcherNode.hasMouse():
            self.over = self.find_over()
        return Task.cont

