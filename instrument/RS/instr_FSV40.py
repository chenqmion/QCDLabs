import socket
import time
import numpy as np
import xarray as xr

import sys
sys.path.insert(0, '../instrument/')
from class_instr import instr

class FSV40(instr):
    def __init__(self, ip_address, port=5025, buffer_size=65536, time_out=3600, line_ending="\n"):
        super().__init__("FSV 40", ip_address, port=port, buffer_size=buffer_size, time_out=time_out, line_ending=line_ending)

        self._start_frequency = None
        self._stop_frequency = None
        self._if_frequency = None
        self._video_frequency = None
        self._points = None
        self._average = None
        self._reference = None

        self._send_command('*IDN?')
        self._send_command('*CLS')
        self._send_command('SYST:ERR?')

        self._send_command('*RST')
        self._send_command('INST:SEL SA')

    @property
    def status(self):
        params_dic = {}
        # params_dic['name'] = self.name
        params_dic['start_frequency'] = self._start_frequency
        params_dic['stop_frequency'] = self._stop_frequency
        params_dic['if_frequency'] = self._if_frequency
        params_dic['video_frequency'] = self._video_frequency
        params_dic['points'] = self._points
        params_dic['average'] = self._average
        params_dic['reference'] = self._reference
        return params_dic

    # settings 
    def center_frequency(self, freq_hz = None):
        command = "SENS:FREQ:CENT"
        if (freq_hz != None):
            self._send_command(command + f" {freq_hz:.3f} Hz")
            _start_frequency = self.start_frequency(force_read=True)
            _stop_frequency = self.stop_frequency(force_read=True)
        else:
            response = self._send_command(command + "?")

            return response
        
    def span(self, freq_hz = None):
        command = "SENS:FREQ:SPAN"
        if (freq_hz != None):
            self._send_command(command + f" {freq_hz:.3f} Hz")
            _start_frequency = self.start_frequency(force_read=True)
            _stop_frequency = self.stop_frequency(force_read=True)
        else:
            response = self._send_command(command + "?")
            return response

    def start_frequency(self, freq_hz=None, force_read=False):
        command = "SENS:FREQ:STARt"
        if (freq_hz != None):
            self._send_command(command + f" {freq_hz:.3f} Hz")
            self._start_frequency = freq_hz
        else:
            if force_read or (self._start_frequency == None):
                response = self._send_command(command + "?")
                self._start_frequency = float(response)
            return self._start_frequency

    def stop_frequency(self, freq_hz=None, force_read=False):
        command = "SENS:FREQ:STOP"
        if (freq_hz != None):
            self._send_command(command + f" {freq_hz:.3f} Hz")
            self._stop_frequency = freq_hz
        else:
            if force_read or (self._stop_frequency == None):
                response = self._send_command(command + "?")
                self._stop_frequency = float(response)
            return self._stop_frequency
        
    def if_frequency(self, freq_hz = None, force_read=False):
        command = "BAND:RES"
        if (freq_hz != None):
            self._send_command(command + f" {freq_hz:.3f} Hz")
            self._if_frequency = freq_hz
        else:
            if force_read or (self._if_frequency == None):
                response = self._send_command(command + "?")
                self._if_frequency = float(response)
            return self._if_frequency

    def video_frequency(self, freq_hz = None, force_read=False):
        command = "BAND:VID"
        if (freq_hz != None):
            self._send_command(command + f" {freq_hz:.3f} Hz")
            self._video_frequency = freq_hz
        else:
            if force_read or (self._video_frequency == None):
                response = self._send_command(command + "?")
                self._video_frequency = float(response)
            return self._video_frequency

    def points(self, n_p=None, force_read=False):
        command = "SENS:SWE:POIN"
        if (n_p != None):
            self._send_command(command + f" {n_p:1d}")
            self._points = n_p
        else:
            if force_read or (self._points == None):
                response = self._send_command(command + "?")
                self._points = int(response)
            return self._points

    def average(self, n_ave = None, force_read=False):
        if n_ave is not None:
            self._send_command("AVERage:STATe ON")
        
        command = "AVERage:COUNt"
        if (n_ave != None):
            self._send_command(command + f" {n_ave:1d}")
            self._average = n_ave
        else:
            if force_read or (self._average == None):
                response = self._send_command(command + "?")
                self._average = int(response)
            return self._average

    def reference(self, ref_source = None, force_read=False):
        command = ":SOURce:ROSCillator:SOURce"
        if (ref_source != None):
            self._send_command(command + f" {ref_source}")
            self._reference = ref_source
        else:
            if force_read or (self._reference == None):
                response = self._send_command(command + "?")
                self._reference = response
            return self._reference
        
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
                                dims=["frequency_hz"],
                                name="spectrum")

        return res_data


