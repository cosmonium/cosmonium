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

from panda3d.core import LQuaterniond, LVector3d, LPoint3d

from ..appstate import AppState
from ..astro import units

from .bigfix import Bigfix

import sys
import re

if sys.version_info[0] < 3:
    import urlparse
    import urllib as urlquote
else:
    from urllib import parse as urlparse
    from urllib import parse as urlquote

class CelUrl(object):
    valid_modes = ["Follow", "SyncOrbit", "Chase", "PhaseLock", "Freeflight"]
    modes_without_target = ["Freeflight"]
    def __init__(self):
        self.reset()

    def reset(self):
        self.valid = False
        self.version = None
        self.flight_mode = None
        self.target = None
        self.time = None
        self.track = None
        self.select = None
        self.fov = None
        self.timescale = None
        self.light_time = None
        self.paused = None
        self.render_flags = None
        self.label_flags = None
        self.time_source = None

    def parse_render_flags(self, flags):
        render= {}
        # ShowStars           =   0x0001
        # ShowPlanets         =   0x0002
        render['galaxy']         = (flags & 0x0004) != 0
        render['asterisms']      = (flags & 0x0008) != 0
        render['clouds']         = (flags & 0x0010) != 0
        render['orbits']         = (flags & 0x0020) != 0
        render['equatorialgrid'] = (flags & 0x0040) != 0
        # ShowNightMaps       =   0x0080
        render['atmospheres']    = (flags & 0x0100) != 0
        # ShowSmoothLines     =   0x0200
        # ShowEclipseShadows  =   0x0400
        # ShowStarsAsPoints   =   0x0800
        # ShowRingShadows     =   0x1000
        # ShowBoundaries      =   0x2000
        render['boundaries']     = (flags & 0x2000) != 0
        # ShowAutoMag         =   0x4000
        # ShowCometTails      =   0x8000
        # ShowMarkers         =  0x10000
        # ShowPartialTrajectories = 0x20000
        # ShowNebulae         =  0x40000
        # ShowOpenClusters    =  0x80000
        # ShowGlobulars       =  0x100000
        # ShowCloudShadows    =  0x200000
        # ShowGalacticGrid    =  0x400000
        render['eclipticgrid']   = (flags & 0x800000) != 0
        # ShowHorizonGrid     = 0x1000000
        # ShowEcliptic        = 0x2000000
        # ShowTintedIllumination = 0x4000000
        return render

    def parse_label_flags(self, flags):
        labels = {}
        labels['star']       = (flags & 0x001) != 0
        labels['planet']     = (flags & 0x002) != 0
        labels['moon']       = (flags & 0x004) != 0
        labels['constellation'] = ((flags & 0x008) != 0) or ((flags & 0x800) != 0)
        labels['galaxy']     = (flags & 0x010) != 0
        labels['asteroid']   = (flags & 0x020) != 0
        labels['spacecraft'] = (flags & 0x040) != 0
        labels['location']   = (flags & 0x080) != 0
        labels['comet']      = (flags & 0x100) != 0
        labels['nebula']     = (flags & 0x200) != 0
        #TODO: OpenClusterLabels   = 0x400
        labels['dwarplanet'] = (flags & 0x1000) != 0
        labels['minormoon']  = (flags & 0x2000) != 0
        labels['globular']   = (flags & 0x4000) != 0
        return labels

    def parse(self, url):
        url = url.strip()
        result = urlparse.urlparse(url, allow_fragments=False)
        parameters = {}
        for entry in urlparse.parse_qsl(result.query):
            value = entry[1].replace(' ', '+')
            # Celestia does not encode '+' character which is then decoded as a space by urlparse
            parameters[entry[0]] = value
        version = parameters.get('ver', '1')
        if version not in ['2', '3']:
            print("Unsupported cel version", version)
            return False
        self.version = int(version)
        if result.scheme != 'cel':
            print("Not a cel:// url")
            return False
        if not result.netloc in self.valid_modes:
            print("Unsupported flight mode", result.netloc)
            return False
        self.flight_mode = result.netloc
        elements = result.path.split('/')
        if len(elements) == 0 or elements[0] != '':
            print("Invalid path")
            return False
        elements.pop(0)
        target = None
        if not result.netloc in self.modes_without_target:
            if len(elements) == 0:
                print("Missing target")
                return False
            target = elements.pop(0)
        self.target = target
        if len(elements) == 0:
                print("Missing date/time")
                return False
        time = elements.pop(0)
        m = re.search('^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d\.\d{5})$', time)
        if m is not None:
            (year, month, day, hours, mins, secs) = m.groups()
            year = int(year)
            month = int(month)
            day = int(day)
            hours = int(hours)
            mins = int(mins)
            secs = float(secs)
            self.time = units.values_to_time(year, month, day, hours, mins, secs)
        else:
            print("Invalid date/time field", time)
            return False
        if len(elements) > 0:
            print("Unsupported extra parameters", elements)
            return False
        if parameters.get('dist') is not None:
            print("Unsupported non absolute reference", elements)
            return False
        (x, y, z) = (parameters.get('x'), parameters.get('y'), parameters.get('z'))
        if x is None or y is None or z is None:
            print("Missing position")
            return False
        x = Bigfix.bigfix_to_float(x)
        y = Bigfix.bigfix_to_float(y)
        z = Bigfix.bigfix_to_float(z)
        self.position = LVector3d(x * units.mLy, -z * units.mLy, y * units.mLy)
        (ox, oy, oz, ow) = (parameters.get('ox'), parameters.get('oy'), parameters.get('oz'), parameters.get('ow'))
        if ox is None or oy is None or oz is None or ow is None:
            print("Missing orientation")
            return False
        ox = float(ox)
        oy = float(oy)
        oz = float(oz)
        ow = float(ow)
        self.orientation = LQuaterniond(-ow, ox, -oz, oy)
        self.track = parameters.get('track', None)
        if self.track is not None:
            self.track = self.track.replace('+', ' ')
        self.select = parameters.get('select', None)
        if self.select is not None:
            self.select = self.select.replace('+', ' ')
        self.fov = parameters.get('fov', None)
        if self.fov is not None:
            self.fov = float(self.fov)
        self.timescale = parameters.get('ts', None)
        if self.timescale is not None:
            self.timescale = float(self.timescale)
        self.light_time = parameters.get('ltd', None)
        if self.light_time is not None:
            self.light_time = bool(int(self.light_time))
        self.paused = parameters.get('p', None)
        if self.paused is not None:
            self.paused = bool(int(self.paused))
        self.render_flags = parameters.get('rf', None)
        if self.render_flags is not None:
            self.render_flags = self.parse_render_flags(int(self.render_flags))
        self.label_flags = parameters.get('lm', None)
        if self.label_flags is not None:
            self.label_flags = self.parse_label_flags(int(self.label_flags))
        self.time_source = parameters.get('tsrc', None)
        self.valid = True
        return self.valid

    def convert_to_state(self, engine):
        if not self.valid: return None
        target = None
        select = None
        track = None
        if self.target is not None:
            target = engine.universe.find_by_path(self.target, separator=':')
            if target is None:
                print("Could not find", self.target)
                return None
        if self.select is not None:
            select = engine.universe.find_by_path(self.select, separator=':')
            if select is None:
                print("Could not find", self.select)
                return None
        if self.track is not None:
            track = engine.universe.find_by_path(self.track, separator=':')
            if track is None:
                print("Could not find", self.track)
                return None
        state = AppState()
        if self.flight_mode == 'Follow':
            state.follow = target
        elif self.flight_mode == 'SyncOrbit':
            state.sync = target
        elif self.flight_mode == 'Chase':
            print('Chase is not supported yet')
        elif self.flight_mode == 'PhaseLock':
            print('PhaseLock is not supported yet')
        state.track = track
        state.selected = select
        state.time_full = self.time
        state.multiplier = self.timescale
        state.running = not self.paused
        state.global_position = None
        state.position = self.position
        state.orientation = self.orientation
        if self.version == 2:
            state.absolute = True
        else:
            state.absolute = False
        state.fov = self.fov
        state.render = self.render_flags
        state.labels = self.label_flags
        return state

    def store_state(self, engine, state):
        self.reset()
        self.valid = True
        if state.follow is not None:
            self.flight_mode = 'Follow'
            self.target = state.follow.get_fullname(':')
        elif state.sync is not None:
            self.flight_mode = 'SyncOrbit'
            self.target = state.sync.get_fullname(':')
        else:
            self.flight_mode = 'Freeflight'
            self.target = None
        if state.selected is not None:
            self.select= state.selected.get_fullname(':')
        if state.track is not None:
            self.track = state.track.get_fullname(':')
        self.time = state.time_full
        self.timescale = state.multiplier
        self.paused = not state.running
        if self.target is None:
            self.position = state.global_position + state.position
        else:
            self.position = state.position
        self.orientation = state.orientation
        self.fov = state.fov
        self.render_flags = state.render
        self.label_flags = state.labels

        #TODO: Fetch also those values
        self.light_time = False
        self.time_source = 0

    def encode_render_flags(self, render):
        flags = 0
        # ShowStars           =   0x0001
        flags |= 0x0001
        # ShowPlanets         =   0x0002
        flags |= 0x0002
        if render.get('galaxy', False):
            flags |= 0x0004
        if render.get('asterisms', False):
            flags |= 0x0008
        if render.get('clouds', False):
            flags |= 0x0010
        if render.get('orbits', False):
            flags |= 0x0020
        if render.get('equatorialgrid', False):
            flags |= 0x0040
        # ShowNightMaps       =   0x0080
        flags |= 0x0080
        if render.get('atmospheres', False):
            flags |= 0x0100
        # ShowSmoothLines     =   0x0200
        flags |= 0x0200
        # ShowEclipseShadows  =   0x0400
        flags |= 0x0400
        # ShowStarsAsPoints   =   0x0800
        flags |= 0x0800
        # ShowRingShadows     =   0x1000
        flags |= 0x1000
        # ShowBoundaries      =   0x2000
        if render.get('boundaries', False):
            flags |=  0x2000
        # ShowAutoMag         =   0x4000
        # ShowCometTails      =   0x8000
        flags |= 0x8000
        # ShowMarkers         =  0x10000
        # ShowPartialTrajectories = 0x20000
        # ShowNebulae         =  0x40000
        flags |= 0x40000
        # ShowOpenClusters    =  0x80000
        flags |= 0x80000
        # ShowGlobulars       =  0x100000
        flags |= 0x100000
        # ShowCloudShadows    =  0x200000
        flags |= 0x200000
        # ShowGalacticGrid    =  0x400000
        if render.get('eclipticgrid', False):
            flags |= 0x800000
        # ShowHorizonGrid     = 0x1000000
        # ShowEcliptic        = 0x2000000
        # ShowTintedIllumination = 0x4000000
        return flags

    def encode_label_flags(self, labels):
        flags = 0
        if labels.get('star', False):
            flags |= 0x001
        if labels.get('planet', False):
            flags |= 0x002
        if labels.get('moon', False):
            flags |= 0x004
        if labels.get('constellation', False):
            flags |= (0x008 | 0x800)
        if labels.get('galaxy', False):
            flags |= 0x010
        if labels.get('asteroid', False):
            flags |= 0x020
        if labels.get('spacecraft', False):
            flags |= 0x040
        if labels.get('location', False):
            flags |= 0x080
        if labels.get('comet', False):
            flags |= 0x100
        if labels.get('nebula', False):
            flags |= 0x200
        #TODO: OpenClusterLabels   = 0x400
        if labels.get('dwarplanet', False):
            flags |= 0x1000
        if labels.get('minormoon', False):
            flags |= 0x2000
        if labels.get('globular', False):
            flags |= 0x4000
        return flags

    def encode(self):
        scheme = 'cel'
        netloc = self.flight_mode
        path = ['']
        if self.target is not None:
            path.append(self.target)
        values = units.time_to_values(self.time)
        path.append("%04d-%02d-%02dT%02d:%02d:%08.5f" % values)
        path = '/'.join(path)
        parameters = ''
        query = []
        (x, y, z) = tuple(self.position)
        query.append(('x', Bigfix.float_to_bigfix(x / units.mLy)))
        query.append(('y', Bigfix.float_to_bigfix(z / units.mLy)))
        query.append(('z', Bigfix.float_to_bigfix(-y / units.mLy)))
        (ow, ox, oy, oz) = tuple(self.orientation)
        query.append(('ow', -ow))
        query.append(('ox', ox))
        query.append(('oy', oz))
        query.append(('oz', -oy))
        if self.track is not None:
            query.append(('track', self.track))
        if self.select is not None:
            query.append(('select', self.select))
        query.append(('fov', self.fov))
        query.append(('ts', self.timescale))
        query.append(('ltd', int(self.light_time)))
        query.append(('p', int(self.paused)))
        if self.render_flags is not None:
            query.append(('rf', self.encode_render_flags(self.render_flags)))
        if self.label_flags is not None:
            query.append(('lm', self.encode_label_flags(self.label_flags)))
        query.append(('tsrc', self.time_source))
        query.append(('ver', 3))
        l = []
        for k, v in query:
            k = urlquote.quote(str(k), '/:+')
            v = urlquote.quote(str(v), '/:+')
            l.append(k + '=' + v)
        query = '&'.join(l)
        fragment = ''
        url = urlparse.urlunparse((scheme, netloc, path, parameters, query, fragment))
        return url

if __name__ == '__main__':
    cel_url = CelUrl()
    cel_url.parse(sys.argv[1])
    print(cel_url.encode())
