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

#ifndef PATCH_H
#define PATCH_H

#include "pandabase.h"
#include "luse.h"
#include "referenceCount.h"
#include "boundingBox.h"
#include <vector>
#include "py_panda.h"

class CullingFrustumBase;
class QuadTreeNode;

class LodControl : public ReferenceCount
{
PUBLISHED:
    virtual ~LodControl(void);

    virtual unsigned int get_density_for(unsigned int lod) = 0;

    virtual void set_texture_size(unsigned int texture_size);

    virtual bool should_split(QuadTreeNode *patch, double apparent_patch_size, double distance) = 0;

    virtual bool should_merge(QuadTreeNode *patch, double apparent_patch_size, double distance) = 0;

    virtual bool should_instanciate(QuadTreeNode *patch, double apparent_patch_size, double distance);

    virtual bool should_remove(QuadTreeNode *patch, double apparent_patch_size, double distance);
};

class TextureLodControl : public LodControl
{
PUBLISHED:
    TextureLodControl(unsigned int min_density, unsigned int density, unsigned int max_lod=100);

    void set_texture_size(unsigned int texture_size);

    virtual unsigned int get_density_for(unsigned int lod);

    virtual bool should_split(QuadTreeNode *patch, double apparent_patch_size, double distance);

    virtual bool should_merge(QuadTreeNode *patch, double apparent_patch_size, double distance);

protected:
    unsigned int min_density;
    unsigned int density;
    unsigned int max_lod;
    unsigned int texture_size;
};

class VertexSizeLodControl : public LodControl
{
PUBLISHED:
    VertexSizeLodControl(unsigned int max_vertex_size, unsigned int density, unsigned int max_lod=100);

    virtual unsigned int get_density_for(unsigned int lod);

    virtual bool should_split(QuadTreeNode *patch, double apparent_patch_size, double distance);

    virtual bool should_merge(QuadTreeNode *patch, double apparent_patch_size, double distance);

protected:
    unsigned int density;
    unsigned int max_lod;
    unsigned int max_vertex_size;
};


class TextureOrVertexSizeLodControl : public TextureLodControl
{
PUBLISHED:
    TextureOrVertexSizeLodControl(unsigned int max_vertex_size, unsigned int min_density, unsigned int density, unsigned int max_lod=100);

    virtual bool should_split(QuadTreeNode *patch, double apparent_patch_size, double distance);

    virtual bool should_merge(QuadTreeNode *patch, double apparent_patch_size, double distance);

protected:
    unsigned int max_vertex_size;
};

class VertexSizeMaxDistanceLodControl : public VertexSizeLodControl
{
PUBLISHED:
    VertexSizeMaxDistanceLodControl(double max_distance, unsigned int max_vertex_size, unsigned int density, unsigned int max_lod=100);

    virtual bool should_instanciate(QuadTreeNode *patch, double apparent_patch_size, double distance);

    virtual bool should_remove(QuadTreeNode *patch, double apparent_patch_size, double distance);

protected:
    double max_distance;
};

class QuadTreeNodeCollection
{
PUBLISHED:
    QuadTreeNodeCollection(void);
    QuadTreeNodeCollection(const QuadTreeNodeCollection &copy);
    void operator =(const QuadTreeNodeCollection &copy);
    virtual ~QuadTreeNodeCollection(void);

    void add(QuadTreeNode *node);

    INLINE size_t size(void) const { return collection.size(); }

    INLINE QuadTreeNode *operator[](size_t index) const { return collection[index]; }

    int get_num_nodes() const { return collection.size(); }

    QuadTreeNode *get_node(size_t index) const { return collection[index]; }

    MAKE_SEQ(get_nodes, get_num_nodes, get_node);

    void sort_by_distance(void);

protected:
    PTA(PT(QuadTreeNode)) collection;
};

class LodResult : public ReferenceCount
{
PUBLISHED:
    LodResult(void);

    virtual ~LodResult(void);

    void add_to_split(QuadTreeNode *patch);

    void add_to_merge(QuadTreeNode *patch);

    void add_to_show(QuadTreeNode *patch);

    void add_to_remove(QuadTreeNode *patch);

    void check_max_lod(QuadTreeNode *patch);

    void sort_by_distance(void);

    QuadTreeNodeCollection to_split;
    QuadTreeNodeCollection to_merge;
    QuadTreeNodeCollection to_show;
    QuadTreeNodeCollection to_remove;
    int max_lod;
};

class QuadTreeNode : public ReferenceCount
{
PUBLISHED:
  QuadTreeNode(PyObject *patch, int lod, int density, LPoint3d centre, double length, LVector3d normal, double offset, BoundingBox *bounds);
  virtual ~QuadTreeNode(void);

  void set_shown(bool shown);

  void set_instance_ready(bool instance_ready);

  void add_child(QuadTreeNode *child);

  void remove_children(void);

  bool can_merge_children(void);

  bool in_patch(LPoint2d local);

  void check_visibility(CullingFrustumBase *culling_frustum, LPoint2d local, LPoint3d model_camera_pos, LVector3d model_camera_vector, double altitude, double pixel_size);

  bool are_children_visibles(CullingFrustumBase *culling_frustum);

  void check_lod(LodResult *lod_result, CullingFrustumBase *culling_frustum, LPoint2d local, LPoint3d model_camera_pos, LVector3d model_camera_vector, double altitude, double pixel_size, LodControl *lod_control);

  INLINE PyObject *get_patch(void);

  INLINE BoundingBox *get_bounds(void);

  MAKE_PROPERTY(patch, get_patch);
  MAKE_PROPERTY(bounds, get_bounds);

PUBLISHED:
  int lod;
  int density;
  LPoint3d centre;
  double length;
  LVector3d normal;
  double offset;
  bool shown;
  bool visible;
  double distance;
  bool instance_ready;
  double apparent_size;
  bool patch_in_view;

public:
  PyObject *patch;
  PT(BoundingBox) bounds;
  std::vector<PT(QuadTreeNode)> children;
  std::vector<PT(BoundingBox)> children_bb;
  std::vector<LVector3d> children_normal;
  std::vector<double> children_offset;
};

INLINE PyObject *QuadTreeNode::get_patch(void)
{
  Py_INCREF(patch);
  return patch;
}

INLINE BoundingBox *QuadTreeNode::get_bounds(void)
{
  return bounds;
}

#endif //PATCH_H

