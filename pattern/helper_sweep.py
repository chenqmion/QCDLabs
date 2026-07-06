import numpy as np
import xarray as xr
import itertools
import os
import shutil
import zarr
import dask.array as da
from tqdm import tqdm


def clean_name(name):
    parts = name.split('_')
    cleaned_parts = []
    for p in parts:
        if p not in cleaned_parts:
            cleaned_parts.append(p)
    return "_".join(cleaned_parts)


def do_sweep(config_device, config_sweep, get_trace, file_path):
    if os.path.exists(file_path):
        shutil.rmtree(file_path)
    flag_init = True

    # 1. Build whitelist reference from device status
    static_coords_original = {}
    for instance in config_device:
        inst_name = instance.name
        _keys = list(instance.status.keys())
        _vals = [[v] for v in instance.status.values()]
        dim_names = [f"{inst_name}_{k}" for k in _keys]
        static_coords_original.update(zip(dim_names, _vals))

    all_axes = []
    for _sweep in config_sweep:
        _funcs, _keys, _vals, _names = [], [], [], []
        for _func, _key, _val in _sweep:
            _name = clean_name(f"{_func.__self__.name}_{_func.__name__}_{_key}")
            _funcs.append(_func)
            _keys.append(_key)
            _vals.append(_val)
            _names.append(_name)
        all_axes.append({'func': _funcs, 'arg_name': _keys, 'vals': _vals, 'dim_name': _names})

    sweep_keys = [axis['dim_name'] for axis in all_axes]
    sweep_shape = [len(axis['vals'][0]) for axis in all_axes]
    _sweep_keys = [_k for _ks in sweep_keys for _k in _ks]

    static_coords = {k: v for k, v in static_coords_original.items() if k not in _sweep_keys}

    idx_iter = itertools.product(*[range(n) for n in sweep_shape])
    zipped_vals = [list(zip(*axis['vals'])) for axis in all_axes]
    values_iter = itertools.product(*zipped_vals)

    current_master_coords, trace_dim, total_keys = None, None, None

    total_steps = np.prod(sweep_shape)
    with tqdm(total=total_steps) as pbar:
        for _idx, _val in zip(idx_iter, values_iter):
            # --- Hardware Control ---
            for ax, val_tuple in zip(all_axes, _val):
                for i, _f in enumerate(ax['func']):
                    _f(**{ax['arg_name'][i]: val_tuple[i]})

            # --- Acquisition & Renaming ---
            _res = get_trace().astype(complex)

            # FIX: Dynamically find the instance name that owns the get_trace method
            try:
                inst_name = get_trace.__self__.name
            except AttributeError:
                # Fallback if it's not a bound method (unlikely in your setup)
                inst_name = list(config_device)[0].name

            _res = _res.rename({dim: f"{inst_name}_{dim}" for dim in _res.dims})
            trace_dim = list(_res.dims)[0]  # Now correctly e.g., 'N9928A_frequency_hz'

            # --- Coordinate Sanitization ---
            _, u_idx = np.unique(_res.coords[trace_dim].values, return_index=True)
            if len(u_idx) < len(_res.coords[trace_dim]):
                _res = _res.isel({trace_dim: np.sort(u_idx)})

            safe_coords = np.round(_res.coords[trace_dim].values, 12)
            _res = _res.assign_coords({trace_dim: safe_coords})

            if flag_init:
                # --- Initialization ---
                trace_dims = list(_res.dims)
                filtered_sweep_keys = [k for k in _sweep_keys if k in static_coords_original]
                total_keys = list(dict.fromkeys(filtered_sweep_keys + trace_dims + list(static_coords.keys())))

                size_map = {dim: size for dim, size in _res.sizes.items()}
                for axis in all_axes:
                    for name in axis['dim_name']:
                        size_map[name] = len(axis['vals'][0])
                for dim in total_keys:
                    if dim not in size_map:
                        size_map[dim] = 1

                total_shape = tuple([size_map[k] for k in total_keys])
                chunks = tuple([size_map[k] if k in _res.dims else 1 for k in total_keys])
                dummy_data = da.full(total_shape, np.nan + 0j, chunks=chunks, dtype=complex)

                coords = {}
                # Priority 1: Measurement coordinates
                coords.update(_res.coords)

                # Priority 2: Sweep coordinates
                for axis in all_axes:
                    for i, name in enumerate(axis['dim_name']):
                        if name in total_keys and name not in coords:
                            coords[name] = axis['vals'][i]

                # Priority 3: Static metadata
                for k, v in static_coords.items():
                    if k in total_keys and k not in coords:
                        val = v[0] if isinstance(v, list) else v
                        coords[k] = np.atleast_1d(val)

                ds_init = xr.Dataset({_res.name: (total_keys, dummy_data)}, coords=coords)
                ds_init.to_zarr(file_path, mode='w', compute=False, consolidated=False, zarr_format=2)
                flag_init, current_master_coords = False, safe_coords

            else:
                # --- Dynamic Coordinate Expansion ---
                if not np.isin(safe_coords, current_master_coords).all():
                    ds_old = xr.open_zarr(file_path, consolidated=False)
                    ds_history = ds_old.load()
                    ds_old.close()

                    current_master_coords = np.union1d(current_master_coords, safe_coords)
                    ds_expanded = ds_history.reindex({trace_dim: current_master_coords})

                    shutil.rmtree(file_path)
                    ds_expanded.to_zarr(file_path, mode='w', consolidated=False, zarr_format=2)

            # --- Region Writing ---
            indices = np.where(np.isin(current_master_coords, safe_coords))[0]
            trace_slice = slice(indices[0], indices[-1] + 1)

            dims_to_expand = {k: 1 for k in total_keys if k not in _res.dims}
            _res_update = _res.expand_dims(dims_to_expand).transpose(*total_keys)

            _region = {}
            for i, axis in enumerate(all_axes):
                for name in axis['dim_name']:
                    if name in total_keys:
                        _region[name] = slice(_idx[i], _idx[i] + 1)

            for k in total_keys:
                if k not in _region:
                    if k == trace_dim:
                        _region[k] = trace_slice
                    else:
                        _region[k] = slice(0, 1)

            _res_update.to_dataset(name=_res.name).drop_vars(_res_update.coords, errors='ignore').to_zarr(
                file_path, region=_region, consolidated=False
            )
            pbar.update(1)

    zarr.consolidate_metadata(file_path)