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
rf.power(-30)
rf.output(1)

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
