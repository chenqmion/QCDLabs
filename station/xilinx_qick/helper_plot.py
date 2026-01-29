import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

#%%
def plot_decimated(iq_data):
    fig, axs = plt.subplots(iq_data.rox.size, dpi=200)
    for idx in range(iq_data.rox.size):
        chn = iq_data.rox.values[idx]
        axs[idx].set_title("Qubit %d" % (chn + 1))
        axs[idx].plot(iq_data.ticks,
                      iq_data.sel(rox=chn, quadrature='I'), label="I value, ADC %d" % (chn))
        axs[idx].plot(iq_data.ticks,
                      iq_data.sel(rox=chn, quadrature='Q'), label="Q value, ADC %d" % (chn))
        axs[idx].plot(iq_data.ticks,
                      np.abs(iq_data.sel(rox=chn, quadrature='I') + 1j * iq_data.sel(rox=chn, quadrature='Q')),
                      label="abs value, ADC %d" % (chn),
                      linestyle='dashed')
        axs[idx].legend(loc=1, prop={'size': 6})
        axs[idx].set_ylabel("a.u.")

    plt.xlabel('ns')
    plt.tight_layout()
    plt.show()

#%%
def plot_sweep(iq_data, scale='linear'):
    fig, axs = plt.subplots(iq_data.rox.size, 2, dpi=200)
    for idx1 in range(iq_data.rox.size):
        for idx2 in range(2):
            chn = iq_data.rox.values[idx1]
            x_name = iq_data.dims[-2]
            y_name = iq_data.dims[-1]

            if scale=='log':
                if idx2 == 0:
                    axs[idx1, 0].pcolormesh(iq_data[x_name], iq_data[y_name],
                                            20*np.log10(np.abs(iq_data.sel(rox=idx1, quadrature='I', reps=1)+1j*iq_data.sel(rox=idx1, quadrature='Q', reps=1))).T)
                else:
                    axs[idx1, 1].pcolormesh(iq_data[x_name], iq_data[y_name],
                                            np.unwrap(np.angle(iq_data.sel(rox=idx1, quadrature='I', reps=1)+1j*iq_data.sel(rox=idx1, quadrature='Q', reps=1)), axis=1).T)
            else:
                if idx2 == 0:
                    axs[idx1, 0].pcolormesh(iq_data[x_name], iq_data[y_name], iq_data.sel(rox=idx1, quadrature='I', reps=1).T)
                else:
                    axs[idx1, 1].pcolormesh(iq_data[x_name], iq_data[y_name], iq_data.sel(rox=idx1, quadrature='Q', reps=1).T)
            axs[idx1, idx2].set_ylabel(y_name)
            axs[idx1, idx2].set_xlabel(x_name)

    plt.xlabel('ns')
    plt.tight_layout()
    plt.show()