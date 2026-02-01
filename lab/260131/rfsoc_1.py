import sys
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import pickle
from tqdm import tqdm

import os
import sys
sys.path.insert(0, '../../station/')
from xilinx_qick.class_drx import drx
from xilinx_qick.class_rox import rox
from xilinx_qick.class_sweep import sweep
from xilinx_qick.instr_xilinx_v1 import XilinxProg

from double_conversion_mixer.instr_double_conversion_mixer import DuoMixer

#%%
lo1_address = "10.0.100.24"
lo2_address = ["10.0.100.32"]
drive = DuoMixer(lo1_address, lo2_address)

dr_frequency = 4.5e9
if_frequency = 2.75e9
lo1_frequency = 8.25e9

drive.set_lo1(frequency=lo1_frequency, power=17)
drive.set_frequency(idx=0, frequency=dr_frequency, if_frequency = if_frequency)
drive.set_lo2(idx=0, power=10)

drive.lo1.output(1)
drive.lo2[0].output(1)

#%% rfsoc
xilinx_1 = XilinxProg(ip_address="10.0.100.21", mode='AveragerProgram')
xilinx_1.reps = 1000

dr_ch = 1
ro_ch = 1

#%% pulse
dr_readout = drx(soc=xilinx_1.soccfg,
                 dr_ch=dr_ch, ro_ch=ro_ch,
                 frequency=if_frequency / 1e6, gain=1,
                 phase=0, delay=0.2, sleep=1)

dr_readout.wave.add(name='x2', t_data=[0, 0.25, 0.5, 0.75, 1.0], s_data=[0, 1, 2, 1, 0], idx=-1, interp_order=3)
dr_readout.rox.set(frequency=if_frequency / 1e6, length=1, delay=0.2, sleep=1)
xilinx_1.add(dr_readout=dr_readout)

#%%
iq_mat = []
dr_freq_list = np.arange(6.75, 6.785+1e-6, 0.5e-3) * 1e9
for dr_frequency in tqdm(dr_freq_list):
    drive.set_frequency(idx=0, frequency=dr_frequency, if_frequency=if_frequency)

    iq_data = xilinx_1.acquire(load_pulses=True, progress=False)
    iq_mat.append(iq_data)

iq_mat = xr.concat(iq_mat, dim=xr.DataArray(dr_freq_list, name='frequency', dims='frequency'))
iq_mat = iq_mat.transpose(..., "frequency")
iq_mat.to_zarr('test_1.zarr', mode='w')

drive.lo1.output(0)
drive.lo2[0].output(0)

with xr.open_zarr("test_1.zarr") as f:
    iq_mat = f['IQ accumulated']

plt.figure()
plt.plot(dr_freq_list/1e9, 20*np.log10(np.abs(iq_mat.sel(rox=1, reps=1))), '.-')
plt.xlim(6.75, 6.785)
plt.show()