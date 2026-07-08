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

#include "objectName.h"
#include <algorithm>
#include <cctype>
#include <unordered_map>
#include <unordered_set>

static std::string
bayer_decode_name(const std::string &name)
{
  // Canonical SIMBAD greek abbreviations -> UTF-8 strings (always encoded as
  // UTF-8 byte sequences so the source file stays ASCII).
  static const std::unordered_map<std::string, std::string> greek_utf8_map = {
      {"ALF", "\xce\xb1"},  // α
      {"BET", "\xce\xb2"},  // β
      {"GAM", "\xce\xb3"},  // γ
      {"DEL", "\xce\xb4"},  // δ
      {"EPS", "\xce\xb5"},  // ε
      {"ZET", "\xce\xb6"},  // ζ
      {"ETA", "\xce\xb7"},  // η
      {"TET", "\xce\xb8"},  // θ
      {"IOT", "\xce\xb9"},  // ι
      {"KAP", "\xce\xba"},  // κ
      {"LAM", "\xce\xbb"},  // λ
      {"MU.", "\xce\xbc"},  // μ
      {"NU.", "\xce\xbd"},  // ν
      {"KSI", "\xce\xbe"},  // ξ
      {"OMI", "\xce\xbf"},  // ο
      {"PI.", "\xcf\x80"},  // π
      {"RHO", "\xcf\x81"},  // ρ
      {"SIG", "\xcf\x83"},  // σ
      {"TAU", "\xcf\x84"},  // τ
      {"UPS", "\xcf\x85"},  // υ
      {"PHI", "\xcf\x86"},  // φ
      {"KHI", "\xcf\x87"},  // χ
      {"PSI", "\xcf\x88"},  // ψ
      {"OME", "\xcf\x89"},  // ω
  };

  // Unicode superscript digits 0-9 as UTF-8 strings
  static const std::string superscripts[10] = {
      "\xe2\x81\xb0",  // ⁰
      "\xc2\xb9",      // ¹
      "\xc2\xb2",      // ²
      "\xc2\xb3",      // ³
      "\xe2\x81\xb4",  // ⁴
      "\xe2\x81\xb5",  // ⁵
      "\xe2\x81\xb6",  // ⁶
      "\xe2\x81\xb7",  // ⁷
      "\xe2\x81\xb8",  // ⁸
      "\xe2\x81\xb9",  // ⁹
  };

  if (name.empty()) return name;

  // Find the space that separates "GREEK[digits]" from "Constellation"
  size_t space_pos = name.find(' ');
  if (space_pos == std::string::npos) return name;

  // Split the prefix into greek letters and optional trailing digits
  std::string prefix = name.substr(0, space_pos);
  std::string greek_part;
  std::string number_part;
  for (size_t i = 0; i < prefix.size(); ++i) {
    if (std::isdigit((unsigned char)prefix[i])) {
      greek_part  = prefix.substr(0, i);
      number_part = prefix.substr(i);
      break;
    }
  }
  if (number_part.empty()) {
    greek_part = prefix;
  }

  // Uppercase the greek part for the map lookup
  std::string greek_upper = greek_part;
  for (char &c : greek_upper) {
    c = std::toupper((unsigned char)c);
  }

  auto letter = greek_utf8_map.find(greek_upper);
  if (letter == greek_utf8_map.end()) {
    // Not a Bayer name
    return name;
  }

  // Build the result: replace digits with superscripts first (higher index),
  // then replace the greek letters at position 0.
  std::string result = name;

  if (!number_part.empty()) {
    std::string superscript_str;
    for (char c : number_part) {
      int digit = c - '0';
      if (digit >= 0 && digit <= 9) {
        superscript_str += superscripts[digit];
      }
    }
    // number_part starts right after greek_part in the original string
    result.replace(greek_part.length(), number_part.length(), superscript_str);
  }

  // Replace greek abbreviation at position 0
  result.replace(0, greek_part.length(), letter->second);

  return result;
}

