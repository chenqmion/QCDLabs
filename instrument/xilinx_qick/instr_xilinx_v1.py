# import numpy as np
# from numpy.polynomial import Polynomial
# import matplotlib.ticker as mtick
# import matplotlib.pyplot as plt
# from matplotlib.ticker import MultipleLocator
#
# import xarray as xr

import os
import sys

from qick import AveragerProgram
from qick import NDAveragerProgram

driver_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, driver_path)

from class_drx import drx
from class_rox import rox
from class_sweep import sweep

class XilinxProg:
    import time

    reps = 1
    soft_avgs = 1
    expts = 1
    ddr4 = False
    mr = False

    # from helper_plot import *

    def __init__(self, name='rfsoc4x2_1', ip_address="10.0.100.21", port=8888, mode=AveragerProgram):
        from qick.pyro import make_proxy
        soc, soccfg = make_proxy(ns_host=ip_address, ns_port=port, proxy_name=name)
        print(soccfg)

        self.soc = soc
        self.soccfg = soccfg
        self.ip_address = ip_address
        self.port = port
        self.mode = mode

    # configuration
    @property
    def config(self):
        _cfg = {"reps": self.reps,
                "soft_avgs": self.soft_avgs,
                "expts": self.expts,
                "ddr4": self.ddr4,
                "mr": self.mr}
        _cfg |= self._config
        return _cfg

    def add(self, **kwargs):
        if (not hasattr(self, '_config')):
            self._config = {}
        self._config.update(kwargs)

    # data
    def acquire(self, load_pulses=True, progress=True):
        if (not hasattr(self, '_prog_cache')) or (self.config != self._prog_cache.cfg):
            if self.mode == 'AveragerProgram':
                from class_AveProg import Prog
                self._prog_cache = Prog(soccfg=self.soccfg, cfg=self.config)
            elif self.mode == 'NDAveragerProgram':
                from class_NDAveProg import NDProg
                self._prog_cache = NDProg(soccfg=self.soccfg, cfg=self.config)
        self.soc.reset_gens()  # clear any DC or periodic values on generators
        return self._prog_cache.acquire(self.soc, load_pulses=load_pulses, progress=progress)

    def acquire_decimated(self, load_pulses=True, progress=True):
        if self.mode == 'AveragerProgram':
            from class_AveProg import Prog
            self._prog_cache = Prog(soccfg=self.soccfg, cfg=self.config)
        elif self.mode == 'NDAveragerProgram':
            from class_NDAveProg import NDProg
            self._prog_cache = NDProg(soccfg=self.soccfg, cfg=self.config)
        self.soc.reset_gens()  # clear any DC or periodic values on generators
        return self._prog_cache.acquire_decimated(self.soc, load_pulses=load_pulses, progress=progress)
