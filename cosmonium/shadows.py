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

from panda3d.core import WindowProperties, FrameBufferProperties, GraphicsPipe, GraphicsOutput
from panda3d.core import Texture, OrthographicLens, PandaNode, NodePath
from panda3d.core import LVector3, LPoint3, LVector3d, LPoint4, Mat4
from panda3d.core import ColorWriteAttrib, LColor, CullFaceAttrib, RenderState, DepthOffsetAttrib

from .foundation import BaseObject
from .shaders import ShaderShadowMap, ShaderRingShadow, ShaderSphereShadow

from . import settings

class ShadowMap(object):
    def __init__(self, size):
        self.size = size
        self.buffer = None
        self.depthmap = None
        self.cam = None
        self.shadow_caster = None
        self.snap_cam = settings.shadows_snap_cam

    def create(self):
        winprops = WindowProperties.size(self.size, self.size)
        props = FrameBufferProperties()
        props.setRgbColor(0)
        props.setAlphaBits(0)
        props.setDepthBits(1)
        self.buffer = base.graphicsEngine.makeOutput(
            base.pipe, "shadowsBuffer", -2,
            props, winprops,
            GraphicsPipe.BFRefuseWindow,
            base.win.getGsg(), base.win)

        if not self.buffer:
            print("Video driver cannot create an offscreen buffer.")
            return
        self.depthmap = Texture()
        self.buffer.addRenderTexture(self.depthmap, GraphicsOutput.RTMBindOrCopy,
                                 GraphicsOutput.RTPDepthStencil)

        self.depthmap.setMinfilter(Texture.FTShadow)
        self.depthmap.setMagfilter(Texture.FTShadow)
        self.depthmap.setBorderColor(LColor(1, 1, 1, 1))
        self.depthmap.setWrapU(Texture.WMBorderColor)
        self.depthmap.setWrapV(Texture.WMBorderColor)

        self.cam = base.makeCamera(self.buffer, lens=OrthographicLens())
        self.cam.reparent_to(render)
        self.node = self.cam.node()
        self.node.setInitialState(RenderState.make(CullFaceAttrib.make_reverse(),
                                                   ColorWriteAttrib.make(ColorWriteAttrib.M_none),
                                                   ))
        self.node.setScene(render)
        if settings.debug_shadow_frustum:
            self.node.showFrustum()

    def align_cam(self):
        mvp = Mat4(base.render.get_transform(self.cam).get_mat() * self.get_lens().get_projection_mat())
        center = mvp.xform(LPoint4(0, 0, 0, 1)) * 0.5 + 0.5
        texel_size = 1.0 / self.size
        offset_x = center.x % texel_size
        offset_y = center.y % texel_size
        mvp.invert_in_place()
        new_center = mvp.xform(LPoint4((center.x - offset_x) * 2.0 - 1.0,
                                       (center.y - offset_y) * 2.0 - 1.0,
                                       (center.z) * 2.0 - 1.0,
                                       1.0))
        self.cam.set_pos(self.cam.get_pos() - LVector3(new_center.x, new_center.y, new_center.z))

    def set_lens(self, size, near, far, direction):
        lens = self.node.get_lens()
        lens.set_film_size(size)
        lens.setNear(near)
        lens.setFar(far)
        lens.set_view_vector(LVector3(*direction), LVector3.up())
 
    def get_lens(self):
        return self.node.get_lens()

    def set_direction(self, direction):
        lens = self.node.get_lens()
        lens.set_view_vector(LVector3(*direction), LVector3.up())

    def get_pos(self):
        return self.cam.get_pos()

    def set_pos(self, position):
        self.cam.set_pos(LPoint3(*position))
        if self.snap_cam:
            self.align_cam()

    def remove(self):
        self.node = None
        self.cam.remove_node()
        self.cam = None
        self.depthmap = None
        self.buffer.set_active(False)
        base.graphicsEngine.removeWindow(self.buffer)
        self.buffer = None

class ShadowCasterBase(object):
    def create(self):
        pass

    def remove(self):
        pass

    def check_settings(self):
        pass

    def is_valid(self):
        return True

    def add_target(self, shape_object):
        pass

    def update(self):
        pass

class ShadowMapShadowCaster(ShadowCasterBase):
    def __init__(self, body, light):
        self.body = body
        self.light = light
        self.name = self.body.get_ascii_name()
        self.shadow_caster = None
        self.shadow_camera = None

    def create_camera(self):
        pass

    def create(self):
        if self.shadow_caster is not None: return
        self.create_camera()
        self.shadow_camera.set_camera_mask(BaseObject.ShadowCameraMask)

    def remove_camera(self):
        pass

    def remove(self):
        self.remove_camera()

    def check_settings(self):
        if settings.debug_shadow_frustum:
            self.shadow_camera.show_frustum()
        else:
            self.shadow_camera.hide_frustum()

    def is_valid(self):
        return self.shadow_caster is not None

    def update(self):
        radius = self.body.get_extend() / settings.scale
        self.shadow_caster.get_lens().set_film_size(radius * 2.1, radius * 2.1)
        #The shadow frustum origin is at the light center which is one radius away from the object
        #So the near plane is 0 to coincide with the boundary of the object
        self.shadow_caster.get_lens().setNear(0)
        self.shadow_caster.get_lens().setFar(radius*2)
        self.shadow_caster.get_lens().set_view_vector(LVector3(*-self.body.vector_to_star), LVector3.up())

