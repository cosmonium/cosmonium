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

from direct.interval.IntervalGlobal import Sequence, Func, Wait
from panda3d.core import LVector3d

from .celestia_utils import body_path
from .. import settings

from math import pi

def ignore(command_name, sequence, base, parameters):
    pass

def not_implemented(command_name, sequence, base, parameters):
    print("Command not implemented", command_name)

def cancel(command_name, sequence, base, parameters):
    """Description:
Stop a currently running goto command . . . like pressing the ESC key.
"""
    sequence.append(Func(base.reset_nav))

def capture(command_name, sequence, base, parameters):
    """Parameters:
string type
string filename
Description:
Take a screenshot of the current window
"""
    file_type = parameters.get('type')
    filename = parameters.get('filename')
    sequence.append(Func(base.save_screenshot, filename))

def center(command_name, sequence, base, parameters):
    """Parameters:
float time = 1.0
Description:
Center the currently selected object in the field of view.
Time specifies how many seconds it should take to slew the camera.
"""
    duration=float(parameters.get('time', '1.0'))
    sequence.append(Func(base.autopilot.center_on_object, duration=duration, proportional=False))

def changedistance(command_name, sequence, base, parameters):
    """Parameters:
float rate = 0.0
float duration = 1.0
Description:
Exponentially change the distance between the camera and the selected object over some duration.
A negative rate will move closer to the object, a positive rate moves farther out.
"""
    rate = float(parameters.get('rate', '0.0'))
    duration = float(parameters.get('duration', '0.0'))
    sequence.append(Func(base.autopilot.change_distance, rate, duration))
    sequence.append(Wait(duration))

def cls(command_name, sequence, base, parameters):
    pass

def display(command_name, sequence, base, parameters):
    """Parameters:
string text = ""
Description:
Show a line of text on the screen.
"""
    text = parameters.get('text', '')
    text = text.replace('\\n', '\n')
    origin = parameters.get('origin', 'bottomleft')
    row = float(parameters.get('row', '0.0'))
    column = float(parameters.get('column', '0.0'))
    duration = float(parameters.get('duration', '0.0'))
    sequence.append(Func(base.gui.update_info, text, duration))

def exit(command_name, sequence, base, parameters):
    """Description:
Exit the application
"""
    sequence.append(Func(base.userExit))

def follow(command_name, sequence, base, parameters):
    """Description:
Follow the currently selected object.
This causes the camera to stay in the same place relative to the center of an object.
"""
    sequence.append(Func(base.follow_selected))

def goto(command_name, sequence, base, parameters):
    """Parameters:
float time = 1.0
float distance = 5.0
string upframe = "observer"
vector up = [ 0 1 0 ]
Description:
Go to the currently selected object.
Trip duration is controlled with the time parameter.
The distance parameter specifies how far away from the object to stop in units of the object's radius.
The goto command executes instantaneously so that you can use other commands such as print while the camera is moving toward the destination.
In order for goto to complete, there should be wait commands with a combined duration equal to the value of the time parameter.
"""
    duration=float(parameters.get('time', '1.0'))
    distance=float(parameters.get('distance', '5.0'))
    upframe=parameters.get('upframe', 'observer')
    up=parameters.get('up', [0, 1, 0])
    up=LVector3d(up[0], -up[2], up[1])
    up.normalize()
    sequence.append(Func(base.autopilot.go_to_object, duration, distance, up))

def gotolonglat(command_name, sequence, base, parameters):
    """Parameters:
float time = 1.0
float distance = 5.0
vector up = [ 0 1 0 ]
float longitude = 0
float latitude = 0
Description:
gotolonglat works exactly the same as goto except that you can specify coordinates on the surface of the object as well as a distance.
Since the distance is in object radii, a distance of 1.0 will put you right on the surface.
Typically, you want to be just above the surface, so giving a radius of 1.001 is a better idea.
Latitude is negative for the southern hemisphere and positive for the northern hemisphere.
Longitude is negative for the western hemisphere and position for the eastern hemisphere.
"""
    duration=float(parameters.get('time', '1.0'))
    distance=float(parameters.get('distance', '5.0'))
    up=parameters.get('up', [0, 1, 0])
    up=LVector3d(up[0], -up[2], up[1])
    up.normalize()
    longitude=float(parameters.get('longitude', '0.0'))
    latitude=float(parameters.get('latitude', '0.0'))
    sequence.append(Func(base.autopilot.go_to_object_long_lat, longitude * pi / 180, latitude * pi / 180, duration, distance, up))

