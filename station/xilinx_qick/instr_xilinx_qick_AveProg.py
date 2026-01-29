# import numpy as np
# from numpy.polynomial import Polynomial
# import matplotlib.ticker as mtick
# import matplotlib.pyplot as plt
# from matplotlib.ticker import MultipleLocator
#
# import xarray as xr

import os
import sys
driver_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, driver_path)

from class_drx_v2 import drx
from class_rox import rox
from class_sweep import sweep

class XilinxAveProg:
    import time

    reps = 100
    soft_avgs = 1

    # from helper_plot import *

    def __init__(self, name='rfsoc4x2_1', ip_address="10.0.100.21", port=8888):
        from qick.pyro import make_proxy
        soc, soccfg = make_proxy(ns_host=ip_address, ns_port=port, proxy_name=name)
        print(soccfg)

        self.soc = soc
        self.soccfg = soccfg
        self.ip_address = ip_address
        self.port = port

    @property
    def config(self):
        _cfg = {"reps": self.reps,
                "soft_avgs": self.soft_avgs}
        _cfg.update(self._configsss)
        return _cfg

    def add(self, **kwargs):
        if (not hasattr(self, '_config')):
            self._config = {}
        self._config.update(kwargs)

    def acquire(self, load_pulses=True, progress=True):
        if (not hasattr(self, '_prog_cache')) or (self.config != self._prog_cache.cfg):
            from class_AveProg import Prog
            self._prog_cache = Prog(soccfg=self.soccfg, cfg=self.config)
        self.soc.reset_gens()  # clear any DC or periodic values on generators
        return self._prog_cache.acquire(self.soc, load_pulses=load_pulses, progress=progress)

    def acquire_decimated(self, load_pulses=True, progress=True):
        if (not hasattr(self, '_prog_cache')) or (self.config != self._prog_cache.cfg):
            from class_AveProg import Prog
            self._prog_cache = Prog(soccfg=self.soccfg, cfg=self.config)
        self.soc.reset_gens()  # clear any DC or periodic values on generators
        return self.self._prog_cache.acquire_decimated(self.soc, load_pulses=load_pulses, progress=progress)
