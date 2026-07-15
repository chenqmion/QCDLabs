import numpy as np
import xarray as xr
from qick import *
from qick.averager_program import AveragerProgram, QickSweep, merge_sweeps

class Prog(AveragerProgram):
    def initialize_phases(self):
        # self.phase_ref_q1 = 0
        pass

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
        # self.sw_names = []
        for val_key, val_x in cfg.items():
            if val_key[:3] == 'dr_':
                self.dr_names.append(val_key)
                self.declare_gen(ch=val_x.dr_ch, nqz=val_x.nqz)
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

                    if cfg['mr']:
                        self.declare_readout(ch=val_x.ro_ch,
                                             length=val_x.rox.length_cyl,
                                             freq=val_x.rox.frequency,
                                             gen_ch=val_x.dr_ch,
                                             sel = 'input')

                    else:
                        self.declare_readout(ch=val_x.ro_ch,
                                             length=val_x.rox.length_cyl,
                                             freq=val_x.rox.frequency,
                                             gen_ch=val_x.dr_ch)


                #
                # print("gen =", val_x.frequency)
                # print("gen =", val_x.frequency_cyl)
                # print("ro  =", val_x.rox.frequency)

            elif val_key[:3] == 'ro_':
                self.ro_names.append(val_key)
                self.ro_chns.append(val_x.ro_ch)
                if cfg['mr']:
                    self.declare_readout(ch=val_x.ro_ch,
                                         length=val_x.length_cyl,
                                         freq=val_x.frequency,
                                         gen_ch=val_x.dr_ch,
                                         sel = 'input')
                else:
                    self.declare_readout(ch=val_x.ro_ch,
                                         length=val_x.length_cyl,
                                         freq=val_x.frequency,
                                         gen_ch=val_x.dr_ch)

                # print("ro2  =", val_x.frequency)

            # elif val_key[:3] == 'sw_':
            #     self.sw_names.append(val_key)
            #
            #     sws = []
            #     for val_sw in val_x.items:
            #         var_name = 'sw_' + str(val_sw.dr_ch) + '_' + val_sw.var
            #         setattr(self, var_name, self.get_gen_reg(val_sw.dr_ch, val_sw.var))
            #         sws.append(QickSweep(self, getattr(self, var_name),
            #                              val_sw.start, val_sw.stop, val_sw.expts))
            #     self.add_sweep(merge_sweeps(sws))

        # self.trigger(ddr4=cfg['ddr4'],
        #              mr=cfg['mr'],
        #              adc_trig_offset=self.us2cycles(self.cfg["adc_trig_offset"]))

        self.synci(self.us2cycles(0.01))  # give processor some time to configure pulses

    def body(self):
        cfg = self.cfg
        self.trigger(ddr4=cfg['ddr4'],
                     mr=cfg['mr'],
                     adcs=self.ro_chns,
                     pins=[0],
                     adc_trig_offset=cfg[self.ro_names[0]].rox.delay_cyl) # wait # cycles after trigger

        self.initialize_phases()
        self.play_seq()
        self.wait_all()
        self.sync_all(cfg[self.ro_names[0]].rox.sleep_cyl) # wait # cycles before next reps

    # %% data
    def test(self, soc, load_pulses=True, progress=True):
        cfg = self.cfg

        self.config_all(soc)
        soc.tproc.start()


    def acquire(self, soc, load_pulses=True, progress=True):
        cfg = self.cfg
        i_data, q_data = super().acquire(soc, load_pulses=load_pulses, progress=progress)

        _coords = [self.ro_chns, [1]]
        _dims = ["rox", "reps"]

        res_data = xr.DataArray(np.array(i_data) + 1j*np.array(q_data),
                                coords=_coords,
                                dims=_dims,
                                name="IQ accumulated")
        return res_data

    def acquire_decimated(self, soc, load_pulses=True, progress=True):
        cfg = self.cfg

        if cfg['mr']:
            soc.arm_mr(ch=0)

        if cfg['ddr4']:
            soc.arm_ddr4(ch=0, nt=10)

        iq_list = super().acquire_decimated(soc, progress=progress)

        if cfg['mr']:
            iq_list_mr = soc.get_mr()
            iq_list_mr = np.transpose(iq_list_mr, (1, 0))

            ticks = np.arange(0, len(iq_list_mr[0]), 1)
            tx = [self.cycles2us(ticks, ro_ch=0)/8.0]

            res_data = xr.DataArray([iq_list_mr[0] + 1j * iq_list_mr[1]],
                                    coords={"rox": [0],
                                            "ticks": ticks,
                                            "tx": (("rox", "ticks"), np.asarray(tx))
                                            },
                                    dims=["rox", "ticks"],
                                    name="IQ mr")

        elif cfg['ddr4']:
            iq_list_ddr4 = soc.get_ddr4(10)
            iq_list_ddr4 = np.transpose(iq_list_ddr4, (1, 0))

            ticks = np.arange(0, len(iq_list_ddr4[0]), 1)
            tx = [self.cycles2us(ticks, ro_ch=0)]

            res_data = xr.DataArray([iq_list_ddr4[0] + 1j * iq_list_ddr4[1]],
                                    coords={"rox": [0],
                                            "ticks": ticks,
                                            "tx": (("rox", "ticks"), np.asarray(tx))
                                            },
                                    dims=["rox", "ticks"],
                                    name="IQ ddr4")

        else:
            ticks_max = np.max([len(_iq[0]) for _iq in iq_list])
            ticks = np.arange(0, ticks_max, 1)

            tx = []
            for idx_iq, data_iq in enumerate(iq_list):
                iq_list[idx_iq] = np.pad(data_iq,((0, 0), (0, ticks_max - data_iq.shape[1])), mode="constant", constant_values=np.nan)
                tx.append(self.cycles2us(ticks, ro_ch=self.ro_chns[idx_iq]))

            iq_list = np.transpose(iq_list, (1, 0, 2))
            res_data = xr.DataArray(iq_list[0] + 1j*iq_list[1],
                                    coords={"rox": self.ro_chns,
                                            "ticks": ticks,
                                            "tx": (("rox", "ticks"), np.asarray(tx))
                                            },
                                    dims=["rox", "ticks"],
                                    name="IQ decimated")



        return res_data