def do_labels(base, set_flags, clear_flags):
    for name in set_flags:
        base.show_label(name)
    for name in clear_flags:
        base.hide_label(name)

def labels(command_name, sequence, base, parameters):
    """Parameters:
string set = ""
string clear = ""
Description:
Change labeling options.
This command works in a manner similar to renderflags.
Options are: planets, moons, spacecraft, asteroids, constellations, stars, galaxies.
"""
    set_flags = parameters.get('set', '')
    if set_flags != '':
        set_flags = set_flags.split('|')
    else:
        set_flags = []
    clear_flags = parameters.get('clear', '')
    if clear_flags != '':
        clear_flags = clear_flags.split('|')
    else:
        clear_flags = []
    sequence.append(Func(do_labels, base, set_flags, clear_flags))

def move(command_name, sequence, base, parameters):
    """Parameters:
float duration = 0.0
vector velocity = [ 0 0 0 ]
Description:
Move at a constant velocity for an amount of time.
The velocity is given in units of kilometers per second.
"""
    duration = float(parameters.get('duration', '0.0'))
    velocity = parameters.get('velocity', '[0 0 0]')
    not_implemented(command_name, sequence, base, parameters)

def lookback(command_name, sequence, base, parameters):
    sequence.append(Func(base.camera.camera_look_back))

def orbit(command_name, sequence, base, parameters):
    """Parameters:
float rate = 0.0
float duration = 1.0
vector axis = [ 0 0 0 ]
Description:
Orbit the selected object around a given axis.
The rate is in units of degrees per second. (Still need to specify which coordinate system the axis is defined in.)
"""
    rate = float(parameters.get('rate', '0.0')) * pi / 180
    duration = float(parameters.get('duration', '1.0'))
    axis = parameters.get('axis', [0, 0, 0])
    axis = LVector3d(axis[0], -axis[2], axis[1])
    length = axis.length()
    axis.normalize()
    sequence.append(Func(base.autopilot.orbit, axis, rate * length, duration))
    sequence.append(Wait(duration))

def do_orbitflags(base, set_flags, clear_flags):
    for name in set_flags:
        base.show_orbit(name)
    for name in clear_flags:
        base.hide_orbit(name)

def orbitflags(command_name, sequence, base, parameters):
    """Parameters:
string set = ""
string clear = ""
Description:
Change orbit rendering options.
"""
    set_flags = parameters.get('set', '')
    if set_flags != '':
        set_flags = set_flags.split('|')
    else:
        set_flags = []
    clear_flags = parameters.get('clear', '')
    if clear_flags != '':
        clear_flags = clear_flags.split('|')
    else:
        clear_flags = []
    sequence.append(Func(do_orbitflags, base, set_flags, clear_flags))

