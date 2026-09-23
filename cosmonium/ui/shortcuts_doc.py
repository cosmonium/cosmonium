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
Generates the shortcuts help document as markdown directly from the loaded shortcuts
configuration, so it can never drift out of sync with the actual key bindings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .shortcut_descriptions import SHORTCUT_DESCRIPTIONS
from .shortcuts import remap_key_for_platform

if TYPE_CHECKING:
    from .config.models import ShortcutCategoryConfig, ShortcutConfig


def _key_display(raw_key: str) -> str:
    return raw_key.replace('_', '-').title()


def _description(shortcut: ShortcutConfig) -> str:
    """Returns shortcut description, or event description if not set."""
    if shortcut.description is not None:
        return shortcut.description
    return SHORTCUT_DESCRIPTIONS.get(shortcut.event, shortcut.event)


def _shortcut_key_strings(shortcut: ShortcutConfig) -> List[str]:
    return [remap_key_for_platform(key if isinstance(key, str) else key.key) for key in shortcut.keys]


def _format_keys_label(keys: List[str]) -> str:
    """Format linked keys"""
    # Collapse a contiguous run of single-digit keys into a range.
    if len(keys) > 1 and all(len(key) == 1 and key.isdigit() for key in keys):
        digits = sorted(int(key) for key in keys)
        if digits == list(range(digits[0], digits[-1] + 1)):
            return f"{digits[0]}-{digits[-1]}"
    # Unrelated keys
    return ' / '.join(_key_display(key) for key in keys)


def _group_shortcuts(shortcuts: List[ShortcutConfig]) -> List[List[ShortcutConfig]]:
    """Group shortcuts sharing the same `link` id, preserving first-occurrence order."""
    groups: List[List[ShortcutConfig]] = []
    group_by_link = {}
    for shortcut in shortcuts:
        group = group_by_link.get(shortcut.link) if shortcut.link is not None else None
        if group is None:
            group = [shortcut]
            groups.append(group)
            if shortcut.link is not None:
                group_by_link[shortcut.link] = group
        else:
            group.append(shortcut)
    return groups


def generate_control_help(categories: List[ShortcutCategoryConfig], translation: Optional[object] = None) -> str:
    """
    Build the markdown control help document from the loaded shortcuts.

    Shortcuts are shown grouped by category, in the order they appear in the
    configuration. Shortcuts sharing the same `link` id are merged into a single entry.

    Args:
        categories: List of shortcut categories
        translation: Optional gettext translation used to translate category
            names and shortcut descriptions

    Returns:
        The control help document, as markdown text
    """

    def translate(text: str) -> str:
        if translation is not None:
            return translation.gettext(text)
        return text

    lines = []
    for category in categories:
        if not category.shortcuts:
            continue
        lines.append(f"### {translate(category.category)}")
        for group in _group_shortcuts(category.shortcuts):
            keys_label = ' / '.join(_format_keys_label(_shortcut_key_strings(shortcut)) for shortcut in group)
            description = ' / '.join(translate(_description(shortcut)) for shortcut in group)
            lines.append(f"- **{keys_label}** : {description}")
        lines.append("")
    return '\n'.join(lines)
