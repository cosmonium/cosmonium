/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2022 Laurent Deru.
 *
 * Cosmonium is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Cosmonium is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Cosmonium.  If not, see <http://www.gnu.org/licenses/>.
 */


#ifndef SCENE_ANCHOR_COLLECTION_H
#define SCENE_ANCHOR_COLLECTION_H


#include "pandabase.h"
#include "pointerToArray.h"


class SceneAnchor;


class SceneAnchorCollection
{
PUBLISHED:
  SceneAnchorCollection();
  SceneAnchorCollection(const SceneAnchorCollection &copy);
  void operator =(const SceneAnchorCollection &copy);
  ~SceneAnchorCollection(void);

  void add_scene_anchor(SceneAnchor *scene_anchor);
  bool remove_scene_anchor(SceneAnchor *scene_anchor);
  void add_scene_anchors_from(const SceneAnchorCollection &other);
  void remove_scene_anchors_from(const SceneAnchorCollection &other);
  void remove_duplicate_scene_anchors(void);
  bool has_scene_anchor(SceneAnchor *scene_anchor) const;
  void clear(void);
  void reserve(size_t num);

  int get_num_scene_anchors() const;
  SceneAnchor *get_scene_anchor(int index) const;
  SceneAnchor *operator [](int index) const;
  int size(void) const;
  void operator +=(const SceneAnchorCollection &other);
  SceneAnchorCollection operator +(const SceneAnchorCollection &other) const;

  void append(SceneAnchor *scene_anchor);
  void extend(const SceneAnchorCollection &other);

private:
  typedef PTA(PT(SceneAnchor)) SceneAnchors;
  SceneAnchors _scene_anchors;
};

#endif
