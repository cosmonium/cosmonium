/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2026 Laurent Deru.
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

#ifndef OBJECTNAME_H
#define OBJECTNAME_H

#include "pandabase.h"
#include "pvector.h"
#include "vector_string.h"
#include <string>
#include <cstdint>
#include <map>

// Dynamic registry of known astronomical catalogs
class CatalogRegistry
{
PUBLISHED:
    CatalogRegistry();

  // Register a catalog and get its ID (auto-assigned)
  uint8_t
  register_catalog(const std::string &prefix, const std::string &description = "");

  // Get ID for a catalog prefix (returns 0 if not found)
  uint8_t
  get_id(const std::string &prefix) const;

  // Get prefix for a catalog ID (returns empty string if not found)
  std::string
  get_prefix(uint8_t catalog_id) const;

  // Get the number of registered catalogs
  unsigned int
  get_num_prefixes() const;

  MAKE_SEQ(get_all_prefixes, get_num_prefixes, get_prefix);

  // Get description for a catalog prefix
  std::string
  get_description(const std::string &prefix) const;

  // Check if a catalog is registered
  bool
  has_catalog(const std::string &prefix) const;

  // Clear all catalogs
  void
  clear();

  // Get the global singleton instance
  static CatalogRegistry&
  get_instance();

public:
  // Get all registered prefixes
  vector_string
  get_all_prefixes() const;

private:
  struct CatalogInfo
  {
    uint8_t id;
    std::string prefix;
    std::string description;
  };

  std::map<std::string, CatalogInfo> _catalogs;  // prefix -> info
  std::map<uint8_t, std::string> _id_to_prefix;  // id -> prefix
  uint8_t _next_id;

  static CatalogRegistry *_instance;
};

// Represents a single name with type information
struct ObjectName
{
PUBLISHED:
  // Enum representing different types of names
  enum NameType
  {
    NT_vernacular = 0,
    NT_bayer = 1,
    NT_flamsteed = 2,
    NT_catalog = 3,
    NT_variable_star = 4,
    NT_custom = 5,
    NT_minor_planet = 6
  };

  ObjectName(const std::string &val, NameType t, uint8_t cat_id, bool trans)
  :
      value(val), type(t), catalog_id(cat_id), translatable(trans)
  {
  }

  // Create an ObjectName for a vernacular name.
  static ObjectName
  make_vernacular(const std::string &name);

  /// Create an ObjectName for a Flamsteed designation.
  static ObjectName
  make_flamsteed(const std::string &name);

  /// Create an ObjectName for a Bayer designation.
  static ObjectName
  make_bayer(const std::string &name);

  /// Create an ObjectName for a catalog entry.
  static ObjectName
  make_catalog(uint8_t catalog_id, const std::string &id);

  /// Create an ObjectName for a minor planet / asteroid designation.
  static ObjectName
  make_minor_planet(const std::string &name);

  /// Return the full name string including catalog prefix if applicable.
  std::string
  get_full_name() const;

  /// Return the display-ready (decoded) name.
  std::string
  decode() const;

PUBLISHED:
  std::string value;
  NameType type;
  uint8_t catalog_id;
  bool translatable;
};

// Manages a collection of object names
class ObjectNames
{
PUBLISHED:
  /// Default constructor.
  ObjectNames();

  /// Add a name to the collection.
  void
  add_name(const ObjectName &name);

  /// Add a name with its original form for translation purposes.
  void
  add_name(const ObjectName &name, const std::string &original);

  /// Return the number of names in the collection.
  unsigned int
  get_num_names() const;

  /// Return the name entry at the specified index.
  const ObjectName&
  get_name_entry(unsigned int index) const;

  /// Return the name at the specified index.
  std::string
  get_name_at(unsigned int index) const;

  /// Sequence of names for Python exposure.
  MAKE_SEQ(get_all_names, get_num_names, get_name_at);

  /// Return the decoded name at the specified index.
  std::string
  get_decoded_name_at(unsigned int index) const;

  /// Sequence of decoded names for Python exposure.
  MAKE_SEQ(get_decoded_names, get_num_names, get_decoded_name_at);

  /// Return the untranslated primary name.
  std::string
  get_c_name() const;

  /// Return the primary name of the object.
  std::string
  get_name() const;

  /// Check if there is an entry for the specified catalog.
  bool
  has_catalog_entry(uint8_t catalog_id) const;

  /// Return the catalog ID string for the specified catalog.
  std::string
  get_catalog_id(uint8_t catalog_id) const;

  /// Set the translated name for the entry at the specified index.
  void
  set_translated(unsigned int index, const std::string &translated);

  /// Parse a string to create an ObjectName.
  /// When reflective is true the minor-planet designation pattern is used
  /// instead of Flamsteed detection.
  static ObjectName
  parse_name(const std::string &name, bool reflective);

public:
  /// Return all names as a vector of strings.
  vector_string
  get_all_names() const;

  /// Return all names decoded for display, applying any type-specific
  /// transformations.
  vector_string
  get_decoded_names() const;

  /// Return the source names (original forms).
  vector_string
  get_source_names() const;

  /// Return names from a specific catalog.
  vector_string
  get_catalog_names(uint8_t catalog_id) const;


private:
  pvector<ObjectName> _names;
  vector_string _originals;  // Sparse: only for translated entries
};

#endif
