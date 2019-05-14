from __future__ import print_function
from __future__ import absolute_import

import time
from .astro.units import time_to_values, values_to_time
from .astro import jdcal

class Time(object):
    def __init__(self):
        self.multiplier = 1
        self.time_full = 0
        self.running = True

    def set_J2000_date(self):
        self.time_full = jdcal.MJD_0 + jdcal.MJD_JD2000
        
    def set_time(self, years, months, days, hours, mins, secs):
        self.time_full = values_to_time(years, months, days, hours, mins, secs)

    def set_time_jd(self, jd):
        self.time_full = jd

    def set_current_date(self):
        current = time.gmtime()
        self.set_time(current.tm_year, current.tm_mon, current.tm_mday, current.tm_hour, current.tm_min, current.tm_sec)

    def time_to_values(self):
        return time_to_values(self.time_full)

    def update_time(self, dt):
        if self.running:
            self.time_full += dt * self.multiplier / (24 * 3600)

    def set_timerate(self, multiplier):
        self.multiplier = multiplier

    def accelerate_time(self, factor):
        self.multiplier *= factor

    def slow_time(self, factor):
        self.multiplier /= factor

    def invert_time(self):
        self.multiplier = -self.multiplier

    def freeze(self):
        self.running = False

    def run(self):
        self.running = True

    def toggle_freeze_time(self):
        self.running = not self.running

    def set_real_time(self):
        self.running = True
        self.multiplier = 1.0

if __name__ == '__main__':
    timecal = Time()
    timecal.set_J2000_date()
    print("JD2000", timecal.time_full)
    print("Split", timecal.time_to_values())
    timecal.set_time(2000, 1, 1, 12, 0, 0)
    print("Set", timecal.time_full)
    print("Current", time.gmtime())
    timecal.set_current_date()
    print("Set", timecal.time_full)
    print("Split", timecal.time_to_values())
