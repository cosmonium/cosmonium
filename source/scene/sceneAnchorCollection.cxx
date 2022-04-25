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


#include "sceneAnchorCollection.h"
#include "sceneAnchor.h"


SceneAnchorCollection::SceneAnchorCollection() {
}


SceneAnchorCollection::SceneAnchorCollection(const SceneAnchorCollection &copy) :
  _scene_anchors(copy._scene_anchors)
{
}


void
SceneAnchorCollection::operator = (const SceneAnchorCollection &copy)
{
  _scene_anchors = copy._scene_anchors;
}


SceneAnchorCollection::~SceneAnchorCollection()
{
}


void
SceneAnchorCollection::add_scene_anchor(SceneAnchor *scene_anchor)
{
  // If the pointer to our internal array is shared by any other
  // SceneAnchorCollections, we have to copy the array now so we won't
  // inadvertently modify any of our brethren SceneAnchorCollection objects.

  if (_scene_anchors.get_ref_count() > 1) {
    SceneAnchors old_scene_anchors = _scene_anchors;
    _scene_anchors = SceneAnchors::empty_array(0);
    _scene_anchors.v() = old_scene_anchors.v();
  }

  _scene_anchors.push_back(scene_anchor);
}


bool
SceneAnchorCollection::remove_scene_anchor(SceneAnchor *scene_anchor)
{
  int scene_anchor_index = -1;
  for (int i = 0; scene_anchor_index == -1 && i < (int)_scene_anchors.size(); i++) {
    if (_scene_anchors[i] == scene_anchor) {
      scene_anchor_index = i;
    }
  }

  if (scene_anchor_index == -1) {
    // The indicated scene_anchor was not a member of the collection.
    return false;
  }

  // If the pointer to our internal array is shared by any other
  // SceneAnchorCollections, we have to copy the array now so we won't
  // inadvertently modify any of our brethren SceneAnchorCollection objects.

  if (_scene_anchors.get_ref_count() > 1) {
    SceneAnchors old_scene_anchors = _scene_anchors;
    _scene_anchors = SceneAnchors::empty_array(0);
    _scene_anchors.v() = old_scene_anchors.v();
  }

  _scene_anchors.erase(_scene_anchors.begin() + scene_anchor_index);
  return true;
}


void SceneAnchorCollection::
add_scene_anchors_from(const SceneAnchorCollection &other)
{
  int other_num_scene_anchors = other.get_num_scene_anchors();
  for (int i = 0; i < other_num_scene_anchors; i++) {
    add_scene_anchor(other.get_scene_anchor(i));
  }
}


void
SceneAnchorCollection::remove_scene_anchors_from(const SceneAnchorCollection &other)
{
  SceneAnchors new_scene_anchors;
  int num_scene_anchors = get_num_scene_anchors();
  for (int i = 0; i < num_scene_anchors; i++) {
    PT(SceneAnchor) scene_anchor = get_scene_anchor(i);
    if (!other.has_scene_anchor(scene_anchor)) {
      new_scene_anchors.push_back(scene_anchor);
    }
  }
  _scene_anchors = new_scene_anchors;
}


void SceneAnchorCollection::remove_duplicate_scene_anchors()
{
  SceneAnchors new_scene_anchors;

  int num_scene_anchors = get_num_scene_anchors();
  for (int i = 0; i < num_scene_anchors; i++) {
    PT(SceneAnchor) scene_anchor = get_scene_anchor(i);
    bool duplicated = false;

    for (int j = 0; j < i && !duplicated; j++) {
      duplicated = (scene_anchor == get_scene_anchor(j));
    }

    if (!duplicated) {
      new_scene_anchors.push_back(scene_anchor);
    }
  }

  _scene_anchors = new_scene_anchors;
}


bool
SceneAnchorCollection::has_scene_anchor(SceneAnchor *scene_anchor) const
{
  for (int i = 0; i < get_num_scene_anchors(); i++) {
    if (scene_anchor == get_scene_anchor(i)) {
      return true;
    }
  }
  return false;
}


void
SceneAnchorCollection::clear()
{
  _scene_anchors.clear();
}


void
SceneAnchorCollection::reserve(size_t num)
{
  _scene_anchors.reserve(num);
}


int
SceneAnchorCollection::get_num_scene_anchors() const
{
  return _scene_anchors.size();
}


SceneAnchor *
SceneAnchorCollection::get_scene_anchor(int index) const
{
  return _scene_anchors[index];
}


SceneAnchor *
SceneAnchorCollection::operator [](int index) const
{
  return _scene_anchors[index];
}


int
SceneAnchorCollection::size(void) const
{
  return _scene_anchors.size();
}

void
SceneAnchorCollection::operator +=(const SceneAnchorCollection &other) {
  add_scene_anchors_from(other);
}


SceneAnchorCollection
SceneAnchorCollection::operator +(const SceneAnchorCollection &other) const {
  SceneAnchorCollection a(*this);
  a += other;
  return a;
}


void
SceneAnchorCollection::append(SceneAnchor *scene_anchor) {
  add_scene_anchor(scene_anchor);
}


void
SceneAnchorCollection::extend(const SceneAnchorCollection &other) {
  operator +=(other);
}


SceneAnchorCollection::iterator
SceneAnchorCollection::begin() const
{
  return _scene_anchors.begin();
}


SceneAnchorCollection::iterator
SceneAnchorCollection::end() const
{
  return _scene_anchors.end();
}
