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

from panda3d.core import LColor, LQuaterniond

from . import config_parser
from .celestia_utils import instanciate_elliptical_orbit, instanciate_custom_orbit, \
    instanciate_uniform_rotation, instanciate_precessing_rotation, instanciate_custom_rotation, \
    instanciate_reference_frame, \
    names_list, body_path
from .shaders import LunarLambertLightingModel

from ..celestia.atmosphere import CelestiaAtmosphere, CelestiaScattering
from ..universe import Universe
from ..systems import StellarSystem, SimpleSystem
from ..bodies import ReflectiveBody, ReferencePoint
from ..surfaces import FlatSurface
from ..bodyelements import Ring, Clouds
from ..appearances import Appearance
from ..shapes import MeshShape, SphereShape
from ..shaders import BasicShader, LambertPhongLightingModel
from ..astro.orbits import FixedOrbit
from ..astro.rotations import FixedRotation, create_uniform_rotation
from ..astro import units
from ..astro.frame import J2000EclipticReferenceFrame, RelativeReferenceFrame, EquatorialReferenceFrame
from ..dircontext import defaultDirContext

from time import time
import sys
import io

def get_color(value):
    if len(value) == 4:
        return LColor(*value)
    if len(value) == 3:
        return LColor(value[0], value[1], value[2], 1.0)
    print("Invalid color", value)
    return None

def instanciate_atmosphere(data):
    atmosphere = None
    clouds = None
    clouds_height = 0
    clouds_appearance = Appearance()
    atmosphere_height = 0.0
    mie_coef = 0.0
    mie_scale_height = 0.0
    mie_phase_asymmetry = 0.0
    rayleigh_coef = None
    rayleigh_scale_height = 0.0
    absorption_coef = None
    for (key, value) in data.items():
        if key == 'CloudHeight':
            clouds_height = value
        elif key == 'CloudMap':
            clouds_appearance.set_texture(value, transparency=True)
        elif key == 'CloudSpeed':
            pass #= value
        elif key == 'CloudShadowDepth':
            pass #= value
        elif key == 'Upper':
            pass #= value
        elif key == 'Lower':
            pass #= value
        elif key == 'Sky':
            pass #= value
        elif key == 'Height':
            atmosphere_height = value
        elif key == 'Rayleigh':
            rayleigh_coef = value
        elif key == 'Mie':
            mie_coef = value
        elif key == 'MieScaleHeight':
            mie_scale_height = value
        elif key == 'MieAsymmetry':
            mie_phase_asymmetry = value
        elif key == 'Absorption':
            absorption_coef = value
        elif key == 'Sunset':
            pass #= value
        else:
            print("Key of Atmosphere", key, "not supported")
    clouds_appearance.bake()
    if mie_phase_asymmetry != 0.0:
        atmosphere = CelestiaAtmosphere(height = atmosphere_height,
                                    appearance=Appearance(),
                                    shader=BasicShader(lighting_model=CelestiaScattering(atmosphere=True)),
                                    mie_scale_height = mie_scale_height,
                                    mie_coef = mie_coef,
                                    mie_phase_asymmetry = mie_phase_asymmetry,
                                    rayleigh_coef = rayleigh_coef,
                                    rayleigh_scale_height = rayleigh_scale_height,
                                    absorption_coef = absorption_coef)
    if clouds_height != 0:
        shader=BasicShader(lighting_model=LambertPhongLightingModel())
        clouds = Clouds(clouds_height, clouds_appearance, shader)
    return (atmosphere, clouds)

def instanciate_rings(data):
    inner_radius = 0
    outer_radius = 0
    appearance = Appearance()
    for (key, value) in data.items():
        if key == 'Inner':
            inner_radius = value
        elif key == 'Outer':
            outer_radius = value
        elif key == 'Texture':
            appearance.set_texture(value, transparency=True, transparency_level=0.5)
        elif key == 'Color':
            appearance.diffuseColor = get_color(value)
        else:
            print("Key of Ring", key, "not supported")
    appearance.bake()
    return Ring(inner_radius,
                outer_radius,
                appearance=appearance,
                shader=BasicShader())

