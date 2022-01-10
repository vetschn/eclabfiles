#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Processing of BioLogic's EC-Lab ASCII export files.

File Structure of `.mpt` Files
``````````````````````````````

These human-readable files are sectioned into headerlines and datalines.
The header part at is made up of information that can be found in the
settings, log and loop modules of the binary `.mpr` file.


Structure of Parsed Data
````````````````````````

The `process` function returns a tuple of data and metadata. The data is
structured into a list of dicts, i.e. [{column -> value}, ...,
{column -> value}]. If the file contains a settings header, each
timestep will contain a POSIX timestamp in the `"uts"` column.

The metadata dict is structured as follows:

.. codeblock:: python

    {
        "raw": str, (optional)                      # The raw file header if present.
        "settings": { (optional)                    # Settings if the file has a header.
            "posix_timestamp": float,               # POSIX timestamp if present.
            "technique": str,                       # Technique name.
        },
        "params": [ (optional)                      # Technique parameter sequences
            {"param1": float, "param2": str, ...},
            ...,
            {"param1": float, "param2": str, ...},
        ],
        "units": {"time": "s", "mode": None, ...},  # Units of the data columns in order.
        "loops": { (optional)                       # Loops if file header contains a loops section.
            "n_indexes": int,
            "indexes": list[int],
        }
    }