def do_renderflags(base, set_flags, clear_flags):
    def apply_setting(name, value):
        if name == 'orbits':
            settings.show_orbits = value
        elif name == 'cloudmaps':
            settings.show_clouds = value
        elif name == "constellations":
            settings.show_asterisms = value
        elif name == "galaxies":
            pass
        elif name == "globulars":
            pass
        elif name == "planets":
            pass
        elif name == "stars":
            pass
        elif name == "pointstars":
            pass
        elif name == "nightmaps":
            pass
        elif name == "eclipseshadows":
            pass
        elif name == "ringshadows":
            pass
        elif name == "comettails":
            pass
        elif name == "boundaries":
            settings.show_boundaries = value
        elif name == "markers":
            pass
        elif name == "automag":
            pass
        elif name == "atmospheres":
            pass
        elif name == "grid" or name == "equatorialgrid":
            if value:
                base.equatorial_grid.show()
            else:
                base.equatorial_grid.hide()
        elif name == "galacticgrid":
            pass
        elif name == "eclipticgrid":
            if value:
                base.ecliptic_grid.show()
            else:
                base.ecliptic_grid.hide()
        elif name == "horizontalgrid":
            pass
        elif name == "smoothlines":
            pass
        elif name == "partialtrajectories":
            pass
        elif name == "nebulae":
            pass
        elif name == "openclusters":
            pass
        elif name == "cloudshadows":
            pass
        elif name == "ecliptic":
            pass
        else:
            print("Setting", name, 'unknown')

    for setting in set_flags:
        apply_setting(setting, True)
    for setting in clear_flags:
        apply_setting(setting, False)
    base.trigger_check_settings = True

def renderflags(command_name, sequence, base, parameters):
    """Parameters:
string set = ""
string clear = ""
Description:
Change rendering options.
Possible options include: orbits, cloudmaps, constellations, galaxies, planets, stars, nightmaps.
Multiple options can be enabled in a single command by listing several names separated by the | character.
"""
    set_flags = parameters.get('set', '')
    if set_flags != '':
        set_flags = set_flags.split('|')
    else:
        set_flags = []
    clear_flags = parameters.get('clear', '')
    if clear_flags != '':
        clear_flags = clear_flags.split('|')
    else:
        clear_flags = []
    sequence.append(Func(do_renderflags, base, set_flags, clear_flags))

def rotate(command_name, sequence, base, parameters):
    """Parameters:
float rate = 0.0
float duration = 1.0
vector axis = [ 0 0 0 ]
Description:
Rotate the observer about its center.
The rate is in units of degrees per second. (Still need to specify which coordinate system the axis is defined in.)
"""
    rate = float(parameters.get('rate', '0.0')) * pi / 180
    duration = float(parameters.get('duration', '1.0'))
    axis = parameters.get('axis', [0, 0, 0])
    axis = LVector3d(axis[0], -axis[2], axis[1])
    length = axis.length()
    axis.normalize()
    sequence.append(Func(base.autopilot.rotate, axis, -rate * length, duration))
    sequence.append(Wait(duration))

def select(command_name, sequence, base, parameters):
    """Parameters:
string object = ""
Description:
Set the selection to the specified object.
Names can be in 'path' form, e.g. "Sol/Earth/Moon" Otherwise, the object selected may depend on the location of the camera.
Just using "Moon" works fine within our solar system, but the full path form is favored.
"""
    path = parameters.get('object', '')
    path = body_path(path)
    body = base.universe.find_by_path(path)
    if body:
        sequence.append(Func(base.select_body, body))
    else:
        print("Path", path, "not found")

def set_cmd(command_name, sequence, base, parameters):
    """Parameters:
string name = ""
float value = 0.0
Set the configuration parameter 'name' to 'value'. Valid parameters and values are :
    name "string"
        "MinOrbitSize"
        "AmbientLightLevel"
        "FOV"
        "StarDistanceLimit" value number (default=0.0)
    or
    name "StarStyle"
    value string
        "fuzzypoints"
        "points"
        "scaleddiscs"
"""
    name = parameters.get('name', '').lower()
    if name == 'StarStyle':
        style = parameters.get('value', '')
    else:
        value = float(parameters.get('value', 0.0))
        if name == 'fov':
            sequence.append(Func(base.observer.set_fov, value))
        elif name == "ambientlightlevel":
            sequence.append(Func(base.set_ambient, value))
        else:
            print("Parameter", name, "not supported")

def setambientlight(command_name, sequence, base, parameters):
    """Parameters:
float brightness = 0.0
Description:
Set the amount of additional light used when rendering planets.
For realism, this should be set to 0.0. Setting it to 1.0 will cause the side of a planet facing away from the sun to appear as bright as the lit side.
"""
    magnitude = float(parameters.get('brightness', '0.0'))
    sequence.append(Func(base.set_ambient, magnitude))

