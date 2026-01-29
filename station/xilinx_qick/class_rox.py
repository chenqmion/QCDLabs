import numpy as np
from scipy.interpolate import make_interp_spline
from dataclasses import dataclass, field
from collections import namedtuple
from itertools import compress


@dataclass
class rox:
    soc: 'QickSoc'
    ro_ch: int
    frequency: float

    dr_ch: int = None
    delay: float = 0.1
    sleep: float = 1.0
    length: float = 0

    @property
    def delay_cyl(self):
        return np.round(self.soc.us2cycles(self.delay, ro_ch=self.ro_ch)).astype(int)

    @property
    def sleep_cyl(self):
        return np.round(self.soc.us2cycles(self.sleep, ro_ch=self.ro_ch)).astype(int)

    @property
    def length_cyl(self):
        return np.round(self.soc.us2cycles(self.length, ro_ch=self.ro_ch)).astype(int)

    def set(self, ro_ch=None, frequency=None, dr_ch=None, delay=None, sleep=None, length=None):
        if ro_ch != None: self.ro_ch = ro_ch
        if frequency != None: self.frequency = frequency
        if dr_ch != None: self.dr_ch = dr_ch
        if delay != None: self.delay = delay
        if sleep != None: self.sleep = sleep
        if length != None: self.length = length

