import numpy as np
import xarray as xr
import itertools
import os
import shutil
import zarr
import dask.array as da
from tqdm import tqdm
import copy

def instr_status_coords(config_device):
    _instr_status_coords = {}

    for instance in config_device:
        inst_name = instance.name
        _keys = list(instance.status.keys())
        _vals = [[v] for v in instance.status.values()]
        dim_names = [f"{inst_name}_{k}" for k in _keys]
        _instr_status_coords.update(zip(dim_names, _vals))

    return _instr_status_coords

def static_coords(_instr_status_coords, _sweep_axis_list):

    _sweep_keys = [
        _key
        for axis in _sweep_axis_list
        for _key in axis['dim_name']
    ]

    _static_coords = {
        k: v
        for k, v in _instr_status_coords.items()
        if k not in _sweep_keys
    }
    return _static_coords

def clean_name(name):
    parts = name.split('_')
    cleaned_parts = []
    for p in parts:
        if (p not in cleaned_parts) and (p != 'sweep'):
            cleaned_parts.append(p)
    return "_".join(cleaned_parts)

def sweep_axis_list(config_sweep):
    _sweep_axis_list = []

    for linked_sweep in config_sweep:

        _funcs, _keys, _vals, _names, _saves = [], [], [], [], []

        for individual_sweep in linked_sweep:

            if len(individual_sweep) == 3:
                _func, _key, _val = individual_sweep
                _save = True
            else:
                _func, _key, _val, _save = individual_sweep

            _name = clean_name(f"{_func.__self__.name}_{_func.__name__}_{_key}")

            _funcs.append(_func)
            _keys.append(_key)
            _vals.append(_val)
            _names.append(_name)
            _saves.append(_save)

        _sweep_axis = {'func': _funcs, 'arg_name': _keys, 'vals': _vals, 'dim_name': _names, 'save': _saves}

        _sweep_axis_list.append(_sweep_axis)
    return _sweep_axis_list

def create_dummy(_trace, _sweep_axis_list):
    _trace_dims = {dim: _trace.coords[dim].values
                   for dim in _trace.dims}

    _trace_coords = {name: coord.values
                     for name, coord in _trace.coords.items()}

    _trace_dims_full = copy.deepcopy(_trace_dims)
    sweep_dims_full = {}
    for _sweep_axis in _sweep_axis_list:
        for dim_name, vals in zip(_sweep_axis['dim_name'], _sweep_axis['vals']):
            sweep_dims_full[dim_name] = np.unique(vals)

    _trace_dims_full.update(sweep_dims_full)
    _shape = tuple(len(v) for v in _trace_dims_full.values())

    ds_dummy = xr.Dataset(
        {_trace.name:
            (
                tuple(_trace_dims_full.keys()),
                np.full(_shape,
                        np.nan,
                        dtype=complex,)
            )},
        coords=_trace_dims_full
    )

    for aux_key in (_trace_coords.keys() - _trace_dims.keys()):
        ds_dummy[aux_key] = (_trace.coords[aux_key].dims, _trace.coords[aux_key].values)
        ds_dummy = ds_dummy.set_coords(aux_key)

    return ds_dummy


