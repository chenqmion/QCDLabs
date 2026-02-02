import sys
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

sys.path.insert(0, '../pattern/')
from double_conversion_mixer.instr_double_conversion_mixer import DuoMixer

lo1_address = "10.0.100.24"
lo2_address = ["10.0.100.32"]
drive = DuoMixer(lo1_address, lo2_address)

drive.set_lo1(frequency=8e9, power=14)
drive.set_lo2(idx=0, frequency=12e9, power=14)
drive.set_frequency(idx=0, frequency=6.7e9, if_frequency = 3e9)

drive.lo1.output(1)
drive.lo2[0].output(1)