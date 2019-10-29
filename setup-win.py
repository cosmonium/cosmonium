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

from setuptools import setup

from setup import config

config['options']['build_apps']['platforms'] = ['win_amd64']
config['options']['build_apps']['requirements_path'] = 'requirements-win.txt'
package_data_dirs = config['options']['build_apps'].setdefault('package_data_dirs', {})
package_data_dirs['win32'] = [('pywin32_system32/*', '', {}),
                              ('win32/*.pyd', '', {}),
                              ('win32/lib/win32con.py', '', {})]
include_modules = config['options']['build_apps'].setdefault('include_modules', {})
all_modules = include_modules.setdefault('*', [])
all_modules.append('win32.*')

setup(**config)

