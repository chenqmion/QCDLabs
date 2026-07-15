import socket
import time
import re
import numpy as np

import sys
sys.path.insert(0, '../instrument/')
from class_instr import instr

class Valon5015(instr):
    def __init__(self, ip_address, port=23, buffer_size=1024, time_out=30, line_ending='\r'):
        super().__init__("Valon_5015", ip_address, port=port, buffer_size=buffer_size, time_out=time_out, line_ending=line_ending)

        self._frequency = None
        self._power = None
        self._output = None
        self._enable = None
        self._reference = None

        self.output(False)
        self._send_command("?")

    @property
    def status(self):
        params_dic = {}
        # params_dic['name'] = self.name
        params_dic['frequency_hz'] = self._frequency
        params_dic['power_dbm'] = self._power
        params_dic['output'] = self._output
        params_dic['enable'] = self._enable
        params_dic['reference'] = self._reference
        return params_dic

    # settings 
    def frequency(self, frequency_hz = None, force_read = False):
        command = "FREQ"
        if (frequency_hz != None):
            self._send_command(command + f" {int(np.round(frequency_hz)):1d}")
            self._frequency = frequency_hz
        else:
            if force_read or (self._frequency == None):
                response = self._send_command(command + "?")
                response = re.search(r"F\s([\d\.]+)\s", response).group(1)
                self._frequency = float(response) * 1e6
            return self._frequency

    def power(self, power_dbm = None, force_read = False):
        command = "PWR"
        if (power_dbm != None):
            self._send_command(command + f" {power_dbm:.3f}")
            self._power = power_dbm
        else:
            if force_read or (self._power == None):
                response = self._send_command(command + "?")
                response = re.search(r"PWR\s(-?[\d\.]+);", response).group(1)
                self._power = float(response)
            return self._power

    def reference(self, ref_source = None, force_read = False):
        if ref_source == 'EXT':
            _num = 1
        else:
            _num = 0
                
        command = "ReferenceSource"    
        if (ref_source != None):
            self._send_command(command + f" {_num:0d}")
            self._reference = 'EXT' if _num == 1 else 'INT'

        else:
            if force_read or (self._reference == None):
                response = self._send_command(command + "?")
                self._reference = response
            return self._reference

    def output(self, flag_output = None, force_read = False):
        if (flag_output == 1) or (flag_output == True):
            str_output = "ON"
            self.enable(True)
        else:
            str_output = "OFF"
        
        command = "OEN"    
        if (flag_output != None):
            self._send_command(command + f" {str_output}")
            self._output = str_output
        else:
            if force_read or (self._output == None):
                response = self._send_command(command + "?")
                self._output = float(response)
            return self._output

    def enable(self, flag_enable = None, force_read = False):
        if (flag_enable == 1) or (flag_enable == True):
            str_enable = "ON"
        else:
            str_enable = "OFF"
        
        command = "PDN"    
        if (flag_enable != None):
            self._send_command(command + f" {str_enable}")
            self._enable = str_enable
        else:
            if force_read or (self._enable == None):
                response = self._send_command(command + "?")
                self._enable = float(response)
            return self._enable

