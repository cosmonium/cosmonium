#include "py_panda.h"
#include "dcast.h"
#include "cullingFrustum.h"
#include "patch.h"
#include <algorithm>

LodControl::~LodControl(void)
{
}

void
LodControl::set_texture_size(unsigned int texture_size)
{
}

bool
LodControl::should_instanciate(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  return patch->visible && patch->children.size() == 0;
}

bool
LodControl::should_remove(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  return !patch->visible;
}

TextureLodControl::TextureLodControl(unsigned int min_density, unsigned int density, unsigned int max_lod) :
    min_density(min_density),
    density(density),
    max_lod(max_lod),
    texture_size(0)
{
}

void
TextureLodControl::set_texture_size(unsigned int texture_size)
{
  this->texture_size = texture_size;
}

unsigned int
TextureLodControl::get_density_for(unsigned int lod)
{
  return max(min_density, density / (1 << lod));
}

bool
TextureLodControl::should_split(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  if (patch->lod < max_lod) {
    return (texture_size > 0 && apparent_patch_size > texture_size * 1.1); //TODO: add appearance.texture.can_split(patch)
  } else {
    return false;
  }

}

bool
TextureLodControl::should_merge(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  return (apparent_patch_size < texture_size / 1.1);
}

TextureOrVertexSizeLodControl::TextureOrVertexSizeLodControl(unsigned int max_vertex_size, unsigned int min_density, unsigned int density, unsigned int max_lod) :
    TextureLodControl(min_density, density, max_lod),
    max_vertex_size(max_vertex_size)
{
}

bool
TextureOrVertexSizeLodControl::should_split(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  if (patch->lod < max_lod) {
    if (texture_size > 0) {
        return apparent_patch_size > texture_size * 1.1;
    } else {
        double apparent_vertex_size = apparent_patch_size / patch->density;
        return apparent_vertex_size > max_vertex_size;
    }
  } else {
    return false;
  }
}

bool
TextureOrVertexSizeLodControl::should_merge(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  if (texture_size > 0) {
      return apparent_patch_size < texture_size / 1.1;
  } else {
      double apparent_vertex_size = apparent_patch_size / patch->density;
      return apparent_vertex_size < max_vertex_size / 1.1;
  }
}

VertexSizeLodControl::VertexSizeLodControl(unsigned int max_vertex_size, unsigned int density, unsigned int max_lod) :
    density(density),
    max_lod(max_lod),
    max_vertex_size(max_vertex_size)
{
}

unsigned int
VertexSizeLodControl::get_density_for(unsigned int lod)
{
  return density;
}

bool
VertexSizeLodControl::should_split(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  if (patch->lod < max_lod) {
      double apparent_vertex_size = apparent_patch_size / patch->density;
      return apparent_vertex_size > max_vertex_size * 1.1;
  } else {
      return false;
  }
}

bool
VertexSizeLodControl::should_merge(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
    double apparent_vertex_size = apparent_patch_size / patch->density;
    return apparent_vertex_size < max_vertex_size / 1.1;
}

VertexSizeMaxDistanceLodControl::VertexSizeMaxDistanceLodControl(double max_distance, unsigned int max_vertex_size, unsigned int density, unsigned int max_lod) :
    VertexSizeLodControl(max_vertex_size, density, max_lod),
    max_distance(max_distance)
{
}

bool
VertexSizeMaxDistanceLodControl::should_instanciate(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  return patch->visible && patch->children.size() == 0 && distance < max_distance;
}

bool
VertexSizeMaxDistanceLodControl::should_remove(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  return !patch->visible;
}

QuadTreeNodeCollection::QuadTreeNodeCollection(void)
{
}

QuadTreeNodeCollection::
QuadTreeNodeCollection(const QuadTreeNodeCollection &copy) :
  collection(copy.collection)
{
}

void QuadTreeNodeCollection::
operator =(const QuadTreeNodeCollection &copy) {
  collection = copy.collection;
}

QuadTreeNodeCollection::~QuadTreeNodeCollection(void)
{
}

void
QuadTreeNodeCollection::add(QuadTreeNode *node)
{
  collection.push_back(node);
}

static inline bool
cmp_by_distance(QuadTreeNode *a, QuadTreeNode *b)
{
  return a->distance < b->distance;
}

void
QuadTreeNodeCollection::sort_by_distance(void)
{
  std::sort(collection.begin(), collection.end(), cmp_by_distance);
}

LodResult::LodResult(void) :
  to_split(),
  to_merge(),
  to_show(),
  to_remove(),
  max_lod(0)
{
}

LodResult::~LodResult(void)
{
}

