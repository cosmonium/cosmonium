from panda3d.core import CardMaker
from panda3d.core import CullFaceAttrib
from panda3d.core import Plane, PlaneNode
from panda3d.core import Point3, Vec3, Vec4
from panda3d.core import RenderState, Shader
from panda3d.core import Texture, TextureStage, TransparencyAttrib

from ..dircontext import defaultDirContext

class WaterNode():
    watercamNP = None
    buffer = None
    def __init__(self, x1, y1, x2, y2, z, scale, parent):

        # Water surface
        maker = CardMaker('water')
        maker.setFrame(x1, x2, y1, y2)

        self.waterNP = parent.instance.attachNewNode(maker.generate())
        self.waterNP.setHpr(0, -90, 0)
        self.waterNP.setPos(0, 0, z)
        self.waterNP.setTransparency(TransparencyAttrib.MAlpha)
        self.waterNP.setShader(Shader.load(Shader.SL_GLSL,
                                           vertex=defaultDirContext.find_shader('water-vertex.glsl'),
                                           fragment=defaultDirContext.find_shader('water-fragment.glsl')))
        self.waterNP.setShaderInput('wateranim', Vec4(0.03, -0.015, scale, 0)) # vx, vy, scale, skip
        # offset, strength, refraction factor (0=perfect mirror, 1=total refraction), refractivity
        self.waterNP.setShaderInput('waterdistort', Vec4(0.4, 4.0, 0.25, 0.45))
        self.waterNP.setShaderInput('time', 0)

        # Reflection plane
        self.waterPlane = Plane(Vec3(0, 0, z + 1), Point3(0, 0, z))
        planeNode = PlaneNode('waterPlane')
        planeNode.setPlane(self.waterPlane)

        if self.watercamNP is None:
            # Buffer and reflection camera
            WaterNode.buffer = base.win.makeTextureBuffer('waterBuffer', 512, 512)
            self.buffer.setClearColor(Vec4(0, 0, 0, 1))

            cfa = CullFaceAttrib.makeReverse()
            rs = RenderState.make(cfa)

            WaterNode.watercamNP = base.makeCamera(self.buffer)
            self.watercamNP.reparentTo(render)

            #sa = ShaderAttrib.make()
            #sa = sa.setShader(loader.loadShader('shaders/splut3Clipped.sha') )

            cam = self.watercamNP.node()
            cam.getLens().setFov(base.camLens.getFov())
            cam.getLens().setNear(1)
            cam.getLens().setFar(5000)
            cam.setInitialState(rs)
            cam.setTagStateKey('Clipped')
            #cam.setTagState('True', RenderState.make(sa))

        # ---- water textures ---------------------------------------------

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

    def update(self, task):
        # update matrix of the reflection camera
        mc = base.camera.getMat()
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
#         if self.watercamNP:
#             self.watercamNP.removeNode()
#             self.watercamNP = None
#         if self.buffer:
#             self.buffer.set_active(False)
#             base.graphicsEngine.removeWindow(self.buffer)
#             self.buffer = None
        if self.task:
            taskMgr.remove(self.task)
            self.task = None