def instanciate_body(universe, names, is_planet, data):
    appearance=Appearance()
    point_color=None
    radius=1.0
    oblateness=None
    scale=None
    lunar_lambert = 0.0
    atmosphere = None
    clouds=None
    rings=None
    orbit=None
    legacy_rotation = False
    rotation_period = None
    rotation_obliquity = 0.0
    rotation_ascending_node = 0.0
    rotation_offset = 0.0
    rotation_epoch = units.J2000
    rotation = None
    model = None
    shape_offset = None
    albedo = 0.5
    bump_map = None
    bump_height = 1.0
    orbit_frame = None
    custom_orbit = False
    body_frame = None
    custom_rotation = False
    if is_planet:
        body_class="planet"
        orbit_global_coord=True
        rotation_global_coord=True
    else:
        body_class="moon"
        orbit_global_coord=False
        rotation_global_coord=False
    for (key, value) in data.items():
        if key == 'Radius':
            radius = value
        elif key == 'Texture':
            appearance.set_texture(value)
        elif key == 'NightTexture':
            appearance.set_night_texture(value)
        elif key == 'BumpHeight':
            bump_height = value
        elif key == 'BumpMap':
            bump_map = value
        elif key == 'NormalMap':
            appearance.set_normal_map(value)
        elif key == 'Color':
            point_color = get_color(value)
        elif key == 'BlendTexture':
            pass #= value
        elif key == 'SpecularPower':
            #Multiply by 4 as we use Blinn-Phong and not Phong specular
            appearance.shininess = value * 4.0
        elif key == 'Albedo':
            albedo = value
        elif key == 'SpecularColor':
            appearance.specularColor = get_color(value)
        elif key == 'SpecularTexture':
            appearance.set_specular_map(value)
        elif key == 'LunarLambert':
            lunar_lambert = value
        elif key == 'Mesh':
            model = value
        elif key == 'MeshCenter':
            shape_offset = value
        elif key == 'Oblateness':
            oblateness = value
        elif key == 'SemiAxes':
            scale = value
        elif key == 'Mass':
            pass #= value
        elif key == 'Orientation':
            pass #= value
        elif key == 'HazeColor':
            pass #= value
        elif key == 'HazeDensity':
            pass #= value
        elif key == 'Rings':
            rings = instanciate_rings(value)
        elif key == 'Atmosphere':
            (atmosphere, clouds) = instanciate_atmosphere(value)
        elif key == 'EllipticalOrbit':
            orbit = instanciate_elliptical_orbit(value, orbit_global_coord)
        elif key == 'CustomOrbit':
            orbit = instanciate_custom_orbit(value)
            custom_orbit = True
        elif key == 'RotationPeriod':
            legacy_rotation = True
            rotation_period = value
        elif key == 'RotationOffset':
            legacy_rotation = True
            rotation_offset = value
        elif key == 'RotationEpoch':
            legacy_rotation = True
            rotation_epoch = value
        elif key == 'Obliquity':
            legacy_rotation = True
            rotation_obliquity = value
        elif key == 'EquatorAscendingNode':
            legacy_rotation = True
            rotation_ascending_node = value
        elif key == 'OrbitFrame':
            orbit_frame, orbit_global_coord = instanciate_reference_frame(universe, value, orbit_global_coord)
        elif key == 'BodyFrame':
            body_frame, rotation_global_coord = instanciate_reference_frame(universe, value, rotation_global_coord)
        elif key == 'UniformRotation':
            rotation = instanciate_uniform_rotation(value, rotation_global_coord)
        elif key == 'PrecessingRotation':
            rotation = instanciate_precessing_rotation(value)
        elif key == 'CustomRotation':
            rotation = instanciate_custom_rotation(value)
            custom_rotation = True
        elif key == 'Class':
            body_class = value
        elif key == 'InfoURL':
            pass #= value
        else:
            print("Key of body", key, "not supported")
    if orbit_frame is None and not custom_orbit:
        if is_planet:
            orbit_frame = J2000EclipticReferenceFrame()
        else:
            orbit_frame = EquatorialReferenceFrame()
    if body_frame is None and not custom_rotation:
        if is_planet:
            body_frame = J2000EclipticReferenceFrame()
        else:
            body_frame = EquatorialReferenceFrame()
    if orbit is None:
        orbit=FixedOrbit(frame=orbit_frame)
    elif not custom_orbit:
        orbit.set_frame(orbit_frame)
    if legacy_rotation:
        rotation = create_uniform_rotation(period=rotation_period,
                                        inclination=rotation_obliquity,
                                        ascending_node=rotation_ascending_node,
                                        meridian_angle=rotation_offset,
                                        epoch=rotation_epoch,
                                        frame=body_frame)
    elif rotation is None:
        rotation = FixedRotation(LQuaterniond(), frame=body_frame)
    elif not custom_rotation:
        rotation.set_frame(body_frame)
    if model != None and not (model.endswith('.cmod') or model.endswith('.cms')):
        shape=MeshShape(model=model, radius=radius, offset=shape_offset)
    else:
        shape=SphereShape()
    if bump_map is not None:
        appearance.set_bump_map(bump_map, bump_height)
    lighting_model = None
    if lunar_lambert > 0.0:
        lighting_model = LunarLambertLightingModel()
    else:
        lighting_model = LambertPhongLightingModel()
    surface = FlatSurface(
                          shape=shape,
                          appearance=appearance,
                          shader=BasicShader(lighting_model=lighting_model))
    body = ReflectiveBody(names=names,
                          radius=radius,
                          surface=surface,
                          oblateness=oblateness,
                          orbit=orbit,
                          rotation=rotation,
                          ring=rings,
                          atmosphere=atmosphere,
                          clouds=clouds,
                          point_color=point_color)
    if atmosphere is not None:
        atmosphere.add_shape_object(surface)
        if clouds is not None:
            atmosphere.add_shape_object(clouds)
    body.albedo = albedo
    body.body_class = body_class
    return body

