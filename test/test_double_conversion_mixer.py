import sys
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

sys.path.insert(0, '../station/')
from double_conversion_mixer.instr_double_conversion_mixer import DuoMixer

lo1_address = "10.0.100.24"
lo2_address = ["10.0.100.32"]
drive = DuoMixer(lo1_address, lo2_address)

drive.set_lo1(frequency=8e9, power=-10)
drive.set_lo2(idx=0, frequency=12e9, power=-10)
drive.set_if(idx=0, frequency=3e9)`