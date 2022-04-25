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


#include "anchorCollection.h"
#include "anchor.h"


AnchorCollection::AnchorCollection() {
}


AnchorCollection::AnchorCollection(const AnchorCollection &copy) :
  _anchors(copy._anchors)
{
}


void
AnchorCollection::operator = (const AnchorCollection &copy)
{
  _anchors = copy._anchors;
}


AnchorCollection::~AnchorCollection()
{
}


void
AnchorCollection::add_anchor(AnchorBase *anchor)
{
  // If the pointer to our internal array is shared by any other
  // AnchorCollections, we have to copy the array now so we won't
  // inadvertently modify any of our brethren AnchorCollection objects.

  if (_anchors.get_ref_count() > 1) {
    AnchorBases old_anchors = _anchors;
    _anchors = AnchorBases::empty_array(0);
    _anchors.v() = old_anchors.v();
  }

  _anchors.push_back(anchor);
}


bool
AnchorCollection::remove_anchor(AnchorBase *anchor)
{
  int anchor_index = -1;
  for (int i = 0; anchor_index == -1 && i < (int)_anchors.size(); i++) {
    if (_anchors[i] == anchor) {
      anchor_index = i;
    }
  }

  if (anchor_index == -1) {
    // The indicated anchor was not a member of the collection.
    return false;
  }

  // If the pointer to our internal array is shared by any other
  // AnchorCollections, we have to copy the array now so we won't
  // inadvertently modify any of our brethren AnchorCollection objects.

  if (_anchors.get_ref_count() > 1) {
    AnchorBases old_anchors = _anchors;
    _anchors = AnchorBases::empty_array(0);
    _anchors.v() = old_anchors.v();
  }

  _anchors.erase(_anchors.begin() + anchor_index);
  return true;
}


void AnchorCollection::
add_anchors_from(const AnchorCollection &other)
{
  int other_num_anchors = other.get_num_anchors();
  for (int i = 0; i < other_num_anchors; i++) {
    add_anchor(other.get_anchor(i));
  }
}


void
AnchorCollection::remove_anchors_from(const AnchorCollection &other)
{
  AnchorBases new_anchors;
  int num_anchors = get_num_anchors();
  for (int i = 0; i < num_anchors; i++) {
    PT(AnchorBase) anchor = get_anchor(i);
    if (!other.has_anchor(anchor)) {
      new_anchors.push_back(anchor);
    }
  }
  _anchors = new_anchors;
}


void AnchorCollection::remove_duplicate_anchors()
{
  AnchorBases new_anchors;

  int num_anchors = get_num_anchors();
  for (int i = 0; i < num_anchors; i++) {
    PT(AnchorBase) anchor = get_anchor(i);
    bool duplicated = false;

    for (int j = 0; j < i && !duplicated; j++) {
      duplicated = (anchor == get_anchor(j));
    }

    if (!duplicated) {
      new_anchors.push_back(anchor);
    }
  }

  _anchors = new_anchors;
}


bool
AnchorCollection::has_anchor(AnchorBase *anchor) const
{
  for (int i = 0; i < get_num_anchors(); i++) {
    if (anchor == get_anchor(i)) {
      return true;
    }
  }
  return false;
}


void
AnchorCollection::clear()
{
  _anchors.clear();
}


void
AnchorCollection::reserve(size_t num)
{
  _anchors.reserve(num);
}


int
AnchorCollection::get_num_anchors() const
{
  return _anchors.size();
}


AnchorBase *
AnchorCollection::get_anchor(int index) const
{
  return _anchors[index];
}


AnchorBase *
AnchorCollection::operator [](int index) const
{
  return _anchors[index];
}


int
AnchorCollection::size(void) const
{
  return _anchors.size();
}

void
AnchorCollection::operator +=(const AnchorCollection &other) {
  add_anchors_from(other);
}


AnchorCollection
AnchorCollection::operator +(const AnchorCollection &other) const {
  AnchorCollection a(*this);
  a += other;
  return a;
}


void
AnchorCollection::append(AnchorBase *anchor) {
  add_anchor(anchor);
}


void
AnchorCollection::extend(const AnchorCollection &other) {
  operator +=(other);
}


AnchorCollection::iterator
AnchorCollection::begin() const
{
  return _anchors.begin();
}


AnchorCollection::iterator
AnchorCollection::end() const
{
  return _anchors.end();
}