def instanciate_reference_point(universe, names, is_planet, data):
    orbit=None
    legacy_rotation = False
    rotation_period = None
    rotation_obliquity = 0.0
    rotation_ascending_node = 0.0
    rotation_offset = 0.0
    rotation_epoch = units.J2000
    rotation = None
    orbit_frame = None
    body_frame = None
    custom_orbit = False
    custom_rotation = False
    if is_planet:
        body_class="planet"
        orbit_global_coord=True
        rotation_global_coord=True
    else:
        body_class="moon"
        orbit_global_coord=False
        rotation_global_coord=False
    for (key, value) in data.items():
        if key == 'EllipticalOrbit':
            orbit = instanciate_elliptical_orbit(value, orbit_global_coord)
        elif key == 'CustomOrbit':
            orbit = instanciate_custom_orbit(value)
            custom_orbit = True
        elif key == 'RotationPeriod':
            legacy_rotation = True
            rotation_period = value
        elif key == 'RotationOffset':
            legacy_rotation = True
            rotation_offset = value
        elif key == 'RotationEpoch':
            legacy_rotation = True
            rotation_epoch = value
        elif key == 'Obliquity':
            legacy_rotation = True
            rotation_obliquity = value
        elif key == 'EquatorAscendingNode':
            legacy_rotation = True
            rotation_ascending_node = value
        elif key == 'OrbitFrame':
            orbit_frame, orbit_global_coord = instanciate_reference_frame(universe, value, orbit_global_coord)
        elif key == 'BodyFrame':
            body_frame, rotation_global_coord = instanciate_reference_frame(universe, value, rotation_global_coord)
        elif key == 'UniformRotation':
            rotation = instanciate_uniform_rotation(value, rotation_global_coord)
        elif key == 'PrecessingRotation':
            rotation = instanciate_precessing_rotation(value)
        elif key == 'CustomRotation':
            rotation = instanciate_custom_rotation(value)
            custom_rotation = True
        else:
            print("Key of ReferencePoint", key, "not supported")
    if orbit_frame is None and not custom_orbit:
        if is_planet:
            orbit_frame = J2000EclipticReferenceFrame()
        else:
            orbit_frame = EquatorialReferenceFrame()
    if body_frame is None and not custom_rotation:
        if is_planet:
            body_frame = J2000EclipticReferenceFrame()
        else:
            body_frame = EquatorialReferenceFrame()
    if orbit is None:
        orbit=FixedOrbit(frame=orbit_frame)
    elif not custom_orbit:
        orbit.set_frame(orbit_frame)
    if legacy_rotation:
        rotation = create_uniform_rotation(period=rotation_period,
                                        inclination=rotation_obliquity,
                                        ascending_node=rotation_ascending_node,
                                        meridian_angle=rotation_offset,
                                        epoch=rotation_epoch,
                                        frame=body_frame)
    elif rotation is None:
        rotation = FixedRotation(LQuaterniond(), frame=body_frame)
    elif not custom_rotation:
        rotation.set_frame(body_frame)
    ref = ReferencePoint(names=names,
                         orbit=orbit,
                         rotation=rotation,
                         body_class=body_class)
    return ref

