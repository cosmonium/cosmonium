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

"""Concrete base class for the autopilot.

Provides :class:`AutoPilotBase`, the core animation infrastructure that all
autopilot modes build on.  It owns the two Panda3D ``LerpFunc`` intervals,
the easing curves, controller wiring, and the coordinate helpers that keep
animation endpoints consistent across anchor reference-point changes.

Autopilot modes (navigation, alignment, continuous, …) receive an
``AutoPilotBase`` instance and call its public methods to drive animations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional, Tuple

from direct.interval.LerpInterval import LerpFunc
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import LPoint3d, LQuaterniond

from .. import settings
from ..mathutil.easing import ExpEasing, SinEasing
from ..mathutil.quaternion import slerp

if TYPE_CHECKING:
    from ..camera import BaseCameraController
    from ..controllers.base import MovementController


class AutoPilotBase:
    """Concrete base for the autopilot with core animation infrastructure.

    Manages animated transitions for position and orientation via two
    independent Panda3D ``LerpFunc`` intervals:

    * ``current_interval`` – position/orientation fly-to animation.
    * ``timed_interval``   – time-limited continuous operation (orbit, zoom, …).

    Position interpolation uses an :class:`~cosmonium.mathutil.easing.ExpEasing`
    curve while rotation interpolation uses a
    :class:`~cosmonium.mathutil.easing.SinEasing` curve.

    Both ``start_pos``/``end_pos`` and ``start_rot``/``end_rot`` are stored
    in the *frame* coordinate system of the current anchor.  Reference
    position changes are handled via :meth:`stash_position` /
    :meth:`pop_position`.
    """

    def __init__(self, ui) -> None:
        self.ui = ui
        self.controller: Optional[MovementController] = None
        self.camera_controller: Optional[BaseCameraController] = None
        # Active position/rotation fly-to interval (LerpFunc or None).
        self.current_interval: Optional[LerpFunc] = None
        # Active timed continuous-operation interval (LerpFunc or None).
        self.timed_interval: Optional[LerpFunc] = None
        # Timestamp of the last timed-interval tick, used to compute delta.
        self.last_interval_time: Optional[float] = None
        # Frame-space start/end positions for the current fly-to animation.
        self.start_pos = LPoint3d()
        self.end_pos = LPoint3d()
        # Easing functions for position and rotation transitions.
        self.trans_easing = ExpEasing()
        self.rot_easing = SinEasing()

    # ------------------------------------------------------------------
    # Controller wiring
    # ------------------------------------------------------------------

    def set_controller(self, controller: MovementController) -> None:
        """Set the movement controller used to read/write position and orientation."""
        self.controller = controller

    def set_camera_controller(self, camera_controller: BaseCameraController) -> None:
        """Set the camera controller, used to prepare for movement (e.g. by cancelling any ongoing
        camera tracking), and to know the camera orientation."""
        self.camera_controller = camera_controller

    def reset(self) -> None:
        """Cancel any in-progress intervals immediately."""
        if self.current_interval is not None:
            self.current_interval.pause()
            self.current_interval = None
        if self.timed_interval is not None:
            self.timed_interval.pause()
            self.timed_interval = None

    # ------------------------------------------------------------------
    # Reference-frame coordinate helpers
    # ------------------------------------------------------------------

    def stash_position(self) -> None:
        """Convert stored frame-space positions to absolute coordinates.

        Called before the reference point changes so that the
        in-progress animation endpoints can be expressed in absolute
        world space and later converted back to frame space via ``pop_position``.
        """
        self.start_pos = self.controller.anchor.calc_absolute_position_of(self.start_pos)
        self.end_pos = self.controller.anchor.calc_absolute_position_of(self.end_pos)

    def pop_position(self) -> None:
        """Convert stored absolute positions back to frame-space coordinates.

        Called after the anchor reference point has changed to restore the
        animation endpoints to the new frame coordinate system.
        """
        self.start_pos = self.controller.anchor.calc_frame_position_of_absolute(self.start_pos)
        self.end_pos = self.controller.anchor.calc_frame_position_of_absolute(self.end_pos)

    # ------------------------------------------------------------------
    # Pure position fly-to
    # ------------------------------------------------------------------

    def do_move(self, step: float) -> None:
        """Interpolation callback for a pure position fly-to animation.

        Linearly interpolates between ``start_pos`` and ``end_pos`` in
        frame space.  ``step`` is driven from 0 to 1 by the LerpFunc
        interval; easing is applied by the interval's blend type.
        """
        position = self.end_pos * step + self.start_pos * (1.0 - step)
        self.controller.set_frame_position(position)
        if step == 1.0:
            self.current_interval = None

    def move_to(self, new_pos: LPoint3d, absolute: bool = True, duration: float = 0, ease: bool = True) -> None:
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

    # ------------------------------------------------------------------
    # Time-limited continuous operation runner
    # ------------------------------------------------------------------

    def do_update_func(self, step: float, func: Callable, extra: Tuple) -> None:
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

    def update_func(self, func: Callable, duration: float = 0, extra: Tuple = ()) -> None:
        """Run *func(delta, *extra)* every frame for *duration* seconds.

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

    # ------------------------------------------------------------------
    # Combined position + rotation fly-to
    # ------------------------------------------------------------------

    def do_move_and_rot(self, step: float) -> None:
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

    def move_and_rotate_to(
        self,
        new_pos: LPoint3d,
        new_rot: LQuaterniond,
        absolute: bool = True,
        duration: float = 0,
        start_rotation: float = 0.0,
        end_rotation: float = 0.5,
    ) -> None:
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
