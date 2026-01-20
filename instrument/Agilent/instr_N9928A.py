import socket
import time
import numpy as np
import xarray as xr
import sys

sys.path.insert(0, '../')
from class_instr import instr

class N9928A(instr):
    port = 5025
    time_out = 3600
    buffer_size = 65536

    def __init__(self, ip_address, port=port, buffer_size=buffer_size, time_out=time_out):
        super().__init__("N9928A", ip_address, port, buffer_size, time_out)

        self._send_command('*IDN?')
        self._send_command('*CLS')
        self._send_command('*RST')

        self._send_command('INST:SEL "NA"')
        self._send_command('CALC:PAR1:DEF S21')

    # settings
    def power(self, P_dbm=None):
        command = "SOUR:POW"
        if (P_dbm != None):
            response = self._send_command(command + f" {P_dbm:.3f}")
        else:
            response = self._send_command(command + "?")
        return response

    def center_frequency(self, freq_hz = None):
        command = "SENS:FREQ:CENT"
        if (freq_hz != None):
            response = self._send_command(command + f" {freq_hz:.3f} Hz")
        else:
            response = self._send_command(command + "?")
        return response
        
    def span(self, freq_hz = None):
        command = "SENS:FREQ:SPAN"
        if (freq_hz != None):
            response = self._send_command(command + f" {freq_hz:.3f} Hz")
        else:
            response = self._send_command(command + "?")
        return response
        
    def if_frequency(self, freq_hz = None):
        command = "SENS:BWID"
        if (freq_hz != None):
            response = self._send_command(command + f" {freq_hz:.3f} Hz")
        else:
            response = self._send_command(command + "?")
        return response

    def start_frequency(self, freq_hz = None):
        command = "SENS:FREQ:STARt"
        if (freq_hz != None):
            response = self._send_command(command + f" {freq_hz:.3f} Hz")
        else:
            response = self._send_command(command + "?")
        return response
        
    def stop_frequency(self, freq_hz = None):
        command = "SENS:FREQ:STOP"
        if (freq_hz != None):
            response = self._send_command(command + f" {freq_hz:.3f} Hz")
        else:
            response = self._send_command(command + "?")
        return response

    def points(self, n_p=None):
        command = "SENS:SWE:POIN"
        if (n_p != None):
            response = self._send_command(command + f" {n_p:1d}")
        else:
            response = self._send_command(command + "?")
        return response

    def average(self, n_ave = None, mode='sweep'):
        if n_ave is not None:
            self._send_command("SENS:AVER:CLE")

        response = []

        command = "SENS:AVER:COUN"
        if (n_ave != None):
            response.append(self._send_command(command + f" {n_ave:1d}"))
        else:
            response.append(self._send_command(command + "?"))

        if mode == 'point':
            command = "AVER:MODE POINT"
        else:
            command = "AVER:MODE SWEEP"

        if (n_ave != None):
            response.append(self._send_command(command))
        else:
            response.append(self._send_command("AVER:MODE?"))

        return response

    def reference(self, ref_source = None):                
        command = "SENS:ROSC:SOUR"
        if (ref_source != None):
            response = self._send_command(command + f" {ref_source}")
        else:
            response = self._send_command(command + "?")
        return response
        
    def get_trace(self):
        self._send_command('INIT:CONT 0')
        self._send_command("SENS:AVER:CLE")

        if self._send_command("AVER:MODE?") == 'SWE':
            for _ite in range(int(self.average()[0])):
                self._send_command('INIT:IMM')
                self._send_command('*WAI')
                self._send_command('*OPC?')
        else:
            self._send_command('INIT:IMM')
            self._send_command('*WAI')
            self._send_command('*OPC?')

        self._send_command('FORMat ASCii')
        trace_data = self._send_command(':CALC:DATA:SDAT?')
        s_raw = np.array([float(val) for val in trace_data.split(',')])

        s_data = s_raw[::2] + 1j*s_raw[1::2]

        center_frequency = float(self.center_frequency())
        span = float(self.span())
        n_points = len(s_data)
        frequencies = np.linspace(center_frequency - span/2, center_frequency + span/2, n_points)

        res_data = xr.DataArray(s_data,
                                coords = [frequencies],
                                dims = ["frequency"],
                                name = "S21")

        return res_data

