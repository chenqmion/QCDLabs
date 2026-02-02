import sys
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import pickle

sys.path.insert(0, '../../instrument/')
from RS.instr_FSV40 import FSV40
from Valon.instr_Valon5015 import Valon5015

sys.path.insert(0, '../../pattern/')
from double_conversion_mixer.instr_double_conversion_mixer import DuoMixer

#%%
if_frequency = 2e9
if_address = "10.0.100.31"
if1 = Valon5015(if_address)
if1.frequency(if_frequency)
if1.power(-30)

if1.output(1)

#%%
dr_frequency = 6.5e9
lo1_frequency = 8e9

lo1_address = "10.0.100.24"
lo2_address = ["10.0.100.32"]
drive = DuoMixer(lo1_address, lo2_address)

drive.set_lo1(frequency=lo1_frequency, power=17)
drive.set_frequency(idx=0, frequency=dr_frequency, if_frequency = if_frequency)
drive.set_lo2(idx=0, power=20)

drive.lo1.output(1)
drive.lo2[0].output(1)

#%%



# spec_address = "10.0.100.110"
# spec = N9928A(spec_address)
#
# f0 = 0.5e9
# f1 = 20.5e9
#
# spec.start_frequency(f0)
# spec.stop_frequency(f1)
# spec.if_frequency(1e3)
# spec.average(5, mode='sweep')
# spec.points(1001)
# spec.power(-10)
#
# #%% cable
# res_data0 = spec.get_trace()
#
# plt.figure()
# plt.plot(res_data0.frequency, 20*np.log10(np.abs(res_data0.data)))
# plt.show()
#
# #%% PD (without 50 load)
# res_data1 = spec.get_trace()
#
# #%% PD (with 50 load)
# res_data2 = spec.get_trace()
#
# #%%
# res = xr.concat([res_data0, res_data1, res_data2], dim='ctrl')
# res = res.assign_coords(ctrl=['cable', 'PD without load', 'PD with load'])
# # res.to_zarr('S21_PD.zarr')

#%%
# with xr.open_zarr("S21_PD.zarr") as f:
#     res = f['S21']

# with open('S21_PD.pkl', 'wb') as f:
#     pickle.dump(res, f, protocol=pickle.HIGHEST_PROTOCOL)

# with open("S21_PD.pkl", "rb") as f:
#     res = pickle.load(f)

# plt.figure()
# plt.plot(res.sel(ctrl='cable').frequency/1e9, 20*np.log10(np.abs(res.sel(ctrl='cable').data)))
# plt.plot(res.sel(ctrl='PD without load').frequency/1e9, 20*np.log10(np.abs(res.sel(ctrl='PD without load').data/res.sel(ctrl='cable').data)))
# plt.plot(res.sel(ctrl='PD with load').frequency/1e9, 20*np.log10(np.abs(res.sel(ctrl='PD with load').data/res.sel(ctrl='cable').data)))
#
# plt.xlim(0, 21)
# plt.xlabel('Frequency (GHz)')
#
# plt.ylim(-12, 0)
# plt.ylabel('S21 (dB)')
#
# plt.savefig('S21_PD.pdf', dpi=300)
# plt.show()