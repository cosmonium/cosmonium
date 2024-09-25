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


class LodControl(object):
    def __init__(self, density=32, max_lod=100):
        self.density = density
        self.max_lod = max_lod

    def get_density_for(self, lod):
        return self.density

    def set_appearance(self, appearance):
        pass

    def set_texture_size(self, appearance):
        pass

    def should_split(self, patch, apparent_patch_size, distance):
        return False

    def should_merge(self, patch, apparent_patch_size, distance):
        return False

    def should_instanciate(self, patch, apparent_patch_size, distance):
        return patch.visible and len(patch.children) == 0

    def should_remove(self, patch, apparent_patch_size, distance):
        return not patch.visible


# The lod control classes uses hysteresis to avoid cycle of split/merge due to
# precision errors.
# When splitting the resulting patch will be 1.1 bigger than the merge limit
# When merging, the resulting patch will be  1.1 smaller than the slit limit


class TextureLodControl(LodControl):
    def __init__(self, min_density, density, max_lod=100):
        LodControl.__init__(self, density, max_lod)
        self.min_density = min_density
        self.texture_size = 0

    def get_density_for(self, lod):
        return max(self.min_density, self.density // (1 << lod))

    def set_appearance(self, appearance):
        self.appearance = appearance
        if appearance is not None and appearance.texture is not None:
            self.texture_size = appearance.texture.source.texture_size
        else:
            self.texture_size = 0

    def set_texture_size(self, texture_size):
        self.texture_size = texture_size

    def should_split(self, patch, apparent_patch_size, distance):
        if patch.lod < self.max_lod:
            return (
                self.texture_size > 0 and apparent_patch_size > self.texture_size * 1.1
            )  # and self.appearance.texture.can_split(patch)
        else:
            return False

    def should_merge(self, patch, apparent_patch_size, distance):
        return apparent_patch_size < self.texture_size / 1.1


class TextureOrVertexSizeLodControl(TextureLodControl):
    def __init__(self, max_vertex_size, min_density, density, max_lod=100):
        TextureLodControl.__init__(self, min_density, density, max_lod)
        self.max_vertex_size = max_vertex_size

    def should_split(self, patch, apparent_patch_size, distance):
        if patch.lod >= self.max_lod:
            return False
        if self.texture_size > 0:
            if apparent_patch_size > self.texture_size * 1.1:
                return True
        else:
            apparent_vertex_size = apparent_patch_size / patch.density
            return apparent_vertex_size > self.max_vertex_size

    def should_merge(self, patch, apparent_patch_size, distance):
        if self.texture_size > 0:
            return apparent_patch_size < self.texture_size / 1.1
        else:
            apparent_vertex_size = apparent_patch_size / patch.density
            return apparent_vertex_size < self.max_vertex_size / 1.1


class VertexSizeLodControl(LodControl):
    def __init__(self, max_vertex_size, density, max_lod=100):
        LodControl.__init__(self, density, max_lod)
        self.max_vertex_size = max_vertex_size

    def should_split(self, patch, apparent_patch_size, distance):
        if patch.lod < self.max_lod:
            apparent_vertex_size = apparent_patch_size / patch.density
            return apparent_vertex_size > self.max_vertex_size * 1.1
        else:
            return False

    def should_merge(self, patch, apparent_patch_size, distance):
        apparent_vertex_size = apparent_patch_size / patch.density
        return apparent_vertex_size < self.max_vertex_size / 1.1


class VertexSizeMaxDistanceLodControl(VertexSizeLodControl):
    def __init__(self, max_distance, max_vertex_size, density, max_lod=100):
        VertexSizeLodControl.__init__(self, max_vertex_size, density, max_lod)
        self.max_distance = max_distance

    def should_instanciate(self, patch, apparent_patch_size, distance):
        return patch.visible and distance < self.max_distance

    def should_remove(self, patch, apparent_patch_size, distance):
        return not patch.visible
