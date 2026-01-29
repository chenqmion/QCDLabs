import numpy as np
from scipy.interpolate import make_interp_spline
from dataclasses import dataclass, field
from collections import namedtuple
from itertools import compress

@dataclass
class wave:
    soc: 'QickSoc'
    dr_ch: int
    maxv: float

    length_cyl: int = 0
    items: list = field(default_factory=list)

    def add(self, name, t_data, s_data, idx=-1, interp_order=1):
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
            self.items.append(waveform)
        else:
            self.items.insert(idx, waveform)

        self.length_cyl += length_cyl

    def sleep(self, name, t, idx=-1):
        length_cyl = np.round(self.soc.us2cycles(t, gen_ch=self.dr_ch)).astype(int) * \
                     self.soc['gens'][self.dr_ch]['samps_per_clk']
        x_cyl = np.zeros(length_cyl)

        waveform = namedtuple('waveform', ['name', 'length_cyl', 'i_data', 'q_data'])(name=name, length_cyl=length_cyl,
                                                                                      i_data=x_cyl,
                                                                                      q_data=x_cyl)
        if idx == -1:
            self.items.append(waveform)
        else:
            self.items.insert(idx, waveform)

        self.length_cyl += length_cyl

    def remove(self, names=None, idxs=None):
        if names != None:
            mask = [(waveform.name in names) for waveform in self.items]
        else:
            mask = [(idx in idxs) for idx in range(len(self.items))]

        self.items = list(compress(self.items, mask))