.. codeauthor:: Nicolas Vetsch <vetschnicolas@gmail.com>
"""
import logging
import re
import warnings

from dateutil import parser as dateparser

from eclabfiles.techniques import technique_params

logger = logging.getLogger(__name__)


# Maps EC-Lab's "canonical" column names to proper names and unit.
column_units = {
    '"Ri"/Ohm': ("'Ri'", "Ohm"),
    "-Im(Z)/Ohm": ("-Im(Z)", "Ohm"),
    "-Im(Zce)/Ohm": ("-Im(Zce)", "Ohm"),
    "-Im(Zwe-ce)/Ohm": ("-Im(Zwe-ce)", "Ohm"),
    "(Q-Qo)/C": ("(Q-Qo)", "C"),
    "(Q-Qo)/mA.h": ("(Q-Qo)", "mA·h"),
    "<Ece>/V": ("<Ece>", "V"),
    "<Ewe>/V": ("<Ewe>", "V"),
    "<I>/mA": ("<I>", "mA"),
    "|Ece|/V": ("|Ece|", "V"),
    "|Energy|/W.h": ("|Energy|", "W·h"),
    "|Ewe|/V": ("|Ewe|", "V"),
    "|I|/A": ("|I|", "A"),
    "|Y|/Ohm-1": ("|Y|", "S"),
    "|Z|/Ohm": ("|Z|", "Ohm"),
    "|Zce|/Ohm": ("|Zce|", "Ohm"),
    "|Zwe-ce|/Ohm": ("|Zwe-ce|", "Ohm"),
    "Analog IN 1/V": ("Analog IN 1", "V"),
    "Analog IN 2/V": ("Analog IN 2", "V"),
    "Capacitance charge/µF": ("Capacitance charge", "µF"),
    "Capacitance discharge/µF": ("Capacitance discharge", "µF"),
    "Capacity/mA.h": ("Capacity", "mA·h"),
    "charge time/s": ("charge time", "s"),
    "Conductivity/S.cm-1": ("Conductivity", "S/cm"),
    "control changes": ("control changes", None),
    "control/mA": ("control_I", "mA"),
    "control/V": ("control_V", "V"),
    "control/V/mA": ("control_V/I", "V/mA"),
    "counter inc.": ("counter inc.", None),
    "Cp-2/µF-2": ("Cp⁻²", "µF⁻²"),
    "Cp/µF": ("Cp", "µF"),
    "Cs-2/µF-2": ("Cs⁻²", "µF⁻²"),
    "Cs/µF": ("Cs", "µF"),
    "cycle number": ("cycle number", None),
    "cycle time/s": ("cycle time", "s"),
    "d(Q-Qo)/dE/mA.h/V": ("d(Q-Qo)/dE", "mA·h/V"),
    "dI/dt/mA/s": ("dI/dt", "mA/s"),
    "discharge time/s": ("discharge time", "s"),
    "dQ/C": ("dQ", "C"),
    "dq/mA.h": ("dq", "mA·h"),
    "dQ/mA.h": ("dQ", "mA·h"),
    "Ece/V": ("Ece", "V"),
    "Ecell/V": ("Ecell", "V"),
    "Efficiency/%": ("Efficiency", "%"),
    "Energy charge/W.h": ("Energy charge", "W·h"),
    "Energy discharge/W.h": ("Energy discharge", "W·h"),
    "Energy/W.h": ("Energy", "W·h"),
    "error": ("error", None),
    "Ewe-Ece/V": ("Ewe-Ece", "V"),
    "Ewe/V": ("Ewe", "V"),
    "freq/Hz": ("freq", "Hz"),
    "half cycle": ("half cycle", None),
    "I Range": ("I Range", None),
    "I/mA": ("I", "mA"),
    "Im(Y)/Ohm-1": ("Im(Y)", "S"),
    "mode": ("mode", None),
    "Ns changes": ("Ns changes", None),
    "Ns": ("Ns", None),
    "NSD Ewe/%": ("NSD Ewe", "%"),
    "NSD I/%": ("NSD I", "%"),
    "NSR Ewe/%": ("NSR Ewe", "%"),
    "NSR I/%": ("NSR I", "%"),
    "ox/red": ("ox/red", None),
    "P/W": ("P", "W"),
    "Phase(Y)/deg": ("Phase(Y)", "deg"),
    "Phase(Z)/deg": ("Phase(Z)", "deg"),
    "Phase(Zce)/deg": ("Phase(Zce)", "deg"),
    "Phase(Zwe-ce)/deg": ("Phase(Zwe-ce)", "deg"),
    "Q charge/discharge/mA.h": ("Q charge/discharge", "mA·h"),
    "Q charge/mA.h": ("Q charge", "mA·h"),
    "Q charge/mA.h/g": ("Q charge", "mA·h/g"),
    "Q discharge/mA.h": ("Q discharge", "mA·h"),
    "Q discharge/mA.h/g": ("Q discharge", "mA·h/g"),
    "R/Ohm": ("R", "Ohm"),
    "Rcmp/Ohm": ("Rcmp", "Ohm"),
    "Re(Y)/Ohm-1": ("Re(Y)", "S"),
    "Re(Y)/Ohm-1": ("Re(Y)", "S"),
    "Re(Z)/Ohm": ("Re(Z)", "Ohm"),
    "Re(Z)/Ohm": ("Re(Z)", "Ohm"),
    "Re(Zce)/Ohm": ("Re(Zce)", "Ohm"),
    "Re(Zce)/Ohm": ("Re(Zce)", "Ohm"),
    "Re(Zwe-ce)/Ohm": ("Re(Zwe-ce)", "Ohm"),
    "Re(Zwe-ce)/Ohm": ("Re(Zwe-ce)", "Ohm"),
    "step time/s": ("step time", "s"),
    "THD Ewe/%": ("THD Ewe", "%"),
    "THD I/%": ("THD I", "%"),
    "time/s": ("time", "s"),
    "x": ("x", None),
    "z cycle": ("z cycle", None),
}


def _process_header(lines: list[str]) -> tuple[dict, list, dict]:
    """Processes the header lines.

    Parameters
    ----------
    lines
        The header lines, starting at line 3 (which is an empty line),
        right after the `"Nb header lines : "` line.

    Returns
    -------
    tuple[dict, list, dict]
        A dictionary containing the settings, parameter sequences and
        and a dictionary containing the loop indexes.

    """
    settings = params = loops = None
    sections = "\n".join(lines).split("\n\n")
    # Can happen that no settings are present but just a loops section.
    if sections[1].startswith("Number of loops : "):
        logger.info("File only contains a loop section.")
    # Again, we need the acquisition time to get timestamped data.
    technique = sections[1].strip()
    settings_lines = sections[2].split("\n")
    technique, params_keys = technique_params(technique, settings_lines)
    params = settings_lines[-len(params_keys) :]
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
    settings_lines = [line.strip() for line in settings_lines[: -len(params_keys)]]
    # Parse the acquisition timestamp.
    # NOTE: These are the formats I have seen:
    # "%m/%d/%Y %H:%M:%S", "%m.%d.%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S.%f"
    timestamp_re = re.compile(r"Acquisition started on : (?P<val>.+)")
    timestamp_match = timestamp_re.search("\n".join(settings_lines))
    timestamp = dateparser.parse(timestamp_match["val"], dayfirst=False)
    if sections[-1].startswith("Number of loops : "):
        # The header contains a loops section.
        loops_lines = sections[-1].split("\n")
        n_loops = int(loops_lines[0].split(":")[-1])
        indexes = []
        for n in range(n_loops):
            index = loops_lines[n + 1].split("to")[0].split()[-1]
            indexes.append(int(index))
        loops = {"n_loops": n_loops, "indexes": indexes}
    settings = {
        "posix_timestamp": timestamp.timestamp(),
        "technique": technique,
    }
    return settings, params, loops


def _process_data(lines: list[str]) -> tuple[list, dict]:
    """Processes the data lines.

    Parameters
    ----------
    lines
        The data lines, starting right after the last header section.
        The first line is an empty line, the column names can be found
        on the second line.

    Returns
    -------
    tuple[dict, dict]
        A dictionary containing the datapoints in records format
        ([{column -> value}, ..., {column -> value}]) and a dictionary
        containing the units indexed by the columns.

    """
    # At this point the first two lines have already been read.
    # Remove extra column due to an extra tab in .mpt file column names.
    names = lines[1].split("\t")[:-1]
    columns, units = zip(*[column_units[n] for n in names])
    data_lines = lines[2:]
    datapoints = []
    for line in data_lines:
        values = line.split("\t")
        datapoint = {}
        for col, val in list(zip(columns, values)):
            datapoint[col] = float(val)
        datapoints.append(datapoint)
    return datapoints, dict(zip(columns, units))


def process(fn: str, encoding: str = "windows-1252") -> tuple[list, dict]:
    """Processes EC-Lab human-readable text export files.

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
    file_magic = "EC-Lab ASCII FILE\n"
    with open(fn, "r", encoding=encoding) as mpt_file:
        assert mpt_file.readline() == file_magic, "Invalid file magic."
        mpt = mpt_file.read()
    lines = mpt.split("\n")
    nb_header_lines = int(lines[0].split()[-1])
    if nb_header_lines < 3:
        raise ValueError(f"Invalid file structure: {fn}")
    header_lines = lines[: nb_header_lines - 3]
    settings, params, loops = _process_header(header_lines)
    data_lines = lines[nb_header_lines - 3 :]
    data, units = _process_data(data_lines)
    # Populate metadata.
    meta = {}
    if settings is not None and params is not None:
        meta["raw"] = "\n".join(header_lines)
        meta["settings"] = settings
        meta["params"] = params
        posix_timestamp = settings["posix_timestamp"]
        for d in data:
            d["uts"] = posix_timestamp + d["time"]
    else:
        warnings.warn("No settings and params present in file.")
    if data is not None and units is not None:
        meta["units"] = units
    else:
        raise ValueError("No data present in file.")
    if loops is not None:
        meta["loops"] = loops
    else:
        logger.info("No loops present in file.")
    return data, meta
