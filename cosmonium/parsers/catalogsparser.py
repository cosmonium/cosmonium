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
from ..parsers.yamlloader import YamlLoader
from .schemas.misc import CatalogsConfig


def load_catalogs(yaml_path):
    """
    Load catalog definitions from a YAML file.

    Args:
        yaml_path: Path to the catalogs YAML file.
    """
    registry = CatalogRegistry.get_instance()
    registry.clear()

    if yaml_path is None:
        return

    try:
        data = YamlLoader.load_file(yaml_path, use_splash=False)
        config = CatalogsConfig.model_validate(data)
        for catalog in config.catalogs:
            registry.register_catalog(catalog.prefix, catalog.description)

    except Exception as e:
        print(f"Warning: Failed to load catalogs from {yaml_path}: {e}")