def setframe(command_name, sequence, base, parameters):
    not_implemented(command_name, sequence, base, parameters)

def seturl(command_name, sequence, base, parameters):
    """Parameters:
string url = ""
Description:
Reconfigure the engine with the given configuration URL.
"""
    url = parameters.get('url', '')
    sequence.append(Func(base.load_cel_url, url))

def setvisibilitylimit(command_name, sequence, base, parameters):
    """Parameters:
float magnitude = 6.0
Description:
Display only stars brighter than the specified magnitude.
"""
    magnitude = float(parameters.get('magnitude', '6.0'))
    not_implemented(command_name, sequence, base, parameters)

def synchronous(command_name, sequence, base, parameters):
    """Description:
Sync orbit the currently selected object.
This causes the camera to stay in the same position and orientation relative to a location on the object's surface.
"""
    sequence.append(Func(base.sync_selected))

def time(command_name, sequence, base, parameters):
    """Parameters:
float jd = 2451545.0
Description:
Set the time to the specified Julian day.
"""
    if 'jd' in parameters:
        jd = float(parameters.get('jd', '2451545.0'))
    elif 'utc' in parameters:
        utc = parameters.get('utc', '')
    else:
        jd = 2451545.0
    sequence.append(Func(base.time.set_time_jd, jd))

def timerate(command_name, sequence, base, parameters):
    """Parameters:
float rate = 1.0
Description:
Set the rate at which simulation time advances relative to real time.
A negative value for rate will cause time to go backwards (but only in the simulation.)
"""
    rate = float(parameters.get('rate', '1.0'))
    sequence.append(Func(base.time.set_timerate, rate))

def track(command_name, sequence, base, parameters):
    """Description:
.
"""
    sequence.append(Func(base.track_selected))

def wait(command_name, sequence, base, parameters):
    """Parameters:
float duration = 1.0
Description:
Pause for a number of seconds specified by the duration parameter.
"""
    duration=float(parameters.get('duration', '1.0'))
    sequence.append(Wait(duration))

def done(base):
    base.sequence = None

commands = {
    "cancel": cancel,
    "capture": capture,
    "center": center,
    "changedistance": changedistance,
    "chase": not_implemented,
    "cls": cls,
    "constellations": not_implemented,
    "constellationcolor": not_implemented,
    "deleteview": not_implemented,
    "exit": exit,
    "follow": follow,
    "goto": goto,
    "gotoloc": not_implemented,
    "gotolonglat": gotolonglat,
    "labels": labels,
    "lock": not_implemented,
    "lookback": lookback,
    "mark": not_implemented,
    "move": move,
    "preloadtex": ignore,
    "orbit": orbit,
    "orbitflags": orbitflags,
    "print": display,
    "renderflags": renderflags,
    "renderpath": ignore,
    "rotate": rotate,
    "select": select,
    "set": set_cmd,
    "setactiveview": not_implemented,
    "setambientlight": setambientlight,
    "setfaintestautomag45deg": not_implemented,
    "setframe": setframe,
    "setgalaxylightgain": not_implemented,
    "setlabelcolor": not_implemented,
    "setlinecolor": not_implemented,
    "setorientation": not_implemented,
    "setposition": not_implemented,
    "setradius": not_implemented,
    "setsurface": not_implemented,
    "settextcolor": not_implemented,
    "settextureresolution": not_implemented,
    "seturl": seturl,
    "setvisibilitylimit": setvisibilitylimit,
    "singleview": not_implemented,
    "splitview": not_implemented,
    "synchronous": synchronous,
    "time": time,
    "timerate": timerate,
    "track": track,
    "unmark": not_implemented,
    "unmarkall": not_implemented,
    "wait": wait
    }

def build_sequence(base, script):
    if script is None:
        return None
    sequence = Sequence(name='script')
    for command_name, parameters in script:
        if command_name in commands:
            commands[command_name](command_name, sequence, base, parameters)
        else:
            print("Unknown command", command_name)
    sequence.append(Func(done, base))
    return sequence
