import socket
import time
import numpy as np
import xarray as xr

import sys
sys.path.insert(0, '../instrument/')
from class_instr import instr

class FSV40(instr):
    def __init__(self, ip_address, port=5025, buffer_size=65536, time_out=3600, line_ending="\n"):
        super().__init__("FSV 40", ip_address, port=port, buffer_size=buffer_size, time_out=time_out)
        
        self._send_command('*IDN?')
        self._send_command('*CLS')
        self._send_command('SYST:ERR?')

        self._send_command('*RST')
        self._send_command('INST:SEL SA')

    # settings 
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
        command = "BAND:RES"
        if (freq_hz != None):
            response = self._send_command(command + f" {freq_hz:.3f} Hz")
        else:
            response = self._send_command(command + "?")
        return response

    def video_frequency(self, freq_hz = None):
        command = "BAND:VID"
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

    def average(self, n_ave = None):
        if n_ave is not None:
            self._send_command("AVERage:STATe ON")
        
        command = "AVERage:COUNt"
        if (n_ave != None):
            response = self._send_command(command + f" {n_ave:1d}")
        else:
            response = self._send_command(command + "?")
        return response

    def reference(self, ref_source = None):                
        command = ":SOURce:ROSCillator:SOURce"
        if (ref_source != None):
            response = self._send_command(command + f" {ref_source}")
        else:
            response = self._send_command(command + "?")
        return response
        
    def get_trace(self, normalize=False):
        self._send_command('TRACe1:MODE MAXH') 
        self._send_command('TRACe1:TYPE AVER')
        
        if normalize:
            self._send_command("UNIT:POW DBMH")
        else:
            self._send_command("UNIT:POW DBM")
        
        self._send_command('INIT:CONT OFF') 
        self._send_command('INIT:IMM') 

        self._send_command('*WAI')
        self._send_command('*OPC?')

        self._send_command('FORMat ASCii')
        trace_data = self._send_command(':TRAC:DATA? TRACE1')
        amplitudes = np.array([float(val) for val in trace_data.split(',')])
        
        center_frequency = float(self.center_frequency())
        span = float(self.span())
        n_points = len(amplitudes)
        frequencies = np.linspace(center_frequency - span/2, center_frequency + span/2, n_points)

        res_data = xr.DataArray(amplitudes,
                                coords=[frequencies],
                                dims=["frequency"],
                                name="spectrum")

        return res_data