def find_parent(universe, path, item_parent):
    body = universe.find_by_path(path, return_system=True)
    if not body:
        path = body_path(item_parent)
        body = universe.find_by_path(path)
        if body:
            print("Creating system for", body.get_name())
            explicit = body.orbit.frame.explicit_body
            if explicit:
                #TODO: This looks completely wrong !
                orbit = FixedOrbit(frame=RelativeReferenceFrame(body.orbit.frame.body, body.orbit.frame))
            else:
                orbit = body.orbit
            system=SimpleSystem(body.get_name() + " System", primary=body, orbit=orbit)
            body.parent.add_child_fast(system)
            if not explicit:
                orbit = FixedOrbit(frame=RelativeReferenceFrame(system, orbit.frame))
                body.set_orbit(orbit)
            system.add_child_fast(body)
            body=system
    return body

def instanciate_item(universe, disposition, item_type, item_name, item_parent, item_alias, item_data):
    if disposition != 'Add':
        print("Disposition", disposition, "not supported")
        return
    if item_type not in ['Body', 'ReferencePoint', 'AltSurface']:
        print("Type", item_type, "not supported")
        return
    if item_type == 'AltSurface':
        return
    names=names_list(item_name)
    path = body_path(item_parent)
    is_planet = len(path) == 1
    parent = find_parent(universe, path, item_parent)
    if not parent:
        print("Parent", item_parent, "not found")
        return
    if item_type == 'Body':
        body = instanciate_body(universe, names, is_planet, item_data)
    elif item_type == 'ReferencePoint':
        body = instanciate_reference_point(universe, names, is_planet, item_data)
    parent.add_child_fast(body)
    
def instanciate(items_list, universe):
    for item in items_list:
        instanciate_item(universe, *item)

def parse_file(filename, universe, context=defaultDirContext):
    filepath = context.find_data(filename)
    if filepath is not None:
        start = time()
        print("Loading", filepath)
        base.splash.set_text("Loading %s" % filepath)
        data = io.open(filepath, encoding='latin-1').read()
        items = config_parser.parse(data)
        if items is not None:
            instanciate(items, universe)
        end = time()
        print("Load time:", end - start)
    else:
        print("File not found", filename)

def load(config_parser, universe):
    if isinstance(config_parser, list):
        for config_parser in config_parser:
            parse_file(config_parser, universe)
    else:
        parse_file(config_parser, universe)

if __name__ == '__main__':
    universe=Universe()
    sol=StellarSystem('Sol', FixedOrbit())
    universe.add_child(sol)
    if len(sys.argv) == 2:
        parse_file(sys.argv[1], universe)
