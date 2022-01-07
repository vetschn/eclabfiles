#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Processing of BioLogic's EC-Lab settings files.

.. codeauthor:: Nicolas Vetsch <vetschnicolas@gmail.com>
"""
import glob
import logging
import os
import warnings
from eclabfiles import mpt, mpr
from eclabfiles.techniques import technique_params

logger = logging.getLogger(__name__)


def _process_techniques(techniques: list[str]) -> dict:
    """Processes the techniques.
    
    Parameters
    ----------
    filename

    techniques
        
    load_data
    
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


def _load_technique_data(filename: str, techniques: dict, load_type: str = None) -> dict:
    """Tries to load technique data from the same folder.

    Parameters
    ----------
    filename

    techniques
        The previously parsed list of technique dicts.
    load_type

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
        warnings.warn("Default loadtype is 'mpr'. Set explicitly to use 'mpt'.")
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
        raise ValueError(f"Unrecognised loadtype: {load_type}")
    for num in expected_techniques:
        techniques[num]["data"] = data.pop(0)
        techniques[num]["meta"] = meta.pop(0)
    return techniques


def process(fn: str, encoding: str = "windows-1252", load_data: bool = False, load_type: str = None) -> dict:
    """Processes EC-Lab settings files.

    If there are .mpr or .mpt files present in the same folder, those
    files are read in and returned as well.

    Parameters
    ----------
    fn
        The file containing the data to parse.
    encoding
        Encoding of ``fn``, by default "windows-1252".

    Returns
    -------
    (data, metadata) : tuple[list, dict]
        Tuple containing the timesteps and metadata

    """
    file_magic = "EC-LAB SETTING FILE\n"
    with open(fn, "r", encoding=encoding) as mps_file:
        if mps_file.readline() != file_magic:
            raise ValueError(f"Invalid file magic: {fn}")
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

if __name__ == "__main__":
    fn = r"G:\Limit\VMP3 data\Ueli\Ampcera-Batch10\20211210_B10P3_Ref_HT400C-3h_Li-3mm-280C-30min\20211210_B10P3_Ref_HT400C-3h_Li-3mm-280C-30min_EIS.mps"
    process(fn, load_data=True, load_type="mpr")
    print("")

