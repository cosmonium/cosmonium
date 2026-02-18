# Controllers Unit Tests

This directory contains unit tests covering functionalities related to the controllers in Cosmonium.

## Test Coverage

### 1. Movement Controller Tests (`test_movement_controllers.py`)

Tests for the base and position-based movement controllers:

- **TestMovementController**: Tests initialization, update logic based on anchor visibility, animation state setting, and compatibility properties.
- **TestCartesianMovementController**: Tests position setting/retrieval, delta movement, relative movement, rotation, local position, and absolute orientation.
- **TestFlatSurfaceMovementController**: Tests initialization, position and altitude management, and position updates on flat surfaces.

### 2. Kinetic Controller Tests (`test_kinetic_controllers.py`)

Tests for physics-based (kinetic) movement controllers:

- **TestKineticMovementController**: Tests initialization and attribute setup for kinetic controllers.
- **TestBulletMovementController**: Tests initialization, position setting with/without physics node, velocity-based movement, relative rotation, and feedback from physics simulation.

### 3. Collision Controller Tests (`test_collision_controllers.py`)

Tests for collision-based movement controllers:

- **TestReactBodyController**: Tests update logic with and without ship objects, and direct local position setting.
