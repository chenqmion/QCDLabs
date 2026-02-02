from qick import *
from qick.averager_program import QickSweep, merge_sweeps

import numpy as np
from numpy.polynomial import Polynomial
import matplotlib.ticker as mtick
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

import xarray as xr

import os
import sys
sys.path.insert(0, '../pattern/')
from xilinx_qick.class_drx_v2 import drx
from xilinx_qick.class_rox import rox
from xilinx_qick.class_sweep import sweep

from helper_plot import *

from double_conversion_mixer.instr_double_conversion_mixer import DuoMixer

#%%
lo1_address = "10.0.100.24"
lo2_address = ["10.0.100.32"]
drive = DuoMixer(lo1_address, lo2_address)

dr_frequency = 4.5e9
if_frequency = 3e9

drive.set_lo1(frequency=8e9, power=17)
drive.set_frequency(idx=0, frequency=dr_frequency, if_frequency = if_frequency)
drive.set_lo2(idx=0, power=20)

drive.lo1.output(1)
drive.lo2[0].output(1)

#%%
from qick.pyro import make_proxy
soc, soccfg = make_proxy(ns_host="10.0.100.21", ns_port=8888, proxy_name="rfsoc4x2_1")
print(soccfg)

class PulseSequence(NDAveragerProgram):
    def initialize_phases(self):
        self.phase_ref_q1 = 0

    def play_seq(self):
        cfg = self.cfg
        for dr_name in self.dr_names:
            dr = cfg[dr_name]
            for waveform in dr.wave.items:
                self.set_pulse_registers(ch=dr.dr_ch,
                                         waveform=waveform.name,
                                         phrst=0,
                                         mode="oneshot")
                self.pulse(ch=dr.dr_ch)

        #modified sync_all with only DAC clocks, no ADC clocks
        self.synci(self.us2cycles(0.01))

    def initialize(self):
        cfg = self.cfg
        self.dr_names = []
        self.ro_chns = []
        self.sw_names = []
        for val_key, val_x in cfg.items():
            if val_key[:3] == 'dr_':
                self.dr_names.append(val_key)
                self.declare_gen(ch=val_x.dr_ch, nqz=1)
                self.default_pulse_registers(ch=val_x.dr_ch,
                                             freq=val_x.frequency_cyl,
                                             gain=val_x.maxv,
                                             phase=val_x.phase_cyl,
                                             style='arb')

                for waveform in val_x.wave.items:
                    self.add_pulse(ch=val_x.dr_ch,
                                   name=waveform.name,
                                   idata=waveform.i_data,
                                   qdata=waveform.q_data)

                if val_x.rox.length != 0:
                    self.ro_chns.append(val_x.ro_ch)
                    self.declare_readout(ch=val_x.ro_ch,
                                         length=val_x.rox.length_cyl,
                                         freq=val_x.rox.frequency,
                                         gen_ch=val_x.dr_ch)

            elif val_key[:3] == 'ro_':
#                 print('x', val_x.ro_ch, val_x.frequency)
                self.ro_chns.append(val_x.ro_ch)
                self.declare_readout(ch=val_x.ro_ch,
                                 length=val_x.length_cyl,
                                 freq=val_x.frequency,
                                 gen_ch=val_x.dr_ch)

            elif val_key[:3] == 'sw_':
                self.sw_names.append(val_key)

                sws = []
                for val_sw in val_x.items:
                    var_name = 'sw_' + str(val_sw.dr_ch) + '_' + val_sw.var
                    setattr(self, var_name, self.get_gen_reg(val_sw.dr_ch, val_sw.var))
                    sws.append(QickSweep(self, getattr(self, var_name),
                                     val_sw.start, val_sw.stop, val_sw.expts))
                self.add_sweep(merge_sweeps(sws))

        self.trigger(ddr4=cfg['ddr4'],
                     mr=cfg['mr'],
                     adc_trig_offset=self.us2cycles(self.cfg["adc_trig_offset"]))

        self.synci(1000)  # give processor some time to configure pulses

    def body(self):
        cfg = self.cfg
        self.trigger(adcs=self.ro_chns,
                     pins=[0],
                     adc_trig_offset=self.us2cycles(self.cfg["adc_trig_offset"]))

        self.initialize_phases()
        self.play_seq()
        self.wait_all()
        self.sync_all(self.us2cycles(self.cfg["relax_delay"]))

    #%% data
    def acquire(self, soc, load_pulses=True, progress=True):
        cfg = self.cfg
        expt_pts, avg_di, avg_dq = super().acquire(soc, load_pulses=load_pulses, progress=progress)

        _coords = [np.array(['I', 'Q'], dtype=str),  self.ro_chns, [1]]
        _dims = ["quadrature", "rox", "reps"]

        for _num, val_key in enumerate(self.sw_names[::-1]):
            _coords.append(np.unique(expt_pts[::-1][_num]))
            _dims.append(val_key[3:])

        res_data = xr.DataArray([avg_di, avg_dq],
                                coords=_coords,
                                dims=_dims,
                                name="IQ accumulated")
        return res_data

    def acquire_decimated(self, soc, load_pulses=True, progress=True):
        cfg = self.cfg
        iq_list = super().acquire_decimated(soc, progress=progress)
        iq_dims = np.shape(iq_list)
        res_data = xr.DataArray(iq_list,
                                coords=[np.arange(0, len(self.ro_chns), 1), np.arange(0, iq_dims[1], 1), np.array(['I', 'Q'])],
                                dims=["rox", "ticks", "quadrature"],
                                name="IQ decimated")

        return res_data

