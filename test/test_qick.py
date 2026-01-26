from qick import *
import numpy as np
from numpy.polynomial import Polynomial
import matplotlib.ticker as mtick
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

import xarray as xr

import os
import sys
sys.path.insert(0, '../station/')
from xilinx_qick.class_drx import drx
from xilinx_qick.class_rox import rox

from double_conversion_mixer.instr_double_conversion_mixer import DuoMixer

#%%
lo1_address = "10.0.100.24"
lo2_address = ["10.0.100.32"]
drive = DuoMixer(lo1_address, lo2_address)

dr_frequency = 4.3e9
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

class PulseSequence(AveragerProgram):
    def initialize_phases(self):
        self.phase_ref_q1 = 0

    def play_seq(self):
        cfg = self.cfg
        for dr_name in self.dr_names:
            dr = cfg[dr_name]
            for waveform in dr.waveforms:
#                 print('xx', dr.dr_ch,
#                       dr.frequency_cyl,
#                       dr.maxv,
#                       waveform.name)

                self.set_pulse_registers(ch=dr.dr_ch,
                                         freq=dr.frequency_cyl,
                                         gain=dr.maxv,
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

        for val_key, val_x in cfg.items():
            if val_key[:3] == 'dr_':
                self.dr_names.append(val_key)
                self.declare_gen(ch=val_x.dr_ch, nqz=1)
                self.default_pulse_registers(ch=val_x.dr_ch,
                                             phase=val_x.phase_cyl,
                                             style='arb')

            elif val_key[:3] == 'ro_':
#                 print('x', val_x.ro_ch, val_x.frequency)
                self.ro_chns.append(val_x.ro_ch)
                self.declare_readout(ch=val_x.ro_ch,
                                 length=val_x.length_cyl,
                                 freq=val_x.frequency,
                                 gen_ch=val_x.dr_ch)

        for dr_name in self.dr_names:
            dr = cfg[dr_name]
            for waveform in dr.waveforms:
#                 print(waveform.name, waveform.i_data, waveform.q_data)
                self.add_pulse(ch=dr.dr_ch,
                               name=waveform.name,
                               idata=waveform.i_data,
                               qdata=waveform.q_data)

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

    #%% helper
    def number2dbm(self, number):
        return 18.63 * np.log10(number) - 63.53

    def acquire_decimated(self, soc, load_pulses=True, progress=True):
        cfg = self.cfg
        iq_list = super().acquire_decimated(soc, load_pulses=load_pulses, progress=progress)
        iq_dims = np.shape(iq_list)
        res_data = xr.DataArray(iq_list,
                                coords = [np.arange(0, iq_dims[0], 1), np.array(['I','Q']), np.arange(0, iq_dims[2],1)],
                                dims = ["rox", "quadrature", "ticks"],
                                name = "IQ decimated")

        return res_data

def plot_2q(iq_data):
    fig, axs = plt.subplots(iq_data.rox.size, dpi=200)
    for idx in range(iq_data.rox.size):
        chn = iq_data.rox.values[idx]
        axs[idx].set_title("Qubit %d" % (chn + 1))
        axs[idx].plot(1000 * soccfg.cycles2us(np.arange(0, iq_data.ticks.size), ro_ch=chn),
                      iq_data.sel(rox=chn, quadrature='I'), label="I value, ADC %d" % (chn))
        axs[idx].plot(1000 * soccfg.cycles2us(np.arange(0, iq_data.ticks.size), ro_ch=chn),
                      iq_data.sel(rox=chn, quadrature='Q'), label="Q value, ADC %d" % (chn))
        axs[idx].plot(1000 * soccfg.cycles2us(np.arange(0, iq_data.ticks.size), ro_ch=chn),
                      np.abs(iq_data.sel(rox=chn, quadrature='I') + 1j * iq_data.sel(rox=chn, quadrature='Q')),
                      label="abs value, ADC %d" % (chn),
                      linestyle='dashed')
        axs[idx].legend(loc=1, prop={'size': 6})
        axs[idx].set_ylabel("a.u.")
        axs[idx].xaxis.set_major_locator(MultipleLocator(1000 * 5 * soccfg.cycles2us(4, gen_ch=0)))
        axs[idx].grid(which='major', color='#CCCCCC', linestyle='--')
        axs[idx].xaxis.set_major_formatter(mtick.FormatStrFormatter('%.1f'))
        axs[idx].tick_params(axis='x', rotation=45)

    plt.xlabel('ns')
    plt.tight_layout()
    plt.show()

#%%
config = {"adc_trig_offset": 0.2,
          "reps": 1,
          "soft_avgs": 1,
          "expts": 1,
          "relax_delay": 1,
          "ddr4": False, # full decimated data
          "mr": False # dds data
         }

dr_qubit = drx(soc=soccfg, dr_ch=0, ro_ch=0, frequency=dr_frequency/1e6, gain=0.5, phase=0, delay=0, sleep=0)
dr_qubit.add_waveform(name='x1', t_data=[0,0.1,0.2, 0.3, 0.4], s_data=[0,1,2,1,0], idx=-1, interp_order=3)
# dr_qubit.add_waveform(name='x2', t_data=[0,0.1,0.2, 0.3, 0.4], s_data=[0j,1j,2j,1j,0j], idx=-1, interp_order=3)
config['dr_qubit'] = dr_qubit

ro_qubit = rox(soc=soccfg, dr_ch=0, ro_ch=0, frequency=dr_frequency/1e6, length=1, delay=0, sleep=0)
config['ro_qubit'] = ro_qubit

dr_readout = drx(soc=soccfg, dr_ch=1, ro_ch=1, frequency=if_frequency/1e6, gain=0.5, phase=0, delay=0, sleep=0)
# dr_readout.add_waveform(name='y1', t_data=[0,0.1,0.2,0.3,0.4], s_data=[0j,1j,2j,1j,0j], idx=-1, interp_order=3)
dr_readout.add_waveform(name='y2', t_data=[0,0.1,0.2,0.3,0.4], s_data=[0,1,2,1,0], idx=-1, interp_order=3)
config['dr_readout'] = dr_readout

ro_readout = rox(soc=soccfg, dr_ch=1, ro_ch=1, frequency=if_frequency/1e6, length=1, delay=0, sleep=0)
config['ro_readout'] = ro_readout

prog = PulseSequence(soccfg, config)
soc.reset_gens()  # clear any DC or periodic values on generators
iq_data = prog.acquire_decimated(soc, load_pulses=True, progress=False)
iq_data.to_zarr('test1.zarr', mode='w')

# drive.lo1.output(0)
# drive.lo2[0].output(0)

#%% plot
with xr.open_zarr("test1.zarr") as f:
    iq_data = f['IQ decimated']

plot_2q(iq_data)

#%% phase correction
idx0 = np.argmax(np.abs(iq_data.sel(rox=0, quadrature='I').data + 1j * iq_data.sel(rox=0, quadrature='Q').data))
phi0 = np.angle(iq_data.sel(rox=0, quadrature='I').data[idx0]+1j*iq_data.sel(rox=0, quadrature='Q').data[idx0]) * 180/np.pi

idx1 = np.argmax(np.abs(iq_data.sel(rox=1, quadrature='I').data + 1j * iq_data.sel(rox=1, quadrature='Q').data))
phi1 = np.angle(iq_data.sel(rox=1, quadrature='I').data[idx1]+1j*iq_data.sel(rox=1, quadrature='Q').data[idx1]) * 180/np.pi

config = {"adc_trig_offset": 0.2,
          "reps": 1,
          "soft_avgs": 1,
          "expts": 1,
          "relax_delay": 1,
          "ddr4": False, # full decimated data
          "mr": False # dds data
         }

dr_qubit = drx(soc=soccfg, dr_ch=0, ro_ch=0, frequency=dr_frequency/1e6, gain=0.5, phase=phi0, delay=0, sleep=0)
dr_qubit.add_waveform(name='x1', t_data=[0,0.1,0.2, 0.3, 0.4], s_data=[0,1,2,1,0], idx=-1, interp_order=3)
dr_qubit.add_waveform(name='x2', t_data=[0,0.1,0.2, 0.3, 0.4], s_data=[0j,1j,2j,1j,0j], idx=-1, interp_order=3)
config['dr_qubit'] = dr_qubit

ro_qubit = rox(soc=soccfg, dr_ch=0, ro_ch=0, frequency=dr_frequency/1e6, length=1, delay=0, sleep=0)
config['ro_qubit'] = ro_qubit

dr_readout = drx(soc=soccfg, dr_ch=1, ro_ch=1, frequency=if_frequency/1e6, gain=0.5, phase=phi1, delay=0, sleep=0)
dr_readout.add_waveform(name='y1', t_data=[0,0.1,0.2,0.3,0.4], s_data=[0j,1j,2j,1j,0j], idx=-1, interp_order=3)
dr_readout.add_waveform(name='y2', t_data=[0,0.1,0.2,0.3,0.4], s_data=[0,1,2,1,0], idx=-1, interp_order=3)
config['dr_readout'] = dr_readout

ro_readout = rox(soc=soccfg, dr_ch=1, ro_ch=1, frequency=if_frequency/1e6, length=1, delay=0, sleep=0)
config['ro_readout'] = ro_readout

prog = PulseSequence(soccfg, config)
soc.reset_gens()  # clear any DC or periodic values on generators
iq_data = prog.acquire_decimated(soc, load_pulses=True, progress=False)
iq_data.to_zarr('test2.zarr', mode='w')

drive.lo1.output(0)
drive.lo2[0].output(0)

#%% plot
with xr.open_zarr("test2.zarr") as f:
    iq_data = f['IQ decimated']

plot_2q(iq_data)
