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


"""
YAML Loading Layer - Handles file I/O and YAML parsing.

It handles:
- Loading YAML files from disk
- Parsing YAML text to Python dictionaries
- Caching loaded data
- Managing file contexts and paths
"""

import builtins
import hashlib
import io
import os
import pickle

import ruamel.yaml

from .. import settings
from ..cache import create_path_for
from ..dircontext import DirContext


class YamlLoader:
    """
    Pure YAML loading layer - handles file I/O and YAML parsing only.

    This class is responsible for:
    - Loading YAML files from disk
    - Parsing YAML text to Python dictionaries
    - Caching loaded data for performance
    - Managing directory contexts for relative paths
    """

    def __init__(self):
        pass

    @staticmethod
    def parse(stream, stream_name=None):
        """
        Parse YAML text into Python dictionary.

        Args:
            stream: String or file-like object containing YAML
            stream_name: Optional name for error reporting

        Returns:
            Parsed Python dictionary, or None on error
        """
        data = None
        try:
            yaml = ruamel.yaml.YAML(typ='safe')
            yaml.allow_duplicate_keys = True
            data = yaml.load(stream)
        except ruamel.yaml.YAMLError as e:
            if stream_name is not None:
                print("Syntax error in '%s' :" % stream_name, e)
            else:
                print("Syntax error : ", e)
        return data

    @staticmethod
    def store(data, stream):
        """
        Store Python dictionary as YAML.

        Args:
            data: Python dictionary to serialize
            stream: File-like object to write to
        """
        yaml = ruamel.yaml.YAML(typ='safe')
        yaml.default_flow_style = False
        yaml.dump(data, stream)

    @staticmethod
    def load_from_cache(filepath, use_splash=True):
        """
        Load cached parsed YAML data if available and fresh.

        Args:
            filepath: Absolute path to YAML file
            use_splash: Whether to update splash screen text

        Returns:
            Cached data dictionary, or None if cache is invalid/missing
        """
        data = None
        config_path = create_path_for('config')
        md5 = hashlib.md5(filepath.encode()).hexdigest()
        cache_file = os.path.join(config_path, md5 + ".dat")

        if os.path.exists(cache_file):
            file_timestamp = os.path.getmtime(filepath)
            cache_timestamp = os.path.getmtime(cache_file)
            if cache_timestamp > file_timestamp:
                print("Loading %s (cached)" % filepath)
                if use_splash:
                    builtins.base.splash.set_text("Loading %s (cached)" % filepath)
                try:
                    with open(cache_file, "rb") as f:
                        data = pickle.load(f)
                except (IOError, ValueError) as e:
                    print("Could not read cache for", filepath, cache_file, ':', e)
        return data

    @staticmethod
    def store_to_cache(data, filepath):
        """
        Store parsed YAML data to cache.

        Args:
            data: Python dictionary to cache
            filepath: Absolute path to original YAML file
        """
        config_path = create_path_for('config')
        md5 = hashlib.md5(filepath.encode()).hexdigest()
        cache_file = os.path.join(config_path, md5 + ".dat")
        try:
            with open(cache_file, "wb") as f:
                print("Caching into", cache_file)
                pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
        except IOError as e:
            print("Could not write cache for", filepath, cache_file, ':', e)

    @staticmethod
    def load_file(filepath, use_cache=None, use_splash=True):
        """
        Load and parse YAML file, using cache if available.

        Args:
            filepath: Absolute path to YAML file
            use_cache: Whether to use cache (defaults to settings.cache_yaml)
            use_splash: Whether to update splash screen text

        Returns:
            Parsed Python dictionary, or None on error
        """
        if use_cache is None:
            use_cache = settings.cache_yaml

        data = None

        # Try to load from cache first
        if use_cache:
            data = YamlLoader.load_from_cache(filepath, use_splash)

        # Load from file if not cached
        if data is None:
            print("Loading %s" % filepath)
            if use_splash:
                builtins.base.splash.set_text("Loading %s" % filepath)
            try:
                text = io.open(filepath, encoding='utf8').read()
                data = YamlLoader.parse(text, filepath)
            except IOError as e:
                print("Could not read", filepath, ':', e)
                return None

            # Cache the loaded data
            if use_cache and data is not None:
                YamlLoader.store_to_cache(data, filepath)

        return data

    @staticmethod
    def load_with_context(filename, context, use_cache=None, use_splash=True):
        """
        Load YAML file using directory context for path resolution.

        Args:
            filename: Relative filename to load
            context: DirContext for resolving relative paths
            use_cache: Whether to use cache (defaults to settings.cache_yaml)
            use_splash: Whether to update splash screen text

        Returns:
            Tuple of (data, filepath, new_context) or (None, None, None) on error
        """
        filepath = context.find_data(filename)
        if filepath is None:
            print("Could not find", filename)
            return None, None, None

        # Create new context for the loaded file's directory
        new_context = DirContext(context)
        path = os.path.dirname(filepath)
        new_context.add_all_path(path)
        for category in new_context.category_paths.keys():
            new_context.add_path(category, os.path.join(path, category))

        # Load the file
        data = YamlLoader.load_file(filepath, use_cache, use_splash)

        return data, filepath, new_context

    @staticmethod
    def save_file(data, filepath):
        """
        Save Python dictionary as YAML file.

        Args:
            data: Python dictionary to save
            filepath: Absolute path to save to

        Returns:
            True on success, False on error
        """
        try:
            with open(filepath, 'w') as stream:
                YamlLoader.store(data, stream)
            return True
        except IOError as e:
            print("Could not write", filepath, ':', e)
            return False