void
LodResult::add_to_split(QuadTreeNode *patch)
{
  to_split.add(patch);
}

void
LodResult::add_to_merge(QuadTreeNode *patch)
{
  to_merge.add(patch);
}

void
LodResult::add_to_show(QuadTreeNode *patch)
{
  to_show.add(patch);
}

void
LodResult::add_to_remove(QuadTreeNode *patch)
{
  to_remove.add(patch);
}

void
LodResult::check_max_lod(QuadTreeNode *patch)
{
  max_lod = max(max_lod, patch->lod);
}

void
LodResult::sort_by_distance(void)
{
  to_split.sort_by_distance();
  to_merge.sort_by_distance();
  to_show.sort_by_distance();
  to_remove.sort_by_distance();
}

QuadTreeNode::QuadTreeNode(PyObject *patch, int lod, int density, LPoint3d centre, double length, LVector3d normal, double offset, BoundingBox *bounds) :
    patch(patch),
    lod(lod),
    density(density),
    centre(centre),
    length(length),
    normal(normal),
    offset(offset),
    bounds(bounds),
    children(),
    children_bb(),
    children_normal(),
    children_offset(),
    shown(false),
    visible(false),
    distance(0.0),
    instance_ready(false),
    apparent_size(0.0),
    patch_in_view(false)
{
  Py_INCREF(patch);
}

QuadTreeNode::~QuadTreeNode(void)
{
  Py_DECREF(patch);
}

void
QuadTreeNode::set_shown(bool shown)
{
  this->shown = shown;
}

void
QuadTreeNode::set_instance_ready(bool instance_ready)
{
  this->instance_ready = instance_ready;
}

void
QuadTreeNode::add_child(QuadTreeNode *child)
{
  children.push_back(child);
  children_bb.push_back(DCAST(BoundingBox, child->bounds->make_copy()));
  children_normal.push_back(child->normal);
  children_offset.push_back(child->offset);
}

void
QuadTreeNode::remove_children(void)
{
  children.clear();
  children_bb.clear();
  children_normal.clear();
  children_offset.clear();
}

bool
QuadTreeNode::can_merge_children(void)
{
  if (children.size() == 0) {
      return false;
  }
  for (auto child : children) {
      if (child->children.size() != 0) {
          return false;
      }
  }
  return true;
}

bool
QuadTreeNode::in_patch(LPoint2d local)
{
  return false;
}

void
QuadTreeNode::check_visibility(CullingFrustumBase *culling_frustum, LPoint2d local, LPoint3d model_camera_pos, LVector3d model_camera_vector, double altitude, double pixel_size)
{
  bool within_patch = false;
  if (false && in_patch(local)) {
      within_patch = true;
      distance = altitude;
  } else {
      distance = max(altitude, (centre - model_camera_pos).length() - length * 0.7071067811865476);
  }
  patch_in_view = culling_frustum->is_patch_in_view(this);
  visible = within_patch || patch_in_view;
  apparent_size = length / (distance * pixel_size);
}

bool
QuadTreeNode::are_children_visibles(CullingFrustumBase *culling_frustum)
{
  bool children_visible = children_bb.size() == 0;
  for (unsigned int i = 0; i < children_bb.size(); ++i) {
      if (culling_frustum->is_bb_in_view(children_bb[i], children_normal[i], children_offset[i])) {
          children_visible = true;
          break;
      }
  }
  return children_visible;
}

void
QuadTreeNode::check_lod(LodResult *lod_result, CullingFrustumBase *culling_frustum, LPoint2d local, LPoint3d model_camera_pos, LVector3d model_camera_vector, double altitude, double pixel_size, LodControl *lod_control)
{
  check_visibility(culling_frustum, local, model_camera_pos, model_camera_vector, altitude, pixel_size);
  lod_result->check_max_lod(this);
  //TODO: Should be checked before calling check_lod
  for (auto child : children) {
      child->check_lod(lod_result, culling_frustum, local, model_camera_pos, model_camera_vector, altitude, pixel_size, lod_control);
  }
  if (children.size() != 0) {
      if (can_merge_children() && lod_control->should_merge(this, apparent_size, distance)) {
          lod_result->add_to_merge(this);
      }
  } else {
      if (lod_control->should_split(this, apparent_size, distance) && (lod > 0 || instance_ready)) {
          if (are_children_visibles(culling_frustum)) {
              lod_result->add_to_split(this);
          }
      }
      if (shown && lod_control->should_remove(this, apparent_size, distance)) {
          lod_result->add_to_remove(this);
      }
      if (!shown && lod_control->should_instanciate(this, apparent_size, distance)) {
          lod_result->add_to_show(this);
      }
  }
}
