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
Parser Base Classes - Domain object instantiation layer.

This module provides base classes for parsers that convert validated data
into domain objects. This is the instantiation layer.

The YAML loading layer is in yamlloader.py.
The validation layer is in validator.py, shared with the UI config loaders.
"""

import functools

from pydantic import BaseModel

from ..catalogs import objectsDB
from .validator import ConfigValidator
from .yamlloader import YamlLoader


class YamlModuleParser:
    """
    Module parser with context management and translation support.

    This class provides:
    - Directory context management for relative paths
    - Translation support for internationalization
    - Loading with context (delegates to YamlLoader)
    """

    context = None
    translation = None
    app = None

    @classmethod
    def set_translation(cls, translation):
        YamlModuleParser.translation = translation

    @classmethod
    def translate_name(cls, name, context=None):
        if context is not None:
            return cls.translation.pgettext(context, name)
        else:
            return cls.translation.gettext(name)

    @classmethod
    def translate_object_names(cls, anchor, context=None):
        """Apply translation to an existing ObjectNames instance.

        Translation is performed as a second step after the ObjectNames instance has
        been created, so the translatable flag on each ObjectName is consulted
        directly without re-parsing the name strings.

        Args:
            anchor: The anchor owning the names (used for registration).
            context: Optional gettext context for disambiguation (pgettext).
        """
        if context is not None:
            translate_fn = functools.partial(cls.translation.pgettext, context)
        else:
            translate_fn = cls.translation.gettext
        object_names = anchor.get_names()
        for i in range(object_names.get_num_names()):
            name_entry = object_names.get_name_entry(i)
            if name_entry.translatable:
                translated = translate_fn(name_entry.value)
                if translated != name_entry.value:
                    object_names.set_translated(i, translated)
                    objectsDB.add_name_for(anchor, translated, name_entry)

    def load_and_parse(self, filename, parent=None, context=None):
        """
        Load YAML file with context management and decode.

        This method now delegates to YamlLoader for the loading,
        then handles context management and decoding.

        Args:
            filename: Relative filename to load
            parent: Optional parent object for decode
            context: Optional DirContext for path resolution

        Returns:
            Decoded domain object, or None on error
        """
        if context is None:
            context = YamlModuleParser.context
        if context is None:
            from ..dircontext import defaultDirContext

            context = defaultDirContext

        # Use YamlLoader to load with context
        data, filepath, new_context = YamlLoader.load_with_context(filename, context)

        if data is None:
            return None

        # Temporarily switch context
        saved_context = YamlModuleParser.context
        YamlModuleParser.context = new_context

        # Decode the loaded data
        try:
            if parent is not None:
                result = self.decode(data, parent=parent)
            else:
                result = self.decode(data)
        finally:
            # Restore context
            YamlModuleParser.context = saved_context

        return result


class TypedYamlParser(YamlModuleParser):
    """
    Base class for parsers that support type-based registration and validation.

    This class provides a common pattern for parsers that handle multiple types
    (e.g., OrbitYamlParser handles 'elliptic', 'fixed', 'global' types).
    Each parser and its associated Pydantic model can be registered for validation.

    Note: Subclasses should define their own parsers and models dictionaries to avoid sharing.
    """

    default_type = None
    detect_trivial = True
    models = {}
    parsers = {}
    _validator = ConfigValidator()

    def __init_subclass__(cls, **kwargs):
        """Ensure each subclass gets its own parsers and models dictionaries."""
        super().__init_subclass__(**kwargs)
        cls.parsers = {}
        cls.models = {}

    @classmethod
    def register_parser(cls, type_name, parser, model=None):
        """
        Register a parser for a given type.

        Args:
            type_name: The type identifier (e.g., 'elliptic', 'uniform')
            parser: The parser instance/class to handle this type
            model: Optional Pydantic model class to validate data before parsing
        """
        cls.parsers[type_name] = parser
        if model is not None:
            cls.models[type_name] = model

    # Aliases for backward compatiblity
    register = register_parser
    register_object_parser = register_parser

    @classmethod
    def get_type_and_data(cls, data, default=None, detect_trivial=True, map_type=True):
        """
        Extract type and parameters from data.

        This method handles various data formats for type detection:
        - If data is None, it uses the default type if provided.
        - If data is a string, it treats it as the type with no parameters.
        - If data is a dictionary and has only one key (and detect_trivial is True),
          it treats that key as the type and its value as parameters.
        - Otherwise, it looks for a 'type' key in the dictionary, and treats the whole dictionary as parameters.
        """
        if data is None:
            if default is not None:
                object_type = default.lower()
                object_data = {'type': object_type}
            else:
                object_type = None
                object_data = None
        elif isinstance(data, str):
            object_type = data.lower()
            object_data = {'type': object_type}
        else:
            if detect_trivial and len(data) == 1 and data.get('type') is None:
                object_type = list(data)[0]
                object_data = data[object_type]
                if isinstance(object_data, dict):
                    if 'type' in object_data:
                        # Avoid conflict if 'type' is already present
                        object_type = object_data.get('type', default)
                    else:
                        # Inject 'type' into the data for consistency
                        object_data['type'] = object_type
                else:
                    if map_type:
                        # If the value is not a dict, treat it as a simple type definition
                        object_data = {'type': object_type, object_type: object_data}
            else:
                object_type = data.get('type', default)
                object_data = data
        return (object_type, object_data)

    @classmethod
    def validate_and_decode(cls, type_name, parameters):
        """
        Validate parameters against registered model if available.

        Args:
            type_name: The type name
            parameters: The raw dictionary parameters

        Returns:
            Validated Pydantic model if model is registered, otherwise raw dict
        """
        if type_name in cls.models:
            model_class = cls.models[type_name]
            return cls._validator.validate_dict(parameters, model_class, context=type_name)
        else:
            print(f"No model registered for {type_name}, skipping validation.")
        return parameters

    @classmethod
    def canonize_data(cls, data):
        """
        Canonize data for type detection.

        This method can be overridden by subclasses to implement specific canonization logic.
        By default, it returns the data unchanged."""
        return data

    @classmethod
    def decode_object(cls, data, **extra):
        """
        Decode a single object from data.

        This method handles both already validated Pydantic models and raw dictionaries.
        If data is a Pydantic model, it uses the 'type' field to find
        the appropriate parser. If data is a raw dictionary, it first canonizes it,
        then extracts the type and parameters, validates them if a model is registered,
        and finally uses the appropriate parser to decode it."""
        if isinstance(data, BaseModel):
            if data.type in cls.parsers:
                parser = cls.parsers[data.type]
                return parser.decode(data, **extra)
            else:
                print("Unknown type '%s'" % data.type)
                return None
        else:
            data = cls.canonize_data(data)
            object_type, parameters = cls.get_type_and_data(data, cls.default_type, detect_trivial=cls.detect_trivial)
            if object_type in cls.parsers:
                parser = cls.parsers[object_type]
                # Validate parameters if model is registered
                validated_parameters = cls.validate_and_decode(object_type, parameters)
                return parser.decode(validated_parameters, **extra)
            else:
                print("Unknown type '%s'" % object_type)
                return None

    @classmethod
    def decode_objects_list(cls, data, **extra):
        """
        Decode a list of objects from data.

         This method expects data to be a list of entries, where each entry can be either
         a validated Pydantic model or a raw dictionary. It iterates over the list,
         decodes each entry using decode_object, and collects the results into a list."""
        if data is None:
            return []
        objects = []
        for entry in data:
            parsed_data = cls.decode_object(entry, **extra)
            if parsed_data is not None:
                objects.append(parsed_data)
        return objects

    @classmethod
    def decode(cls, data, **extra):
        """Decode data which can be a single object or a list of objects."""
        if isinstance(data, list):
            return cls.decode_objects_list(data, **extra)
        else:
            return cls.decode_object(data, **extra)