// CatalogRegistry implementation
CatalogRegistry *CatalogRegistry::_instance = nullptr;

CatalogRegistry::CatalogRegistry() :
    _next_id(1)
{
}

CatalogRegistry&
CatalogRegistry::get_instance()
{
  if (_instance == nullptr) {
    _instance = new CatalogRegistry();
  }
  return *_instance;
}

uint8_t
CatalogRegistry::register_catalog(const std::string &prefix, const std::string &description)
{
  // Check if already registered
  auto it = _catalogs.find(prefix);
  if (it != _catalogs.end()) {
    return it->second.id;
  }

  // Register new catalog with auto-assigned ID
  uint8_t catalog_id = _next_id++;
  CatalogInfo info;
  info.id = catalog_id;
  info.prefix = prefix;
  info.description = description;

  _catalogs[prefix] = info;
  _id_to_prefix[catalog_id] = prefix;

  return catalog_id;
}

uint8_t
CatalogRegistry::get_id(const std::string &prefix) const
{
  auto it = _catalogs.find(prefix);
  if (it != _catalogs.end()) {
    return it->second.id;
  }
  return 0;  // Vernacular
}

unsigned int
CatalogRegistry::get_num_prefixes() const
{
  return _catalogs.size();
}

std::string
CatalogRegistry::get_prefix(uint8_t catalog_id) const
{
  auto it = _id_to_prefix.find(catalog_id);
  if (it != _id_to_prefix.end()) {
    return it->second;
  }
  return "";
}

std::string
CatalogRegistry::get_description(const std::string &prefix) const
{
  auto it = _catalogs.find(prefix);
  if (it != _catalogs.end()) {
    return it->second.description;
  }
  return "";
}

bool
CatalogRegistry::has_catalog(const std::string &prefix) const
{
  return _catalogs.find(prefix) != _catalogs.end();
}

pvector<std::string>
CatalogRegistry::get_all_prefixes() const
{
  pvector<std::string> result;
  for (const auto &pair : _catalogs) {
    result.push_back(pair.first);
  }
  return result;
}

void
CatalogRegistry::clear()
{
  _catalogs.clear();
  _id_to_prefix.clear();
  _next_id = 1;
}

// ObjectName implementation
ObjectName
ObjectName::make_vernacular(const std::string &name)
{
  return ObjectName(name, ObjectName::NameType::NT_vernacular, 0, true);
}

ObjectName
ObjectName::make_flamsteed(const std::string &name)
{
  return ObjectName(name, ObjectName::NameType::NT_flamsteed, 0, false);
}

ObjectName
ObjectName::make_bayer(const std::string &name)
{
  return ObjectName(name, ObjectName::NameType::NT_bayer, 0, false);
}

ObjectName
ObjectName::make_catalog(uint8_t catalog_id, const std::string &id)
{
  return ObjectName(id, ObjectName::NameType::NT_catalog, catalog_id, false);
}

ObjectName
ObjectName::make_minor_planet(const std::string &name)
{
  return ObjectName(name, ObjectName::NameType::NT_minor_planet, 0, true);
}

std::string
ObjectName::get_full_name() const
{
  if (type == ObjectName::NameType::NT_catalog && catalog_id != 0) {
    std::string prefix = CatalogRegistry::get_instance().get_prefix(catalog_id);
    if (!prefix.empty()) {
      return prefix + " " + value;
    }
  }
  return value;
}

std::string
ObjectName::decode() const
{
  if (type == ObjectName::NameType::NT_bayer) {
    return bayer_decode_name(get_full_name());
  }
  return get_full_name();
}

// ObjectNames implementation
ObjectNames::ObjectNames()
{
}

void
ObjectNames::add_name(const ObjectName &name)
{
  _names.push_back(name);
  _originals.push_back("");  // Keep parallel vectors aligned
}

void
ObjectNames::add_name(const ObjectName &name, const std::string &original)
{
  _names.push_back(name);
  _originals.push_back(original);
}

