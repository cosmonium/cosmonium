#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

from math import log2, pow, exp, isinf, isnan

from ..foundation import BaseObject
from ..scene.scenemanager import SceneManagerBase
from .. import settings

from .pipeline import Pipeline
from .screen import Screen
from .stages.annotations import AnnotationsRenderStage
from .stages.average_luminosity import AverageLuminosityStage
from .stages.bloom_apply import BloomApplyStage
from .stages.color_correction import ColorCorrectionStage
from .stages.downscale_bloom import DownscaleBloomStage
from .stages.passthrough import PassthroughStage
from .stages.render import RenderStage
from .stages.blur_bloom import BlurBloomStage
from .stages.tone_mapping import ToneMappingStage


class ScenePipelineBase(Pipeline):

    def __init__(self, engine):
        Pipeline.__init__(self, win=None, engine=engine)

    def incr_exposure(self, incr: float) -> None:
        raise NotImplementedError()

    def init_window(self) -> None:
        raise NotImplementedError()

    def evaluate_pipeline(self) -> None:
        raise NotImplementedError()

    def build_pipeline(self) -> None:
        raise NotImplementedError()

    def init(self) -> None:
        self.evaluate_pipeline()
        self.init_window()
        self.build_pipeline()

    def set_scene_manager(self, scene_manager: SceneManagerBase) -> None:
        for stage in self.stages.values():
            stage.set_scene_manager(scene_manager)

    def process_last_frame(self, dt: float) -> None:
        pass


class BasicScenePipeline(ScenePipelineBase):

    def __init__(self, engine=None):
        ScenePipelineBase.__init__(self, engine=engine)
        self.screen = None
        self.framebuffer_srgb = settings.use_srgb
        self.framebuffer_multisamples = settings.multisamples if settings.use_multisampling else 0

    def incr_exposure(self, incr):
        pass

    def init_window(self):
        self.screen = Screen(
            base,
            srgb=self.framebuffer_srgb,
            multisamples=self.framebuffer_multisamples,
            stereoscopic=settings.stereoscopic_framebuffer,
        )
        self.screen.request()
        self.set_win(base.win)

    def evaluate_pipeline(self):
        pass

    def build_pipeline(self):
        ldr_colors = (8, 8, 8, 8)
        render_stage = RenderStage(
            "render", colors=ldr_colors, camera_mask=BaseObject.DefaultCameraFlag | BaseObject.AnnotationCameraFlag
        )
        self.add_stage(render_stage)
        render_stage.set_scene_stage(True)
        render_stage.set_screen_stage(True)


class ScenePipeline(ScenePipelineBase):

    def __init__(self, engine=None):
        ScenePipelineBase.__init__(self, engine=engine)
        self.screen = None
        self.scene_manager = None
        self.framebuffer_srgb = settings.use_srgb
        self.render_buffer_multisamples = settings.multisamples if settings.use_multisampling else 0
        self.render_buffer_srgb = settings.use_srgb
        self.hdr_color_bits = 32
        self.ldr_color_bits = 8
        self.alpha_bits = 8
        self.inverse_z = False
        self.hdr = False
        self.bloom = False
        self.adaptive_exposure = False
        self.avg_luminosity = 1.0
        self.ev100 = 1.0
        self.ev100_corrected = 1.0
        self.max_luminance = 1.0
        self.exposure = 1.0
        self.exposure_correction = 0.0
        self.adaptation_rate = 5

    def incr_exposure(self, incr: float) -> None:
        self.exposure_correction += incr

    def init_window(self) -> None:
        self.screen = Screen(
            base, srgb=self.framebuffer_srgb, multisamples=0, stereoscopic=settings.stereoscopic_framebuffer
        )
        self.screen.request()
        self.set_win(base.win)

    def evaluate_pipeline(self) -> None:
        if settings.use_inverse_z:
            self.inverse_z = True
        if settings.use_pbr:
            self.hdr = True
            self.bloom = True
            self.adaptive_exposure = True
        self.render_buffer_multisamples = settings.multisamples if settings.use_multisampling else 0

    def build_pipeline(self) -> None:
        hdr_colors_alpha = (self.hdr_color_bits, self.hdr_color_bits, self.hdr_color_bits, self.alpha_bits)
        hdr_colors = (self.hdr_color_bits, self.hdr_color_bits, self.hdr_color_bits, 0)
        ldr_colors_alpha = (self.ldr_color_bits, self.ldr_color_bits, self.ldr_color_bits, self.alpha_bits)
        ldr_colors = (self.ldr_color_bits, self.ldr_color_bits, self.ldr_color_bits, 0)
        if self.hdr:
            render_stage = RenderStage(
                "render",
                camera_mask=BaseObject.DefaultCameraFlag,
                colors=hdr_colors_alpha,
                srgb=False,
                multisamples=self.render_buffer_multisamples,
                inverse_z=self.inverse_z,
                create_mimap=True,
            )
        else:
            render_stage = RenderStage(
                "render",
                camera_mask=BaseObject.DefaultCameraFlag | BaseObject.AnnotationCameraFlag,
                colors=ldr_colors_alpha,
                srgb=self.render_buffer_srgb,
                multisamples=self.render_buffer_multisamples,
                inverse_z=self.inverse_z,
            )
        self.add_stage(render_stage)
        if self.hdr:
            self.avg = self.add_stage(AverageLuminosityStage("average_luminosity"))
            if self.bloom:
                if True:
                    self.add_stage(DownscaleBloomStage("mipmap_bloom", hdr_colors))
                else:
                    self.add_stage(BlurBloomStage("simple_bloom", hdr_colors))
                self.add_stage(BloomApplyStage("bloom_appply", hdr_colors))
            self.add_stage(ToneMappingStage("tone_mapping", ldr_colors))
            annotation_render_stage = AnnotationsRenderStage(
                "annotations",
                camera_mask=BaseObject.AnnotationCameraFlag,
                colors=hdr_colors_alpha,
                srgb=False,
                inverse_z=self.inverse_z,
            )
            self.add_stage(annotation_render_stage)
        if settings.use_srgb and not self.framebuffer_srgb:
            self.add_stage(ColorCorrectionStage("color_correction", ldr_colors))
        if not self.ordered_stages[-1].can_render_to_screen():
            self.add_stage(PassthroughStage("passthrough", ldr_colors))
        self.ordered_stages[0].set_scene_stage(True)
        self.ordered_stages[-1].set_screen_stage(True)

    def process_last_frame(self, dt: float) -> None:
        if self.hdr:
            if self.adaptive_exposure:
                avg_luminosity = self.avg.extract_level()
                if not isinf(avg_luminosity) and not isnan(avg_luminosity):
                    self.avg_luminosity += (avg_luminosity - self.avg_luminosity) * (
                        1 - exp(-dt * self.adaptation_rate)
                    )
                self.ev100 = log2(max(self.avg_luminosity, 0.00000001) * 100 / 12.5)
                self.ev100_corrected = self.ev100 - self.exposure_correction
                self.max_luminance = 1.2 * pow(2, self.ev100_corrected)
                self.exposure = 1.0 / self.max_luminance
            for stage in self.ordered_stages:
                stage.update(self)
