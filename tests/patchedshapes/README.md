# Patched Shapes Unit Tests

This directory contains unit tests covering functionalities related to terrain patches, level of detail (LOD) systems, and spatial data structures.

## Test Coverage

### 1. Patch Neighbors Tests (`test_patch_neighbours.py`)

Tests the patch neighbor calculation system that manages adjacent terrain patches:

- **Neighbor Management**: Adding, setting, and retrieving neighbors on different faces (North, East, South, West)
- **Neighbor Collection**: Collecting all neighbors from all faces
- **Overlap Detection**: Removing neighbors that don't overlap with the current patch
- **Edge Cases**: Testing boundary conditions and no-neighbor scenarios


### 2. LOD Control Tests (`test_lod_control.py`)

Tests the Level of Detail control system that determines when patches should split or merge:

- **TextureLodControl**: Tests texture-based LOD decisions
- **VertexSizeLodControl**: Tests vertex-size-based LOD decisions
- **TextureOrVertexSizeLodControl**: Tests combined texture and vertex-size LOD logic
- **VertexSizeMaxDistanceLodControl**: Tests distance-based LOD culling
- **Split/Merge Logic**: Validates hysteresis to avoid oscillation
- **Max LOD Limits**: Ensures proper behavior at maximum detail levels


### 3. QuadTree Splitting Tests (`test_quadtree.py`)

Tests the quadtree node structure used for hierarchical terrain patch management:

- **Node Initialization**: Tests proper setup of quadtree nodes
- **Child Management**: Adding and removing child nodes
- **Visibility Checks**: Testing patch visibility and culling
- **Split Decisions**: Validates when patches should split into children
- **Merge Decisions**: Validates when child patches should merge back to parent
- **LOD Traversal**: Tests recursive LOD checks through the tree


### 4. Patch face rotation Tests (`test_face_rotation.py`)

Tests for cube face rotation convention and xyz_to_face_xy inverse mappings.

- **TestFaceRotationConvention**: Verify face rotations produce correct normals and UV orientations
- **TestEdgeAdjacency**: Verify that adjacent faces share edge vertices correctly
