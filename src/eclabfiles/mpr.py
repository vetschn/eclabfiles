#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read BioLogic's EC-Lab binary modular files into lists of dicts.

This code is partly an adaptation of the `galvani` module by Chris Kerr
(https://github.com/echemdata/galvani) and builds on the work done by
the previous civilian service member working on the project, Jonas
Krieger.

Author:         Nicolas Vetsch (veni@empa.ch / vetschnicolas@gmail.com)
Organisation:   EMPA Dübendorf, Materials for Energy Conversion (501)
Date:           2021-09-29

"""
import logging
from io import TextIOWrapper

import numpy as np

from eclabfiles.techniques import technique_params_dtypes
from eclabfiles.utils import read_value, read_values

# Module header at the top of every VMP MODULE block.
module_header_dtype = np.dtype(
    [
        ("short_name", "|S10"),
        ("long_name", "|S25"),
        ("length", "<u4"),
        ("version", "<u4"),
        ("date", "|S8"),
    ]
)


# Relates the offset in the settings DATA to the corresponding dtype.
settings_dtypes = {
    0x0007: ("comments", "pascal"),
    0x0107: ("active_material_mass", "<f4"),
    0x010B: ("at_x", "<f4"),
    0x010F: ("molecular_weight", "<f4"),
    0x0113: ("atomic_weight", "<f4"),
    0x0117: ("acquisition_start", "<f4"),
    0x011B: ("e_transferred", "<u2"),
    0x011E: ("electrode_material", "pascal"),
    0x01C0: ("electrolyte", "pascal"),
    0x0211: ("electrode_area", "<f4"),
    0x0215: ("reference_electrode", "pascal"),
    0x024C: ("characteristic_mass", "<f4"),
    0x025C: ("battery_capacity", "<f4"),
    0x0260: ("battery_capacity_unit", "|u1"),
    # NOTE: The compliance limits are apparently not always at this
    # offset, hence commented out...
    # 0x19d2: ('compliance_min', '<f4'),1
    # 0x19d6: ('compliance_max', '<f4'),
}


# Maps the flag column ID bytes to the corresponding name, bitmask and
# bitshift.
flag_columns = {
    0x0001: ("mode", 0x03, 0),
    0x0002: ("ox/red", 0x04, 2),
    0x0003: ("error", 0x08, 3),
    0x0015: ("control changes", 0x10, 4),
    0x001F: ("Ns changes", 0x20, 5),
    # NOTE: I think the missing bitmask (0x40) is a stop bit. It appears
    # in the flag bytes of the very last data point.
    0x0041: ("counter inc.", 0x80, 7),
}


# Maps the data column ID bytes to the corresponding dtype.
data_column_dtypes = {
    0x0004: ("time/s", "<f8"),
    0x0005: ("control/V/mA", "<f4"),
    0x0006: ("Ewe/V", "<f4"),
    0x0007: ("dq/mA.h", "<f8"),
    0x0008: ("I/mA", "<f4"),
    0x0009: ("Ece/V", "<f4"),
    0x000B: ("<I>/mA", "<f8"),
    0x000D: ("(Q-Qo)/mA.h", "<f8"),
    0x0010: ("Analog IN 1/V", "<f4"),
    0x0011: ("Analog IN 2/V", "<f4"),
    0x0013: ("control/V", "<f4"),
    0x0014: ("control/mA", "<f4"),
    0x0017: ("dQ/mA.h", "<f8"),
    0x0018: ("cycle number", "<f8"),
    0x0020: ("freq/Hz", "<f4"),
    0x0021: ("|Ewe|/V", "<f4"),
    0x0022: ("|I|/A", "<f4"),
    0x0023: ("Phase(Z)/deg", "<f4"),
    0x0024: ("|Z|/Ohm", "<f4"),
    0x0025: ("Re(Z)/Ohm", "<f4"),
    0x0026: ("-Im(Z)/Ohm", "<f4"),
    0x0027: ("I Range", "<u2"),
    0x0046: ("P/W", "<f4"),
    0x004A: ("Energy/W.h", "<f8"),
    0x004B: ("Analog OUT/V", "<f4"),
    0x004C: ("<I>/mA", "<f4"),
    0x004D: ("<Ewe>/V", "<f4"),
    0x004E: ("Cs-2/µF-2", "<f4"),
    0x0060: ("|Ece|/V", "<f4"),
    0x0062: ("Phase(Zce)/deg", "<f4"),
    0x0063: ("|Zce|/Ohm", "<f4"),
    0x0064: ("Re(Zce)/Ohm", "<f4"),
    0x0065: ("-Im(Zce)/Ohm", "<f4"),
    0x007B: ("Energy charge/W.h", "<f8"),
    0x007C: ("Energy discharge/W.h", "<f8"),
    0x007D: ("Capacitance charge/µF", "<f8"),
    0x007E: ("Capacitance discharge/µF", "<f8"),
    0x0083: ("Ns", "<u2"),
    0x00A3: ("|Estack|/V", "<f4"),
    0x00A8: ("Rcmp/Ohm", "<f4"),
    0x00A9: ("Cs/µF", "<f4"),
    0x00AC: ("Cp/µF", "<f4"),
    0x00AD: ("Cp-2/µF-2", "<f4"),
    0x00AE: ("<Ewe>/V", "<f4"),
    0x00F1: ("|E1|/V", "<f4"),
    0x00F2: ("|E2|/V", "<f4"),
    0x010F: ("Phase(Z1) / deg", "<f4"),
    0x0110: ("Phase(Z2) / deg", "<f4"),
    0x012D: ("|Z1|/Ohm", "<f4"),
    0x012E: ("|Z2|/Ohm", "<f4"),
    0x014B: ("Re(Z1)/Ohm", "<f4"),
    0x014C: ("Re(Z2)/Ohm", "<f4"),
    0x0169: ("-Im(Z1)/Ohm", "<f4"),
    0x016A: ("-Im(Z2)/Ohm", "<f4"),
    0x0187: ("<E1>/V", "<f4"),
    0x0188: ("<E2>/V", "<f4"),
    0x01A6: ("Phase(Zstack)/deg", "<f4"),
    0x01A7: ("|Zstack|/Ohm", "<f4"),
    0x01A8: ("Re(Zstack)/Ohm", "<f4"),
    0x01A9: ("-Im(Zstack)/Ohm", "<f4"),
    0x01AA: ("<Estack>/V", "<f4"),
    0x01AE: ("Phase(Zwe-ce)/deg", "<f4"),
    0x01AF: ("|Zwe-ce|/Ohm", "<f4"),
    0x01B0: ("Re(Zwe-ce)/Ohm", "<f4"),
    0x01B1: ("-Im(Zwe-ce)/Ohm", "<f4"),
    0x01B2: ("(Q-Qo)/C", "<f4"),
    0x01B3: ("dQ/C", "<f4"),
    0x01B9: ("<Ece>/V", "<f4"),
    0x01CE: ("Temperature/°C", "<f4"),
    0x01D3: ("Q charge/discharge/mA.h", "<f8"),
    0x01D4: ("half cycle", "<u4"),
    0x01D5: ("z cycle", "<u4"),
    0x01D7: ("<Ece>/V", "<f4"),
    0x01D9: ("THD Ewe/%", "<f4"),
    0x01DA: ("THD I/%", "<f4"),
    0x01DC: ("NSD Ewe/%", "<f4"),
    0x01DD: ("NSD I/%", "<f4"),
    0x01DF: ("NSR Ewe/%", "<f4"),
    0x01E0: ("NSR I/%", "<f4"),
    0x01E6: ("|Ewe h2|/V", "<f4"),
    0x01E7: ("|Ewe h3|/V", "<f4"),
    0x01E8: ("|Ewe h4|/V", "<f4"),
    0x01E9: ("|Ewe h5|/V", "<f4"),
    0x01EA: ("|Ewe h6|/V", "<f4"),
    0x01EB: ("|Ewe h7|/V", "<f4"),
    0x01EC: ("|I h2|/A", "<f4"),
    0x01ED: ("|I h3|/A", "<f4"),
    0x01EE: ("|I h4|/A", "<f4"),
    0x01EF: ("|I h5|/A", "<f4"),
    0x01F0: ("|I h6|/A", "<f4"),
    0x01F1: ("|I h7|/A", "<f4"),
}


# Relates the offset in the log DATA to the corresponding dtype.
# NOTE: The safety limits are maybe at 0x200?
# NOTE: The log also seems to contain the settings again. These are left
# away for now.
# NOTE: Looking at .mpl files, the log module appears to consist of
# multiple 'modify on' sections that start with an OLE timestamp.
log_dtypes = {
    0x0009: ("channel_number", "|u1"),
    0x00AB: ("channel_sn", "<u2"),
    0x01F8: ("ewe_ctrl_min", "<f4"),
    0x01FC: ("ewe_ctrl_max", "<f4"),
    0x0249: ("ole_timestamp", "<f8"),
    0x0251: ("filename", "pascal"),
    0x0351: ("host", "pascal"),
    0x0384: ("address", "pascal"),
    0x03B7: ("ec_lab_version", "pascal"),
    0x03BE: ("server_version", "pascal"),
    0x03C5: ("interpreter_version", "pascal"),
    0x03CF: ("device_sn", "pascal"),
    0x0922: ("averaging_points", "|u1"),
}


def _parse_settings(data: bytes) -> dict:
    """Parses the contents of settings modules into a dictionary.

    Note
    ----
    Unfortunately this data contains a few pascal strings and some 0x00
    padding, which seems to be incompatible with simply specifying a
    struct in np.dtype and using np.frombuffer() to read the whole thing
    in.

    The offsets from the start of the data part are hardcoded in as they
    do not seem to change. (Maybe watch out for very long comments that
    could span over the entire padding.)

    Parameters
    ----------
    data
        The module data bytes to parse through.

    Returns
    -------
    dict
        A dict with the contents parsed and structured.

    """
    settings = {}
    # First parse the settings right at the top of the data block.
    technique, params_dtype = technique_params_dtypes[data[0x0000]]
    settings["technique"] = technique
    for offset, (name, dtype) in settings_dtypes.items():
        settings[name] = read_value(data, offset, dtype)
    # Then determine the technique parameters. The parameters' offset
    # changes depending on the technique present and apparently on some
    # other factor that is unclear to me.
    params_offset = None
    for offset in [0x0572, 0x1845, 0x1846]:
        logging.debug(f"Trying to find the technique parameters at {offset}.")
        n_params = read_value(data, offset + 0x0002, "<u2")
        if isinstance(params_dtype, dict):
            # The params_dtype has multiple possible lengths if it's a
            # dictionary.
            for dtype in params_dtype.values():
                if len(dtype) == n_params:
                    params_dtype = dtype
                    params_offset = offset
        elif len(params_dtype) == n_params:
            params_offset = offset
            logging.debug(f"Determined  at 0x{offset:x}.")
            break
    if params_offset is None:
        raise NotImplementedError(
            "Unknown parameter offset or unrecognized technique dtype."
        )
    logging.debug(f"Reading number of parameter sequences at 0x{params_offset:x}.")
    ns = read_value(data, params_offset, "<u2")
    logging.debug(f"Reading {ns} parameter sequences of {n_params} parameters.")
    settings["params"] = read_values(data, params_offset + 0x0004, params_dtype, ns)
    return settings


def _construct_data_dtype(column_ids: list[int]) -> tuple[np.dtype, dict]:
    """Puts together a dtype from a list of data column IDs.

    Note
    ----
    The binary layout of the data in the MPR file is described by the
    sequence of column ID numbers in the file header. This function
    converts that sequence into a numpy dtype which can then be used to
    load data from the file with np.frombuffer().

    Some column IDs refer to small values (flags) which are packed into
    a single byte. The second return value is a dict describing the bit
    masks with which to extract these columns from the flags byte.

    Parameters
    ----------
    column_ids
        A list of column IDs.

    Returns
    -------
    tuple[nd.dtype, dict]
        A numpy dtype for the given columns, a dict of flags.

    """
    column_dtypes = []
    flags = {}
    for column_id in column_ids:
        if column_id in flag_columns:
            name, bitmask, shift = flag_columns[column_id]
            flags[name] = (bitmask, shift)
            if ("flags", "|u1") not in column_dtypes:
                # Flags column only needs to be added once.
                logging.debug("Found flags column.")
                column_dtypes.append(("flags", "|u1"))
        elif column_id in data_column_dtypes:
            logging.debug(
                f"Found {data_column_dtypes[column_id]} ({column_id}) column."
            )
            column_dtypes.append(data_column_dtypes[column_id])
        else:
            raise NotImplementedError(
                f"Column ID {column_id} after column {column_dtypes[-1][0]} "
                f"is unknown."
            )
    return np.dtype(column_dtypes), flags


def _parse_data(data: bytes, version: int) -> dict:
    """Parses through the contents of data modules.

    Parameters
    ----------
    data
        The module data to parse through.
    version
        The version of the data module.

    Returns
    -------
    dict
        A modified dict with the parsed contents.

    """
    n_datapoints = read_value(data, 0x0000, "<u4")
    n_columns = read_value(data, 0x0004, "|u1")
    column_ids = read_values(data, 0x0005, "<u2", n_columns)
    data_dtype, flags = _construct_data_dtype(column_ids)
    # Depending on the version in the header, the data points start at a
    # slightly different point in the data part.
    if version == 2:
        offset = 0x0195
    elif version == 3:
        offset = 0x0196
    else:
        raise NotImplementedError(f"Unknown data module version: {version}")
    logging.debug(
        f"Reading {n_datapoints} datapoints at an offset of 0x{offset:x} bytes."
    )
    datapoints = read_values(data, offset, data_dtype, n_datapoints)
    if flags:
        logging.debug("Extracting flag values.")
        for datapoint in datapoints:
            for name, (bitmask, shift) in flags.items():
                datapoint[name] = (datapoint["flags"] & bitmask) >> shift
    data = {
        "n_datapoints": n_datapoints,
        "n_columns": n_columns,
        "datapoints": datapoints,
    }
    return data


def _parse_log(data: bytes) -> dict:
    """Parses through the contents of log modules.

    Parameters
    ----------
    data
        The module data to parse through.

    Returns
    -------
    dict
        A modified dict with the parsed contents.

    """
    log = {}
    for offset, (name, dtype) in log_dtypes.items():
        log[name] = read_value(data, offset, dtype)
    return log


def _parse_loop(data: bytes) -> dict:
    """Parses through the contents of loop modules.

    Parameters
    ----------
    data
        The module data to parse through.

    Returns
    -------
    dict
        A modified dict with the parsed contents.

    """
    n_indexes = read_value(data, 0x0000, "<u4")
    indexes = read_values(data, 0x0004, "<u4", n_indexes)
    loop = {"n_indexes": n_indexes, "indexes": indexes}
    return loop


def _read_modules(file: TextIOWrapper) -> list:
    """Reads in modules from the given file object.

    Parameters
    ----------
    file
        The open file object to read.

    Returns
    -------
    list
        Returns a list of modules with corresponding header and data.

    """
    logging.debug("Reading `.mpr` modules.")
    modules = []
    while file.read(len(b"MODULE")) == b"MODULE":
        header_bytes = file.read(module_header_dtype.itemsize)
        header = read_value(header_bytes, 0, module_header_dtype)
        data_bytes = file.read(header["length"])
        modules.append({"header": header, "data": data_bytes})
        logging.debug(f"Read '{header['short_name']}' module.")
    return modules


def parse_mpr(path: str) -> list[dict]:
    """Parses an EC-Lab MPR file.

    Parameters
    ----------
    path
        Filepath of the EC-Lab MPR file to read in.

    Returns
    -------
    list[dict]
        A list of modules containing parsed module data.

    """
    file_magic = b"BIO-LOGIC MODULAR FILE\x1a                         \x00\x00\x00\x00"
    with open(path, "rb") as mpr:
        logging.debug(f"Checking the file magic.")
        if mpr.read(len(file_magic)) != file_magic:
            raise ValueError("Invalid file magic for given `.mpr` file.")
        modules = _read_modules(mpr)
    for module in modules:
        name = module["header"]["short_name"]
        if name == "VMP Set   ":
            logging.debug("Parsing settings module.")
            module["data"] = _parse_settings(module["data"])
        elif name == "VMP data  ":
            # The data points' offset depends on the module version.
            logging.debug("Parsing data module.")
            version = module["header"]["version"]
            module["data"] = _parse_data(module["data"], version)
        elif name == "VMP LOG   ":
            logging.debug("Parsing log module.")
            module["data"] = _parse_log(module["data"])
        elif name == "VMP loop  ":
            logging.debug("Parsing loop module.")
            module["data"] = _parse_loop(module["data"])
        else:
            raise NotImplementedError(f"Unknown module {name}.")
    return modules
