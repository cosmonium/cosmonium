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
#include <unordered_map>
#include <string>

class SystemAnchor : public StellarAnchor
{
public:
  SystemAnchor(PyObject *ref_object,
      OrbitBase *orbit,
      RotationBase *rotation,
      LColor point_color,
      const pvector<std::string> names,
      const pvector<std::string> source_names);

PUBLISHED:
  SystemAnchor(PyObject *ref_object,
      OrbitBase *orbit,
      RotationBase *rotation,
      LColor point_color,
      PyObject *names = nullptr,
      PyObject *source_names = nullptr);

private:
  SystemAnchor(SystemAnchor const &other);
  void operator = (const SystemAnchor &other);

PUBLISHED:
  virtual void traverse(AnchorTraverser &visitor);
  virtual void update_luminosity(StellarAnchor *star = 0);
  virtual void rebuild(void);
  virtual bool is_system(void) const;
  virtual std::string get_fullname(const std::string &separator = "/") const;

  virtual SystemAnchor *get_or_create_system(void);

  void add_child(AnchorBase *child);
  void remove_child(AnchorBase *child);

  unsigned int get_num_children(void) const;
  AnchorBase *get_child_at(unsigned int index) const;
  MAKE_SEQ(get_children, get_num_children, get_child_at);

  StellarAnchor *get_primary(void) const;
  void set_primary(StellarAnchor *primary);
  MAKE_PROPERTY(primary, get_primary, set_primary);

  void set_star_system(bool star_system);
  bool get_star_system(void) const;
  MAKE_PROPERTY(star_system, get_star_system, set_star_system);

  // Child lookup methods
  AnchorBase *find_child_by_name(const std::string &name) const;
  AnchorBase *find_nth_child(int index) const;
  AnchorBase *find_by_path(const std::string &path, const std::string &separator = "/") const;
  AnchorBase *find_by_path(PyObject *path, const std::string &separator = "/") const;

public:
  AnchorBase *find_by_path(const std::vector<std::string> &parts) const;

public:
  std::vector<PT(AnchorBase)> children;
  PT(StellarAnchor) _primary;
  bool _star_system;

  // Fast name-to-anchor map (keys are upper-cased primary names)
  std::unordered_map<std::string, PT(AnchorBase)> children_map;

  MAKE_TYPE("SystemAnchor", StellarAnchor);
};

#endif
