#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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


from panda3d.core import LVector3d

from ..scattering.oneil.oneil import ONeilScattering, ONeilSimpleScattering
from .scatteringparser import ScatteringYamlParser
from .schemas.atmosphere import ONeilAtmosphereConfig, ONeilSimpleAtmosphereConfig
from .yamlparser import YamlParser


class ONeilSimpleScatteringYamlParser(YamlParser):
    @classmethod
    def decode(cls, data):
        scattering = ONeilSimpleScattering(
            wavelength=[0.650, 0.570, 0.465],
            mie_phase_asymmetry=data.g,
            mie_coef=data.mie,
            rayleigh_coef=data.rayleigh,
            sun_power=data.sun_power,
            samples=data.samples,
            calc_in_fragment=data.calc_in_fragment,
            atm_calc_in_fragment=data.atm_calc_in_fragment,
            normalize=data.normalize,
            atm_normalize=data.atm_normalize,
            hdr=data.hdr,
            exposure=data.exposure,
            atm_hdr=data.atm_hdr,
            atm_exposure=data.atm_exposure,
        )
        return scattering


class ONeilScatteringYamlParser(YamlParser):
    @classmethod
    def decode(cls, data):
        height = data.height
        rayleigh_scale_depth = data.rayleigh_scale_depth
        if rayleigh_scale_depth is not None:
            rayleigh_scale_depth /= height
        else:
            rayleigh_scale_depth = 0.25
        mie_scale_depth = data.mie_scale_depth
        if mie_scale_depth is not None:
            mie_scale_depth /= height
        else:
            mie_scale_depth = 0.1
        scattering = ONeilScattering(
            height=height,
            wavelength=[0.650, 0.570, 0.465],
            mie_phase_asymmetry=data.g,
            rayleigh_scale_depth=rayleigh_scale_depth,
            rayleigh_coef=data.rayleigh,
            rayleigh_absorption=LVector3d(*data.rayleigh_absorption),
            mie_scale_depth=mie_scale_depth,
            mie_alpha_coef=data.mie_alpha_coef,
            mie_beta_coef=data.mie_beta_coef,
            sun_power=data.sun_power,
            samples=data.samples,
            calc_in_fragment=data.calc_in_fragment,
            atm_calc_in_fragment=data.atm_calc_in_fragment,
            normalize=data.normalize,
            atm_normalize=data.atm_normalize,
            hdr=data.hdr,
            exposure=data.exposure,
            atm_hdr=data.atm_hdr,
            atm_exposure=data.atm_exposure,
            lookup_size=256,
            lookup_samples=50,
        )
        return scattering


def register_oneil_parsers():
    # TODO: Using atmosphere config model until proper scattering config is available
    ScatteringYamlParser.register('oneil', ONeilScatteringYamlParser(), ONeilAtmosphereConfig)
    ScatteringYamlParser.register('oneil:simple', ONeilSimpleScatteringYamlParser(), ONeilSimpleAtmosphereConfig)
