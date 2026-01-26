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
    delay: float = 0.0
    sleep: float = 0.0
    length: float = 0
    waveforms: list = field(default_factory=list)

    @property
    def delay_cyl(self):
        return np.round(self.soc.us2cycles(self.delay, ro_ch=self.ro_ch)).astype(int)

    @property
    def sleep_cyl(self):
        return np.round(self.soc.us2cycles(self.sleep, ro_ch=self.ro_ch)).astype(int)

    @property
    def length_cyl(self):
        return np.round(self.soc.us2cycles(self.length, ro_ch=self.ro_ch)).astype(int)
