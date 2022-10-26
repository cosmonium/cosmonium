#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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


from panda3d.core import Texture, Filename
from direct.stdpy import threading
from direct.task.Task import Task, AsyncFuture

from queue import Queue, Empty


# These will be initialized in cosmonium base class
asyncTextureLoader = None
syncTextureLoader = None


class AsyncMethod():
    def __init__(self, name, base, method, callback):
        self.base = base
        self.method = method
        self.callback = callback
        self.done = False
        self.error = None
        self.process_thread = threading.Thread(target=self.processTask, name= name + 'ProcessThead')
        self.callback_task = self.base.taskMgr.add(self.callbackTask, name + 'CallbackTask')
        self.process_thread.start()

    def processTask(self):
        try:
            self.method()
        except Exception as e:
            self.error = e
        self.done = True

    def callbackTask(self, task):
        if not self.done:
            return task.cont
        else:
            if self.error:
                raise self.error
            self.callback()
            return task.done


class AsyncLoader():
    def __init__(self, base, name):
        self.base = base
        self.in_queue = Queue()
        self.cb_queue = Queue()
        self.process_thread = threading.Thread(target=self.processTask, name= name + 'ProcessThead', daemon=True)
        self.callback_task = self.base.taskMgr.add(self.callbackTask, name + 'CallbackTask')
        self.process_thread.start()

    def add_job(self, func, fargs):
        future = AsyncFuture()
        job = [func, fargs, future]
        self.in_queue.put(job)
        return future

    def processTask(self):
        while True:
            try:
                job = self.in_queue.get()
                (func, fargs, future) = job
                if not future.cancelled():
                    result = func(*fargs)
                    self.cb_queue.put([future, result])
                else:
                    #print("job cancelled")
                    pass
            except Empty:
                pass

    def callbackTask(self, task):
        try:
            while True:
                job = self.cb_queue.get_nowait()
                (future, result) = job
                if not future.cancelled():
                    future.set_result(result)
                else:
                    #print("Result cancelled")
                    pass
        except Empty:
            pass
        return Task.cont


class AsyncTextureLoader(AsyncLoader):
    def __init__(self, base):
        AsyncLoader.__init__(self, base, 'TextureLoader')

    async def load_texture(self, filename, alpha_filename):
        return await self.add_job(self.do_load_texture, [filename, alpha_filename])

    async def load_texture_array(self, textures):
        return await self.add_job(self.do_load_texture_array, [textures])

    def do_load_texture(self, filename, alpha_filename):
        tex = Texture()
        panda_filename = Filename.from_os_specific(filename)
        if alpha_filename is not None:
            panda_alpha_filename = Filename.from_os_specific(alpha_filename)
        else:
            panda_alpha_filename = Filename('')
        tex.read(fullpath=panda_filename, alpha_fullpath=panda_alpha_filename,
                 primary_file_num_channels=0, alpha_file_channel=0)
        return tex

    def do_load_texture_array(self, textures):
        tex = Texture()
        tex.setup_2d_texture_array(len(textures))
        for (page, texture) in enumerate(textures):
            filename = texture.source.texture_filename(None)
            if filename is not None:
                panda_filename = Filename.from_os_specific(filename)
                tex.read(fullpath=panda_filename, z=page, n=0, read_pages=False, read_mipmaps=False)
            else:
                print("Could not find", texture.source.texture_name(None))
                image = texture.create_default_image()
                tex.load(image, z=page, n=0)
        return tex


class SyncTextureLoader():
    def load_texture(self, filename, alpha_filename=None):
        texture = None
        try:
            panda_filename = Filename.from_os_specific(filename).get_fullpath()
            if alpha_filename is not None:
                panda_alpha_filename = Filename.from_os_specific(filename).get_fullpath()
            else:
                panda_alpha_filename = None
            texture = loader.loadTexture(panda_filename, alphaPath=panda_alpha_filename)
        except IOError:
            print("Could not load texture", filename)
        return texture

    def load_texture_array(self, textures):
        tex = Texture()
        tex.setup_2d_texture_array(len(textures))
        for (page, texture) in enumerate(textures):
            filename = texture.source.texture_filename(None)
            if filename is not None:
                panda_filename = Filename.from_os_specific(filename)
                tex.read(fullpath=panda_filename, z=page, n=0, read_pages=False, read_mipmaps=False)
            else:
                print("Could not find", texture.source.texture_name(None))
                image = texture.create_default_image()
                tex.load(image, z=page, n=0)
        return tex
