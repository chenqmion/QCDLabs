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

        self.name = name

        self.soc = soc
        self.soccfg = soccfg
        self.ip_address = ip_address
        self.port = port
        self.mode = mode

    # def register_sweep(self, fun):
    #     self._sweep_fun = fun
    #
    # def sweep(self, **kwargs):
    #     return self._sweep_fun(self, **kwargs)

    def register_sweep(self, fun, **defaults):
        if not hasattr(self, "_sweep_fun"):
            self._sweep_fun = {}

        for name, value in defaults.items():
            self._sweep_fun[name] = fun
            setattr(self, name, value)

    def sweep(self, **kwargs):
        fun_dict = {}

        for name, value in kwargs.items():
            fun = self._sweep_fun[name]
            fun_dict.setdefault(fun, {})
            fun_dict[fun][name] = value

        for fun, args in fun_dict.items():
            fun(self, **args)

    @property
    def status(self):
        params_dic = {}
        # params_dic['name'] = self.name
        # params_dic['start_frequency'] = self._start_frequency
        # params_dic['stop_frequency'] = self._stop_frequency
        # params_dic['if_frequency'] = self._if_frequency
        # params_dic['video_frequency'] = self._video_frequency
        # params_dic['points'] = self._points
        # params_dic['average'] = self._average
        # params_dic['reference'] = self._reference
        return params_dic

    # configuration
    @property
    def config(self):
        _cfg = {"reps": self.reps,
                "soft_avgs": self.soft_avgs,
                "expts": self.expts,
                "ddr4": self.ddr4,
                "mr": self.mr}

        if (hasattr(self, '_config')):
            _cfg |= self._config

        return _cfg

    def add(self, **kwargs):
        if (not hasattr(self, '_config')):
            self._config = {}

        self._config.update(kwargs)

    # data
    def test(self, load_pulses=True, progress=False):
        if (not hasattr(self, '_prog_cache')) or (self.config != self._prog_cache.cfg):
            if self.mode == 'AveragerProgram':
                from class_AveProg import Prog
                self._prog_cache = Prog(soccfg=self.soccfg, cfg=self.config)
        self.soc.reset_gens()  # clear any DC or periodic values on generators
        return self._prog_cache.test(self.soc, load_pulses=load_pulses, progress=progress)

    def acquire(self, load_pulses=True, progress=False):
        if (not hasattr(self, '_prog_cache')) or (self.config != self._prog_cache.cfg):
            if self.mode == 'AveragerProgram':
                from class_AveProg import Prog
                self._prog_cache = Prog(soccfg=self.soccfg, cfg=self.config)
            elif self.mode == 'NDAveragerProgram':
                from class_NDAveProg import NDProg
                self._prog_cache = NDProg(soccfg=self.soccfg, cfg=self.config)
        self.soc.reset_gens()  # clear any DC or periodic values on generators
        return self._prog_cache.acquire(self.soc, load_pulses=load_pulses, progress=progress)

    def acquire_decimated(self, load_pulses=True, progress=False):
        if self.mode == 'AveragerProgram':
            from class_AveProg import Prog
            self._prog_cache = Prog(soccfg=self.soccfg, cfg=self.config)
        elif self.mode == 'NDAveragerProgram':
            from class_NDAveProg import NDProg
            self._prog_cache = NDProg(soccfg=self.soccfg, cfg=self.config)
        self.soc.reset_gens()  # clear any DC or periodic values on generators
        return self._prog_cache.acquire_decimated(self.soc, load_pulses=load_pulses, progress=progress)
