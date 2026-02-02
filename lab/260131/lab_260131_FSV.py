import sys
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import pickle
import itertools
from tqdm import tqdm

from qick import *
from qick.averager_program import QickSweep, merge_sweeps

sys.path.insert(0, '../../instrument/')
from Valon.instr_Valon5015 import Valon5015
from Agilent.instr_N9928A import N9928A
from RS.instr_FSV40 import FSV40

import sys
sys.path.insert(0, '../../pattern/')
from xilinx_qick.class_drx import drx
from xilinx_qick.class_rox import rox
from xilinx_qick.class_sweep import sweep
import time

from double_conversion_mixer.instr_double_conversion_mixer import DuoMixer

#%% converter
lo1_address = "10.0.100.24"
lo2_address = ["10.0.100.32"]
drive = DuoMixer(lo1_address, lo2_address)

dr_frequency = 8.5e9
lo1_frequency = 8.4e9
if_frequency = 2.8e9

drive.set_lo1(frequency=lo1_frequency, power=17)
drive.set_frequency(idx=0, frequency=dr_frequency, if_frequency = if_frequency)
drive.set_lo2(idx=0, power=12)

drive.lo1.output(1)
drive.lo2[0].output(1)

#%% xilinx
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

#%% spectrum analyzer
spec_address = "10.0.100.226"
spec = FSV40(spec_address)

f0 = 0.5e9
f1 = 20e9

spec.start_frequency(f0)
spec.stop_frequency(f1)
spec.if_frequency(5e6)
spec.video_frequency(1e6)
spec.average(10)
spec.points(10001)
res_data = spec.get_trace()

#%%
drive.lo1.output(0)
drive.lo2[0].output(0)
soc.reset_gens()

res_data.to_zarr('test_2_2.zarr', mode='w')

with xr.open_zarr("test_2_2.zarr") as f:
    res_data = f['spectrum']

# res_data.to_netcdf('my_data.nc', engine='h5netcdf', invalid_netcdf=True)
#
# res_data = xr.open_dataarray('my_data.nc', engine='h5netcdf')

plt.figure()
plt.plot(res_data.frequency, res_data.data)
# plt.vlines(7*if_frequency-lo1_frequency, -50, -15, color='red')
# plt.vlines(-5*if_frequency+3*lo1_frequency, -50, -15, color='red')
# plt.vlines(4*if_frequency, -50, -15, color='green')
# plt.vlines(-2*if_frequency+2*lo1_frequency, -50, -15, color='green')

plt.vlines(dr_frequency, -80, 0, color='red', linewidth=20, alpha=0.1)
plt.show()

