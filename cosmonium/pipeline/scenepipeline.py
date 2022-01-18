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


from .pipeline import Pipeline
from .screen import Screen
from .stages.render import RenderStage
from .stages.color_correction import ColorCorrectionStage
from .stages.passthrough import PassthroughStage

from .. import settings


class ScenePipeline(Pipeline):
    def __init__(self, engine=None):
        Pipeline.__init__(self, win=None, engine=engine)
        self.screen = None
        self.force_basic_pipeline = False
        self.basic_pipeline = False
        self.framebuffer_srgb = settings.use_srgb
        self.framebuffer_multisamples = 0
        self.render_buffer_multisamples = 0
        self.render_buffer_srgb = settings.use_srgb
        self.color_bits = 8
        self.alpha_bits = 8

    def init_window(self):
        self.screen = Screen(base,
                             srgb=self.framebuffer_srgb,
                             multisamples=self.framebuffer_multisamples,
                             stereoscopic=settings.stereoscopic_framebuffer)
        self.screen.request()
        self.set_win(base.win)

    def evaluate_pipeline(self):
        if not self.force_basic_pipeline:
            if settings.use_inverse_z:
                self.inverse_z = True
                self.basic_pipeline = False
        else:
            self.basic_pipeline = True
        if self.basic_pipeline:
            self.framebuffer_multisamples = settings.multisamples if settings.use_multisampling else 0
            self.render_multisamples = 0
        else:
            self.framebuffer_multisamples = 0
            self.render_buffer_multisamples = settings.multisamples if settings.use_multisampling else 0

    def buid_basic_pipeline(self):
        render_stage = RenderStage("render")
        self.add_stage(render_stage)
        render_stage.set_scene_stage(True)
        render_stage.set_screen_stage(True)

    def build_pipeline(self):
        render_stage = RenderStage("render",
                                   srgb=self.render_buffer_srgb,
                                   multisamples=self.render_buffer_multisamples,
                                   inverse_z=settings.use_inverse_z)
        self.add_stage(render_stage)
        if settings.use_srgb and not self.framebuffer_srgb:
            self.add_stage(ColorCorrectionStage("color_correction"))
        if not self.ordered_stages[-1].can_render_to_screen():
            self.add_stage(PassthroughStage("passthrough"))
        self.ordered_stages[0].set_scene_stage(True)
        self.ordered_stages[-1].set_screen_stage(True)

    def init(self):
        self.evaluate_pipeline()
        self.init_window()
        if self.basic_pipeline:
            self.buid_basic_pipeline()
        else:
            self.build_pipeline()
#         render_scene_to_buffer = False
#         if settings.use_srgb and not settings.use_hardware_srgb:
#             render_scene_to_buffer = True
# 
#         if settings.use_hdr:
#             render_scene_to_buffer = True
# 
#         if settings.use_inverse_z:
#             render_scene_to_buffer = True

    def set_scene_manager(self, scene_manager):
        self.ordered_stages[0].set_scene_manager(scene_manager)
