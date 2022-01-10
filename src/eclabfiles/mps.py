#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Processing of BioLogic's EC-Lab settings files.

File Structure of `.mps` Files
``````````````````````````````


Structure of Parsed Data
````````````````````````

The `process` function returns a tuple of techniques and metadata. The
techniques dictionary is structured like this:

.. codeblock:: python

    {
        "1": {
            "technique": str,                           # Technique short name.
            "params": [ (optional)                      # Technique parameter sequences.
                {"param1": float, "param2": str, ...},
                ...,
                {"param1": float, "param2": str, ...},
            ],
            "data": list (optional)                     # Data processed from data files.
            "meta": dict (optional)                     # Metadata processed from data files.
        },
        "2":  {
            "technique": str,                           #
            "params": [ (optional)                      # Technique parameter sequences
                {"param1": float, "param2": str, ...},
                ...,
                {"param1": float, "param2": str, ...},
            ],
        },
        ...
    }

The metadata only contains the raw header from the top of settings
files.

.. codeauthor:: Nicolas Vetsch <vetschnicolas@gmail.com>
"""
import glob
import os
import warnings

from eclabfiles import mpr, mpt
from eclabfiles.techniques import technique_params


def _process_techniques(techniques: list[str]) -> dict:
    """Processes the techniques.

    Parameters
    ----------
    techniques
        A list of the linked techniques.

    Returns
    -------
    dict
        The processed techniques, indexed by technique number.

    """
    processed_techniques = {}
    for technique in techniques:
        technique_num, technique_name, *params = technique.split("\n")
        technique_num = technique_num.split(" : ")[-1]
        technique, params_keys = technique_params(technique_name, params)
        # The sequence param columns are always allocated 20 characters.
        n_sequences = int(len(params[0]) / 20)
        params_values = []
        for seq in range(1, n_sequences):
            values = []
            for param in params:
                try:
                    val = float(param[seq * 20 : (seq + 1) * 20])
                except ValueError:
                    val = param[seq * 20 : (seq + 1) * 20].strip()
                values.append(val)
            params_values.append(values)
        params = [dict(zip(params_keys, values)) for values in params_values]
        processed_techniques[technique_num] = {
            "technique": technique,
            "params": params,
        }
    return processed_techniques


def _load_technique_data(
    filename: str, techniques: dict, load_type: str = None
) -> dict:
    """Loads technique data from the same folder.

    Parameters
    ----------
    filename
        The complete filename of the settings file.
    techniques
        The dictionary of the previously processed techniques.
    load_type
        The type of file to load in. Defaults to using binary data
        files. Possible options are "mpr" and "mpt".

    Returns
    -------
    list[dict]
        The list of technique dictionaries now including any data.

    """
    # Determine the number of files that are expected. LOOP and WAIT do
    # not write data.
    expected_techniques = {}
    for num, technique in techniques.items():
        if technique["technique"] not in {"LOOP", "WAIT"}:
            expected_techniques[num] = technique
    base_path, __ = os.path.splitext(filename)
    # Load data and metadata.
    if load_type is None:
        warnings.warn("Default load_type is 'mpr'. Set explicitly to use 'mpt'.")
        load_type = "mpr"
    # NOTE: It's assumed that sorting your data files by name puts them
    # in the order in which they appear in the settings file.
    if load_type == "mpr":
        mpr_paths = sorted(glob.glob(base_path + "*.mpr"))
        if len(expected_techniques) != len(mpr_paths):
            raise ValueError("Data incomplete.")
        data, meta = [list(t) for t in zip(*[mpr.process(path) for path in mpr_paths])]
    elif load_type == "mpt":
        mpt_paths = sorted(glob.glob(base_path + "*.mpt"))
        if len(expected_techniques) != len(mpt_paths):
            raise ValueError("Data incomplete.")
        data, meta = [list(t) for t in zip(*[mpt.process(path) for path in mpt_paths])]
    else:
        raise ValueError(f"Unrecognised load_type: {load_type}")
    for num in expected_techniques:
        techniques[num]["data"] = data.pop(0)
        techniques[num]["meta"] = meta.pop(0)
    return techniques


def process(
    fn: str,
    encoding: str = "windows-1252",
    load_data: bool = False,
    load_type: str = None,
) -> dict:
    """Processes EC-Lab settings files.

    Parameters
    ----------
    fn
        The file containing the settings to parse.
    encoding
        Encoding of ``fn``, by default "windows-1252".
    load_data
        Whether to try and load data from the same folder as the given
        settings file.
    load_type
        The type of file to load in. Defaults to using binary data
        files. Possible options are "mpr" and "mpt".

    Returns
    -------
    (data, metadata) : tuple[list, dict
        Tuple containing the timesteps and metadata

    """
    file_magic = "EC-LAB SETTING FILE\n"
    with open(fn, "r", encoding=encoding) as mps_file:
        assert mps_file.readline() == file_magic, "Invalid file magic."
        mps = mps_file.read()
    n_linked_techniques, filename, settings, *techniques = mps.split("\n\n")
    n_linked_techniques = int(n_linked_techniques.strip().split()[-1])
    assert len(techniques) == n_linked_techniques, "Inconsistent file."
    filename = filename.split(" : ")[-1]
    techniques = _process_techniques(techniques)
    if load_data:
        techniques = _load_technique_data(fn, techniques, load_type)
    meta = {}
    meta["raw"] = filename + "\n\n" + settings
    return techniques, meta
