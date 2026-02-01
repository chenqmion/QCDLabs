import sys
# import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import pickle
import itertools
from tqdm import tqdm

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QPushButton, QLabel, QGroupBox)
from PyQt5.QtCore import QTimer, Qt

sys.path.insert(0, '../../instrument/')
from Valon.instr_Valon5015 import Valon5015
from Agilent.instr_N9928A import N9928A
from RS.instr_FSV40 import FSV40

from virtual_instrument import VirtualInstrument

# #%%
# rf_address = "10.0.100.31"
# rf = Valon5015(rf_address)
#
# rf.frequency(8.428e9)
# rf.power(-30)
# rf.output(1)
#
# #%%
# spec_address = "10.0.100.110"
# spec = N9928A(spec_address)
#
# f0 = 0.48e9
# f1 = 0.55e9
#
# spec.start_frequency(f0)
# spec.stop_frequency(f1)
# spec.if_frequency(1e3)
# spec.average(1, mode='sweep')
# spec.points(1001)
# spec.power(-30)
#
# res_data0 = spec.get_trace()
#
# rf.output(0)
# res_data0.to_zarr('test_1.zarr', mode='w')
#
# with xr.open_zarr("test_1.zarr") as f:
#     res_data0 = f['S21']
#
# plt.figure()
# plt.plot(res_data0.frequency, 20*np.log10(np.abs(res_data0.data)))
# plt.show()
#
# # # plt.figure()
# # # plt.pcolormesh(res_mat.rf_frequency/1e9, res_mat.frequency, 20*np.log10(np.abs(res_mat.sel(rf_power=10))).T)
# # # plt.show()
# #
# # plt.figure()
# # plt.pcolormesh(res_mat.rf_frequency/1e9, res_mat.frequency, 20*np.log10(np.abs(res_mat.sum(dim='rf_power'))).T)
# # plt.show()

app = QApplication(sys.argv)

spec_address = "10.0.100.226"
spec = FSV40(spec_address)

f0 = 6.50e9

spec.center_frequency(f0)
spec.span(1e9)
spec.if_frequency(5e6)
spec.video_frequency(1e6)
spec.average(1)
spec.points(1001)

# res_data = spec.get_trace()

# 2. 启动界面
window = VirtualInstrument(spec)
window.show()
sys.exit(app.exec_())