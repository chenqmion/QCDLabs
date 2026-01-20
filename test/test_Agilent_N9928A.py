import sys
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

sys.path.insert(0, '../instrument/')
from Agilent.instr_N9928A import N9928A

spec_address = "10.0.100.110"
spec = N9928A(spec_address)

f0 = 6.70e9

spec.center_frequency(f0)
spec.span(0.5e9)
spec.if_frequency(1e3)
spec.average(2, mode='sweep')
spec.points(1001)
spec.power(-30)

res_data = spec.get_trace()

plt.figure()
plt.plot(res_data.frequency, np.abs(res_data.data))
plt.show()
