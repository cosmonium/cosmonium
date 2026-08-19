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
Skin loader.

This module handles loading of UI skin configurations from YAML files.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from pydantic import TypeAdapter

from ...parsers.yamlloader import YamlLoader
from ..config.models import (
    SkinEntryConfig,
    SkinFileEntryConfig,
    SkinRootConfig,
    SkinSelectorConfig,
    SkinVariablesConfig,
)
from ..skin import ParentSelector, Selector, UISkin, UISkinEntry, report_error
from .base import BaseComponentLoader
from .parsers import ParsersCollection

if TYPE_CHECKING:
    from ...parsers.validator import ConfigValidator
    from ..gui import Gui


# Matches CSS custom-property-like references: var(name)
_VAR_REFERENCE = re.compile(r'var\(([-\w]+)\)')

# Classifies a raw skin file item as a `variables:` block or a regular styling entry.
_SKIN_FILE_ENTRY_ADAPTER = TypeAdapter(SkinFileEntryConfig)


def resolve_variables(value: Any, variables: Dict[str, Any], context: str = None) -> Any:
    """
    Recursively substitute `var(name)` references in a skin entry's raw YAML data.

    Skin variables are similar to CSS custom properties: they are resolved
    once, at load time, against a single flat namespace collected from every
    `variables:` block in the skin file (regardless of where the block or the
    reference appears) - there is no per-selector scoping or cascading override.

    Note: Unresolved variable references are left as-is, and a warning is logged.

    Args:
        value: A raw YAML value possibly containing `var(name)` references
        variables: Mapping of variable name to its resolved raw value
        context: Optional context (e.g. file and entry index) for error reporting

    Returns:
        The value with every `var(name)` reference replaced by the variable's value
    """
    if isinstance(value, str):
        stripped = value.strip()
        full_match = _VAR_REFERENCE.fullmatch(stripped)
        if full_match:
            # The whole value is a single reference: substitute in place so a
            # variable holding a non-string value (a list, a number) keeps its type.
            name = full_match.group(1)
            if name in variables:
                return variables[name]
            report_error(f"Undefined skin variable 'var({name})'", context)
            return value

        # The value is a string containing one or more references: replace them in-place.
        def substitute(match: re.Match) -> str:
            name = match.group(1)
            if name in variables:
                return str(variables[name])
            report_error(f"Undefined skin variable 'var({name})'", context)
            return match.group(0)

        return _VAR_REFERENCE.sub(substitute, value)
    if isinstance(value, list):
        return [resolve_variables(item, variables, context) for item in value]
    if isinstance(value, dict):
        return {key: resolve_variables(item, variables, context) for key, item in value.items()}
    return value


