import numpy as np
from scipy.interpolate import make_interp_spline
from dataclasses import dataclass, field
from collections import namedtuple
from itertools import compress


@dataclass
class drx:
    soc: 'QickSoc'
    dr_ch: int
    frequency: float
    gain: float

    ro_ch: int = None
    phase: float = 0.0
    delay: float = 0.0
    sleep: float = 0.0
    length_cyl: int = 0
    waveforms: list = field(default_factory=list)

    @property
    def maxv(self):
        return np.round(self.soc.get_maxv(gen_ch=self.dr_ch) * self.gain).astype(int)

    @property
    def maxdbm(self):
        return 20 * np.log10(self.gain) - 10

    @property
    def phase_cyl(self):
        return self.soc.deg2reg(self.phase, gen_ch=self.dr_ch)

    @property
    def delay_cyl(self):
        return np.round(self.soc.us2cycles(self.delay, gen_ch=self.dr_ch)).astype(int)

    @property
    def sleep_cyl(self):
        return np.round(self.soc.us2cycles(self.sleep, gen_ch=self.dr_ch)).astype(int)

    @property
    def frequency_cyl(self):
        if (self.ro_ch != None):
            return self.soc.freq2reg(self.frequency, gen_ch=self.dr_ch, ro_ch=self.ro_ch)
        else:
            return self.frequency

    def add_waveform(self, name, t_data, s_data, idx=-1, interp_order=1):
        fun_i = make_interp_spline(t_data, np.real(s_data), k=interp_order)
        fun_q = make_interp_spline(t_data, np.imag(s_data), k=interp_order)

        length_cyl = np.round(self.soc.us2cycles(t_data[-1], gen_ch=self.dr_ch)).astype(int) * \
                     self.soc['gens'][self.dr_ch]['samps_per_clk']
        i_cyl = fun_i(np.linspace(0, t_data[-1], length_cyl))
        q_cyl = fun_q(np.linspace(0, t_data[-1], length_cyl))
        s_cyl = i_cyl + 1j * q_cyl

        waveform = namedtuple('waveform', ['name', 'length_cyl', 'i_data', 'q_data'])(name=name, length_cyl=length_cyl,
                                                                                  i_data=i_cyl / np.max(
                                                                                      np.abs(s_cyl)) * self.maxv,
                                                                                  q_data=-q_cyl / np.max(
                                                                                      np.abs(s_cyl)) * self.maxv)

        if idx == -1:
            self.waveforms.append(waveform)
        else:
            self.waveforms.insert(idx, waveform)

        self.length_cyl += length_cyl

    def add_sleep(self, name, t, idx=-1):
        length_cyl = np.round(self.soc.us2cycles(t, gen_ch=self.dr_ch)).astype(int) * \
                     self.soc['gens'][self.dr_ch]['samps_per_clk']
        x_cyl = np.zeros(length_cyl)

        waveform = namedtuple('waveform', ['name', 'length_cyl', 'i_data', 'q_data'])(name=name, length_cyl=length_cyl,
                                                                                      i_data=x_cyl,
                                                                                      q_data=x_cyl)
        if idx == -1:
            self.waveforms.append(waveform)
        else:
            self.waveforms.insert(idx, waveform)

        self.length_cyl += length_cyl


    def remove_waveform(self, names=None, idxs=None):
        if names != None:
            mask = [(waveform.name in names) for waveform in self.waveforms]
        else:
            mask = [(idx in idxs) for idx in range(len(self.waveforms))]

        self.waveforms = list(compress(self.waveforms, mask))




