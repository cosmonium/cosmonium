# Camera Package

This package contains the camera system for Cosmonium.

## Components

### Base Classes (`base.py`)

- **CameraBase**: Base class for camera functionality including field of view, zoom, and pixel calculations
- **CameraHolder**: Main camera holder with anchor and scattering support
- **EventsControllerBase**: Base class for event handling
- **BaseCameraController**: Base class for all camera controllers with shared functionality
- **CameraController**: Alias for BaseCameraController (backward compatibility)
- **OrbitTargetHelper**: Helper class for orbiting around targets
- **RotateAnchorHelper**: Helper class for anchor rotation

### Camera Controllers

#### Fixed Camera Controller (`fixed_controller.py`)
- **FixedCameraController**: A stationary camera that can be rotated manually
- Features:
  - Mouse drag rotation
  - Look back functionality
  - State management (default, mouse drag)

#### Track Camera Controller (`track_controller.py`)
- **TrackCameraController**: Automatically tracks a target object
- Features:
  - Continuous target tracking
  - Automatic orientation updates

#### Follow Camera Controllers (`follow_controller.py`)
- **FollowCameraController**: Follows the reference anchor at a specified distance
- Features:
  - Maintains minimum/maximum distance from target
  - Automatic orientation to face target

- **SurfaceFollowCameraController**: Advanced follow camera for surface navigation
- Features:
  - Orbit control via mouse and keyboard
  - Distance adjustment with mouse wheel
  - Terrain height awareness
  - State management (default, orbit mouse, orbit keyboard)

#### Look Around Camera Controller (`lookaround_controller.py`)
- **LookAroundCameraController**: Free look camera controlled by mouse position
- Features:
  - Mouse-based orientation control
  - No automatic tracking
