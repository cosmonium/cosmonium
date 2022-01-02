#include <math.h>

double
EllipticalOrbit::get_period(void)
{
  return 2 * M_PI / mean_motion;
}

void
EllipticalOrbit::set_period(double period)
{
  mean_motion =  2 * M_PI / period;
}

double
EllipticalOrbit::get_argument_of_periapsis(void)
{
  return argument_of_periapsis;
}

void
EllipticalOrbit::set_argument_of_periapsis(double argument_of_periapsis)
{
  this->argument_of_periapsis = argument_of_periapsis;
  update_rotation();
}

double
EllipticalOrbit::get_inclination(void)
{
  return inclination;
}

void
EllipticalOrbit::set_inclination(double inclination)
{
  this->inclination = inclination;
  update_rotation();
}

double
EllipticalOrbit::get_ascending_node(void)
{
  return ascending_node;
}

void
EllipticalOrbit::set_ascending_node(double ascending_node)
{
  this->ascending_node = ascending_node;
  update_rotation();
}

double
EllipticalOrbit::get_epoch(void)
{
  return epoch;
}

void
EllipticalOrbit::set_epoch(double epoch)
{
  this->epoch = epoch;
}

void
EllipticalOrbit::set_mean_motion(double mean_motion)
{
  this->mean_motion = mean_motion;
}

double
EllipticalOrbit::get_mean_anomaly(void)
{
  return mean_anomaly;
}

void
EllipticalOrbit::set_mean_anomaly(double mean_anomaly)
{
  this->mean_anomaly = mean_anomaly;
}

double
EllipticalOrbit::get_pericenter_distance(void)
{
  return pericenter_distance;
}

void
EllipticalOrbit::set_pericenter_distance(double pericenter_distance)
{
  this->pericenter_distance = pericenter_distance;
}

double
EllipticalOrbit::get_eccentricity(void)
{
  return eccentricity;
}

void
EllipticalOrbit::set_eccentricity(double eccentricity)
{
  this->eccentricity = eccentricity;
}
