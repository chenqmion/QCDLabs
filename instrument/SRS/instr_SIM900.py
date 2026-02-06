import socket
import time
import numpy as np
import xarray as xr
# import pyvisa
import vxi11

import sys

# sys.path.insert(0, '../instrument/')
# from class_instr import instr

class SIM900():
    def __init__(self, ip_address, slot=1, port=23, buffer_size=4096, time_out=600, line_ending="\r"):

        inst_str = f"TCPIP::{ip_address}::gpib0,2::INSTR"
        self.inst = vxi11.Instrument(inst_str)
        self.inst.timeout = time_out
        self.line_ending = line_ending
        self.slot = slot
        self.name = f"SIM900 slot {self.slot}"

        self._voltage = None
        self._output = None

        self.inst.write("*CLS" + self.line_ending)
        self.inst.write(f"FLSH {slot}" + self.line_ending)
        idn = self.inst.ask("*IDN?" + self.line_ending)

    @property
    def status(self):
        params_dic = {}
        # params_dic['name'] = self.name
        params_dic['voltage'] = self._voltage
        params_dic['output'] = self._output
        return params_dic

    def _send_command(self, cmd):
        full_cmd = (cmd + self.line_ending )

        if ("?" in cmd):
            self.inst.write(f'SNDT {self.slot}, "{full_cmd}"')
            time.sleep(0.1)
            response = self.inst.ask(f'GETN? {self.slot}, 80'+self.line_ending)

            return response.strip()
        else:
            self.inst.write(f'SNDT {self.slot}, "{full_cmd}"')

    def output(self, flag_output=None, force_read = False):
        if (flag_output == 1) or (flag_output == True):
            str_output = "ON"
        else:
            str_output = "OF"

        command = "OP"
        if (flag_output != None):
            self._send_command(command + f"{str_output}")
            self._output = 1 if str_output == "ON" else 0
        else:
            return self._output

    def voltage(self, volt = None, force_read = False):
        command = "VOLT"
        if (volt != None):
            self._send_command(command + f" {volt:.3f}")
            self._voltage = volt
        else:
            if force_read or (self._voltage == None):
                response = self._send_command(command + "?")

                if response.startswith("#"):
                    header_digits = int(response[1])
                    offset = 2 + header_digits
                    response = response[offset:]
                    self._voltage = float(response)

            return self._voltage

    def slow_set(self, volt, dv = 0.01, dt = 1):
        if self.output == 0:
            volt_0 = self.voltage(0)
            self.output(1)

        volt_0 = self.voltage(force_read=True) # to be sure that self._voltage is correct

        if np.abs(volt - volt_0) <= dv:
            volt_list = [volt]
        else:
            if volt_0 > volt:
                dv = -dv
            volt_list = np.round(np.arange(volt, volt_0, -dv)[::-1],3)

        for val_volt in volt_list:
            self.voltage(val_volt)
            time.sleep(dt)

    def close(self):
        self.inst.close()
