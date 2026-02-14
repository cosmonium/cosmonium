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


from ..engine.objectname import CatalogRegistry
from .yamlparser import YamlParser


def load_catalogs(yaml_path):
    """
    Load catalog definitions from a YAML file.

    Args:
        yaml_path: Path to the catalogs YAML file.
    """
    # Clear the registry
    registry = CatalogRegistry.get_instance()
    registry.clear()

    if yaml_path is None:
        # No path provided, skip loading and keep the registry empty
        return

    try:
        data = YamlParser().load_and_parse(yaml_path, use_splash=False)

        # Load catalogs from YAML - IDs are auto-assigned based on order
        for catalog in data.get('catalogs', []):
            prefix = catalog['prefix']
            description = catalog.get('description', '')
            registry.register_catalog(prefix, description)

    except Exception as e:
        # If loading fails, ignore the error and keep the registry empty
        print(f"Warning: Failed to load catalogs from {yaml_path}: {e}")
