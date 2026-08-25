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


"""Pydantic models for UI configuration validation."""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import ConfigDict, Field, model_validator

from ...parsers.schemas.base import ConfigBase

AlignmentLiteral = Literal['left', 'right', 'center', 'min', 'max']
AnchorLiteral = Literal['top', 'bottom', 'left', 'right', 'top-left', 'top-right', 'bottom-left', 'bottom-right']
CornerLiteral = Literal['top-left', 'top-right', 'bottom-left', 'bottom-right']
OrientationLiteral = Literal['horizontal', 'vertical']
TextAlignLiteral = Literal['left', 'center', 'right']


# ============================================================================
# Widget Configuration Models
# ============================================================================


class StyleableConfig(ConfigBase):
    """Base class for UI configuration models that can be targeted by a skin selector.

    Adds the CSS-like `class` and `id` fields used for skin targeting.
    """

    model_config = ConfigDict(extra='forbid')

    class_: Optional[Union[str, List[str]]] = Field(
        None, alias='class', description="Extra CSS-like class name(s) for skin targeting"
    )
    id: Optional[str] = Field(None, description="Element ID for skin targeting")


class ButtonWidgetConfig(StyleableConfig):
    """Configuration for button dock widgets."""

    type: Literal['button'] = Field(description="Widget type identifier")
    text: Optional[str] = Field(None, description="Button label text")
    code: Optional[str] = Field(None, pattern=r'^[0-9a-fA-F]+$', description="Unicode hex code for icon")
    event: Optional[str] = Field(None, description="Event name to send when clicked")
    menu: Optional[str] = Field(
        None, description="Name of a popup menu to open when clicked (mutually exclusive with 'event')"
    )
    rescale: Optional[bool] = Field(False, description="Auto-resize button to fit content")
    align: Optional[List[AlignmentLiteral]] = Field(None, min_length=2, max_length=2, description="Widget alignment")
    borders: Optional[Any] = Field(None, description="Border configuration")
    tooltip: Optional[str] = Field(None, description="Tooltip text")

    @model_validator(mode='after')
    def validate_text_or_code(self):
        """Button must have either text or code, but not both."""
        if self.text is None and self.code is None:
            raise ValueError("Button must have either 'text' or 'code' field")
        if self.text is not None and self.code is not None:
            raise ValueError("Button cannot have both 'text' and 'code' fields")
        return self

    @model_validator(mode='after')
    def validate_event_or_menu(self):
        """A button cannot both send an event and open a menu."""
        if self.event is not None and self.menu is not None:
            raise ValueError("Button cannot have both 'event' and 'menu' fields")
        return self


class OptionMenuWidgetConfig(StyleableConfig):
    """Configuration for option-menu dock widgets."""

    type: Literal['option-menu'] = Field(description="Widget type identifier")
    items: List[str] = Field(min_length=1, description="Selectable option labels")
    event: str = Field(description="Event name to send, with the selected label as argument, on selection")
    selected: Optional[str] = Field(None, description="Python expression evaluating to the initially selected item")
    align: Optional[List[AlignmentLiteral]] = Field(None, min_length=2, max_length=2, description="Widget alignment")
    borders: Optional[Any] = Field(None, description="Border configuration")
    tooltip: Optional[str] = Field(None, description="Tooltip text")


class TextWidgetConfig(StyleableConfig):
    """Configuration for text dock widgets."""

    type: Literal['text'] = Field(description="Widget type identifier")
    text: str = Field(description="Template text to display")
    # TODO: align is the alignment of the text inside the label, not the label itself.
    align: Optional[TextAlignLiteral] = Field('left', description="Text alignment (left/center/right)")
    borders: Optional[Any] = Field(None, description="Border configuration")


class SpacerWidgetConfig(ConfigBase):
    """Configuration for spacer dock widgets."""

    model_config = ConfigDict(extra='forbid')

    type: Literal['spacer'] = Field(description="Widget type identifier")
    size: List[Union[float, str]] = Field(
        default=[0, 0], min_length=2, max_length=2, description="[width, height], as CSS lengths"
    )
    align: Optional[List[AlignmentLiteral]] = Field(None, min_length=2, max_length=2, description="Widget alignment")


class LayoutWidgetConfig(StyleableConfig):
    """Configuration for layout dock widgets."""

    type: Literal['layout'] = Field(description="Widget type identifier")
    orientation: OrientationLiteral = Field('horizontal', description="Layout orientation")
    widgets: List['WidgetConfig'] = Field(default_factory=list, description="Child widgets")
    align: Optional[List[AlignmentLiteral]] = Field(None, description="Widget alignment")
    borders: Optional[Any] = Field(None, description="Border configuration")
    gaps: Optional[List[float]] = Field(None, description="Spacing between widgets")


