from panda3d.core import CardMaker
from panda3d.core import CullFaceAttrib
from panda3d.core import Plane, PlaneNode
from panda3d.core import Point3, Vec3, Vec4
from panda3d.core import RenderState, Shader
from panda3d.core import Texture, TextureStage, TransparencyAttrib

from ..dircontext import defaultDirContext

class WaterNode():
    buffer = None
    watercamNP = None
    def __init__(self, x1, y1, x2, y2, z, scale, parent):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.z = z
        self.scale = scale
        self.parent = parent
        self.waterNP = None
        self.task = None

    def create_instance(self):
        self.create_buffer()
        # Water surface
        maker = CardMaker('water')
        maker.setFrame(self.x1, self.x2, self.y1, self.y2)

        self.waterNP = self.parent.instance.attachNewNode(maker.generate())
        self.waterNP.setHpr(0, -90, 0)
        self.waterNP.setPos(0, 0, self.z)
        self.waterNP.setTransparency(TransparencyAttrib.MAlpha)
        self.waterNP.setShader(Shader.load(Shader.SL_GLSL,
                                           vertex=defaultDirContext.find_shader('water-vertex.glsl'),
                                           fragment=defaultDirContext.find_shader('water-fragment.glsl')))
        self.waterNP.setShaderInput('wateranim', Vec4(0.03, -0.015, self.scale, 0)) # vx, vy, scale, skip
        # offset, strength, refraction factor (0=perfect mirror, 1=total refraction), refractivity
        self.waterNP.setShaderInput('waterdistort', Vec4(0.4, 4.0, 0.25, 0.45))
        self.waterNP.setShaderInput('time', 0)

        # Reflection plane
        self.waterPlane = Plane(Vec3(0, 0, self.z + 1), Point3(0, 0, self.z))
        planeNode = PlaneNode('waterPlane')
        planeNode.setPlane(self.waterPlane)

        # reflection texture, created in realtime by the 'water camera'
        tex0 = self.buffer.getTexture()
        tex0.setWrapU(Texture.WMClamp)
        tex0.setWrapV(Texture.WMClamp)
        ts0 = TextureStage('reflection')
        self.waterNP.setTexture(ts0, tex0)

        # distortion texture
        tex1 = loader.loadTexture('textures/water.png')
        ts1 = TextureStage('distortion')
        self.waterNP.setTexture(ts1, tex1)
        self.task = taskMgr.add(self.update, "waterTask")

    @classmethod
    def create_buffer(cls):
        if cls.buffer is None:
            cls.buffer = base.win.makeTextureBuffer('waterBuffer', 512, 512)
            cls.buffer.setClearColor(Vec4(0, 0, 0, 1))

    @classmethod
    def create_cam(cls):
        cls.create_buffer()
        if cls.watercamNP is None:
            cfa = CullFaceAttrib.makeReverse()
            rs = RenderState.make(cfa)

            cls.watercamNP = base.makeCamera(cls.buffer)
            cls.watercamNP.reparentTo(render)

            #sa = ShaderAttrib.make()
            #sa = sa.setShader(loader.loadShader('shaders/splut3Clipped.sha') )

            cam = cls.watercamNP.node()
            cam.getLens().setFov(base.camLens.getFov())
            cam.getLens().setNear(1)
            cam.getLens().setFar(5000)
            cam.setInitialState(rs)
            cam.setTagStateKey('Clipped')
            #cam.setTagState('True', RenderState.make(sa))

    def update(self, task):
        # update matrix of the reflection camera
        if self.watercamNP is not None:
            mc = base.cam.getMat()
            mf = self.waterPlane.getReflectionMat()
            self.watercamNP.setMat(mc * mf)
        self.waterNP.setShaderInput('time', task.time)
        #self.waterNP.setX(base.cam.getX())
        #self.waterNP.setY(base.cam.getY())
        return task.cont

    def remove_instance(self):
        if self.waterNP:
            self.waterNP.removeNode()
            self.waterNP = None
#         if self.buffer:
#             self.buffer.set_active(False)
#             base.graphicsEngine.removeWindow(self.buffer)
#             self.buffer = None
        if self.task:
            taskMgr.remove(self.task)
            self.task = None

    @classmethod
    def remove_cam(cls):
        if cls.watercamNP:
            cls.watercamNP.removeNode()
            cls.watercamNP = None
