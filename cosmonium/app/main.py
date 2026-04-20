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


import os

from .. import settings
from ..cosmonium import Cosmonium
from .args import parse_args
from .config import CosmoniumConfigParser


def main():
    args = parse_args()
    parser = CosmoniumConfigParser(os.path.join(settings.config_dir, 'cosmonium.yaml'))
    app_config = parser.load()
    app_config.update_from_args(args)

    app = Cosmonium(app_config)
    app.run()
