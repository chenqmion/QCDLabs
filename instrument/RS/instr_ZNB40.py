import socket
import time
import numpy as np
import xarray as xr
import sys

sys.path.insert(0, '../')
from class_instr import instr

class ZNB40(instr):
    port = 5025
    time_out = 3600
    buffer_size = 65536

    def __init__(self, ip_address, port=port, buffer_size=buffer_size, time_out=time_out):
        super().__init__("ZNB40", ip_address, port, buffer_size, time_out)

        self._start_frequency = None
        self._stop_frequency = None
        self._if_frequency = None
        self._power = None
        self._points = None
        self._average = None
        self._mode = None
        self._reference = self.reference(force_read=True)

        self._send_command('*IDN?')
        self._send_command('*CLS')
        self._send_command('*RST')

        self._send_command('INST:SEL "NA"')
        self._send_command('CALC:PAR1:DEF S21')

    @property
    def status(self):
        params_dic = {}
        # params_dic['name'] = self.name
        # params_dic['start_frequency'] = self._start_frequency
        # params_dic['stop_frequency'] = self._stop_frequency
        params_dic['if_frequency_hz'] = self._if_frequency
        params_dic['power_dbm'] = self._power
        params_dic['points'] = self._points
        params_dic['average'] = self._average
        params_dic['mode'] = self._mode
        params_dic['reference'] = self._reference
        return params_dic

    # settings
    def center_frequency(self, center_frequency_hz=None):
        command = "SENS:FREQ:CENT"
        if (center_frequency_hz != None):
            self._send_command(command + f" {center_frequency_hz:.3f} Hz")
            _start_frequency = self.start_frequency(force_read=True)
            _stop_frequency = self.stop_frequency(force_read=True)
        else:
            response = self._send_command(command + "?")
            return response

    def span(self, frequency_hz=None):
        command = "SENS:FREQ:SPAN"
        if (frequency_hz != None):
            self._send_command(command + f" {frequency_hz:.3f} Hz")
            _start_frequency = self.start_frequency(force_read=True)
            _stop_frequency = self.stop_frequency(force_read=True)
        else:
            response = self._send_command(command + "?")
            return response

    def start_frequency(self, start_frequency_hz=None, force_read=False):
        command = "SENS:FREQ:STARt"
        if (start_frequency_hz != None):
            self._send_command(command + f" {start_frequency_hz:.3f} Hz")
            self._start_frequency = start_frequency_hz
        else:
            if force_read or (self._start_frequency == None):
                response = self._send_command(command + "?")
                self._start_frequency = float(response)
            return self._start_frequency

    def stop_frequency(self, stop_frequency_hz=None, force_read=False):
        command = "SENS:FREQ:STOP"
        if (stop_frequency_hz != None):
            self._send_command(command + f" {stop_frequency_hz:.3f} Hz")
            self._stop_frequency = stop_frequency_hz
        else:
            if force_read or (self._stop_frequency == None):
                response = self._send_command(command + "?")
                self._stop_frequency = float(response)
            return self._stop_frequency

    def if_frequency(self, if_frequency_hz=None, force_read=False):
        command = "SENS:BWID"
        if (if_frequency_hz != None):
            self._send_command(command + f" {if_frequency_hz:.3f} Hz")
            self._if_frequency = if_frequency_hz
        else:
            if force_read or (self._if_frequency == None):
                response = self._send_command(command + "?")
                self._if_frequency = float(response)
            return self._if_frequency

    def power(self, power_dbm=None, force_read=False):
        command = "SOUR:POW"
        if (power_dbm != None):
            self._send_command(command + f" {power_dbm:.3f}")
            self._power = power_dbm
        else:
            if force_read or (self._power == None):
                response = self._send_command(command + "?")
                self._power = float(response)
            return self._power

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

    def average(self, n_ave=None, mode='sweep', force_read=False):
        if n_ave is not None:
            self._send_command("SENS:AVER:CLE")

        command = "SENS:AVER:COUN"
        if (n_ave != None):
            self._send_command(command + f" {n_ave:1d}")
            self._average = n_ave
        else:
            if force_read or (self._average == None):
                response = self._send_command(command + "?")
                self._average = int(response)

        if mode == 'point':
            command = "AVER:MODE POINT"
        else:
            command = "AVER:MODE SWEEP"

        if (n_ave != None):
            self._send_command(command)
            self._mode = mode
        else:
            if force_read or (self._average == None):
                response = self._send_command("AVER:MODE?")
                self._mode = response

        return [self._average, self._mode]

    def reference(self, ref_source=None, force_read=False):
        command = "SENS:ROSC:SOUR"
        if (ref_source != None):
            self._send_command(command + f" {ref_source}")
            self._reference = ref_source
        else:
            if force_read or (self._reference == None):
                response = self._send_command(command + "?")
                self._reference = response
            return self._reference

    # def get_trace(self):
    #     self._send_command('TRACe1:MODE MAXH')
    #     self._send_command('TRACe1:TYPE AVER')
    #
    #     self._send_command('INIT:CONT OFF')
    #     self._send_command('INIT:IMM')
    #
    #     self._send_command('*WAI')
    #     self._send_command('*OPC?')
    #
    #     self._send_command('FORMat ASCii')
    #     trace_data = self._send_command(':TRAC:DATA? SDATA')
    #     s_data = np.array([float(val) for val in trace_data.split(',')])
    #
    #     center_frequency = float(self.center_frequency())
    #     span = float(self.span())
    #     n_points = len(s_data)
    #     frequencies = np.linspace(center_frequency - span / 2, center_frequency + span / 2, n_points)
    #
    #     res_data = xr.DataArray(s_data,
    #                             coords=[frequencies],
    #                             dims=["frequency_hz"],
    #                             name="S21")
    #
    #     return res_data

    def get_trace(self):
        self._send_command('INIT:CONT 0')
        self._send_command("SENS:AVER:CLE")

        if self._send_command("AVER:MODE?") == 'SWE':
            for _ite in range(int(self._average)):
                self._send_command('INIT:IMM')
                self._send_command('*WAI')
                self._send_command('*OPC?')
        else:
            self._send_command('INIT:IMM')
            self._send_command('*WAI')
            self._send_command('*OPC?')

        self._send_command('FORMat ASCii')
        trace_data = self._send_command('CALCulate1:DATA? SDATa')
        s_raw = np.array([float(val) for val in trace_data.split(',')])

        s_data = s_raw[::2] + 1j * s_raw[1::2]

        center_frequency = float(self.center_frequency())
        span = float(self.span())
        n_points = len(s_data)
        frequencies = np.linspace(center_frequency - span / 2, center_frequency + span / 2, n_points)

        res_data = xr.DataArray(s_data,
                                coords=[frequencies],
                                dims=["frequency_hz"],
                                name="S21")

        return res_data