#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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

# This code is imported from Celesta bigfix.cpp to be used for cel:// url
# parsing and encoding
#
# Copyright (C) 2007-2008, Chris Laurel <claurel@shatters.net>
#
# 128-bit fixed point (64.64) numbers for high-precision celestial
# coordinates.  When you need millimeter accurate navigation across a scale
# of thousands of light years, double precision floating point numbers
# are inadequate.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.


from math import floor


class Bigfix:

    INT64_MAX = 9223372036854775807
    POW2_31 = 2147483648.0
    POW2_32 = 4294967296.0
    POW2_64 = POW2_32 * POW2_32
    WORD0_FACTOR = 1.0 / POW2_64
    WORD1_FACTOR = 1.0 / POW2_32
    WORD2_FACTOR = 1.0
    WORD3_FACTOR = POW2_32

    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    valid_char = [False for i in range(255)]
    decoder = [0 for i in range(255)]
    for i in range(len(alphabet)):
        c = ord(alphabet[i])
        valid_char[c] = True
        decoder[c] = i

    @classmethod
    def bigfix_to_float(cls, value):
        n = [0, 0, 0, 0, 0, 0, 0, 0]
        char_count = 0
        bits = 0
        i = 0
        for j in range(len(value)):
            c = value[j]
            oc = ord(c)
            if c == '=':
                break
            if oc > 255 or not cls.valid_char[oc]:
                continue
            bits += cls.decoder[oc]
            char_count += 1
            if char_count == 4:
                n[i // 2] >>= 8
                n[i // 2] += (bits >> 8) & 0xFF00
                i += 1
                n[i // 2] >>= 8
                n[i // 2] += bits & 0xFF00
                i += 1
                n[i // 2] >>= 8
                n[i // 2] += (bits << 8) & 0xFF00
                i += 1
                bits = 0
                char_count = 0
            else:
                bits <<= 6
        if char_count == 2:
            n[i // 2] >>= 8
            n[i // 2] += (bits >> 2) & 0xFF00
            i += 1
        elif char_count == 3:
            n[i // 2] >>= 8
            n[i // 2] += (bits >> 8) & 0xFF00
            i += 1
            n[i // 2] >>= 8
            n[i // 2] += bits & 0xFF00
            i += 1

        if (i & 1) != 0:
            n[i // 2] >>= 8

        # Now, convert the 8 16-bit values to a 2 64-bit values
        lo = (n[0] | (n[1] << 16) | (n[2] << 32) | (n[3] << 48)) & 0xFFFFFFFFFFFFFFFF
        hi = (n[4] | (n[5] << 16) | (n[6] << 32) | (n[7] << 48)) & 0xFFFFFFFFFFFFFFFF

        if hi > cls.INT64_MAX:
            hi = (~hi) & 0xFFFFFFFFFFFFFFFF
            lo = (~lo) & 0xFFFFFFFFFFFFFFFF
            lo += 1
            if lo == 0:
                hi += 1
            sign = -1
        else:
            sign = 1

        w0 = lo & 0xFFFFFFFF
        w1 = lo >> 32
        w2 = hi & 0xFFFFFFFF
        w3 = hi >> 32
        d = (w0 * cls.WORD0_FACTOR + w1 * cls.WORD1_FACTOR + w2 * cls.WORD2_FACTOR + w3 * cls.WORD3_FACTOR) * sign
        return d

    @classmethod
    def float_to_bigfix(cls, value):
        # Handle negative values by inverting them before conversion,
        # then inverting the converted value.
        if value < 0:
            isNegative = True
            value = -value
        else:
            isNegative = False

        # Need to break the number into 32-bit chunks because a 64-bit
        # integer has more bits of precision than a double.
        e = floor(value * (1.0 / cls.WORD3_FACTOR))
        if e < cls.POW2_31:
            w3 = int(e) & 0xFFFFFFFF
            value -= w3 * cls.WORD3_FACTOR
            w2 = int(value * (1.0 / cls.WORD2_FACTOR)) & 0xFFFFFFFF
            value -= w2 * cls.WORD2_FACTOR
            w1 = int(value * (1.0 / cls.WORD1_FACTOR)) & 0xFFFFFFFF
            value -= w1 * cls.WORD1_FACTOR
            w0 = int(value * (1.0 / cls.WORD0_FACTOR)) & 0xFFFFFFFF

            hi = (w3 << 32) | w2
            lo = (w1 << 32) | w0

        if isNegative:
            # For a twos-complement number, -n = ~n + 1
            hi = (~hi) & 0xFFFFFFFFFFFFFFFF
            lo = (~lo) & 0xFFFFFFFFFFFFFFFF
            lo += 1
            if lo == 0:
                hi += 1

        n = [0, 0, 0, 0, 0, 0, 0, 0]
        n[0] = lo & 0xFFFF
        n[1] = (lo >> 16) & 0xFFFF
        n[2] = (lo >> 32) & 0xFFFF
        n[3] = (lo >> 48) & 0xFFFF

        n[4] = hi & 0xFFFF
        n[5] = (hi >> 16) & 0xFFFF
        n[6] = (hi >> 32) & 0xFFFF
        n[7] = (hi >> 48) & 0xFFFF

        encoded = ""

        char_count = 0
        bits = 0

        # Find first significant (non null) byte
        i = 16
        while True:
            i -= 1
            c = n[i // 2]
            if (i & 1) != 0:
                c >>= 8
            c &= 0xFF
            if not ((c == 0) and (i != 0)):
                break

        if i == 0:
            return encoded

        # Then we encode starting by the LSB (i+1 bytes to encode)
        j = 0
        while j <= i:
            c = n[j // 2]
            if (j & 1) != 0:
                c >>= 8
            c &= 0xFF
            j += 1
            bits += c
            char_count += 1
            if char_count == 3:
                encoded += cls.alphabet[bits >> 18]
                encoded += cls.alphabet[(bits >> 12) & 0x3F]
                encoded += cls.alphabet[(bits >> 6) & 0x3F]
                encoded += cls.alphabet[bits & 0x3F]
                bits = 0
                char_count = 0
            else:
                bits <<= 8
        if char_count != 0:
            bits <<= 16 - (8 * char_count)
            encoded += cls.alphabet[bits >> 18]
            encoded += cls.alphabet[(bits >> 12) & 0x3F]
            if char_count != 1:
                encoded += cls.alphabet[(bits >> 6) & 0x3F]
        return encoded
