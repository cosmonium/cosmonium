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


#ifndef ANCHOR_COLLECTION_H
#define ANCHOR_COLLECTION_H


#include "pandabase.h"
#include "pointerToArray.h"


class AnchorBase;


class AnchorCollection
{
PUBLISHED:
  AnchorCollection();
  AnchorCollection(const AnchorCollection &copy);
  void operator =(const AnchorCollection &copy);
  ~AnchorCollection(void);

  void add_anchor(AnchorBase *anchor);
  bool remove_anchor(AnchorBase *anchor);
  void add_anchors_from(const AnchorCollection &other);
  void remove_anchors_from(const AnchorCollection &other);
  void remove_duplicate_anchors(void);
  bool has_anchor(AnchorBase *anchor) const;
  void clear(void);
  void reserve(size_t num);

  int get_num_anchors() const;
  AnchorBase *get_anchor(int index) const;
  AnchorBase *operator [](int index) const;
  int size(void) const;
  void operator +=(const AnchorCollection &other);
  AnchorCollection operator +(const AnchorCollection &other) const;

  void append(AnchorBase *anchor);
  void extend(const AnchorCollection &other);

public:
  typedef typename pvector<PT(AnchorBase)>::iterator iterator;
  iterator begin() const;
  iterator end() const;

private:
  typedef PTA(PT(AnchorBase)) AnchorBases;
  AnchorBases _anchors;
};

#endif