class PandaShadowCaster(ShadowMapShadowCaster):
    def create_camera(self):
        print("Create Panda3D shadow camera for", self.body.get_name())
        self.light.setShadowCaster(True, settings.shadow_size, settings.shadow_size)
        self.shadow_caster = self.directional_light
        self.shadow_camera = self.directional_light

    def remove_camera(self):
        print("Remove Panda3D shadow camera for", self.body.get_name())
        self.light.setShadowCaster(False)
        self.shadow_caster = None
        self.shadow_camera = None

class CustomShadowMapShadowCaster(ShadowMapShadowCaster):
    def __init__(self, body, light):
        ShadowMapShadowCaster.__init__(self, body, light)
        self.targets = {}

    def create_camera(self):
        print("Create shadow camera for", self.body.get_name())
        self.shadow_caster = ShadowMap(settings.shadow_size)
        self.shadow_caster.create()
        self.shadow_camera = self.shadow_caster.node

    def remove_camera(self):
        print("Remove shadow camera for", self.body.get_name())
        self.shadow_caster.remove()
        for target in list(self.targets.keys()):
            self.remove_target(target)
        self.shadow_caster = None
        self.shadow_camera = None

    def update(self):
        ShadowMapShadowCaster.update(self)
        self.shadow_caster.set_pos(self.body.light_source.getPos())

    def add_target(self, shape_object, self_shadow=False):
        shape_object.shadows.add_generic_occluder(self, self_shadow)

class RingShadowCaster(ShadowCasterBase):
    def __init__(self, ring):
        ShadowCasterBase.__init__(self)
        self.ring = ring

    def add_target(self, shape_object):
        shape_object.shadows.add_ring_occluder(self)

class SphereShadowCaster(ShadowCasterBase):
    def __init__(self, body):
        ShadowCasterBase.__init__(self)
        self.body = body

    def add_target(self, shape_object):
        shape_object.shadows.add_sphere_occluder(self)

class ShadowBase(object):
    pass

class SphereShadows(ShadowBase):
    def __init__(self):
        self.occluders = []
        self.shader_component = ShaderSphereShadow()

    def add_occluder(self, occluder):
        if not occluder in self.occluders:
            self.occluders.append(occluder)

    def empty(self):
        return len(self.occluders) == 0

    def clear(self):
        self.occluders = []

class GenericShadows(ShadowBase):
    def __init__(self, target):
        self.target = target
        self.occluders = []
        self.old_occluders = []
        self.shader_components = {}
        self.update_needed = False

    def add_occluder(self, occluder, self_shadow):
        if not occluder.is_valid(): return
        self.occluders.append(occluder)
        if not occluder in self.old_occluders:
            print("Add shadow caster", occluder.name)
            shadow_shader =  ShaderShadowMap(occluder.name, occluder.body, occluder.shadow_caster, self_shadow)
            self.shader_components[occluder] = shadow_shader
            self.target.shader.add_shadows(shadow_shader)
            self.update_needed = True
        else:
            self.old_occluders.remove(occluder)

    def start_update(self):
        self.old_occluders = self.occluders
        self.occluders = []
        self.update_needed = False

    def end_update(self):
        for occluder in self.old_occluders:
            print("Remove shadow caster", occluder.name)
            shadow_shader = self.shader_components[occluder]
            self.target.shader.remove_shadows(self.target.shape, self.target.appearance, shadow_shader)
            del self.shader_components[occluder]
            self.update_needed = True
        self.old_occluders = []
        return self.update_needed

class MultiShadows(ShadowBase):
    def __init__(self, target):
        self.target = target
        self.ring_shadow = None
        self.sphere_shadows = SphereShadows()
        self.generic_shadows = GenericShadows(target)
        self.update_needed = False
        self.had_sphere_occluder = False

    def clear_shadows(self):
        self.ring_shadow = None
        self.sphere_shadows.clear()
        self.shadow_map = None
        self.target.shader.clear_shadows(self.target.shape, self.target.appearance)
        self.update_needed = True
        self.had_sphere_occluder = False

    def start_update(self):
        self.had_sphere_occluder = not self.sphere_shadows.empty()
        self.sphere_shadows.clear()
        self.generic_shadows.start_update()

    def end_update(self):
        if self.sphere_shadows.empty() and self.had_sphere_occluder:
            print("Remove sphere shadow component")
            self.target.shader.remove_shadows(self.target.shape, self.target.appearance, self.sphere_shadows.shader_component)
            self.update_needed = True
        elif not self.had_sphere_occluder and not self.sphere_shadows.empty():
            self.target.shader.add_shadows(self.sphere_shadows.shader_component)
            #TODO: This is an extremely ugly hack :
            #Currently only ring shape support oblate sphere shadow caster
            #To know if we target a ring without introducing an import loop
            #we check the shadow caster type... this is to remove ASAP
            if isinstance(self.target.shadow_caster, RingShadowCaster):
                self.sphere_shadows.shader_component.oblate_occluder = True
            print("Add sphere shadow component")
            self.update_needed = True
        self.update_needed = self.generic_shadows.end_update() or self.update_needed

    def add_ring_occluder(self, shadow_caster):
        if self.ring_shadow is None:
            print("Add ring shadow component")
            self.ring_shadow = shadow_caster
            self.target.shader.add_shadows(ShaderRingShadow())
            self.update_needed = True
        else:
            print("Can not switch ring shadow caster")

    def add_sphere_occluder(self, shadow_caster):
        self.sphere_shadows.add_occluder(shadow_caster)

    def add_generic_occluder(self, occluder, self_shadow):
        self.generic_shadows.add_occluder(occluder, self_shadow)
