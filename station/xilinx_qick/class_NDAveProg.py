import numpy as np
import xarray as xr
from qick import *
from qick.averager_program import AveragerProgram, QickSweep, merge_sweeps

import numpy as np
import xarray as xr
from qick import *
from qick.averager_program import AveragerProgram, QickSweep, merge_sweeps

class NDProg(NDAveragerProgram):
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

        # modified sync_all with only DAC clocks, no ADC clocks
        self.synci(self.us2cycles(0.01))

    def initialize(self):
        cfg = self.cfg
        self.dr_names = []
        self.ro_names = []
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
                    self.ro_names.append(val_key)
                    self.ro_chns.append(val_x.ro_ch)
                    self.declare_readout(ch=val_x.ro_ch,
                                         length=val_x.rox.length_cyl,
                                         freq=val_x.rox.frequency,
                                         gen_ch=val_x.dr_ch)

            elif val_key[:3] == 'ro_':
                self.ro_names.append(val_key)
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

        # self.trigger(ddr4=cfg['ddr4'],
        #              mr=cfg['mr'],
        #              adc_trig_offset=self.us2cycles(self.cfg["adc_trig_offset"]))

        self.synci(1000)  # give processor some time to configure pulses

    def body(self):
        cfg = self.cfg
        self.trigger(adcs=self.ro_chns,
                     pins=[0],
                     adc_trig_offset=cfg[self.ro_names[0]].delay_cyl)

        self.initialize_phases()
        self.play_seq()
        self.wait_all()
        self.sync_all(cfg[self.ro_names[0]].sleep_cyl)  # need fix!!!

    # %% data
    def acquire(self, soc, load_pulses=True, progress=True):
        cfg = self.cfg
        expt_pts, i_data, q_data = super().acquire(soc, load_pulses=load_pulses, progress=progress)
        _coords = [self.ro_chns, [1]]
        _dims = ["rox", "reps"]

        for _num, val_key in enumerate(self.sw_names[::-1]):
            _coords.append(np.unique(expt_pts[::-1][_num]))
            _dims.append(val_key[3:])

        res_data = xr.DataArray(np.array(i_data) + 1j*np.array(q_data),
                                coords=_coords,
                                dims=_dims,
                                name="IQ accumulated")

        return res_data

    def acquire_decimated(self, soc, load_pulses=True, progress=True):
        cfg = self.cfg
        iq_list = super().acquire_decimated(soc, progress=progress)
        iq_list = np.transpose(iq_list, (3,0,1,2))
        print('hahaha', np.shape(iq_list[0] + 1j * iq_list[1]))
        res_data = xr.DataArray(iq_list[0] + 1j * iq_list[1],
                                coords=[self.ro_chns,
                                        np.arange(0, np.shape(iq_list)[-2], 1),
                                        np.arange(0, np.shape(iq_list)[-1], 1)],
                                dims=["rox", "params", "ticks"],
                                name="IQ decimated")

        return res_data