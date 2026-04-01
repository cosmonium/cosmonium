#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from direct.interval.LerpInterval import LerpFunc
from direct.showbase.ShowBaseGlobal import globalClock
from math import acos, pi, exp, log
from panda3d.core import LQuaterniond, LVector3d, LPoint3d
from panda3d.core import lookAt

from .astro.frame import J2000EclipticReferenceFrame, J2000EquatorialReferenceFrame
from .astro import units
from .mathutil.easing import ExpEasing, SinEasing
from .mathutil.quaternion import slerp
from .objects.systems import StellarSystem
from .utils import isclose
from . import settings


class AutoPilot(object):
    """Autopilot for smooth camera navigation in the simulation.

    Manages animated transitions for position, orientation and continuous
    movements (orbiting, rotating, distance changes).  Two independent
    intervals are maintained:

    * ``current_interval`` – handles position/orientation fly-to animations.
    * ``timed_interval``   – handles time-limited continuous operations such
      as orbiting or zooming.

    Position interpolation uses an ``ExpEasing`` curve (slow start, fast
    middle, slow end) while rotation interpolation uses a ``SinEasing``
    curve.

    Both ``start_pos``/``end_pos`` and ``start_rot``/``end_rot``
    are stored in the *frame* coordinate system of the current anchor.
    Reference position changes are handled via ``stash_position`` / ``pop_position``.
    """

    def __init__(self, ui):
        self.ui = ui
        self.controller = None
        self.camera_controller = None
        # Active position/rotation fly-to interval (LerpFunc or None).
        self.current_interval = None
        # Active timed continuous-operation interval (LerpFunc or None).
        self.timed_interval = None
        # Timestamp of the last timed-interval tick, used to compute delta.
        self.last_interval_time = None
        # Frame-space start/end positions for the current fly-to animation.
        self.start_pos = LPoint3d()
        self.end_pos = LPoint3d()
        # Easing functions for position and rotation transitions.
        self.trans_easing = ExpEasing()
        self.rot_easing = SinEasing()

    def set_controller(self, controller):
        """Set the movement controller used to read/write position and orientation."""
        self.controller = controller

    def set_camera_controller(self, camera_controller):
        """Set the camera controller, used to prepare for movement (e.g. by cancelling any ongoing
        camera tracking),and to know the camera orientation."""
        self.camera_controller = camera_controller

    def reset(self):
        """Cancel any in-progress intervals immediately."""
        if self.current_interval is not None:
            self.current_interval.pause()
            self.current_interval = None
        if self.timed_interval is not None:
            self.timed_interval.pause()
            self.timed_interval = None

    def stash_position(self):
        """Convert stored frame-space positions to absolute coordinates.

        Called before the reference point changes so that the
        in-progress animation endpoints can be expressed in absolute
        world space and later converted back to frame space via ``pop_position``.
        """
        self.start_pos = self.controller.anchor.calc_absolute_position_of(self.start_pos)
        self.end_pos = self.controller.anchor.calc_absolute_position_of(self.end_pos)

    def pop_position(self):
        """Convert stored absolute positions back to frame-space coordinates.

        Called after the anchor reference point has changed to restore the
        animation endpoints to the new frame coordinate system.
        """
        self.start_pos = self.controller.anchor.calc_frame_position_of_absolute(self.start_pos)
        self.end_pos = self.controller.anchor.calc_frame_position_of_absolute(self.end_pos)

    # ------------------------------------------------------------------
    # Low-level animation helpers
    # ------------------------------------------------------------------

    def do_move(self, step):
        """Interpolation callback for a pure position fly-to animation.

        Linearly interpolates between ``start_pos`` and ``end_pos`` in
        frame space.  ``step`` is driven from 0 to 1 by the LerpFunc
        interval; easing is applied by the interval's blend type.
        """
        position = self.end_pos * step + self.start_pos * (1.0 - step)
        self.controller.set_frame_position(position)
        if step == 1.0:
            self.current_interval = None

    def move_to(self, new_pos, absolute=True, duration=0, ease=True):
        """Animate the camera to a new position over *duration* seconds.

        Args:
            new_pos: Target position. If *absolute* is ``True`` this is a local
                (reference point relative) position; otherwise it is already in frame
                space.
            absolute: When ``True``, *new_pos* is treated as a local position and is
                converted to frame space before interpolation.
            duration: Length of the animation in seconds. ``0`` applies the
                position instantly.
            ease: When ``True`` a smooth ease-in/ease-out blend is used;
                otherwise motion is linear.
        """
        if settings.debug_jump:
            duration = 0
        if duration == 0:
            if absolute:
                self.controller.set_local_position(new_pos)
            else:
                self.controller.set_frame_position(new_pos)
        else:
            if self.current_interval is not None:
                self.current_interval.pause()
            self.start_pos = self.controller.get_frame_position()
            if absolute:
                self.end_pos = self.controller.anchor.calc_frame_position_of_local(new_pos)
            else:
                self.end_pos = new_pos
            blend_type = 'easeInOut' if ease else 'noBlend'
            self.current_interval = LerpFunc(
                self.do_move, fromData=0, toData=1, duration=duration, blendType=blend_type, name=None
            )
            self.current_interval.start()

    def do_update_func(self, step, func, extra):
        """Per-frame callback for time-limited continuous operations.

        Computes the real-time delta since the last tick and passes it to
        *func*.  The function is only called when no position fly-to is
        active (``current_interval is None``), so continuous movements are
        naturally paused during fly-to animations.
        """
        delta = globalClock.get_real_time() - self.last_interval_time
        self.last_interval_time = globalClock.get_real_time()
        if self.current_interval is None:
            func(delta, *extra)
        if step == 1.0:
            self.timed_interval = None

    def update_func(self, func, duration=0, extra=()):
        """Run *func(delta, *extra)* every frame for *duration* seconds.

        Used by :meth:`orbit`, :meth:`rotate` and :meth:`change_distance`
        to drive continuous operations that depend on the elapsed time.

        When ``settings.debug_jump`` is ``True`` or *duration* is ``0``,
        *func* is called once immediately with ``delta=0`` (no-op for most
        callers that scale by delta).
        """
        if settings.debug_jump:
            duration = 0
        if duration == 0:
            func(duration, *extra)
        else:
            if self.timed_interval is not None:
                self.timed_interval.pause()
            self.last_interval_time = globalClock.get_real_time()
            self.timed_interval = LerpFunc(
                self.do_update_func, fromData=0, toData=1, duration=duration, extraArgs=[func, extra], name=None
            )
            self.timed_interval.start()

    def do_move_and_rot(self, step):
        """Interpolation callback for a combined position+rotation fly-to.

        Position uses ``trans_easing`` (ExpEasing) applied over the full
        [0, 1] range.  Rotation uses ``rot_easing`` (SinEasing) applied
        only over the sub-range [``start_rotation``, ``end_rotation``],
        allowing the rotation to begin and end at different points during
        the overall movement.
        """
        # Compute the normalised rotation progress within its sub-range.
        rot_range = self.end_rotation - self.start_rotation
        if rot_range != 0.0:
            rot_step = (step - self.start_rotation) / rot_range
        else:
            # start_rotation == end_rotation: rotation is already complete.
            rot_step = 1.0

        if rot_step < 0.0:
            rot = self.start_rot
        elif rot_step > 1.0:
            rot = self.end_rot
        else:
            rot = slerp(self.start_rot, self.end_rot, self.rot_easing.easing(rot_step))
            rot.normalize()
        self.controller.set_frame_orientation(rot)

        pos_step = self.trans_easing.easing(step)
        position = self.end_pos * pos_step + self.start_pos * (1.0 - pos_step)
        self.controller.set_frame_position(position)

        if step == 1.0:
            self.current_interval = None

    def move_and_rotate_to(self, new_pos, new_rot, absolute=True, duration=0, start_rotation=0.0, end_rotation=0.5):
        """Animate the camera to a new position and orientation simultaneously.

        The rotation sub-animation starts at *start_rotation* and ends at
        *end_rotation*, expressed as fractions of the total *duration*.
        This allows the camera to begin turning after it has started moving
        (e.g. start_rotation=0.25) and finish turning before it arrives
        (e.g. end_rotation=0.75).

        Args:
            new_pos: Target position (local or frame space, depending on *absolute*).
            new_rot: Target orientation (absolute or frame space, depending on
                *absolute*).
            absolute: When ``True``, *new_pos* is a local position and *new_rot* is
                an absolute orientation; both are converted to frame space.
            duration: Animation duration in seconds.  ``0`` applies instantly.
            start_rotation: Fraction of *duration* at which the rotation begins [0, 1].
            end_rotation: Fraction of *duration* at which the rotation ends [0, 1].
        """
        if settings.debug_jump:
            duration = 0
        self.camera_controller.prepare_movement()
        if duration == 0:
            if absolute:
                self.controller.set_local_position(new_pos)
                self.controller.set_absolute_orientation(new_rot)
            else:
                self.controller.set_frame_position(new_pos)
                self.controller.set_frame_orientation(new_rot)
        else:
            if self.current_interval is not None:
                self.current_interval.pause()
            self.start_pos = self.controller.get_frame_position()
            self.start_rot = self.controller.get_frame_orientation()
            if absolute:
                self.end_pos = self.controller.anchor.calc_frame_position_of_local(new_pos)
                self.end_rot = self.controller.anchor.calc_frame_orientation_of(new_rot)
            else:
                self.end_pos = new_pos
                self.end_rot = new_rot
            self.start_rotation = start_rotation
            self.end_rotation = end_rotation
            self.current_interval = LerpFunc(self.do_move_and_rot, fromData=0, toData=1, duration=duration, name=None)
            self.current_interval.start()

    # ------------------------------------------------------------------
    # High-level navigation commands
    # ------------------------------------------------------------------

    def go_to(self, target, duration, position, direction, up, start_rotation, end_rotation):
        """Fly to *position* facing *direction*, with an optional *up* hint.

        Builds the target orientation from *direction* and *up* using
        ``lookAt``.  If *up* is not provided the camera's current
        up vector is used.  The up vector is orthogonalised against
        *direction* via Gram-Schmidt before being passed to ``lookAt``.

        Args:
            target: The celestial object being navigated to (reserved for future
                use, e.g. keeping the object in view during the fly-to).
            duration: Animation duration in seconds.
            position: Target position in the local (anchor-relative) coordinate frame.
            direction: Unit vector pointing from the camera toward the target object.
            up: Preferred up vector for the camera.  Pass ``None`` to keep the
                current camera up direction.
            start_rotation: Rotation sub-range fraction (see :meth:`move_and_rotate_to`).
            end_rotation: Rotation sub-range fraction (see :meth:`move_and_rotate_to`).
        """
        if up is None:
            up = self.camera_controller.get_local_orientation().xform(LVector3d.up())
        if isclose(abs(up.dot(direction)), 1.0):
            print("Warning: lookat vector identical to up vector")
        else:
            # Make the up vector orthogonal to direction (Gram-Schmidt) and
            # normalise so that lookAt receives a proper unit vector.
            up = (up - direction * up.dot(direction)).normalized()
        orientation = LQuaterniond()
        lookAt(orientation, direction, up)
        self.move_and_rotate_to(
            position, orientation, duration=duration, start_rotation=start_rotation, end_rotation=end_rotation
        )

    def go_to_front(self, duration=None, distance=None, up=None, star=False, start_rotation=0.0, end_rotation=0.5):
        """Fly to the illuminated face of the selected object.

        The camera is positioned *distance* radii away from the object,
        looking from the direction of the primary light source.  For a
        star (or the primary of a system), the first registered light
        source is used; for a planet the system primary is used as the
        viewpoint.

        Args:
            duration: Animation duration. Defaults to ``settings.slow_move``.
            distance: Distance from the object surface in object radii. Defaults to
                ``settings.default_distance``.
            up: Preferred camera up vector. ``None`` keeps the current up.
            star: When ``True``, treat the selected object as a star and look from
                its own light source rather than from the system primary.
            start_rotation: Rotation timing fraction (see :meth:`move_and_rotate_to`).
            end_rotation: Rotation timing fraction (see :meth:`move_and_rotate_to`).
        """
        if not self.ui.selected:
            return
        target = self.ui.selected
        if duration is None:
            duration = settings.slow_move
        if distance is None:
            distance = settings.default_distance
        distance_unit = target.get_apparent_radius()
        if distance_unit == 0.0:
            distance_unit = target.get_bounding_radius()
        print("Go to front", target.get_name())
        self.ui.follow_selected()
        center = target.anchor.calc_absolute_relative_position_to(self.controller.get_absolute_reference_point())
        # Determine the position from which we are viewing the object (i.e. where the light comes from).
        light_position = None
        if star:
            if target.lights is not None and len(target.lights.lights) > 0:
                light_position = target.lights.lights[0].source
        else:
            if (
                target.parent is not None
                and isinstance(target.parent, StellarSystem)
                and target.parent.primary is not None
            ):
                if target.parent.primary == target:
                    if target.lights is not None and len(target.lights.lights) > 0:
                        light_position = target.lights.lights[0].source
                else:
                    light_position = target.parent.primary
        if light_position is not None:
            print("Looking from", light_position.get_name())
            view_origin = light_position.anchor.calc_absolute_relative_position_to(
                self.controller.get_absolute_reference_point()
            )
        else:
            view_origin = self.controller.get_local_position()
        direction = center - view_origin
        direction.normalize()
        new_position = center - direction * distance * distance_unit
        self.go_to(target, duration, new_position, direction, up, start_rotation, end_rotation)

    def go_to_object(self, duration=None, distance=None, up=None, start_rotation=0.0, end_rotation=0.5):
        """Fly toward the selected object from the current camera direction.

        The camera travels to a point *distance* radii in front of the
        object, keeping the current viewing direction.

        Args:
            duration: Animation duration.  Defaults to ``settings.slow_move``.
            distance: Distance from the object surface in object radii.  Defaults to
                ``settings.default_distance``.
            up: Preferred camera up vector.  ``None`` keeps the current up.
            start_rotation: Rotation timing fraction (see :meth:`move_and_rotate_to`).
            end_rotation: Rotation timing fraction (see :meth:`move_and_rotate_to`).
        """
        if not self.ui.selected:
            return
        target = self.ui.selected
        if duration is None:
            duration = settings.slow_move
        if distance is None:
            distance = settings.default_distance
        distance_unit = target.get_apparent_radius()
        if distance_unit == 0.0:
            distance_unit = target.get_bounding_radius()
        print("Go to", target.get_name())
        self.ui.follow_selected()
        center = target.anchor.calc_absolute_relative_position_to(self.controller.get_absolute_reference_point())
        direction = center - self.controller.get_local_position()
        direction.normalize()
        new_position = center - direction * distance * distance_unit
        self.go_to(target, duration, new_position, direction, up, start_rotation, end_rotation)

    def go_to_object_long_lat(
        self, longitude, latitude, duration=None, distance=None, up=None, start_rotation=0.25, end_rotation=0.75
    ):
        """Fly to a specific longitude/latitude on the selected object.

        The camera is placed *distance* radii above the geodetic position
        given by (*longitude*, *latitude*) on the object's surface,
        looking toward the object centre.

        Args:
            longitude: Target longitude in radians.
            latitude: Target latitude in radians.
            duration: Animation duration. Defaults to ``settings.slow_move``.
            distance: Distance from the surface in object radii. Defaults to
                ``settings.default_distance``.
            up: Preferred camera up vector. ``None`` keeps the current up.
            start_rotation: Rotation timing fraction (see :meth:`move_and_rotate_to`).
            end_rotation: Rotation timing fraction (see :meth:`move_and_rotate_to`).
        """
        if not self.ui.selected:
            return
        target = self.ui.selected
        if duration is None:
            duration = settings.slow_move
        if distance is None:
            distance = settings.default_distance
        distance_unit = target.get_apparent_radius()
        if distance_unit == 0.0:
            distance_unit = target.get_bounding_radius()
        print("Go to long-lat", target.get_name())
        self.ui.follow_selected()
        center = target.anchor.calc_absolute_relative_position_to(self.controller.get_absolute_reference_point())
        # Compute the camera offset from the object centre in the object's
        # body-fixed frame, then rotate it into the world frame.
        offset = target.surface.geodetic_to_cartesian(longitude, latitude, (distance - 1) * distance_unit)
        offset = target.anchor._orientation.xform(offset)
        direction = -offset.normalized()
        self.go_to(target, duration, center + offset, direction, up, start_rotation, end_rotation)

    def go_to_surface(self, duration=None, altitude=2):
        """Fly the camera down to just above the surface below the current position.

        The camera is placed at the terrain height directly below its
        current position (as reported by ``get_height_under``), offset by a
        small margin, and oriented to look toward the object centre.

        Args:
            duration: Animation duration.  Defaults to ``settings.slow_move``.
            height: Reserved for future use; currently the landing height is
                computed from the actual terrain height plus a fixed 10-metre
                safety margin.
        """
        if not self.ui.selected:
            return
        target = self.ui.selected
        if duration is None:
            duration = settings.slow_move
        print("Go to surface", target.get_name())
        self.ui.sync_selected()
        center = target.anchor.calc_absolute_relative_position_to(self.controller.get_absolute_reference_point())
        direction = self.controller.get_local_position() - center
        new_orientation = LQuaterniond()
        lookAt(new_orientation, direction)
        distance = target.get_height_under(self.controller.get_local_position()) + altitude * units.m
        new_position = center + new_orientation.xform(LVector3d(0, distance, 0))
        self.move_and_rotate_to(new_position, new_orientation, duration=duration)

    def go_pole(self, target, lat, duration, zoom):
        """Fly to the pole at *lat* radians latitude on the given object.

        Args:
            target: The celestial object to fly to.
            lat: Target latitude in radians (``+pi/2`` = north, ``-pi/2`` = south).
            duration: Animation duration. ``None`` uses ``settings.slow_move``.
            zoom: When ``True``, use ``settings.default_distance``; otherwise
                preserve the current distance.
        """
        if zoom:
            distance = settings.default_distance
        else:
            distance_unit = target.get_apparent_radius()
            if distance_unit == 0.0:
                distance_unit = target.get_bounding_radius()
            distance = target.anchor.distance_to_obs / distance_unit
        self.go_to_object_long_lat(0, lat, duration, distance)

    def go_north(self, duration=None, zoom=False):
        """Fly to the north pole of the selected object.

        Args:
            duration: Animation duration.  Defaults to ``settings.slow_move``.
            zoom: When ``True``, use ``settings.default_distance`` rather than
                preserving the current distance.
        """
        if not self.ui.selected:
            return
        target = self.ui.selected
        lat = pi / 2
        if target.anchor.rotation.is_flipped():
            lat = -lat
        self.go_pole(target, lat, duration, zoom)

    def go_south(self, duration=None, zoom=False):
        """Fly to the south pole of the selected object.

        Args:
            duration: Animation duration.  Defaults to ``settings.slow_move``.
            zoom: When ``True``, use ``settings.default_distance`` rather than
                preserving the current distance.
        """
        if not self.ui.selected:
            return
        target = self.ui.selected
        lat = -pi / 2
        if target.anchor.rotation.is_flipped():
            lat = -lat
        self.go_pole(target, lat, duration, zoom)

    def go_meridian(self, duration=None, zoom=False):
        """Fly to the prime meridian (longitude=0, latitude=0) of the selected object.

        Args:
            duration: Animation duration.  Defaults to ``settings.slow_move``.
            zoom: When ``True``, use ``settings.default_distance`` rather than
                preserving the current distance.
        """
        if not self.ui.selected:
            return
        target = self.ui.selected
        if zoom:
            distance = settings.default_distance
        else:
            distance_unit = target.get_apparent_radius()
            if distance_unit == 0.0:
                distance_unit = target.get_bounding_radius()
            distance = target.anchor.distance_to_obs / distance_unit
        self.go_to_object_long_lat(0, 0, duration, distance)

    def _compute_roll_to_align(self, plane_normal):
        """Compute the roll angle required to align the camera to a reference plane.

        Given the normal of a reference plane (e.g. the ecliptic or
        equatorial plane) expressed in the camera's local frame, returns a
        quaternion representing the roll correction needed to align the
        camera's up axis with that plane.

        Args:
            plane_normal: The plane normal vector, already expressed in the camera's
                local frame (i.e. already transformed by the inverse of the
                frame orientation).

        Returns:
            Roll quaternion around the camera's forward axis.
        """
        angle = acos(plane_normal.dot(LVector3d.right()))
        direction = plane_normal.cross(LVector3d.right()).dot(LVector3d.forward())
        if direction < 0:
            angle = 2 * pi - angle
        rot = LQuaterniond()
        rot.setFromAxisAngleRad(pi / 2 - angle, LVector3d.forward())
        return rot

    def align_on_ecliptic(self, duration=None):
        """Roll the camera so its up axis aligns with the J2000 ecliptic plane.

        The alignment is applied instantly regardless of *duration* (animated
        alignment is not yet implemented).

        Args:
            duration: Reserved for future animated alignment support.
        """
        ecliptic_normal = (
            self.controller.get_frame_orientation()
            .conjugate()
            .xform(J2000EclipticReferenceFrame().get_orientation().xform(LVector3d.up()))
        )
        rot = self._compute_roll_to_align(ecliptic_normal)
        self.controller.step_turn_local(rot)

    def align_on_equatorial(self, duration=None):
        """Roll the camera so its up axis aligns with the J2000 equatorial plane.

        The alignment is applied instantly regardless of *duration* (animated
        alignment is not yet implemented).

        Args:
            duration: Reserved for future animated alignment support.
        """
        equatorial_normal = (
            self.controller.get_frame_orientation()
            .conjugate()
            .xform(J2000EquatorialReferenceFrame().get_orientation().xform(LVector3d.up()))
        )
        rot = self._compute_roll_to_align(equatorial_normal)
        self.controller.step_turn_local(rot)

    # ------------------------------------------------------------------
    # Continuous movement operations
    # ------------------------------------------------------------------

    def do_change_distance(self, delta, rate):
        """Per-frame callback for exponential distance change toward the selected object.

        Applies an exponential zoom so that the *rate* of change feels
        uniform in log-space (similar to a dolly move on a logarithmic
        scale).  Movement is clamped so the camera cannot pass through the
        object.

        Args:
            delta: Elapsed time in seconds since the last call.
            rate: Zoom rate (positive = move away, negative = move closer).
        """
        target = self.ui.selected
        center = target.anchor.calc_absolute_relative_position_to(self.controller.get_absolute_reference_point())
        min_distance = target.get_apparent_radius()
        natural_distance = 4.0 * min_distance
        relative_pos = self.controller.get_local_position() - center

        # If already inside the minimum distance, halve it to avoid
        # locking the camera in place.
        if target.anchor.distance_to_obs < min_distance:
            min_distance = target.anchor.distance_to_obs * 0.5

        if target.anchor.distance_to_obs >= min_distance and natural_distance != 0:
            r = (target.anchor.distance_to_obs - min_distance) / natural_distance
            new_distance = min_distance + natural_distance * exp(log(r) + rate * delta)
            new_pos = relative_pos * (new_distance / target.anchor.distance_to_obs)
            self.controller.set_local_position(center + new_pos)

    def change_distance(self, rate, duration=None):
        """Zoom in or out relative to the selected object over *duration* seconds.

        Args:
            rate: Zoom rate (positive = move away, negative = move closer).
            duration: Duration of the zoom operation.  Defaults to ``settings.fast_move``.
        """
        if duration is None:
            duration = settings.fast_move
        self.update_func(self.do_change_distance, duration, [rate])

    def do_orbit(self, delta, axis, rate):
        """Per-frame callback that rotates the camera around the selected object.

        The camera is orbited about the object's centre in frame space.
        The orbit rotation is applied both to the camera position (to move
        it around the object) and to the camera orientation (to keep the
        object centred in the view).

        Args:
            delta: Elapsed time in seconds since the last call.
            axis: World-space rotation axis.
            rate: Angular velocity in radians per second.
        """
        target = self.ui.selected
        center = target.anchor.calc_absolute_relative_position_to(self.controller.get_absolute_reference_point())
        center = self.controller.anchor.calc_frame_position_of_local(center)
        relative_pos = self.controller.get_frame_position() - center
        rot = LQuaterniond()
        rot.setFromAxisAngleRad(rate * delta, axis)
        # Transform the world-space rotation into the camera's local frame.
        frame_orient = self.controller.get_frame_orientation()
        rot_local = frame_orient.conjugate() * rot * frame_orient
        rot_local.normalize()
        # Rotate the relative position and update camera position.
        distance = relative_pos.length()
        relative_pos.normalize()
        new_pos = rot_local.xform(relative_pos) * distance
        self.controller.set_frame_position(new_pos + center)
        # Apply the same rotation to the camera orientation so it keeps the object in the centre of the view.
        self.controller.turn_local(frame_orient * rot_local)

    def orbit(self, axis, rate, duration=None):
        """Orbit the camera around the selected object for *duration* seconds.

        Args:
            axis: World-space rotation axis.
            rate: Angular velocity in radians per second.
            duration: Duration of the orbit.  Defaults to ``settings.slow_move``.
        """
        if duration is None:
            duration = settings.slow_move
        self.update_func(self.do_orbit, duration, [axis, rate])

    def do_rotate(self, delta, axis, rate):
        """Per-frame callback that rotates the camera in place.

        Args:
            delta: Elapsed time in seconds since the last call.
            axis: Local-space rotation axis.
            rate: Angular velocity in radians per second.
        """
        rot = LQuaterniond()
        rot.setFromAxisAngleRad(rate * delta, axis)
        self.controller.step_turn_local(rot)

    def rotate(self, axis, rate, duration=None):
        """Rotate the camera in place for *duration* seconds.

        Args:
            axis: Local-space rotation axis.
            rate: Angular velocity in radians per second.
            duration: Duration of the rotation.  Defaults to ``settings.slow_move``.
        """
        if duration is None:
            duration = settings.slow_move
        self.update_func(self.do_rotate, duration, [axis, rate])
