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


import pytest

from cosmonium.engine.anchors import OriginAnchor


def make_anchor(name):
    return OriginAnchor(0, None, name)


class TestAsciiName:
    """Test AnchorBase.get_ascii_name()."""

    @pytest.mark.parametrize(
        "name, expected",
        [
            ("Sirius", "Sirius"),
            ("Alpha Centauri", "AlphaxCentauri"),
            ("HIP 32349", "HIPx32349"),
            ("Sol-3", "Solx3"),
            ("2007 OR10", "x2007xOR10"),
            ("", "x"),
        ],
    )
    def test_ascii_names(self, name, expected):
        assert make_anchor(name).get_ascii_name() == expected

    @pytest.mark.parametrize(
        "name, expected",
        [
            # U+2019 (right single quotation mark) is a 3 bytes sequence in UTF-8: e2 80 99
            ("Hi’iaka", "Hixiaka"),
            ("Namaka’s", "Namakaxs"),
            # 2 bytes sequence, c3 a9
            ("Éris", "xris"),
            ("Cañon", "Caxon"),
            # 4 bytes sequence
            ("A\U0001f680B", "AxB"),
        ],
    )
    def test_non_ascii_characters_are_replaced_as_a_whole(self, name, expected):
        ascii_name = make_anchor(name).get_ascii_name()
        assert ascii_name == expected
        # Must always be a valid, pure ASCII string (the C++ version used to return invalid UTF-8)
        assert ascii_name.isascii()
        assert ascii_name.encode("utf-8").decode("utf-8") == ascii_name