# Union type for all widget configs
WidgetConfig = Union[
    ButtonWidgetConfig, TextWidgetConfig, SpacerWidgetConfig, LayoutWidgetConfig, OptionMenuWidgetConfig
]

LayoutWidgetConfig.model_rebuild()  # Rebuild to resolve forward reference


# ============================================================================
# Component Configuration Models
# ============================================================================


class DockConfig(StyleableConfig):
    """Configuration for dock widgets."""

    orientation: OrientationLiteral = Field('horizontal', description="Dock orientation")
    anchor: AnchorLiteral = Field('bottom', description="Screen location for the dock")
    widgets: List[WidgetConfig] = Field(default_factory=list, description="Widgets in the dock")
    gaps: Optional[List[float]] = Field(None, description="Spacing between widgets")
    borders: Optional[Any] = Field(None, description="Border configuration")


class HUDEntryConfig(ConfigBase):
    """Configuration for a HUD text entry."""

    model_config = ConfigDict(extra='forbid')

    condition: Optional[str] = Field(None, description="Python expression for visibility condition")
    title: Optional[str] = Field(None, description="Entry title")
    text: Optional[str] = Field(None, description="Template text to display")
    entries: Optional[List['HUDEntryConfig']] = Field(None, description="Nested entries")

    @model_validator(mode='after')
    def validate_text_or_entries(self):
        """Entry must have either text or entries, but not both."""
        if self.text is None and self.entries is None:
            raise ValueError("HUD entry must have either 'text' or 'entries' field")
        if self.text is not None and self.entries is not None:
            raise ValueError("HUD entry cannot have both 'text' and 'entries' fields")
        return self


HUDEntryConfig.model_rebuild()  # Rebuild to resolve forward reference


class HUDWidgetConfig(StyleableConfig):
    """Configuration for HUD widgets."""

    anchor: CornerLiteral = Field(description="Screen anchor position")
    size: int = Field(5, ge=1, description="Maximum number of lines to display")
    entries: List[HUDEntryConfig] = Field(default_factory=list, description="HUD entries to display")
    type: Optional[str] = Field(None, description="Type of HUD widget")


class UIDocksConfig(ConfigBase):
    """Configuration for dock file."""

    dock: List[DockConfig] = Field(default_factory=list)


class UIHudsConfig(ConfigBase):
    """Configuration for hud file."""

    hud: List[HUDWidgetConfig] = Field(default_factory=list)


# ============================================================================
# Menu Configuration Models
# ============================================================================


class MenuEntryConfig(ConfigBase):
    """Configuration for a menu entry."""

    model_config = ConfigDict(extra='forbid')

    title: Optional[str] = Field(None, description="Menu entry title (only if sub entries)")
    event: Optional[Union[str, Literal[0]]] = Field(None, description="Event to send when activated (0 to deactivate)")
    menu: Optional[str] = Field(None, description="Named submenu reference")
    entries: Optional[List[Union['MenuEntryConfig', None]]] = Field(
        None, description="Inline submenu entries (None for separator)"
    )
    state: Optional[str] = Field(None, description="Python expression for entry state")
    enabled: Optional[str] = Field(None, description="Python expression for enabled condition")
    visible: Optional[str] = Field(None, description="Python expression for visibility condition")

    @model_validator(mode='after')
    def validate_text_or_entries(self):
        """Entry with entries must have a title and no event nor state."""
        if self.menu is not None and self.entries is not None:
            raise ValueError("Menu entry cannot have both 'menu' and 'entries' fields")
        if self.entries is not None or self.menu is not None:
            if self.title is None:
                raise ValueError("Menu entry with sub entries must have a 'title' field")
            if self.event is not None:
                raise ValueError("Menu entry with sub entries can not have an 'event' field")
            if self.state is not None:
                raise ValueError("Menu entry with sub entries can not have an 'state' field")
        return self


MenuEntryConfig.model_rebuild()  # Rebuild to resolve forward reference


class MenusConfigModel(ConfigBase):
    """Configuration for the menus and menubar."""

    model_config = ConfigDict(extra='forbid')

    menus: Dict[str, List[Union[MenuEntryConfig, None]]] = Field(default_factory=dict, description="Named menus")
    menubar: Optional[List[MenuEntryConfig]] = Field(None, description="Menubar entries")


class PopupMenuConfig(ConfigBase):
    """Configuration for popup menus."""

    model_config = ConfigDict(extra='forbid')

    popup: List[Union[MenuEntryConfig, None]] = Field(default_factory=list, description="Popup menu entries")


class ShortcutConfig(ConfigBase):
    """Configuration for a keyboard shortcut."""

    model_config = ConfigDict(extra='forbid')

    event: str = Field(description="Event name to trigger")
    keys: List[str] = Field(min_length=1, description="Key combinations")


