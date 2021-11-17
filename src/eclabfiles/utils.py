#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility functions for the eclabfiles package.

Author:         Nicolas Vetsch (veni@empa.ch / vetschnicolas@gmail.com)
Organisation:   EMPA Dübendorf, Materials for Energy Conversion (501)
Date:           2021-11-17

"""
import ast
import logging
from typing import Any

import numpy as np


def literal_eval(literal: str) -> Any:
    """Evaluates a string as Python literal.

    Parameters
    ----------
    literal
        A string representation of a literal, a float (like 'nan', 'inf'
        or '-inf'), or a non-eval-able string.

    Returns
    -------
    Any
        The result of ast.literal_eval(), of float conversion or the
        stripped input string itself if it is not convertible.

    """
    try:
        return ast.literal_eval(literal)
    except Exception as ex:
        logging.debug(f"Failed to evaluate string literal: {ex}.")
    try:
        return float(literal)
    except ValueError as ex:
        logging.debug(f"Failed to convert string literal to float: {ex}")
    logging.debug(f"Failed to convert string literal. Returning it as str.")
    return literal.strip()


def read_pascal_string(
    pascal_bytes: bytes,
    encoding: str = 'windows-1252'
) -> str:
    """Parses a length-prefixed string given some encoding.

    Parameters
    ----------
    bytes
        The bytes of the string starting at the length-prefix byte.
    encoding
        The encoding of the string to be converted.

    Returns
    -------
    str
        The string decoded from the input bytes.

    """
    if len(pascal_bytes) < pascal_bytes[0] + 1:
        raise ValueError("Insufficient number of bytes.")
    string_bytes = pascal_bytes[1:pascal_bytes[0]+1]
    return string_bytes.decode(encoding)


def read_value(
    data: bytes,
    offset: int,
    dtype: np.dtype,
    encoding: str = 'windows-1252'
) -> Any:
    """Reads a single value from a buffer at a certain offset.

    Just a handy wrapper for np.frombuffer() With the added benefit of
    allowing the 'pascal' keyword as an indicator for a length-prefixed
    string.

    The read value is converted to a built-in datatype using
    np.dtype.item().

    Parameters
    ----------
    data
        An object that exposes the buffer interface. Here always bytes.
    offset
        Start reading the buffer from this offset (in bytes).
    dtype
        Data-type to read in.
    encoding
        The encoding of the bytes to be converted.

    Returns
    -------
    Any
        The unpacked and converted value from the buffer.

    """
    if dtype == 'pascal':
        # Allow the use of 'pascal' in all of the dtype maps.
        return read_pascal_string(data[offset:])
    value = np.frombuffer(data, offset=offset, dtype=dtype, count=1)
    item = value.item()
    if value.dtype.names:
        item = [i.decode(encoding) if isinstance(i, bytes) else i for i in item]
        return dict(zip(value.dtype.names, item))
    return item.decode(encoding) if isinstance(item, bytes) else item


def read_values(data: bytes, offset: int, dtype, count) -> list:
    """Reads in multiple values from a buffer starting at offset.

    Just a handy wrapper for np.frombuffer() with count >= 1.

    The read values are converted to a list of built-in datatypes using
    np.ndarray.tolist().

    Parameters
    ----------
    data
        An object that exposes the buffer interface. Here always bytes.
    offset
        Start reading the buffer from this offset (in bytes).
    dtype
        Data-type to read in.
    count
        Number of items to read. -1 means all data in the buffer.

    Returns
    -------
    Any
        The values read from the buffer as specified by the arguments.

    """
    values = np.frombuffer(data, offset=offset, dtype=dtype, count=count)
    if values.dtype.names:
        return [dict(zip(value.dtype.names, value.item())) for value in values]
    # The ndarray.tolist() method converts python scalars to numpy
    # scalars, hence not just list(values).
    return values.tolist()
