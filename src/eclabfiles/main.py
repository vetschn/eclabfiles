#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Functions for converting parsed EC-Lab file data to DataFrame, .csv
and .xlsx.

See the individual parsers to get an idea of the data formats used.

.. codeauthor:: Nicolas Vetsch <vetschnicolas@gmail.com>
"""
import os

import pandas as pd

from eclabfiles import mpr, mps, mpt


def _construct_fn(other_fn: str, ext: str) -> str:
    """Constructs a new file name from the given name and extension.

    Parameters
    ----------
    other_fn
        The path to some file.
    ext
        The new extension to add to the other_fn.

    Returns
    -------
    str
        A new file name with the given extension.

    """
    head, tail = os.path.split(other_fn)
    tail, __ = os.path.splitext(tail)
    this_fn = os.path.join(head, tail + ext)
    return this_fn


def process(fn: str, encoding: str = "windows-1252", **kwargs) -> tuple[dict, dict]:
    """Processes an EC-Lab file.

    The function finds the file extension and tries to choose the
    correct parser.

    Parameters
    ----------
    fn
        The path to an EC-Lab file.
    encoding
        Encoding of ``fn``, by default "windows-1252".

    Returns
    -------
    tuple[dict, dict]
        The processed file. Data files produce one dictionary containing
        the data and another with metadata. Settings files produce a
        dictionary containing the linked techniques, optionally with the
        data from all techniques loaded in, and another dict with
        metadata. See the respective parser for more information.

    Other Parameters
    ----------------
    load_data
        Whether to try and load data from the same folder as the given
        settings file.
    load_type
        The type of file to load in. Defaults to using binary data
        files. Possible options are "mpr" and "mpt".

    """
    __, ext = os.path.splitext(fn)
    if ext == ".mpt":
        return mpt.process(fn, encoding=encoding)
    if ext == ".mpr":
        return mpr.process(fn, encoding=encoding)
    if ext == ".mps":
        return mps.process(
            fn,
            encoding=encoding,
            load_data=kwargs.get("load_data", False),
            load_type=kwargs.get("load_type", None),
        )
    raise NotImplementedError(f"Unrecognized file extension: {ext}")


def to_df(fn: str, encoding: str = "windows-1252", **kwargs) -> pd.DataFrame:
    """Extracts data from an EC-Lab file and returns it as DataFrame.

    The function finds the file extension and tries to choose the
    correct parser. The DataFrame.attrs will contain any metadata.

    If the file is a settings file, this returns a MultiIndex Dataframe,
    the first index being the technique number. The DataFrame.attrs will
    contain the settings file metadata as well as all the linked
    techniques' metadata.

    Parameters
    ----------
    fn
        The path to an EC-Lab file.
    encoding
        Encoding of ``fn``, by default "windows-1252".

    Returns
    -------
    pd.DataFrame
        Data parsed from an .mpt/.mpr file or the data parsed from all
        techniques in an .mps file. Optionally also the parsed data is
        returned.

    Other Parameters
    ----------------
    load_type
        The type of file to load in. Defaults to using binary data
        files. Possible options are "mpr" and "mpt".

    """
    __, ext = os.path.splitext(fn)
    if ext in {".mpt", ".mpr"}:
        data, meta = process(fn, encoding=encoding)
        df = pd.DataFrame.from_records(data)
        df.attrs = meta
    elif ext == ".mps":
        techniques, meta = mps.process(
            fn,
            encoding=encoding,
            load_data=True,
            load_type=kwargs.get("load_type", "mpr"),
        )
        dfs = {}
        for num, technique in techniques.items():
            if "data" in technique:
                dfs[num] = pd.DataFrame.from_records(technique.pop("data"))
        df = pd.concat(dfs, names=["Technique"])
        df.attrs = meta | {"techniques": techniques}
    else:
        raise ValueError(f"Unrecognized file extension: {ext}")
    return df


def to_csv(fn: str, encoding: str = "windows-1252", csv_fn: str = None) -> None:
    """Extracts the data from an EC-Lab file and writes it to csv.

    Parameters
    ----------
    fn
        The path to the EC-Lab file to read in.
    encoding
        Encoding of ``fn``, by default "windows-1252".
    csv_fn
        Base path to use for the csv file. Defaults to generate the csv
        file name from the input file name.

    """
    df = to_df(fn, encoding=encoding)
    if csv_fn is None:
        csv_fn = _construct_fn(fn, ".csv")
    df.to_csv(csv_fn, float_format="%.15f")


def to_excel(fn: str, encoding: str = "windows-1252", excel_fn: str = None) -> None:
    """Extracts the data from an EC-Lab file and writes it to Excel.

    Parameters
    ----------
    fn
        The path to the EC-Lab file to read in.
    excel_fn
        Path to the Excel file to write. Defaults to generate the xlsx
        file name from the input file name.

    """
    df = to_df(fn, encoding=encoding)
    if excel_fn is None:
        excel_fn = _construct_fn(fn, ".xlsx")
    df.to_excel(excel_fn)
