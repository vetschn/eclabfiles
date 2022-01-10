# eclabfiles
This is a package to process and convert files from BioLogic's EC-Lab.
The parsers build on [Chris Kerr's `galvani` package](https://github.com/chatcannon/galvani)
and on the work of a previous civilian service member at Empa Lab 501,
Jonas Krieger.

## Installation
Use [pip](https://pip.pypa.io/en/stable/) to install eclabfiles.

```bash
> pip install eclabfiles
```

## Example Usage

### `process`: Processing Into Dictionaries
Process the data as it is stored in the corresponding file. The method
automatically determines filetype and tries to apply the respective
parser.

For `.mps` settings files you can specify the keyword `load_data` to
also load the data files from the same folder.

```python
import eclabfiles as ecf
data, meta = ecf.process("./mpt_files/test_01_OCV.mpt")
```

The returned data structure may look a bit different depending on which
filetype you read in.

See [Filetypes and Processed Data Structure](#filetypes-and-processed-data-structure).

### `to_df`: Processing Into Dataframe
Processes the file and converts it into a [Pandas `DataFrame`](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html).
The `pd.DataFrame.attrs` will contain all the processed metadata.

```python
import eclabfiles as ecf
df = ecf.to_df("./mpr_files/test_02_CP.mpr")
```

If the given file is an `.mps`, all data files from the same folder will
be read into a `pd.DataFrame` with a [hierarchical index](https://pandas.pydata.org/pandas-docs/stable/user_guide/advanced.html#multiindex-advanced-indexing). The top-level index is the technique
number. The `pd.DataFrame.attrs` will contain `.mps` metadata, as well
as all techniques and their loaded metadata.

### `to_csv`: Converting to CSV
Process the file and write the data part into a `.csv` file at the
specified location.

```python
>>> import eclabfiles as ecf
>>> ecf.to_csv("./mpt_files/test_03_PEIS.mpt", csv_fn="./csv_files/test_PEIS.csv")
```

The `csv_fn` parameter is optional. If left away, the method writes a
`.csv` file into the same folder as the input file.

### `to_excel`: Converting to Excel
Process the file and write the data part into an Excel `.xlsx` file at
the specified location.

```python
>>> import eclabfiles as ecf
>>> ecf.to_excel("./experiment/test.mps")
```

The `excel_fn` parameter is optional. If left away, the method writes
a `.xlsx` file at the location of the input file.

## Filetypes and Processed Data Structure.
The file types that are implemented are:

| Filetype | Description                                                                          |
|----------|--------------------------------------------------------------------------------------|
| `.mpr`   | Raw data binary file, which also contains the current parameter settings             |
| `.mpt`   | Text format file generated when the user exports the raw `.mpr` file in text format. |
| `.mps`   | Settings file, which contains all the parameters of the experiment.                  |

### Processed `.mpr` Files
```python
data, meta = ecf.process("./test_01_OCV.mpr")
```

Any `data` returned by the `process` function for `.mpr` files is
structured into record dictionaries:
```python
[{column -> value}, ..., {column -> value}]
```

The `meta` processed from `.mpr` files looks like this:
```python
{
    "settings": {  # (optional) Settings if present.
        "technique": str,  # Technique name.
        "comments": str,  # Cell characteristics.
        "active_material_mass": float,
        "at_x": float,
        "molecular_weight": float,
        "atomic_weight": float,
        "acquisition_start": float,
        "e_transferred": int,
        "electrode_material": str,
        "electrolyte": str,
        "electrode_area": float,
        "reference_electrode": str,
        "characteristic_mass": float,
        "battery_capacity": float,
        "battery_capacity_unit": int
    },
    "params": [  # (optional) Technique parameter sequences.
        {"param1": float, "param2": str, ...},
        ...,
        {"param1": float, "param2": str, ...},
    ],
    "units": {  # Units of the data columns.
        "time": "s",
        "mode": None,
        ...,
        },
    "log": {  # (optional) Log if present.
        "channel_number": int,
        "channel_sn": int,
        "Ewe_ctrl_min": float,
        "Ewe_ctrl_max": float,
        "ole_timestamp": float,
        "filename": str,
        "host": str,
        "address": str,
        "ec_lab_version": str,
        "server_version": str,
        "interpreter_version": str,
        "device_sn": str,
        "averaging_points": int,
        "posix_timestamp": float,
    },
}
```

### Processed `.mpt` Files
```python
data, meta = ecf.process("./test_01_OCV.mpt")
```

Any `data` returned by the `process` function for `.mpr` files is
structured into record dictionaries:
```python
[{column -> value}, ..., {column -> value}]
```

The `.mpt` files generally contain a few more `data` columns than the
corresponding binary `.mpr` files from what I have seen.

The `meta` processed from `.mpt` files looks like this:

```python
{
    "raw": str,  # (optional) The raw file header if present.
    "settings": {  # (optional) Settings if the file has a header.
        "posix_timestamp": float,  # POSIX timestamp if present.
        "technique": str,  # Technique name.
    },
    "params": [  # (optional) Technique parameter sequences.
        {"param1": float, "param2": str, ...},
        {"param1": float, "param2": str, ...},
        ...,
    ],
    "units": {  # Units of the data columns.
        "time": "s",
        "mode": None,
        ...,
    },
    "loops": {  # (optional) Loops if present.
        "n_indexes": int,
        "indexes": list[int],
    }
}
```

### Processed `.mps` Files
```python
techniques, meta = ecf.process("./test.mps")
```

`.mps` files simply relate different `techniques` together and store no
data, while the other files contain the measurements.

For `.mps` settings files the `process` function returns the following
the linked `techniques` instead of the data (each technique can contain
data depending on `load_data`):

```python
{
    "1": {
        "technique": str,  # Technique name.
        "params": [  # (optional) Technique parameter sequences.
            {"param1": float, "param2": str, ...},
            ...,
            {"param1": float, "param2": str, ...},
        ],
        "data": list[dict]  # (optional) Data processed from data files.
        "meta": dict  # (optional) Metadata processed from data files.
    },
    ...
}
```

The `meta` processed from `.mpr` only contains the raw file header.
```python
{
    "raw": str
}
```

## Techniques
Detecting and processing the technique parameter sequences is not
implemented for all techniques as this is pretty tedious to do.
Currently, the following techniques are implemented:

| Short Name | Full Name                                       |
|------------|-------------------------------------------------|
| CA         | Chronoamperometry / Chronocoulometry            |
| CP         | Chronopotentiometry                             |
| CV         | Cyclic Voltammetry                              |
| GCPL       | Galvanostatic Cycling with Potential Limitation |
| GEIS       | Galvano Electrochemical Impedance Spectroscopy  |
| LOOP       | Loop                                            |
| LSV        | Linear Sweep Voltammetry                        |
| MB         | Modulo Bat                                      |
| OCV        | Open Circuit Voltage                            |
| PEIS       | Potentio Electrochemical Impedance Spectroscopy |
| WAIT       | Wait                                            |
| ZIR        | IR compensation (PEIS)                          |

### Implementing further techniques
In the best case you should have an `.mps`, `.mpr` and `.mpt` files
ready that contain the technique you would like to implement.

For the parsing of EC-Lab ASCII files (`.mpt`/`.mps`) you add a function
with a `list` of parameter names in `techniques.py` in the order they
appear in the text files. See `_wait_params()` to get an idea.

If the technique has a changing number of parameters in these ASCII
files, e.g. it contains a modifiable number of 'Limits' or 'Records',
you have to write a slightly more complicated function. Compare
`_peis_params()`.

Finally, add a case for the parsing function into `technique_params()`.

If you want to implement the technique in the `.mpr` file parser, you
will need to define a corresponding Numpy `np.dtype` in the
`techniques.py` module. I would recommend getting a solid hex editor
(e.g. Hexinator, Hex Editor Neo) to find the actual binary data type of
each parameter.

From the `.mpr` files I have seen, you will usually find the parameter
sequences at an offset of `0x1845` from the start of the data section in
the `VMP settings` module or somewhere around there. Compare the
parameter values in the binary data to the values in the corresponding
ASCII files.

As a rule of thumb, floats are usually 32bit little-endian (`<f4`),
integers are often 8bit (`|u1`) or 16bit (`<u2`) wide and units are
stored in 8bit integers. I have not gotten around to linking the integer
value with the corresponding unit yet.

If the technique has a changing number of parameters, make a list of
Numpy `dtype`s. Compare `_mb_params_dtypes` to see how this looks.

Finally, add your `np.dtype` or `list[np.dtype]` to the
`technique_params_dtypes` dictionary indexed by the technique ID. This
ID is the first byte value after the `VMP settings` module's header.

Good luck!
