#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""
import argparse
import os

import pandas as pd

from .mpr_parser import parse_mpr
from .mps_parser import parse_mps
from .mpt_parser import parse_mpt


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
    this_path = os.path.join(head, tail+ext)
    return this_path


def mpr_to_df(mpr_path: str) -> pd.DataFrame:
    """Extracts the data from an MPR file and returns it as a DataFrame.

    Parameters
    ----------
    mpr_path
        The path to the MPR file to read in.

    Returns
    -------
    pd.DataFrame
        The data parsed from the MPR file.

    """
    mpr = parse_mpr(mpr_path)
    mpr_records = mpr[1]['data']['data_points']
    mpr_df = pd.DataFrame.from_dict(mpr_records)
    return mpr_df


def mpr_to_csv(mpr_path: str, csv_path: str = None) -> None:
    """Extracts the data from an MPR file and writes it to a CSV file.

    Parameters
    ----------
    mpr_path
        The path to the MPR file to read in.
    csv_path (optional)
        Path to the CSV file to write. Defaults to construct the
        filename from the mpt_path.

    """
    mpr_df = mpr_to_df(mpr_path)
    if csv_path:
        mpr_df.to_csv(csv_path, float_format='%.15f')
    mpr_df.to_csv(_construct_path(mpr_path, '.csv'), float_format='%.15f',
                  index=False)


def mpr_to_xlsx(mpr_path: str, excel_path: str = None) -> None:
    """Extracts the data from an MPR file and writes it to an Excel file.

    Parameters
    ----------
    mpr_path
        The path to the MPR file to read in.
    excel_path (optional)
        Path to the Excel file to write. Defaults to construct the
        filename from the mpt_path.

    """
    mpr_df = mpr_to_df(mpr_path)
    if excel_path:
        mpr_df.to_excel(excel_path, index=False)
    mpr_df.to_excel(_construct_path(mpr_path, '.xlsx'), index=False)


def mpt_to_df(mpt_path: str) -> pd.DataFrame:
    """Extracts the data from an MPT file and returns it as a DataFrame.

    Parameters
    ----------
    mpt_path
        The path to the MPT file to read in.

    Returns
    -------
    pd.DataFrame
        The data parsed from the MPT file.

    """
    mpt = parse_mpt(mpt_path)
    mpt_records = mpt['data']
    mpt_df = pd.DataFrame.from_dict(mpt_records)
    return mpt_df


def mpt_to_csv(mpt_path: str, csv_path: str = None) -> None:
    """Extracts the data from an MPT file and writes it to a CSV file.

    Parameters
    ----------
    mpt_path
        The path to the MPT file to read in.
    csv_path (optional)
        Path to the CSV file to write. Defaults to construct the
        filename from the mpt_path.

    """
    mpt_df = mpr_to_df(mpt_path)
    if csv_path:
        mpt_df.to_csv(csv_path, float_format='%.15f', index=False)
    mpt_df.to_csv(_construct_path(mpt_path, '.csv'), float_format='%.15f',
                  index=False)


def mpt_to_xlsx(mpt_path: str, excel_path: str = None) -> None:
    """Extracts the data from an MPT file and writes it to an Excel file.

    Parameters
    ----------
    mpt_path
        The path to the MPT file to read in.
    excel_path (optional)
        Path to the Excel file to write. Defaults to construct the
        filename from the mpt_path.

    """
    mpt_df = mpr_to_df(mpt_path)
    if excel_path:
        mpt_df.to_excel(excel_path, index=False)
    mpt_df.to_excel(_construct_path(mpt_path, '.xlsx'), index=False)


def mps_to_dfs(mps_path: str) -> list[pd.DataFrame]:
    """Extracts the data from the techniques of an MPS file.

    Parameters
    ----------
    mps_path
        The path to the MPS file to read in.

    Returns
    -------
    list[pd.DataFrame]
        The DataFrames from all the techniques specified in the MPS
        file.

    """
    mps = parse_mps(mps_path, load_data=True)
    dfs = []
    for technique in mps['techniques']:
        if 'data' not in technique.keys():
            continue
        data = technique['data']
        # It's intentional to prefer MPT over MPR files.
        if 'mpt' in data.keys():
            mpt_records = data['mpt']['data']
            mpt_df = pd.DataFrame.from_dict(mpt_records)
            dfs.append(mpt_df)
        elif 'mpr' in data.keys():
            mpr_records = data['mpr'][1]['data']['datapoints']
            mpr_df = pd.DataFrame.from_dict(mpr_records)
            dfs.append(mpr_df)
    return dfs


def mps_to_csv(mps_path: str, csv_path: str = None) -> None:
    """Extracts the data from the techniques of an MPS file and writes
    it to a number of CSV files.

    Parameters
    ----------
    mps_path
        The path to the MPS file to read in.
    csv_path
        Base path to use for the CSV files. The function automatically
        appends the technique number to the file name. Defaults to
        construct the CSV filename from the mpt_path.

    """
    dfs = mps_to_dfs(mps_path)
    for i, df in enumerate(dfs):
        if csv_path:
            df.to_csv(
                _construct_path(csv_path, f'_{i+1:02d}.csv'),
                float_format='%.15f', index=False)
        df.to_csv(
            _construct_path(mps_path, f'_{i+1:02d}.csv'),
            float_format='%.15f', index=False)


def mps_to_xlsx(mps_path: str, excel_path: str = None):
    """Extracts the data from the techniques of an MPS file and writes
    it to multiple sheets of an Excel file.

    Parameters
    ----------
    mps_path
        The path to the MPS file to read in.
    excel_path
        Path to the Excel file to write. Defaults to construct the
        filename from the mpt_path.

    """
    dfs = mps_to_dfs(mps_path)
    if not excel_path:
        excel_path = _construct_path(mps_path, '.xlsx')
    with pd.ExcelWriter(excel_path) as writer:
        for i, df in enumerate(dfs):
            df.to_excel(writer, sheet_name=f'{i+1:02d}' , index=False)


def _parse_arguments() -> argparse.Namespace:
    """Parses the arguments if invoked from the command line."""
    parser = argparse.ArgumentParser(
        description="Process the given file and write it to the specified "
                    "output file or to a file in the specified format.\n"
                    "You must specify either the file to write to or the file "
                    "format.")
    parser.add_argument("file", type=str, help="the file to read")
    parser.add_argument(
        "-f", "--format", type=str, choices=['csv', 'xlsx'], default='csv',
        help="type of file to write")
    args = parser.parse_args()
    return args


def _run():
    args = _parse_arguments()
    __, file_ext = os.path.splitext(args.file)
    if file_ext == '.mpr':
        if args.format == 'csv':
            mpr_to_csv(args.file)
        elif args.format == 'xlsx':
            mpr_to_xlsx(args.file)
    elif file_ext == '.mpt':
        if args.format == 'csv':
            mpt_to_csv(args.file)
        elif args.format == 'xlsx':
            mpt_to_xlsx(args.file)
    elif file_ext == '.mps':
        if args.format == 'csv':
            mps_to_csv(args.file)
        elif args.format == 'xlsx':
            mps_to_xlsx(args.file)


if __name__ == '__main__':
    _run()


# TODO: to_df, to_csv, to_xlsx
# TODO: