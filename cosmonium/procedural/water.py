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

from panda3d.core import CardMaker
from panda3d.core import CullFaceAttrib
from panda3d.core import Plane, PlaneNode, Point3, Vec3, Vec4
from panda3d.core import RenderState, Shader, Filename
from panda3d.core import Texture, TransparencyAttrib

from ..foundation import BaseObject
from ..dircontext import defaultDirContext
from .. import settings

class WaterNode():
    buffer = None
    texture = None
    watercamNP = None
    z = None
    observer = None
    task = None

    def __init__(self, x, y, size, scale, parent):
        self.x = x
        self.y = y
        self.size = size
        self.scale = 1.0 #scale
        self.parent = parent
        self.waterNP = None

    def create_instance(self):
        self.create_buffer()
        # Water surface
        maker = CardMaker('water')
        maker.setFrame(0, 1, 0, 1)

        self.waterNP = self.parent.instance.attachNewNode(maker.generate())
        self.waterNP.hide(BaseObject.AllCamerasMask)
        self.waterNP.show(BaseObject.DefaultCameraFlag)
        self.waterNP.setHpr(0, -90, 0)
        self.waterNP.setPos(self.x, self.y, self.z)
        self.waterNP.setScale(self.size, self.size, 1.0)
        self.waterNP.setTransparency(TransparencyAttrib.MAlpha)
        vertex_shader = defaultDirContext.find_shader('water-vertex.glsl')
        fragment_shader = defaultDirContext.find_shader('water-fragment.glsl')
        self.waterNP.setShader(Shader.load(Shader.SL_GLSL,
                                           vertex=Filename.from_os_specific(vertex_shader).get_fullpath(),
                                           fragment=Filename.from_os_specific(fragment_shader).get_fullpath()))
        self.waterNP.setShaderInput('wateranim', Vec4(0.03, -0.015, self.scale, 0)) # vx, vy, scale, skip
        # offset, strength, refraction factor (0=perfect mirror, 1=total refraction), refractivity
        self.waterNP.setShaderInput('waterdistort', Vec4(0.4, 1.0, 0.25, 0.45))
        self.waterNP.setShaderInput('time', 0)

        self.waterNP.setShaderInput('reflection_tex', self.texture)

        # distortion texture
        tex1 = loader.loadTexture('textures/water.png')
        self.waterNP.setShaderInput('distortion_tex', tex1)

    @classmethod
    def create_buffer(cls):
        if cls.buffer is None:
            cls.buffer = base.win.makeTextureBuffer('waterBuffer', 512, 512)
            cls.buffer.setClearColor(Vec4(0, 0, 0, 1))
            cls.texture = cls.buffer.getTexture()
            cls.texture.setWrapU(Texture.WMClamp)
            cls.texture.setWrapV(Texture.WMClamp)

    @classmethod
    def create_cam(cls):
        cls.create_buffer()
        if cls.watercamNP is None:
            cfa = CullFaceAttrib.makeReverse()
            rs = RenderState.make(cfa)

            cls.watercamNP = base.makeCamera(cls.buffer, camName='waterCam')
            cls.watercamNP.reparentTo(render)

            #sa = ShaderAttrib.make()
            #sa = sa.setShader(loader.loadShader('shaders/splut3Clipped.sha') )

            cam = cls.watercamNP.node()
            cam.set_camera_mask(BaseObject.WaterCameraFlag)
            cam.getLens().setFov(base.camLens.getFov())
            cam.getLens().setNear(0.01)
            cam.getLens().setFar(float("inf"))
            cam.setInitialState(rs)
            cam.setTagStateKey('Clipped')
            #cam.setTagState('True', RenderState.make(sa))
            #cam.showFrustum()

            cls.task = taskMgr.add(cls.update, "waterTask")

    @classmethod
    def update(cls, task):
        # Reflection plane
        if settings.camera_at_origin:
            camera_offset = -cls.observer.get_local_position()[2] + cls.z
        else:
            camera_offset = cls.z
        waterPlane = Plane(Vec3(0, 0, camera_offset + 1), Point3(0, 0, camera_offset))
        # update matrix of the reflection camera
        if not settings.debug_lod_freeze and cls.watercamNP is not None:
            mc = base.camera.getMat()
            mf = waterPlane.getReflectionMat()
            cls.watercamNP.setMat(mc * mf)
        return task.cont

    def remove_instance(self):
        if self.waterNP:
            self.waterNP.removeNode()
            self.waterNP = None

    @classmethod
    def remove_cam(cls):
        if cls.watercamNP:
            cls.watercamNP.removeNode()
            cls.watercamNP = None
        if cls.task:
            taskMgr.remove(cls)
            cls.task = None
