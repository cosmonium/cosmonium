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

#include "octreeNode.h"
#include "anchors.h"
#include "anchorTraverser.h"

#include "iostream"
#include "math.h"

int OctreeNode::max_level = 200;
int OctreeNode::max_leaves = 75;
double OctreeNode::child_threshold = 0.5; //1.5 Correspond roughly to 1/4 less luminosity

OctreeNode::OctreeNode(int level, OctreeNode *parent, LPoint3d center, double width, double threshold, int index) :
  AnchorTreeBase(~0),
  level(level),
  center(center),
  width(width),
  threshold(threshold),
  index(index),
  has_children(false),
  children()
{
    radius = width / 2.0 * sqrt(3);
    max_magnitude = 1000.0;
}

OctreeNode::~OctreeNode(void)
{
  for(auto child : children) {
    delete child;
  }
}

void
OctreeNode::set_rebuild_needed(void)
{
    rebuild_needed = true;
    if (parent != 0) {
        parent->set_rebuild_needed();
    }
}

void
OctreeNode::rebuild(void)
{
    for (auto child : children) {
        if (child != 0 && child->rebuild_needed) {
            child->rebuild();
        }
    }
    rebuild_needed = false;
}

size_t
OctreeNode::get_num_children(void) const
{
  size_t nb_children = 0;
  for (auto child : children) {
    if (child != 0) {
      nb_children++;
    }
  }
  return nb_children;
}

size_t
OctreeNode::get_num_leaves(void) const
{
  return leaves.size();
}

void
OctreeNode::traverse(AnchorTraverser &traverser)
{
  traverser.traverse_octree_node(this, leaves);
  for(auto child : children) {
    if (child != 0 && traverser.enter_octree_node(child)) {
      child->traverse(traverser);
    }
  }
}

void
OctreeNode::add(StellarAnchor *leaf)
{
  _add(leaf, leaf->get_absolute_reference_point(), leaf->get_absolute_magnitude());
}

void
OctreeNode::add_in_child(StellarAnchor *leaf, LPoint3d const &position, double magnitude)
{
    int index = 0;
    if (position[0] >= center[0]) index |= 1;
    if (position[1] >= center[1]) index |= 2;
    if (position[2] >= center[2]) index |= 4;
    if (children[index] == 0) {
        double child_offset = width / 4.0;
        LPoint3d child_center = center;
        if ((index & 1) != 0) {
            child_center[0] += child_offset;
        } else {
            child_center[0] -= child_offset;
        }
        if ((index & 2) != 0) {
            child_center[1] += child_offset;
        } else {
            child_center[1] -= child_offset;
        }
        if ((index & 4) != 0) {
            child_center[2] += child_offset;
        } else {
            child_center[2] -= child_offset;
        }
        OctreeNode *child = new OctreeNode(level + 1, this, child_center, width / 2.0, threshold + child_threshold, index);
        children[index] = child;
    }
    children[index]->_add(leaf, position, magnitude);
}

void
OctreeNode::_add(StellarAnchor *leaf, LPoint3d const &position, double magnitude)
{
    if (magnitude < max_magnitude) {
        max_magnitude = magnitude;
    }
    if (!has_children || magnitude < threshold) {
        leaves.push_back(leaf);
        leaf->parent = this;
    } else {
        add_in_child(leaf, position, magnitude);
    }
    if (level < max_level && leaves.size() > max_leaves && !has_children) {
        split();
    }
}

void
OctreeNode::split(void)
{
    std::vector<PT(StellarAnchor)> new_leaves;
    for (const auto leaf : leaves) {
        const auto position = leaf->get_absolute_reference_point();
        if (leaf->get_absolute_magnitude() < threshold || (center - position).length() < leaf->_extend) {
            new_leaves.push_back(leaf);
        } else {
            add_in_child(leaf, position, leaf->get_absolute_magnitude());
        }
    }
    leaves = new_leaves;
    has_children = true;
}

OctreeNode *
OctreeNode::get_child(int index)
{
  if (has_children && index >= 0 && index < 8) {
    return children[index];
  } else {
    return 0;
  }
}

StellarAnchor *
OctreeNode::get_leaf(int index) const
{
  return leaves[index];
}

void
OctreeNode::output(std::ostream &out) const
{
    out << "octree, leaves: " << leaves.size();
}

void
OctreeNode::write(std::ostream &out, int indent_level) const
{
  indent(out, indent_level) << *this << "\n";
}