class SkinLoader(BaseComponentLoader):
    """
    Loader for UI skin configuration.

    Handles loading of UI skin entries that define visual styling for
    UI elements including colors, fonts, margins, padding, and sizes.
    """

    def __init__(self, gui: Gui, validator: ConfigValidator) -> None:
        """Initialize the skin loader with parsers.

        Args:
            gui: UI instance
            validator: ConfigValidator instance
        """
        self.gui = gui
        self.validator = validator
        self.parsers = ParsersCollection()

    def load_skin_selector(self, selector_config: SkinSelectorConfig) -> Any:
        """
        Load a CSS-like selector from configuration data.

        Args:
            selector_config: SkinSelectorConfig Pydantic model

        Returns:
            Selector or ParentSelector instance
        """

        selector = Selector(selector_config.element, selector_config.state, selector_config.class_, selector_config.id)

        if selector_config.parent is not None:
            parent_selector = self.load_skin_selector(selector_config.parent)
            selector = ParentSelector(parent_selector, selector)

        return selector

    @staticmethod
    def describe_selector(selector_config: SkinSelectorConfig) -> str:
        """
        Build a short human-readable description of a selector, for error reporting.

        Args:
            selector_config: SkinSelectorConfig Pydantic model

        Returns:
            A CSS-like textual rendering of the selector, e.g. "button.primary#ok:hover"
        """
        parts = [selector_config.element or '*']
        if selector_config.class_:
            classes = selector_config.class_ if isinstance(selector_config.class_, list) else [selector_config.class_]
            parts.append(''.join(f'.{class_name}' for class_name in classes))
        if selector_config.id:
            parts.append(f'#{selector_config.id}')
        if selector_config.state:
            parts.append(f':{selector_config.state}')
        description = ''.join(parts)
        if selector_config.parent is not None:
            description = f'{SkinLoader.describe_selector(selector_config.parent)} {description}'
        return description

    def load_skin_entry(self, entry_config: SkinEntryConfig, context: str = None) -> UISkinEntry:
        """
        Load a skin entry from configuration data.

        Args:
            entry_config: SkinEntryConfig Pydantic model
            context: Optional context (e.g. file and entry index) for error reporting

        Returns:
            UISkinEntry instance
        """
        # Load selector
        selector = self.load_skin_selector(entry_config)
        entry = UISkinEntry(selector, {})

        entry_context = f'{context}, selector "{self.describe_selector(entry_config)}"' if context else None

        # Parse colors using Pydantic model fields
        entry.background_color = self.parsers.color.parse(entry_config.background_color, entry_context)
        entry.text_color = self.parsers.color.parse(entry_config.text_color, entry_context)
        entry.border_color = self.parsers.color.parse(entry_config.border_color, entry_context)
        entry.border_radius = self.parsers.length.parse(entry_config.border_radius, entry_context)
        entry.border_width = self.parsers.length.parse(entry_config.border_width, entry_context)

        # Parse font properties
        entry.font_family = entry_config.font_family
        # `font-size` is the one property whose "em" values are relative to the parent element's
        # font size instead of the element's own, as in CSS.
        entry.font_size = self.parsers.length.parse(entry_config.font_size, entry_context, relative_to_parent=True)
        entry.font_style = entry_config.font_style
        entry.font_weight = entry_config.font_weight

        # Parse layout properties
        entry.margin = self.parsers.length.parse_edge_lengths(entry_config.margin, entry_context)
        entry.padding = self.parsers.length.parse_edge_lengths(entry_config.padding, entry_context)
        entry.width = self.parsers.length.parse(entry_config.width, entry_context)
        entry.height = self.parsers.length.parse(entry_config.height, entry_context)

        return entry

    @staticmethod
    def resolve_root_font_size(root_config: SkinRootConfig, context: str = None) -> Optional[float]:
        """
        Resolve a validated `root` entry `font-size` into a plain pixel value.

        The root font size is what "rem" lengths are relative to. It must be a plain
        pixel value (a bare number or a "px" string).

        Args:
            root_config: SkinRootConfig Pydantic model
            context: Optional context (e.g. file and entry index) for error reporting

        Returns:
            The root font size in px, or None if unset or invalid
        """
        value = root_config.font_size
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str) and value.endswith('px'):
            try:
                return float(value[:-2])
            except ValueError:
                report_error(f"Invalid root font-size {value!r}", context)
                return None
        report_error(f"Invalid root font-size {value!r} (must be a plain number or px value)", context)
        return None

    def load_skin_entries(self, data: List[Any], filepath: str = None) -> UISkin:
        """
        Load skin entries from configuration data.

        Args:
            data: List of skin entry configurations, root definition, or `variables:` blocks
            filepath: Optional path of the skin file being loaded, for error reporting

        Returns:
            UISkin instance
        """
        skin = UISkin()

        # First pass: Validate every raw item and collect the variables (merged from every `variables:` block,
        # regardless of where it appears in the file) so it's available to every entry below, irrespective of
        # declaration order.
        variables: Dict[str, Any] = {}
        pending: List[Tuple[int, Any, Any]] = []
        for index, raw_item in enumerate(data):
            context = f'{filepath or "<skin>"}, entry #{index}'
            parsed = self.validator.validate_union(raw_item, _SKIN_FILE_ENTRY_ADAPTER, context)
            if isinstance(parsed, SkinVariablesConfig):
                variables.update(parsed.variables)
                continue
            pending.append((index, raw_item, parsed))

        for index, raw_item, parsed in pending:
            context = f'{filepath or "<skin>"}, entry #{index}'
            if isinstance(parsed, SkinRootConfig):
                root_font_size = self.resolve_root_font_size(parsed, context)
                if root_font_size is not None:
                    skin.root_font_size = root_font_size
                continue
            # parsed is ignored for entries as we want to re-validate it with the variables resolved,
            # so that any `var(name)` references are replaced with their values and validated again.
            resolved_data = resolve_variables(raw_item, variables, context)
            validated = self.validator.validate_dict(resolved_data, SkinEntryConfig)
            entry = self.load_skin_entry(validated, context)
            skin.add_entry(entry)
        return skin

    def load(self, filepath: str) -> UISkin:
        """
        Load skin configuration from a YAML file.

        Args:
            filepath: Path to skin YAML file

        Returns:
            UISkin instance
        """
        data = YamlLoader.load_file(filepath, use_splash=False)
        skin = self.load_skin_entries(data, filepath)
        return skin
