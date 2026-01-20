import socket
import time
from class_instr import instr

class Valon5015(instr):
    port = 23
    time_out = 30
    buffer_size = 1024

    def __init__(self, ip_address, port=port, buffer_size=buffer_size, time_out=time_out):
        super().__init__("Valon 5015", ip_address, port=port, buffer_size=buffer_size, time_out=time_out)
        
        self.line_ending = "\r"
        
        self.output(False)

    # settings 
    def frequency(self, freq_hz = None):
        command = "FREQ"
        if (freq_hz != None):
            response = self._send_command(command + f" {freq_hz:.3f}")
        else:
            response = self._send_command(command + "?")
        return response

    def power(self, power_dbm = None):
        command = "Power"
        if (power_dbm != None):
            response = self._send_command(command + f" {power_dbm:.3f}")
        else:
            response = self._send_command(command + "?")
        return response

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
