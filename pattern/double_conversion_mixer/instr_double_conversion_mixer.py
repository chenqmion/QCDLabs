import sys
import os
import time

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

station_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
instrument_path = os.path.join(os.path.dirname(station_path), "instrument")

sys.path.insert(0, station_path)
sys.path.insert(0, instrument_path)

from class_instr import instr
from RS.instr_FSV40 import FSV40
from Valon.instr_Valon5015 import Valon5015

class DuoMixer:
    time_out = 30
    buffer_size = 1024
    name = 'DuoMixer'

    def __init__(self, ip_address1, ip_address2, buffer_size=buffer_size, time_out=time_out):
        lo1 = Valon5015(ip_address1, buffer_size=buffer_size, time_out=time_out)
        lo2 = []
        try:
            for ip2 in ip_address2:
                print(ip2)
                lo2.append(Valon5015(ip2, buffer_size=buffer_size, time_out=time_out))
        except:
            print(ip_address2)
            lo2.append(Valon5015(ip_address2, buffer_size=buffer_size, time_out=time_out))

        self.lo1 = lo1
        self.lo2 = lo2

        self._set_frequency = None
        # self._lo1_frequency = None
        # self._lo2_frequency = None
        self._if_frequency = None

    @property
    def status(self):
        params_dic = {}
        # params_dic['name'] = self.name
        params_dic['set_frequency_hz'] = self._set_frequency
        # params_dic['lo1_frequency'] = self._lo1_frequency
        # params_dic['lo2_frequency'] = self._lo2_frequency
        params_dic['if_frequency_hz'] = self._if_frequency
        return params_dic

    def set_reference(self, ref_source=None):
        self.lo1.reference(ref_source = ref_source, force_read = False)
        for _lo2 in self.lo2:
            _lo2.reference(ref_source = ref_source, force_read=False)

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

    def set_frequency(self, *, idx=0, set_frequency_hz=None, if_frequency_hz=None):
        if not (set_frequency_hz == None):
            if not (if_frequency_hz == None):
                self._if_frequency = if_frequency_hz

            freq2 = self.lo1.frequency() + np.floor(set_frequency_hz) + self._if_frequency
            self.lo2[idx].frequency(freq2)
            # self.frequency = freq2

            self._set_frequency = set_frequency_hz

            time.sleep(0.01)

        return self._set_frequency
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