unsigned int
ObjectNames::get_num_names() const
{
  return _names.size();
}

std::string
ObjectNames::get_name_at(unsigned int index) const
{
  // Return the name at the specified index
  return index >= _names.size() ? "" : _names[index].get_full_name();
}

std::string
ObjectNames::get_decoded_name_at(unsigned int index) const
{
  // Return the name at the specified index
  return index >= _names.size() ? "" : _names[index].decode();
}

const ObjectName&
ObjectNames::get_name_entry(unsigned int index) const
{
  return _names[index];
}

std::string
ObjectNames::get_c_name() const
{
  // Return the first name untranslated (original before translation)
  if (!_originals.empty() && !_originals[0].empty()) {
    return _originals[0];
  }
  // Otherwise return the first name's full name
  return _names.empty() ? "" : _names[0].get_full_name();
}

std::string
ObjectNames::get_name() const
{
  // Return the primary name
  return _names.empty() ? "" : _names[0].get_full_name();
}

pvector<std::string>
ObjectNames::get_all_names() const
{
  pvector<std::string> result;
  for (const auto &name : _names) {
    result.push_back(name.get_full_name());
  }
  return result;
}

pvector<std::string>
ObjectNames::get_decoded_names() const
{
  pvector<std::string> result;
  for (const auto &name : _names) {
    result.push_back(name.decode());
  }
  return result;
}

pvector<std::string>
ObjectNames::get_source_names() const
{
  pvector<std::string> result;
  for (size_t i = 0; i < _names.size(); ++i) {
    const auto &name = _names[i];
    // Include non-translatable names
    if (!name.translatable) {
      result.push_back(name.get_full_name());
    }
    // Include originals for translated entries
    else if (i < _originals.size() && !_originals[i].empty()) {
      result.push_back(_originals[i]);
    }
  }
  return result;
}

pvector<std::string>
ObjectNames::get_catalog_names(uint8_t catalog_id) const
{
  pvector<std::string> result;
  for (const auto &name : _names) {
    if (name.type == ObjectName::NameType::NT_catalog && name.catalog_id == catalog_id) {
      result.push_back(name.get_full_name());
    }
  }
  return result;
}

bool
ObjectNames::has_catalog_entry(uint8_t catalog_id) const
{
  for (const auto &name : _names) {
    if (name.type == ObjectName::NameType::NT_catalog && name.catalog_id == catalog_id) {
      return true;
    }
  }
  return false;
}

std::string
ObjectNames::get_catalog_id(uint8_t catalog_id) const
{
  for (const auto &name : _names) {
    if (name.type == ObjectName::NameType::NT_catalog && name.catalog_id == catalog_id) {
      return name.value;
    }
  }
  return "";
}

void
ObjectNames::set_translated(unsigned int index, const std::string &translated)
{
  if (index >= _names.size()) {
    return;  // Index out of bounds
  }

  // Ensure _originals is sized properly
  if (index >= _originals.size()) {
    _originals.resize(_names.size());
  }
  // Store original if not already stored
  if (_originals[index].empty()) {
    _originals[index] = _names[index].value;
  }
  _names[index].value = translated;
}

