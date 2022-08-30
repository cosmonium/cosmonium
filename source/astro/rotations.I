#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif


void
UniformRotation::set_period(double period)
{
  mean_motion =  2 * M_PI / period;
}


LQuaterniond
UniformRotation::get_equatorial_orientation(void)
{
  return equatorial_orientation;
}


void
UniformRotation::set_equatorial_orientation(LQuaterniond equatorial_orientation)
{
  this->equatorial_orientation = equatorial_orientation;
}


double
UniformRotation::get_mean_motion(void)
{
  return mean_motion;
}


void
UniformRotation::set_mean_motion(double mean_motion)
{
  this->mean_motion = mean_motion;
}


double
UniformRotation::get_meridian_angle(void)
{
  return meridian_angle;
}


void
UniformRotation::set_meridian_angle(double meridian_angle)
{
  this->meridian_angle = meridian_angle;
}


double
UniformRotation::get_epoch(void)
{
  return epoch;
}


void
UniformRotation::set_epoch(double epoch)
{
  this->epoch = epoch;
}

LQuaterniond
SynchronousRotation::get_equatorial_orientation(void)
{
  return equatorial_orientation;
}


void
SynchronousRotation::set_equatorial_orientation(LQuaterniond equatorial_orientation)
{
  this->equatorial_orientation = equatorial_orientation;
}


double
SynchronousRotation::get_meridian_angle(void)
{
  return meridian_angle;
}


void
SynchronousRotation::set_meridian_angle(double meridian_angle)
{
  this->meridian_angle = meridian_angle;
}


double
SynchronousRotation::get_epoch(void)
{
  return epoch;
}


void
SynchronousRotation::set_epoch(double epoch)
{
  this->epoch = epoch;
}
