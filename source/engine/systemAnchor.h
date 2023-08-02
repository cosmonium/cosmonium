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

#ifndef SYSTEMANCHOR_H
#define SYSTEMANCHOR_H

#include "stellarAnchor.h"

class SystemAnchor : public StellarAnchor
{
PUBLISHED:
  SystemAnchor(PyObject *ref_object,
      OrbitBase *orbit,
      RotationBase *rotation,
      LColor point_color);

private:
  SystemAnchor(SystemAnchor const &other);
  void operator = (const SystemAnchor &other);

PUBLISHED:
  virtual void traverse(AnchorTraverser &visitor);
  virtual void update_luminosity(StellarAnchor *star = 0);
  virtual void rebuild(void);

  void add_child(AnchorBase *child);
  void remove_child(AnchorBase *child);

  void set_primary(StellarAnchor *primary);

public:
  std::vector<PT(AnchorBase)> children;
  PT(StellarAnchor) primary;

  MAKE_TYPE("SystemAnchor", StellarAnchor);
};

#endif
