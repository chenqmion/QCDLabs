import numpy as np
from scipy.interpolate import make_interp_spline
from dataclasses import dataclass, field
from functools import cached_property
from collections import namedtuple
from itertools import compress
from pathlib import Path
import sys
import os

class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, class_path)

from class_wave import wave
from class_rox import rox

@dataclass
class drx:
    soc: 'QickSoc'
    dr_ch: int
    frequency: float
    gain: float

    ro_ch: int = None

    phase: float = 0.0
    delay: float = 0.0
    sleep: float = 0.0
    length_cyl: int = 0

    @property
    def maxv(self):
        return np.round(self.soc.get_maxv(gen_ch=self.dr_ch) * self.gain).astype(int)

    @property
    def maxdbm(self):
        return 20 * np.log10(self.gain) - 10

    @property
    def phase_cyl(self):
        return self.soc.deg2reg(self.phase, gen_ch=self.dr_ch)

    @property
    def delay_cyl(self):
        return np.round(self.soc.us2cycles(self.delay, gen_ch=self.dr_ch)).astype(int)

    @property
    def sleep_cyl(self):
        return np.round(self.soc.us2cycles(self.sleep, gen_ch=self.dr_ch)).astype(int)

    @property
    def frequency_cyl(self):
        return self.soc.freq2reg(self.frequency, gen_ch=self.dr_ch, ro_ch=self.ro_ch)

    @cached_property
    def wave(self):
        return wave(self.soc, self.dr_ch, self.maxv)

    @cached_property
    def rox(self):
        return rox(self.soc, self.ro_ch, self.frequency, self.dr_ch)