# ============================================================================
# Skin Configuration Models
# ============================================================================


class SkinSelectorConfig(ConfigBase):
    """Configuration for a skin selector."""

    model_config = ConfigDict(extra='forbid')

    element: Optional[str] = Field(None, description="Element type (e.g., 'button', 'label')")
    state: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Element state (e.g., 'hover', 'active') as a CSS-like pseudo-class, or as a list of pseudo-classes "
            "all required to be active at once."
        ),
    )
    class_: Optional[Union[str, List[str]]] = Field(
        None, alias='class', description="CSS-like class name, or list of class names all required to match"
    )
    id: Optional[str] = Field(None, description="Element ID")
    parent: Optional['SkinSelectorConfig'] = Field(None, description="Parent selector for nesting")


SkinSelectorConfig.model_rebuild()  # Rebuild to resolve forward reference


class SkinEntryConfig(ConfigBase):
    """Configuration for a skin style entry."""

    model_config = ConfigDict(extra='forbid')

    element: Optional[str] = Field(None, description="Element type")
    state: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Element state (e.g., 'hover', 'active') as a CSS-like pseudo-class, or as a list of pseudo-classes "
            "all required to be active at once."
        ),
    )
    class_: Optional[Union[str, List[str]]] = Field(
        None, alias='class', description="CSS class, or list of class names all required to match"
    )
    id: Optional[str] = Field(None, description="Element ID")
    parent: Optional[SkinSelectorConfig] = Field(None, description="Parent selector")

    # Style properties
    background_color: Optional[Union[str, List[float]]] = Field(
        None, description="Background color (hex string or RGB list)"
    )
    text_color: Optional[Union[str, List[float]]] = Field(None, description="Text color (hex string or RGB list)")
    border_color: Optional[Union[str, List[float]]] = Field(None, description="Border color (hex string or RGB list)")
    border_radius: Optional[Union[float, str]] = Field(None, description="Border radius (CSS value)")
    border_width: Optional[Union[float, str]] = Field(None, description="Border width (CSS value)")
    font_family: Optional[str] = Field(None, description="Font family name")
    font_size: Optional[Union[float, str]] = Field(None, description="Font size (numeric or CSS string)")
    font_style: Optional[str] = Field(None, description="Font style (e.g., 'italic')")
    font_weight: Optional[str] = Field(None, description="Font weight (e.g., 'bold')")
    margin: Optional[Union[str, List[str]]] = Field(None, description="Margin around the element")
    padding: Optional[Union[str, List[str]]] = Field(None, description="Padding inside the element")
    width: Optional[str] = Field(None, description="Element width (CSS value)")
    height: Optional[str] = Field(None, description="Element height (CSS value)")


class SkinRootConfig(ConfigBase):
    """Configuration for the CSS-like `root` pseudo-element.

    A skin entry targeting the `root` pseudo-element configures root-level skin
    properties instead of styling a widget`.
    """

    model_config = ConfigDict(extra='forbid')

    element: Literal['root'] = Field(description="Must be 'root' to target the root pseudo-element")
    font_size: Optional[Union[float, str]] = Field(None, description="Root font size (plain number or px value)")


class SkinVariablesConfig(ConfigBase):
    """Configuration for a `variables:` block, declaring skin variables shared across entries."""

    model_config = ConfigDict(extra='forbid')

    variables: Dict[str, Any] = Field(description="Named variables, referenced elsewhere via var(name)")


# An item in a skin file is a variables declaration, a `root` directive, or a regular styling entry;
# tried in that order (left to right) since a root-only entry `{element: root, font-size: ...}`
# would also satisfy SkinEntryConfig's (all-optional) fields.
SkinFileEntryConfig = Annotated[
    Union[SkinVariablesConfig, SkinRootConfig, SkinEntryConfig], Field(union_mode='left_to_right')
]


class UISkinConfig(ConfigBase):
    """Configuration for a skin style."""

    entries: List[SkinEntryConfig] = Field(default_factory=list)


# ============================================================================
# Main UI Configuration Model
# ============================================================================


class UIConfigModel(ConfigBase):
    """Main UI configuration file model."""

    model_config = ConfigDict(extra='forbid')

    skin: Optional[str] = Field(None, description="Path to skin YAML file")
    shortcuts: Optional[str] = Field(None, description="Path to shortcuts YAML file")
    menus: Optional[str] = Field(
        None,
        description="Path to a YAML file with the menus definitions",
    )
    popup: Optional[str] = Field(None, description="Path to popup menu YAML file")
    dock: Optional[str] = Field(None, description="Path to dock YAML file")
    hud: Optional[str] = Field(None, description="Path to HUD YAML file")
    locale: Optional[str] = Field(None, description="Path to locale directory")
