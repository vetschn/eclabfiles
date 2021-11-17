#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read BioLogic's EC-Lab ASCII data files into dicts.

Author:         Nicolas Vetsch (veni@empa.ch / vetschnicolas@gmail.com)
Organisation:   EMPA Dübendorf, Materials for Energy Conversion (501)
Date:           2021-10-11

"""
import csv
import logging
import re
from io import StringIO

from eclabfiles.techniques import construct_params
from eclabfiles.utils import literal_eval


def _parse_technique_params(technique: str, settings: list[str]) -> dict:
    """Finds the appropriate set of technique parameters.

    Additionally takes care of the techniques that have a changing
    number of parameters.

    Parameters
    ----------
    technique
        The name of the technique.
    settings
        The lines containing all the settings including the technique
        parameters.

    Returns
    -------
    dict
        A list of parameter keys corresponding to the given technique.

    """
    logging.debug("Parsing technique parameters from `.mpt` header section...")
    params_keys = construct_params(technique, settings)
    logging.debug(
        f"Determined a parameter set of length {len(params_keys)} for "
        f"{technique} technique.")
    params = settings[-len(params_keys):]
    # The sequence param columns are always allocated 20 characters.
    n_sequences = int(len(params[0])/20)
    logging.debug(f"Determined {n_sequences} technique sequences.")
    params_values = []
    for seq in range(1, n_sequences):
        params_values.append(
            [literal_eval(param[seq*20:(seq+1)*20]) for param in params])
    params = [dict(zip(params_keys, values)) for values in params_values]
    return params, len(params_keys)


def _parse_loop_indexes(loops_lines: list[str]) -> dict:
    """Parses the loops section of an .mpt file header.

    The function puts together the loop indexes like they are saved in
    .mpr files.

    Parameters
    ----------
    loops_lines
        The .mpt file loops section as a list of strings.

    Returns
    -------
    dict
        A dictionary with the number of loops and the loop indexes.

    """
    logging.debug("Parsing the loops section in the `.mpt` header...")
    n_loops = int(
        re.match(r'Number of loops : (?P<val>.+)', loops_lines[0])['val'])
    loop_indexes = []
    for loop in range(n_loops):
        index = re.match(
            r'Loop (.+) from point number (?P<val>.+) to (.+)',
            loops_lines[loop+1])['val']
        loop_indexes.append(int(index))
    return {'n': n_loops, 'indexes': loop_indexes}


def _parse_header(lines: list[str], n_header_lines: int) -> dict:
    """Parses the header part of an .mpt file including loops.

    Parameters
    ----------
    lines
        All the lines of the .mpt file (except the two very first ones).
    n_header_lines
        The number of header lines from the line after the .mpt file
        magic.

    Returns
    -------
    dict
        A dictionary containing the technique name, the general
        settings, and a list of technique parameters.

    """
    logging.debug("Parsing the `.mpt` header...")
    header = {}
    if n_header_lines == 3:
        logging.debug("No settings or loops present in given .mpt file.")
        return header
    # At this point the first two lines have already been read.
    header_lines = lines[:n_header_lines-3]
    if header_lines[0].startswith(r'Number of loops : '):
        logging.debug(
            "No settings but a loops section present in given .mpt file.")
        header['loops'] = _parse_loop_indexes(header_lines)
        return header
    header_sections = ''.join(header_lines).split(sep='\n\n')
    technique_name = header_sections[0].strip()
    settings_lines = header_sections[1].split('\n')
    header['technique'] = technique_name
    header['params'], n_params = _parse_technique_params(
        technique_name, settings_lines)
    header['settings'] = [line.strip() for line in settings_lines[:-n_params]]
    if len(header_sections) == 3 and header_sections[2]:
        # The header contains a loops section.
        loops_lines = header_sections[2].split('\n')
        header['loops'] = _parse_loop_indexes(loops_lines)
    return header


def _parse_datapoints(lines: list[str], n_header_lines: int) -> list[dict]:
    """Parses the data part of an .mpt file.

    Parameters
    ----------
    lines
        All the lines of the .mpt file as a list.
    n_header_lines
        The number of header lines parsed from the top of the .mpt file.

    Returns
    -------
    list[dict]
        A list of dicts, each corresponding to a single data point.

    """
    # At this point the first two lines have already been read.
    logging.debug("Parsing the datapoints...")
    # Remove the extra column due to an extra tab in .mpt file field
    # names.
    field_names = lines[n_header_lines-3].split('\t')[:-1]
    data_lines = lines[n_header_lines-2:]
    reader = csv.DictReader(
        StringIO(''.join(data_lines)), fieldnames=field_names, delimiter='\t')
    datapoints_str = list(reader)
    datapoints = []
    for datapoint_str in datapoints_str:
        datapoint = {
            key: literal_eval(value) for key, value in datapoint_str.items()}
        datapoints.append(datapoint)
    return datapoints


def parse_mpt(path: str, encoding: str = 'windows-1252') -> dict:
    """Parses an EC-Lab .mpt file.

    Parameters
    ----------
    path
        Filepath of the EC-Lab .mpt file to read in.

    Returns
    -------
    dict
        A dict containing all the parsed .mpt data.

    """
    file_magic = 'EC-Lab ASCII FILE\n'
    with open(path, 'r', encoding=encoding) as mpt:
        if mpt.readline() != file_magic:
            raise ValueError(f"Invalid file magic for given .mpt file: {path}")
        logging.debug(f"Reading `.mpt` file at {path}")
        n_header_lines = int(mpt.readline().strip().split()[-1])
        lines = mpt.readlines()
    header = _parse_header(lines, n_header_lines)
    datapoints = _parse_datapoints(lines, n_header_lines)
    return {'header': header, 'datapoints': datapoints}
