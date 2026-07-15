import numpy as np
import xarray as xr
import itertools
import shutil
import zarr
import dask.array as da
import copy
from tqdm import tqdm

import os
os.environ["ZARR_CONCURRENCY"] = "0"

import sys

driver_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, driver_path)

import sweep_configure as scfg

def do_sweep(config_device, config_sweep, get_trace, file_path, flag_init=True):

    if os.path.exists(file_path):
        shutil.rmtree(file_path)

    # flag_init = True
    inst_name = get_trace.__self__.name

    _instr_status_coords = scfg.instr_status_coords(config_device) # name: value
    _sweep_axis_list = scfg.sweep_axis_list(config_sweep)
    _static_coords = scfg.static_coords(_instr_status_coords, _sweep_axis_list)

    sweep_shape = [
        len(axis['vals'][0])
        for axis in _sweep_axis_list
    ]
    total_steps = np.prod(sweep_shape)

    idx_iters = itertools.product(
        *[
            range(n)
            for n in sweep_shape
        ]
    )

    value_iters = itertools.product(
        *[
        list(zip(*axis['vals']))
        for axis in _sweep_axis_list
        ]
    )

    params_coords = copy.deepcopy(_static_coords)

    with tqdm(total=total_steps) as pbar:
        for params_idx, params_val in zip(idx_iters, value_iters):

            fun_dict = {}
            sweep_dims = {}

            for ax, val_tuple in zip(_sweep_axis_list, params_val):
                for i, func in enumerate(ax["func"]):
                    if func not in fun_dict:
                        fun_dict[func] = {}

                    fun_dict[func][ax["arg_name"][i]] = val_tuple[i]
                    sweep_dims[ax["dim_name"][i]] = val_tuple[i]

            params_coords.update(sweep_dims)

            for func, kwargs in fun_dict.items():
                func(**kwargs)

            _trace = get_trace().astype(complex)

            _trace = _trace.rename(
                {
                    dim:
                    f"{inst_name}_{dim}"
                    for dim in _trace.dims
                }
            )

            _trace = _trace.expand_dims({k: [v]
                                        for k, v in params_coords.items()
                                        })

            if pbar.n == 0:
                chunks = tuple(len(_trace.coords[dim]) for dim in _trace.dims)
                if flag_init:
                    ds = scfg.create_dummy(_trace, _sweep_axis_list)

                    ds.to_zarr(
                        file_path,
                        mode='w',
                        consolidated=False,
                        zarr_format=2,
                        encoding = {_trace.name: {"chunks": chunks}}
                    )

                    flag_init = False
                else:
                    ds = xr.open_zarr(file_path, consolidated=False)[_trace.name]

            # update region
            _trace = _trace.transpose(*ds[_trace.name].dims)
            ds_new = _trace.to_dataset(name=_trace.name)

            try:
                region = {}
                for dim in ds[_trace.name].dims:
                    zarr_coord = np.asarray(ds.coords[dim].values)
                    new_coord = np.asarray(_trace.coords[dim].values)

                    idx = np.where(np.isin(zarr_coord, new_coord))[0]
                    region[dim] = slice(idx.min(), idx.max() + 1)

                ds_new.reset_coords(drop=True).to_zarr(
                                                        file_path,
                                                        region=region,
                                                        consolidated=False,
                                                        zarr_format=2
                                                        )
            except:
                ds = xr.open_zarr(file_path, consolidated=False)[_trace.name]
                ds = xr.merge([ds, ds_new], join="outer")
                ds.to_zarr(
                    file_path,
                    mode='w',
                    consolidated=False,
                    zarr_format=2,
                    encoding={_trace.name: {"chunks": chunks}}
                )

            pbar.update(1)

    zarr.consolidate_metadata(file_path)
