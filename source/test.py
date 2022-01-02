
from panda3d.core import LPoint3d, LMatrix4, PerspectiveLens, LVector3
from engine import OctreeNode, OctreeLeaf, InfiniteFrustum, VisibleObjectsTraverser


def test_empty():
    o = OctreeNode(0, LPoint3d(), 0, 0)
    assert o.level == 0
    assert o.center == LPoint3d()
    assert o.width == 0
    assert o.threshold == 0
    assert o.index == -1
    assert o.get_num_children() == 0
    assert o.get_num_leaves() == 0
    o = OctreeNode(66, LPoint3d(1, 2, 3), 77, 88, 99)
    assert o.level == 66
    assert o.center == LPoint3d(1, 2, 3)
    assert o.width == 77
    assert o.threshold == 88
    assert o.index == 99
    assert o.get_num_children() == 0
    assert o.get_num_leaves() == 0

def test_one_leaf():
    o = OctreeNode(66, LPoint3d(1, 2, 3), 77, 88, 99)
    leaf = OctreeLeaf("leaf", LPoint3d(), 0, 0)
    o.add(leaf)
    assert o.level == 66
    assert o.center == LPoint3d(1, 2, 3)
    assert o.width == 77
    assert o.threshold == 88
    assert o.index == 99
    assert o.get_num_children() == 0
    assert o.get_num_leaves() == 1

def create_frustum(pos=None, mat=None):
    """Return an infinite frustum centered on the origin, looking towards +Y
    and with a near plane at (0, 1.0, 0)
    The default FoV is 30deg"""

    if pos is None:
        pos = LPoint3d()
    if mat is None:
        mat = LMatrix4()
    lens = PerspectiveLens()
    bh = lens.make_bounds()
    f = InfiniteFrustum(bh, mat, pos)
    return f

def test_frustum():
    f = create_frustum(pos=LPoint3d())
    assert f.get_position() == LPoint3d()
    f = create_frustum(pos=LPoint3d(1, 2, 3))
    assert f.get_position() == LPoint3d(1, 2, 3)

def test_frustum_intersection():
    f = create_frustum()
    assert not f.is_sphere_in(LPoint3d(), 0)
    assert f.is_sphere_in(LPoint3d(), 1.1)
    assert f.is_sphere_in(LPoint3d(0, 1.1, 0), 0)

    mat = LMatrix4()
    mat.set_rotate_mat(90, LVector3.up())
    f = create_frustum(mat=mat)
    assert not f.is_sphere_in(LPoint3d(), 0)
    assert f.is_sphere_in(LPoint3d(), 1.1)
    assert f.is_sphere_in(LPoint3d(-1.1, 0, 0), 0)
    assert not f.is_sphere_in(LPoint3d(0, 1.1, 0), 0)

    pos = LPoint3d(0, 1, 0)
    f = create_frustum(pos=pos)
    assert not f.is_sphere_in(LPoint3d(), 0)
    assert not f.is_sphere_in(LPoint3d(), 1.1)
    assert not f.is_sphere_in(LPoint3d(0, 1.1, 0), 0)
    assert f.is_sphere_in(LPoint3d(), 2.1)
    assert f.is_sphere_in(LPoint3d(0, 2.1, 0), 0)

def test_traverse_empty():
    o = OctreeNode(0, LPoint3d(), 0, 0)
    f = create_frustum()
    t = VisibleObjectsTraverser(f, 6.0, 1)
    o.traverse(t)
    assert t.get_leaves() == ()

def test_traverse_center():
    o = OctreeNode(0, LPoint3d(), 0, 0)
    f = create_frustum()
    leaf_center = OctreeLeaf("center", LPoint3d(), 0, 0)
    o.add(leaf_center)
    t = VisibleObjectsTraverser(f, 6.0, 1)
    o.traverse(t)
    assert t.get_leaves() == (leaf_center, )
    assert leaf_center.get_update_id() == 1

def test_traverse_front():
    o = OctreeNode(0, LPoint3d(), 0, 0)
    f = create_frustum()
    leaf_center = OctreeLeaf("center", LPoint3d(), 0, 0)
    leaf_front = OctreeLeaf("front", LPoint3d(0, 2, 0), 0, 0)
    leaf_back = OctreeLeaf("back", LPoint3d(0, -2, 0), 0, 0)
    o.add(leaf_center)
    o.add(leaf_front)
    o.add(leaf_back)
    t = VisibleObjectsTraverser(f, 6.0, 1)
    o.traverse(t)
    assert t.get_leaves() == (leaf_center, leaf_front)
    assert leaf_center.get_update_id() == 1
    assert leaf_front.get_update_id() == 1
    assert leaf_back.get_update_id() == 0

def test_ref():
    o = OctreeNode(0, LPoint3d(0, 2, 0), 1, 1)
    for i in range(75):
        leaf = OctreeLeaf("leaf", LPoint3d(), 0, 0)
        o.add(leaf)
    leaf_child = OctreeLeaf("child", LPoint3d(), 2, 0)
    o.add(leaf_child)
    assert o.get_num_leaves() == 75
    assert o.get_num_children() == 1

def test_ref_2():
    o = OctreeNode(0, LPoint3d(0, 2, 0), 1, 1)
    for i in range(75):
        leaf = OctreeLeaf("leaf", LPoint3d(0, -2, 0), 0, 0)
        o.add(leaf)
    leaf_child = OctreeLeaf("child", LPoint3d(0, 2, 0), 2, 0)
    o.add(leaf_child)
    assert o.get_num_leaves() == 75
    assert o.get_num_children() == 1
    f = create_frustum()
    for i in range(100):
        t = VisibleObjectsTraverser(f, 6.0, 1)
        o.traverse(t)
        assert t.get_leaves() == (leaf_child, )

def test_split():
    o = OctreeNode(0, LPoint3d(0, 2, 0), 1, 1)
    a = []
    for i in range(75):
        leaf = OctreeLeaf("leaf", LPoint3d(0, 2, 0), 0, 0)
        o.add(leaf)
        a.append(leaf)
    assert o.get_num_leaves() == 75
    assert o.get_num_children() == 0
    leaf_child = OctreeLeaf("child", LPoint3d(0, 2, 0), 2, 0)
    o.add(leaf_child)
    assert o.get_num_leaves() == 75
    assert o.get_num_children() == 1
    child = o.get_child(7)
    assert child != None
    assert child.get_num_leaves() == 1
    assert child.get_num_children() == 0
    assert child.get_leaves() == (leaf_child, )
    f = create_frustum()
    t = VisibleObjectsTraverser(f, 6.0, 1)
    o.traverse(t)
    assert leaf_child in t.get_leaves()
    t = VisibleObjectsTraverser(f, 6.0, 2)
    child.traverse(t)
    assert t.get_leaves() == (leaf_child, )
