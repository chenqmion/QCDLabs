import sys
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import pickle
import itertools
from tqdm import tqdm

sys.path.insert(0, '../../instrument/')
from Valon.instr_Valon5015 import Valon5015
from Agilent.instr_N9928A import N9928A

#%%
rf_address = "10.0.100.31"
rf = Valon5015(rf_address)

rf.frequency(8.428e9)
rf.power(-10)
rf.output(1)

# rf.output(0)

#%%
spec_address = "10.0.100.110"
spec = N9928A(spec_address)

f0 = 0.48e9
f1 = 0.55e9

spec.start_frequency(f0)
spec.stop_frequency(f1)
spec.if_frequency(1e3)
spec.average(1, mode='sweep')
spec.points(1001)
spec.power(-30)

res_data0 = spec.get_trace()

plt.figure()
plt.plot(res_data0.frequency, 20*np.log10(np.abs(res_data0.data)))
plt.show()

#%% cable
rf_power_list = np.arange(-10, 0+1e-6, 5)
rf_freq_list = np.arange(8.31e9, 8.55e9+1e-6, 10e6)

res_mat2 = []
for rf_power in tqdm(rf_power_list):
    res_mat = []
    for rf_freq in rf_freq_list:
        rf.frequency(rf_freq)
        rf.power(rf_power)
        res_data = spec.get_trace()
        res_mat.append(res_data)

    res_mat = xr.concat(res_mat, dim=xr.DataArray(rf_freq_list, name='rf_frequency', dims='rf_frequency'))
    res_mat2.append(res_mat)
res_mat2 = xr.concat(res_mat2, dim=xr.DataArray(rf_power_list, name='rf_power', dims='rf_power'))

rf.output(0)
res_mat2.to_zarr('test_1.zarr', mode='w')

with xr.open_zarr("test_1.zarr") as f:
    res_mat = f['S21']

# plt.figure()
# plt.pcolormesh(res_mat.rf_frequency/1e9, res_mat.frequency, 20*np.log10(np.abs(res_mat.sel(rf_power=10))).T)
# plt.show()

plt.figure()
plt.pcolormesh(res_mat.rf_frequency/1e9, res_mat.frequency, 20*np.log10(np.abs(res_mat.sum(dim='rf_power'))).T)
plt.show()

# spec.power(-20)
# res_data1 = spec.get_trace()
#
# spec.power(-10)
# res_data2 = spec.get_trace()

# plt.figure()
# plt.plot(res_data0.frequency, 20*np.log10(np.abs(res_data0.data)))
# plt.plot(res_data1.frequency, 20*np.log10(np.abs(res_data1.data)))
# plt.plot(res_data2.frequency, 20*np.log10(np.abs(res_data2.data)))
# plt.show()

# res = xr.concat([res_data0, res_data1, res_data2], dim='ctrl')
# res = res.assign_coords(ctrl=['-10dBm', '0dBm', '10dBm'])
# res.to_zarr('S21_300_500.zarr')

# res_data0.to_zarr('S21_5d5GHz_1.zarr')

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
#
# #%%
# with xr.open_zarr("S21_PD.zarr") as f:
#     res = f['S21']
#
# # with open('S21_PD.pkl', 'wb') as f:
# #     pickle.dump(res, f, protocol=pickle.HIGHEST_PROTOCOL)
#
# # with open("S21_PD.pkl", "rb") as f:
# #     res = pickle.load(f)
#
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