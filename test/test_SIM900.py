import sys
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

sys.path.insert(0, '../instrument/')
from SRS.instr_SIM900 import SIM900

sim_address = "10.0.100.113"
spec = SIM900(sim_address, slot=1)

# lo2_address = ["10.0.100.32"]
# lo2 = []
# try:
#     for ip2 in lo2_address:
#         print(ip2)
#         lo2.append(Valon5015(ip2))
# except:
#     print(lo2_address)
#     lo2.append(Valon5015(lo2_address))

# f0 = 6.70e9
#
# spec.center_frequency(f0)
# spec.span(0.5e9)
# spec.if_frequency(1e3)
# spec.average(2, mode='sweep')
# spec.points(1001)
# spec.power(-30)
#
# res_data = spec.get_trace()
#
# plt.figure()
# plt.plot(res_data.frequency, np.abs(res_data.data))
# plt.show()
