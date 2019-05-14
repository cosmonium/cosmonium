from __future__ import print_function

from panda3d.core import Texture, Filename
from direct.task.Task import Task
try:
    import queue
except ImportError:
    import Queue as queue
import sys
import traceback

# These will be initialized in cosmonium base class
asyncTextureLoader = None
syncTextureLoader = None

class AsyncMethod():
    def __init__(self, name, base, method, callback):
        self.base = base
        self.method = method
        self.callback = callback
        self.done = False
        self.base.taskMgr.setupTaskChain(name,
                                         numThreads = 1,
                                         tickClock = False,
                                         threadPriority = None,
                                         frameBudget = -1,
                                         frameSync = False,
                                         timeslicePriority = True)

        self.process_task = self.base.taskMgr.add(self.processTask, name + 'ProcessTask', taskChain=name)
        self.callback_task = self.base.taskMgr.add(self.callbackTask, name + 'CallbackTask')

    def processTask(self, task):
        #TODO: Investigate why a task aborted by exception is restarted...
        try:
            self.method()
        except Exception:
            traceback.print_exc()
            raise SystemExit
        self.done = True
        return task.done

    def callbackTask(self, task):
        if not self.done:
            return task.cont
        else:
            self.callback()
            return task.done

class AsyncLoader():
    def __init__(self, base, name):
        self.base = base
        self.in_queue = queue.Queue()
        self.cb_queue = queue.Queue()
        self.base.taskMgr.setupTaskChain(name,
                                         numThreads = 1,
                                         tickClock = False,
                                         threadPriority = None,
                                         frameBudget = -1,
                                         frameSync = False,
                                         timeslicePriority = True)

        self.process_task = self.base.taskMgr.add(self.processTask, name + 'ProcessTask', taskChain=name)
        self.callback_task = self.base.taskMgr.add(self.callbackTask, name + 'CallbackTask')

    def remove(self):
        self.base.taskMgr.remove(self.process_task)
        self.process_task = None
        self.base.taskMgr.remove(self.callback_task)
        self.callback_task = None

    def add_job(self, func, fargs, callback, cb_args):
        job = [func, fargs, callback, cb_args]
        self.in_queue.put(job)

    def processTask(self, task):
        try:
            job = self.in_queue.get_nowait()
            (func, fargs, callback, cb_args) = job
            result = func(*fargs)
            self.cb_queue.put([callback, result, cb_args])
        except queue.Empty:
            pass
        return Task.cont

    def callbackTask(self, task):
        try:
            while True:
                job = self.cb_queue.get_nowait()
                (callback, result, cb_args) = job
                callback(result, *cb_args)
        except queue.Empty:
            pass
        return Task.cont

class AsyncTextureLoader(AsyncLoader):
    def __init__(self, base):
        AsyncLoader.__init__(self, base, 'TextureLoader')

    def load_texture(self, filename, callback, args):
        self.add_job(self.do_load_texture, [filename], callback, args)

    def do_load_texture(self, filename):
        tex = Texture()
        tex.read(Filename.from_os_specific(filename).get_fullpath())
        return tex

class SyncTextureLoader():
    def load_texture(self, filename):
        texture = None
        try:
            texture = loader.loadTexture(Filename.from_os_specific(filename).get_fullpath())
        except IOError:
            print("Could not load texture", filename)
        return texture

if __name__ == '__main__':
    import direct.directbase.DirectStart
    import sys

    loader = AsyncTextureLoader(base)

    def callback(texture, args):
        print(texture, args)
        sys.exit()

    def tick(task):
        frame = globalClock.getFrameCount()
        print(frame, 'tick')
        return task.cont

    taskMgr.add(tick, 'tick')

    loader.load_texture('textures/earth.png', callback, ["args"])
    base.accept('escape', sys.exit)
    base.run()
