from qick import *
from qick.averager_program import QickSweep, merge_sweeps

import numpy as np
from numpy.polynomial import Polynomial
import matplotlib.ticker as mtick
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

import xarray as xr

import os
import sys
sys.path.insert(0, '../station/')
# from xilinx_qick.class_drx import drx
# from xilinx_qick.class_rox import rox
# from xilinx_qick.class_sweep import sweep
import time

# from helper_plot import *

from double_conversion_mixer.instr_double_conversion_mixer import DuoMixer

#%%
lo1_address = "10.0.100.24"
lo2_address = ["10.0.100.32"]
drive = DuoMixer(lo1_address, lo2_address)

dr_frequency = 7e9
if_frequency = 3e9

drive.set_lo1(frequency=8e9, power=17)
drive.set_frequency(idx=0, frequency=dr_frequency, if_frequency = if_frequency)
drive.set_lo2(idx=0, power=20)

drive.lo1.output(1)
drive.lo2[0].output(1)

#%%
from qick.pyro import make_proxy
soc, soccfg = make_proxy(ns_host="10.0.100.21", ns_port=8888, proxy_name="rfsoc4x2_1")
print(soccfg)

ch = 1

dr_prog = QickProgram(soccfg)
dr_prog.declare_gen(ch=ch, nqz=1, ro_ch=ch)
dr_prog.set_pulse_registers(ch=ch,
                               freq=soccfg.freq2reg(if_frequency/1e6, gen_ch=ch, ro_ch=ch),
                               phase=0, gain=30000, mode='periodic',
                               style='const', length=10)
dr_prog.pulse(ch=ch)
dr_prog.end()

dr_prog.config_all(soc)
soc.tproc.start()

# ro_prog = QickProgram(soccfg)
# ro_prog.declare_readout(ch=0, freq=2000, length=soccfg.us2cycles(1), gen_ch=0, sel='product')
# ro_prog.trigger()
# ro_prog.end()
#
# ro_prog.config_all(soccfg)
# soc.tproc.start()

# soc.reset_gens()

