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


import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("script", help="CEL script to run at start up", nargs='?', default=None)
    parser.add_argument("--celestia", help="Load data from Celestia", nargs='?', const='', default=None)
    parser.add_argument("--common", help="Path to the file with the basic common configuration", default=None)
    parser.add_argument("--main", help="Path to the file with the universe configuration", default=None)
    parser.add_argument("--ui", help="Path to the file with the UI configuration", default=None)
    parser.add_argument("--home", help="Default home system of body", default=None)
    parser.add_argument("--default", help="Default body to show when there is no start up script", default=None)
    parser.add_argument("--extra", help="Extra configuration files or directories to load", nargs='+', default=None)
    parser.add_argument("--test-start", help=argparse.SUPPRESS, action='store_true', default=False)
    if sys.platform == "darwin":
        # Ignore -psn_<app_id> from MacOS
        parser.add_argument('-p', help=argparse.SUPPRESS)
    args = parser.parse_args()
    return args
