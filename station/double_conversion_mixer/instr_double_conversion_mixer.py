import sys
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

sys.path.insert(0, '../../instrument/')
from class_instr import instr
from RS.instr_FSV40 import FSV40
from Valon.instr_Valon5015 import Valon5015

class DuoMixer(instr):
    time_out = 3600
    buffer_size = 65536

    def __init__(self, ip_address1, ip_address2, buffer_size=buffer_size, time_out=time_out):
        super().__init__("N9928A", ip_address1, ip_address2)

        lo1 = Valon5015(ip_address1)
        lo2 = []
        try:
            for ip2 in ip_address2:
                lo2.append(Valon5015(ip2))
        except:
            lo2.append(Valon5015(ip_address2))

        self.lo1 = lo1
        self.lo2 = lo2

    def set_lo1(self, *, frequency=None, power=None):
        if not(frequency==None):
            self.lo1.frequency(frequency)
        if not (power == None):
            self.lo1.power(power)

    def set_lo2(self, *, idx=0, frequency=None, power=None):
        if not (frequency == None):
            self.lo2[idx].frequency(frequency)
        if not (power == None):
            self.lo2[idx].power(power)

    def set_if(self, *, idx=0, frequency=None):
        if not (frequency == None):
            freq2 = self.lo1.frequency() + np.floor(frequency) + 3
#
# lo1_address = '10.0.100.27'
# port = 23
# lo1 = Valon5015(lo1_address, port)
#
# lo2_address = '10.0.100.29'
# port = 23
# lo2 = Valon5015(lo2_address, port)
#
# if_address = '10.0.100.24'
# port = 23
# if_ = Valon5015(if_address, port)
#
# spec_address = "10.0.100.226"
# port = 5025
# spec = FSV40(spec_address, port)