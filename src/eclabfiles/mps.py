#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read BioLogic's EC-Lab settings files into dicts.

Author:         Nicolas Vetsch (veni@empa.ch / vetschnicolas@gmail.com)
Organisation:   EMPA Dübendorf, Materials for Energy Conversion (501)
Date:           2021-10-13

"""
import glob
import logging
import os

from eclabfiles.mpr import parse_mpr
from eclabfiles.mpt import parse_mpt
from eclabfiles.techniques import construct_params
from eclabfiles.utils import literal_eval


def _parse_header(headers: list[str]) -> dict:
    """Parses the header of a .mps file."""
    logging.debug("Parsing the `.mps` header...")
    header = {}
    header['filename'] = headers[0].strip().split()[-1]
    header['general_settings'] = [
        line.strip() for line in headers[1].split('\n')]
    return header


def _parse_techniques(technique_sections: list[str]) -> list:
    """Parses the techniques section of a .mps file."""
    logging.debug("Parsing the techniques section of the `.mps` file...")
    techniques = []
    for section in technique_sections:
        technique = {}
        technique_lines = section.split('\n')
        technique_name = technique_lines[1]
        technique['technique'] = technique_name
        params = technique_lines[2:]
        params_keys = construct_params(technique_name, params)
        logging.debug(
            f"Determined a parameter set of length {len(params_keys)} for "
            f"{technique_name} technique.")
        # The sequence param columns are always allocated 20 characters.
        n_sequences = int(len(params[0])/20)
        logging.debug(f"Determined {n_sequences} technique sequences.")
        params_values = []
        for seq in range(1, n_sequences):
            params_values.append(
                [literal_eval(param[seq*20:(seq+1)*20]) for param in params])
        technique['params'] = [
            dict(zip(params_keys, values)) for values in params_values]
        techniques.append(technique)
    return techniques


def _load_technique_data(
    techniques: list[dict],
    mpr_paths: list[str],
    mpt_paths: list[str]
) -> dict:
    """Tries to load technique data from the same folder.

    Parameters
    ----------
    techniques
        The previously parsed list of technique dicts.
    mpr_paths
        A list of paths to .mpr files to read in.
    mpt_paths
        A list of paths to .mpt files to read in.

    Returns
    -------
    list[dict]
        The list of technique dictionaries now including any data.

    """
    logging.debug(
        f"Trying to load data from {len(mpr_paths)} .mpr files and "
        f"{len(mpt_paths)} .mpt files...")
    # Determine the number of files that are expected and initialize the
    # data sections. Loops and waits do not write data.
    expected_techniques = [
        technique for technique in techniques
        if technique['technique'] not in {'Loop', 'Wait'}]
    data = {}
    if not expected_techniques:
        return data
    if len(expected_techniques) == len(mpt_paths):
        data['mpt'] = [parse_mpt(path) for path in mpt_paths]
    if len(expected_techniques) == len(mpr_paths):
        data['mpr'] = [parse_mpr(path) for path in mpr_paths]
    return data


def parse_mps(
    path: str,
    encoding: str = 'windows-1252',
    load_data: bool = True
) -> dict:
    """Parses an EC-Lab .mps file.

    If there are .mpr or .mpt files present in the same folder, those
    files are read in and returned as well. .mpt files are preferred, as
    they contain slightly more info.

    Parameters
    ----------
    path
        Filepath of the EC-Lab .mps file to read in.
    parse_data
        Whether to parse the associated data

    Returns
    -------
    dict
        A dict containing all the parsed .mps data and .mpt/.mpr data in
        case it exists.

    """
    file_magic = 'EC-LAB SETTING FILE\n'
    with open(path, 'r', encoding=encoding) as mps:
        if mps.readline() != file_magic:
            raise ValueError("Invalid file magic for given .mps file.")
        logging.debug("Reading `.mps` file...")
        sections = mps.read().split('\n\n')
    n_linked_techniques = int(sections[0].strip().split()[-1])
    header = _parse_header(sections[1:3])
    techniques = _parse_techniques(sections[3:])
    if len(techniques) != n_linked_techniques:
        raise ValueError(
            f"The number of parsed techniques ({len(techniques)}) does not "
            f"match the number of linked techniques in the header "
            f"({n_linked_techniques}).")
    base_path, __ = os.path.splitext(path)
    mpr_paths = glob.glob(base_path + '*.mpr')
    mpt_paths = glob.glob(base_path + '*.mpt')
    if (load_data and (mpr_paths or mpt_paths)):
        data = _load_technique_data(techniques, mpr_paths, mpt_paths)
        return {'header': header, 'techniques': techniques, 'data': data}
    return {'header': header, 'techniques': techniques}
