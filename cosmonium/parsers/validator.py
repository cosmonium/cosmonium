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
Configuration validation layer.
"""

import logging
from pathlib import Path
from typing import Any, Type, TypeVar, Union

from pydantic import BaseModel, TypeAdapter, ValidationError

from .yamlloader import YamlLoader

logger = logging.getLogger('config')

T = TypeVar('T', bound=BaseModel)


class ConfigValidationError(ValueError):
    """Error during configuration validation.

    Subclasses `ValueError` so existing code that catches the more generic `ValueError` catches also validation errors.
    """

    def __init__(self, message: str, errors: list = None, filepath: str = None):
        self.message = message
        self.errors = errors or []
        self.filepath = filepath
        super().__init__(self._format_message())

    def _format_message(self):
        """Format validation error message."""
        msg = self.message
        if self.filepath:
            msg = f"{self.filepath}: {msg}"

        if self.errors:
            msg += "\nValidation errors:\n"
            for error in self.errors:
                loc = " -> ".join(str(x) for x in error['loc'])
                msg += f"  * {loc}: {error['msg']}\n"

        return msg


class ConfigValidator:
    """Validator for configuration files."""

    def validate_file(self, filepath: Union[str, Path], model_class: Type[T]) -> T:
        """Validate a YAML configuration file.

        Args:
            filepath: Path to YAML file
            model_class: Pydantic model class to validate against

        Returns:
            Validated model instance if successful

        Raises:
            ConfigValidationError: If validation fails
        """
        filepath = Path(filepath)

        # Load YAML file
        data = YamlLoader.load_file(filepath)

        # Validate against model
        try:
            validated = model_class.model_validate(data)
            logger.debug(f"Successfully validated {filepath} against {model_class.__name__}")
            return validated
        except ValidationError as e:
            errors = e.errors()
            error_msg = f"Configuration validation failed for {model_class.__name__}"
            raise ConfigValidationError(error_msg, errors=errors, filepath=str(filepath))

    def validate_dict(self, data: dict, model_class: Type[T], context: dict = None) -> T:
        """Validate a dictionary against a Pydantic model.

        Args:
            data: Dictionary to validate
            model_class: Pydantic model class
            context: Optional context for error messages

        Returns:
            Validated model instance

        Raises:
            ConfigValidationError: If validation fails
        """
        try:
            validated = model_class.model_validate(data)
            logger.debug(f"Successfully validated data against {model_class.__name__}")
            return validated
        except ValidationError as e:
            errors = e.errors()
            error_msg = f"Configuration validation failed for {model_class.__name__}"

            if context:
                error_msg += f" (context: {context})"

            raise ConfigValidationError(error_msg, errors=errors)

    def validate_union(self, data: Any, type_adapter: TypeAdapter, context: str = None) -> Any:
        """Validate a value against a Pydantic union type, via a pre-built TypeAdapter.

        Used to classify a raw value against several candidate models at once. The caller
        then dispatches on the returned instance's type.

        Args:
            data: Value to validate
            type_adapter: A `TypeAdapter` built from the candidate union types
            context: Optional context for error messages

        Returns:
            An instance of whichever union member matched

        Raises:
            ConfigValidationError: If validation fails against every union member
        """
        try:
            return type_adapter.validate_python(data)
        except ValidationError as e:
            errors = e.errors()
            error_msg = "Configuration validation failed"

            if context:
                error_msg += f" (context: {context})"

            raise ConfigValidationError(error_msg, errors=errors)
