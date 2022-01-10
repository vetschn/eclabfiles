#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Functions for converting parsed EC-Lab file data to DataFrame, .csv
and .xlsx.

.. codeauthor:: Nicolas Vetsch <vetschnicolas@gmail.com>
"""
import os
from typing import Union

import pandas as pd

from eclabfiles import mpr, mps, mpt


def _construct_path(other_path: str, ext: str) -> str:
    """Constructs a new file path from the given path and extension.

    Parameters
    ----------
    other_path
        The path to some file.
    ext
        The new extension to add to the other_path.

    Returns
    -------
    str
        A new filepath with the given extension.

    """
    head, tail = os.path.split(other_path)
    tail, __ = os.path.splitext(tail)
    this_path = os.path.join(head, tail + ext)
    return this_path


def process(fn: str) -> Union[list, dict]:
    """Processes an EC-Lab file.

    The function finds the file extension and tries to choose the
    correct parser.

    Parameters
    ----------
    fn
        The path to an EC-Lab file (.mpt/.mpr/.mps)

    Returns
    -------
    Union[dict, dict]
        The processed file. Data files return 

    """
    __, ext = os.path.splitext(fn)
    if ext == ".mpt":
        return mpt.process(fn)
    if ext == ".mpr":
        return mpr.process(fn)
    if ext == ".mps":
        return mps.process(fn)
    raise NotImplementedError(f"Unrecognized file extension: {ext}")


def to_df(path: str) -> Union[pd.DataFrame, list[pd.DataFrame]]:
    """Extracts the data from an EC-Lab file and returns it as Pandas
    DataFrame(s)

    The function finds the file extension and tries to choose the
    correct parser. If the file is an .mps settings file, this returns a
    MultiIndex Dataframe.

    Parameters
    ----------
    path
        The path to an EC-Lab file (.mpt/.mpr/.mps)

    Returns
    -------
    pd.DataFrame
        Data parsed from an .mpt/.mpr file or the data parsed from all
        techniques in an .mps file. Optionally also the parsed data is
        returned.

    """
    __, ext = os.path.splitext(path)
    if ext == ".mpt" or ".mpr":
        data, meta = process(path)
        df = pd.DataFrame.from_dict(data)
        df.attrs = meta
    elif ext == ".mps":
        techniques, meta = mps.process(path)
        # TODO
        data = mps["data"]
        dfs = []
        if "mpt" in data.keys():
            # It's intentional to prefer .mpt over .mpr files here as
            # they often contain a few more columns than the .mpr files.
            for mpt in data["mpt"]:
                mpt_records = mpt["datapoints"]
                mpt_df = pd.DataFrame.from_dict(mpt_records)
                dfs.append(mpt_df)
        elif "mpr" in data.keys():
            for mpr in data["mpr"]:
                mpr_records = mpr[1]["data"]["datapoints"]
                mpr_df = pd.DataFrame.from_dict(mpr_records)
                dfs.append(mpr_df)
        else:
            raise ValueError("The given .mps file does not contain any data.")
        return dfs
    else:
        raise ValueError(f"Unrecognized file extension: {ext}")
    return df


def to_csv(path: str, csv_path: str = None) -> None:
    """Extracts the data from an .mpt/.mpr file or from the techniques
    in an .mps file and writes it to a number of .csv files.

    Parameters
    ----------
    path
        The path to the EC-Lab file to read in.
    csv_path
        Base path to use for the .csv files. The function automatically
        appends the technique number to the file name. Defaults to
        construct the .csv filename from the mpt_path.

    """
    df = to_df(path)
    if isinstance(df, pd.DataFrame):
        if csv_path is None:
            csv_path = _construct_path(path, ".csv")
        df.to_csv(csv_path, float_format="%.15f", index=False)
    elif isinstance(df, list):
        for i, df in enumerate(df):
            if csv_path:
                df.to_csv(
                    _construct_path(csv_path, f"_{i+1:02d}.csv"),
                    float_format="%.15f",
                    index=False,
                )
            df.to_csv(
                _construct_path(path, f"_{i+1:02d}.csv"),
                float_format="%.15f",
                index=False,
            )


def to_xlsx(path: str, xlsx_path: str = None) -> None:
    """Extracts the data from an .mpt/.mpr file or from the techniques in
    an .mps file and writes it to an Excel file.

    If the file is an .mps, this method writes the data to numbered
    worksheets in the Excel file.

    Parameters
    ----------
    path
        The path to the EC-Lab file to read in.
    xlsx_path
        Path to the Excel file to write. Defaults to construct the
        filename from the mpt_path.

    """
    df = to_df(path)
    if xlsx_path is None:
        xlsx_path = _construct_path(path, ".xlsx")
    if isinstance(df, pd.DataFrame):
        df.to_excel(xlsx_path, index=False)
    elif isinstance(df, list):
        # pylint: disable=abstract-class-instantiated
        with pd.ExcelWriter(xlsx_path) as writer:
            for i, df in enumerate(df):
                df.to_excel(writer, sheet_name=f"{i+1:02d}", index=False)
