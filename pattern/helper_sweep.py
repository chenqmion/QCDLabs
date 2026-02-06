import numpy as np
import xarray as xr
import itertools
import os
import shutil
import zarr
from tqdm import tqdm

def do_sweep(config_device, config_sweep, get_trace, file_path):
    if os.path.exists(file_path):
        shutil.rmtree(file_path)
    flag_init = True

    static_coords = {}
    for instance in config_device:
        inst_name = instance.name
        _keys = list(instance.status.keys())
        _vals = list(instance.status.values())

        dim_name = [f"{inst_name}_{_key}" for _key in _keys]
        _vals = [[_val] for _val in _vals]
        static_coords.update(zip(dim_name, _vals))

    all_axes = []
    for func, params in config_sweep:
        for _key, _val in params.items():
            inst_name = func.__self__.name

            # func_name = func.__name__
            # dim_name = f"{inst_name}_{func_name}_{_key}"
            dim_name = f"{inst_name}_{_key}"

            all_axes.append({
                'func': func,
                'arg_name': _key,
                'vals': _val,
                'dim_name': dim_name
            })

    sweep_keys = [axis['dim_name'] for axis in all_axes]
    sweep_shape = [len(axis['vals']) for axis in all_axes]
    static_coords = {_key: _val for _key, _val in static_coords.items() if _key not in sweep_keys}

    idx_iter = itertools.product(*[range(n) for n in sweep_shape])
    values_iter = itertools.product(*[axis['vals'] for axis in all_axes])

    total_steps = np.prod(sweep_shape)
    with tqdm(total=total_steps) as pbar:
        for _idx, _val in zip(idx_iter, values_iter):
            func_args_map = {}
            sweep_coords = {}

            for ax, val in zip(all_axes, _val):
                if ax['func'] not in func_args_map:
                    func_args_map[ax['func']] = {}
                func_args_map[ax['func']][ax['arg_name']] = val
                sweep_coords[ax['dim_name']] = [val]

            for func, kwargs in func_args_map.items():
                func(**kwargs)

            # acquisition function
            _res = get_trace().astype(complex)

            inst_name = func.__self__.name
            rename_map = {dim: f"{inst_name}_{dim}" for dim in _res.dims}
            _res = _res.rename(rename_map)

            if flag_init:
                update_keys = sweep_keys + list(_res.dims)
                static_keys = list(static_coords.keys())
                total_keys = update_keys + static_keys

                total_shape = tuple(sweep_shape) + _res.shape + (1,) * len(static_keys)
                chunks = (1,) * len(sweep_keys) + _res.shape + (1,) * len(static_keys)

                import dask.array as da
                dummy_data = da.full(total_shape, np.nan, chunks=chunks, dtype=complex)

                coords = {axis['dim_name']: axis['vals'] for axis in all_axes}
                coords.update(_res.coords)
                coords.update(static_coords)

                ds_init = xr.Dataset(
                    data_vars={_res.name: (total_keys, dummy_data)},
                    coords=coords
                )

                ds_init.to_zarr(file_path, mode='w', compute=False, consolidated=False, zarr_format=2)

                flag_init = False

            _res_update = _res.expand_dims(sweep_coords | static_coords)
            _res_update = _res_update.transpose(*total_keys).to_dataset(name=_res.name)
            _region = {k: slice(i, i + 1) for k, i in zip(sweep_keys, _idx)}

            _res_update = _res_update.drop_vars(_res_update.coords)
            _res_update.to_zarr(file_path, region=_region, consolidated=False)

            pbar.update(1)

    import zarr
    zarr.consolidate_metadata(file_path)

