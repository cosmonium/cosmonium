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

from panda3d.core import WindowProperties, FrameBufferProperties, GraphicsPipe, GraphicsOutput, Texture, OrthographicLens, PandaNode, NodePath
from panda3d.core import DrawMask
from panda3d.core import LVector3, ColorWriteAttrib, LColor, CullFaceAttrib

from .shaders import ShaderShadowMap, ShaderRingShadow, ShaderSphereShadow

from . import settings

class ShadowMap(object):
    def __init__(self, size):
        self.size = size
        self.buffer = None
        self.depthmap = None
        self.cam = None
        self.shadow_caster = None

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
        lci = NodePath(PandaNode("Light Camera Initializer"))
        lci.set_attrib(ColorWriteAttrib.make(ColorWriteAttrib.M_none), 1000)
        lci.set_attrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise), 1000)
        self.node.setInitialState(lci.getState())
        self.node.setScene(render)
        if settings.debug_shadow_frustum:
            self.node.showFrustum()

    def set_lens(self, size, near, far, direction):
        lens = self.node.get_lens()
        lens.set_film_size(size)
        lens.setNear(near)
        lens.setFar(far)
        lens.set_view_vector(direction, LVector3.up())
 
    def get_lens(self):
        return self.node.get_lens()

    def set_direction(self, direction):
        lens = self.node.get_lens()
        lens.set_view_vector(direction, LVector3.up())

    def get_pos(self):
        return self.cam.get_pos()

    def set_pos(self, position):
        self.cam.set_pos(position)

    def remove(self):
        self.node = None
        self.cam.remove_node()
        self.cam = None
        self.depthmap = None
        self.buffer.set_active(False)
        base.graphicsEngine.removeWindow(self.buffer)
        self.buffer = None

class ShadowCasterBase(object):
    def add_target(self, shape_object):
        pass

    def remove_target(self, shape_object):
        pass

class ShadowBase(object):
    pass

class ShadowMapShadowCaster(ShadowCasterBase):
    def __init__(self, body, light):
        self.body = body
        self.light = light
        self.shadow_caster = None
        self.shadow_camera = None

    def create_camera(self):
        pass

    def create(self):
        self.create_camera()
        if settings.debug_shadow_frustum:
            self.shadow_camera.showFrustum()
        self.shadow_camera.set_camera_mask(DrawMask(1))

    def remove_camera(self):
        pass

    def remove(self):
        self.remove_camera()

    def update(self):
        radius = self.body.get_extend() / settings.scale
        self.shadow_caster.get_lens().set_film_size(radius * 2.1, radius * 2.1)
        self.shadow_caster.get_lens().setNear(-self.body.context.observer.infinity)
        self.shadow_caster.get_lens().setFar(self.body.context.observer.infinity)
        self.shadow_caster.get_lens().set_view_vector(LVector3(*-self.body.vector_to_star), LVector3.up())

class PandaShadowCaster(ShadowMapShadowCaster):
    def create_camera(self):
        print("Create Panda3D shadow caster")
        self.light.setShadowCaster(True, settings.shadow_size, settings.shadow_size)
        self.shadow_caster = self.dir_light
        self.shadow_camera = self.dir_light

    def remove_camera(self):
        self.light.setShadowCaster(False)
        self.shadow_caster = None
        self.shadow_camera = None

class CustomShadowMapShadowCaster(ShadowMapShadowCaster):
    def __init__(self, body, light):
        ShadowMapShadowCaster.__init__(self, body, light)
        self.bias = 0.

    def create_camera(self):
        print("Create custom shadow caster for", self.body.get_name())
        self.shadow_caster = ShadowMap(settings.shadow_size)
        self.shadow_caster.create()
        self.shadow_camera = self.shadow_caster.node
        #TODO: should be done in surface
        #TODO
        #self.body.surface.appearance.set_shadow(self.shadow_caster)
        #self.body.surface.shader.add_shadows(ShadowsMap())
        if self.body.surface.instance_ready:
            self.body.surface.shader.apply(self.body.surface.shape, self.body.surface.appearance)

    def remove_camera(self):
        print("Remove custom shadow caster", self.body.get_name())
        self.shadow_caster.remove()
        #TODO: Temporary until all dangling instance references have been removed
        self.body.surface.appearance.set_shadow(None)
        self.body.surface.shader.remove_shadows(self.body.surface.shape, self.body.surface.appearance)
        if self.body.surface.instance_ready:
            self.body.surface.shader.apply(self.body.surface.shape, self.body.surface.appearance)
        self.shadow_caster = None
        self.shadow_camera = None

    def update(self):
        ShadowMapShadowCaster.update(self)
        self.shadow_caster.set_pos(self.body.sunLight.getPos())

class RingShadowCaster(ShadowCasterBase):
    def __init__(self, ring):
        ShadowCasterBase.__init__(self)
        self.ring = ring

    def add_target(self, shape_object):
        shape_object.shadows.add_ring_occluder(self)

    def remove_target(self, shape_object):
        shape_object.shadows.remove_ring_occluder(self)

class SphereShadowCaster(ShadowCasterBase):
    def __init__(self, body):
        ShadowCasterBase.__init__(self)
        self.body = body

    def add_target(self, shape_object):
        shape_object.shadows.add_sphere_occluder(self)

    def remove_target(self, shape_object):
        shape_object.shadows.remove_sphere_occluder(self)

class SphereShadows(ShadowBase):
    def __init__(self):
        self.occluders = []
        self.old_occluders = []
        self.shader_component = ShaderSphereShadow()

    def add_occluder(self, occluder):
        if not occluder in self.occluders:
            self.occluders.append(occluder)

    def remove_occluder(self, occluder):
        if occluder in self.occluders:
            self.occluders.remove(occluder)

    def empty(self):
        return len(self.occluders) == 0

    def clear(self):
        self.occluders = []

class MultiShadows(ShadowBase):
    def __init__(self, target):
        self.target = target
        self.ring_shadow = None
        self.sphere_shadows = SphereShadows()
        self.shadow_map = None
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

    def add_ring_occluder(self, shadow_caster):
        if self.ring_shadow is None:
            print("Add ring shadow component")
            self.ring_shadow = shadow_caster
            self.target.shader.add_shadows(ShaderRingShadow())
            self.update_needed = True
        else:
            print("Can not switch ring shadow caster")

    def remove_ring_occluder(self, shadow_caster):
        if shadow_caster == self.ring_shadow_caster:
            print("Remove ring shadow component")
            self.target.shader.remove_shadows(self.ring_shadow_caster)
            self.ring_shadow_caster = None
            self.update_needed = True
        else:
            print("Wrong ring shadow caster")

    def add_sphere_occluder(self, shadow_caster):
        self.sphere_shadows.add_occluder(shadow_caster)

    def remove_sphere_occluder(self, shadow_caster):
        self.sphere_shadows.remove_occluder(shadow_caster)

    def add_generic_occluder(self, occluder):
        pass

    def remove_generic_occluder(self, occluder):
        pass
