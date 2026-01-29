from dataclasses import dataclass, field
from collections import namedtuple
import numpy as np

@dataclass
class sweep:
    items: list = field(default_factory=list)

    def add(self, drx, var, start, stop, expts):
        if var == 'gain':
            _start = np.round(start * drx.maxv).astype(int)
            _stop = np.round(stop * drx.maxv).astype(int)
        # elif var == 'phase':
        #     _start = drx.soc.deg2reg(start, gen_ch=drx.dr_ch)
        #     _stop = drx.soc.deg2reg(stop, gen_ch=drx.dr_ch)
        # elif var == 'freq':
        #     _start = drx.soc.freq2reg(start, gen_ch=drx.dr_ch, ro_ch=drx.ro_ch)
        #     _stop = drx.soc.freq2reg(stop, gen_ch=drx.dr_ch, ro_ch=drx.ro_ch)
        else:
            _start = start
            _stop = stop

        _sweep = namedtuple('sweep', ['dr_ch', 'var', 'start', 'stop', 'expts'])(dr_ch=drx.dr_ch,
                                                                               var=var,
                                                                               start=_start,
                                                                               stop=_stop,
                                                                               expts=expts)

        print(_sweep)
        self.items.append(_sweep)