ObjectName
ObjectNames::parse_name(const std::string &name, bool reflective)
{
  if (name.empty()) {
    return ObjectName::make_vernacular(name);
  }

  // SIMBAD Bayer greek abbreviations
  static const std::unordered_set<std::string> bayer_prefixes = {
      "ALF", "BET", "GAM", "DEL", "EPS", "ZET", "ETA", "TET",
      "IOT", "KAP", "LAM", "MU.", "NU.", "KSI", "OMI", "PI.",
      "RHO", "SIG", "TAU", "UPS", "PHI", "KHI", "PSI", "OME",
      // Canonical aliases
      "ALP", "THE", "MU", "NU", "XI", "XI.", "PI", "CHI"
  };

  // 3-letter constellation abbreviations (subset for pattern matching)
  static const std::unordered_set<std::string> constellations = {
      "Aql", "And", "Ara", "Lib", "Cet", "Ari", "Pyx", "Boo", "Cae",
      "Cha", "Cnc", "Cap", "Car", "Cas", "Cen", "Cep", "Com", "CVn",
      "Aur", "Col", "Cir", "Crv", "Crt", "CrA", "CrB", "Cru", "Cyg",
      "Del", "Dor", "Dra", "Sct", "Eri", "Sge", "For", "Gem", "Cam",
      "CMa", "UMa", "Gru", "Her", "Hor", "Hya", "Hyi", "Ind", "Lac",
      "Mon", "Lep", "Leo", "Lup", "Lyn", "Lyr", "Ant", "Mic", "Mus",
      "Oct", "Aps", "Oph", "Ori", "Pav", "Peg", "Pic", "Per", "Equ",
      "CMi", "LMi", "Vul", "UMi", "Phe", "PsA", "Vol", "Psc", "Pup",
      "Nor", "Ret", "Sgr", "Sco", "Scl", "Ser", "Sex", "Men", "Tau",
      "Tel", "Tuc", "Tri", "TrA", "Aqr", "Vir", "Vel"
  };

  // Check for catalog prefix (e.g., "HIP 32349")
  size_t space_pos = name.find(' ');
  if (space_pos != std::string::npos && space_pos > 0) {
    std::string prefix = name.substr(0, space_pos);

    // Convert to uppercase for catalog lookup
    std::string upper_prefix = prefix;
    std::transform(upper_prefix.begin(), upper_prefix.end(), upper_prefix.begin(), ::toupper);

    // Use the registry to look up the catalog
    CatalogRegistry &registry = CatalogRegistry::get_instance();
    uint8_t cat_id = registry.get_id(upper_prefix);
    if (cat_id != 0) {
      std::string id = name.substr(space_pos + 1);
      return ObjectName::make_catalog(cat_id, id);
    }

    // Check for Bayer designation (e.g., "ALF CMa", "BET2 Ori")
    // Extract just the greek letters (may have numbers attached)
    std::string bayer_prefix = upper_prefix;
    for (size_t i = 0; i < upper_prefix.length(); ++i) {
      if (std::isdigit(upper_prefix[i])) {
        bayer_prefix = upper_prefix.substr(0, i);
        break;
      }
    }

    if (bayer_prefixes.find(bayer_prefix) != bayer_prefixes.end()) {
      std::string rest = name.substr(space_pos + 1);

      // May have optional number followed by constellation
      size_t rest_space = rest.find(' ');
      if (rest_space != std::string::npos) {
        std::string maybe_constellation = rest.substr(rest_space + 1);
        if (constellations.find(maybe_constellation) != constellations.end()) {
          return ObjectName::make_bayer(name);
        }
      } else {
        // Just prefix + constellation
        if (constellations.find(rest) != constellations.end()) {
          return ObjectName::make_bayer(name);
        }
      }
    }

    // "NUMBER Word" patterns: Flamsteed (stars) vs minor-planet (reflective bodies)
    bool is_number = true;
    for (char c : prefix) {
      if (!std::isdigit(c)) {
        is_number = false;
        break;
      }
    }

    if (is_number) {
      std::string rest = name.substr(space_pos + 1);

      // Check that rest is entirely alphabetic
      bool is_word = true;
      for (char c : rest) {
        if (!std::isalpha(c)) {
          is_word = false;
          break;
        }
      }

      if (is_word) {
        if (reflective) {
          // Reflective bodies (minor planets, asteroids): any alphabetic name
          // after the number is a minor-planet designation.
          return ObjectName::make_minor_planet(name);
        } else {
          // Stars / stellar systems: a 2-4 letter word is a constellation
          // abbreviation → Flamsteed designation.
          if (rest.length() >= 2 && rest.length() <= 4) {
            return ObjectName::make_flamsteed(name);
          }
        }
      }
    }
  }

  // Default to vernacular name (translatable)
  return ObjectName::make_vernacular(name);
}