#%%
config = {"adc_trig_offset": 0.2,
          "reps": 100,
          "soft_avgs": 1,
          "expts": 1,
          "relax_delay": 1,
          "ddr4": False, # full decimated data
          "mr": False # dds data
         }

dr_qubit = drx(soc=soccfg, dr_ch=0, ro_ch=0, frequency=dr_frequency/1e6, gain=0.5, phase=0, delay=0, sleep=0)
dr_qubit.wave.add(name='x1', t_data=[0,0.25,0.5, 0.75, 1.0], s_data=[0,1,2,1,0], idx=-1, interp_order=3)
dr_qubit.rox.set(frequency=dr_frequency/1e6, length=1, delay=0, sleep=0)
config['dr_qubit'] = dr_qubit

dr_readout = drx(soc=soccfg, dr_ch=1, ro_ch=1, frequency=if_frequency/1e6, gain=0.5, phase=0, delay=0, sleep=0)
dr_readout.wave.add(name='x2', t_data=[0,0.25,0.5,0.75,1.0], s_data=[0,1,2,1,0], idx=-1, interp_order=3)
dr_readout.rox.set(frequency=if_frequency/1e6, length=1, delay=0, sleep=0)
config['dr_readout'] = dr_readout

#%% sweep
sw_gain = sweep()
sw_gain.add(dr_qubit, 'gain', 0.1, 1, 10)
sw_gain.add(dr_readout, 'gain', 0.1, 1, 10)
config['sw_gain'] = sw_gain

#%%
dr_freq_list = np.linspace(6.75e9, 6.785e9, 200)

dr_frequency = 6.77e9
drive.set_frequency(idx=0, frequency=dr_frequency, if_frequency=if_frequency)

iq_mat = []
for dr_frequency in dr_freq_list:
    # drive.set_frequency(idx=0, frequency=dr_frequency, if_frequency=if_frequency)
    if_frequency = 3e9 -(dr_frequency - 6.77e9)

    dr_readout = drx(soc=soccfg, dr_ch=1, ro_ch=1, frequency=if_frequency / 1e6, gain=0.5, phase=0, delay=0, sleep=0)
    dr_readout.wave.add(name='x2', t_data=[0, 0.25, 0.5, 0.75, 1.0], s_data=[0, 1, 2, 1, 0], idx=-1, interp_order=3)
    dr_readout.rox.set(frequency=if_frequency / 1e6, length=1, delay=0, sleep=0)
    config['dr_readout'] = dr_readout

    #%%
    prog = PulseSequence(soccfg, config)
    soc.reset_gens()  # clear any DC or periodic values on generators
    iq_data = prog.acquire(soc, load_pulses=True, progress=True)
    # iq_data.to_zarr('test_v2.zarr', mode='w')
    iq_mat.append(iq_data)

iq_mat = xr.concat(iq_mat, dim=xr.DataArray(dr_freq_list, name='frequency', dims='frequency'))
iq_mat = iq_mat.transpose(..., "frequency")

drive.lo1.output(0)
drive.lo2[0].output(0)
#
# #%% plot
# with xr.open_zarr("test_v2.zarr") as f:
#     iq_data = f['IQ accumulated']
#
plot_sweep(iq_mat, scale='log')

plt.figure()
plt.plot(dr_freq_list/1e9, np.abs(iq_mat.sel(rox=1, quadrature='I', reps=1)+1j*(iq_mat.sel(rox=1, quadrature='Q', reps=1))).isel(gain=-1), 'o-')
plt.xlim(6.75, 6.785)
plt.show()
