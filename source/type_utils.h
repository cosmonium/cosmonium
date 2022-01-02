/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2021 Laurent Deru.
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

#ifndef TYPE_UTILS_H
#define TYPE_UTILS_H

#define MAKE_TYPE(type_name, parent_type) \
public: \
  static TypeHandle get_class_type() { \
    return _type_handle; \
  } \
  static void init_type() { \
    parent_type::init_type(); \
    register_type(_type_handle, (type_name), parent_type::get_class_type()); \
  } \
  virtual TypeHandle get_type() const { \
    return get_class_type(); \
  } \
  virtual TypeHandle force_init_type() { \
    init_type(); \
    return get_class_type(); \
  } \
private: \
  static TypeHandle _type_handle; \

#define MAKE_TYPE_2(type_name, parent1_type, parent2_type) \
public: \
  static TypeHandle get_class_type() { \
    return _type_handle; \
  } \
  static void init_type() { \
    parent1_type::init_type(); \
    parent2_type::init_type(); \
    register_type(_type_handle, (type_name), parent1_type::get_class_type(), parent2_type::get_class_type()); \
  } \
  virtual TypeHandle get_type() const { \
    return get_class_type(); \
  } \
  virtual TypeHandle force_init_type() { \
    init_type(); \
    return get_class_type(); \
  } \
private: \
  static TypeHandle _type_handle; \

#endif
