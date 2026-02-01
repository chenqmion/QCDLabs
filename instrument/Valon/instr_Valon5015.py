import socket
import time
import re
import numpy as np

import sys
sys.path.insert(0, '../instrument/')
from class_instr import instr

class Valon5015(instr):
    def __init__(self, ip_address, port=23, buffer_size=1024, time_out=30, line_ending='\r'):
        super().__init__("Valon 5015", ip_address, port=port, buffer_size=buffer_size, time_out=time_out, line_ending=line_ending)

        self._frequency = None
        self._power = None

        self.output(False)
        self._send_command("?")

    # settings 
    def frequency(self, freq_hz = None):
        command = "FREQ"
        if (freq_hz != None):
            response = self._send_command(command + f" {int(np.round(freq_hz)):1d}")
            self._frequency = freq_hz
        else:
            if self._frequency == None:
                response = self._send_command(command + "?")
                response = re.search(r"F\s([\d\.]+)\s", response).group(1)
                self._frequency = float(response) * 1e6
            return self._frequency

    def power(self, power_dbm = None):
        command = "PWR"
        if (power_dbm != None):
            self._send_command(command + f" {power_dbm:.3f}")
            self._power = power_dbm
        else:
            if self._power == None:
                response = self._send_command(command + "?")
                response = re.search(r"PWR\s(-?[\d\.]+);", response).group(1)
                self._power = float(response)
            return self._power

    def reference(self, ref_source = None):
        if ref_source == 'EXT':
            _num = 1
        else:
            _num = 0
                
        command = "ReferenceSource"    
        if (ref_source != None):
            response = self._send_command(command + f" {_num:0d}")
        else:
            response = self._send_command(command + "?")
        return response

    def output(self, flag_output = None):
        if (flag_output == 1) or (flag_output == True):
            str_output = "ON"
            self.enable(True)
        else:
            str_output = "OFF"
        
        command = "OEN"    
        if (flag_output != None):
            response = self._send_command(command + f" {str_output}")
        else:
            response = self._send_command(command + "?")
        return response

    def enable(self, flag_enable = None):
        if (flag_enable == 1) or (flag_enable == True):
            str_enable = "ON"
        else:
            str_enable = "OFF"
        
        command = "PDN"    
        if (flag_enable != None):
            response = self._send_command(command + f" {str_enable}")
        else:
            response = self._send_command(command + "?")
        return response
    
    # functions        
    def get_status(self):
        return self._send_command("Status")
