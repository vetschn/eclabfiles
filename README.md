# eclabfiles

This is a package to parse files from BioLogic's EC-Lab. The parsers build on [Chris Kerr's `galvani` package](https://github.com/chatcannon/galvani) and on the work of a previous civilian service member at Empa Lab 501, Jonas Krieger.

```bash
> pip install eclabfiles
```

## Example Usage

### `parse`

Parse the data as it is stored in the corresponding file. The method automatically determines filetype and tries to apply the respective parser.

```python
>>> import eclabfiles as ecf
>>> ecf.parse("./mpt_files/test_01_OCV.mpt")
```

The returned data structure may look quite different depending on which file type you read in as the different filetypes also store the same data in very different ways. See [section filetypes](#Filetypes).


### `to_df`

Parse the file and transform only the data part into a Pandas `DataFrame`. 


```python
>>> import eclabfiles as ecf
>>> ecf.to_df("./mpr_files/test_02_CP.mpr")
```

If the given file is an `.mps` settings file, then the program tries to read the data from any `.mpt` and `.mpr` files in the same folder if they are present. In that case a `list` of `DataFrame`s is returned.


### `to_csv`

Parse the file and write the data part into a `.csv` file at the specified location.

```python
>>> import eclabfiles as ecf
>>> ecf.to_csv("./mpt_files/test_03_PEIS.mpt", "./csv_files/test_PEIS.csv")
```

The `csv_path` parameter is optional. If left away, the method writes a `.csv` file at the location of the input file.

If the file is a settings file, this method does as `to_df()` does and writes multiple numbered `.csv` files.


### `to_xlsx`

Parse the file and write the data part into an Excel `.xlsx` file at the specified location.

```python
>>> import eclabfiles as ecf
>>> ecf.to_xlsx("./experiment/test.mps")
```

The `xlsx_path` parameter is optional. If left away, the method writes a `.xlsx` file at the location of the input file.

If the file is a settings file, this method writes multiple numbered sheets into the Excel file.


## Filetypes

The file types that are implemented are:

- `.mpt`: The `.mpt` file is a text format file generated when the user exports the raw `.mpr` file in text format.
- `.mpr`: Raw data binary file, which contains the current parameter settings (refreshed at each modification) of the detailed diagram and cell characteristic windows.
- `.mps`: Settings file, which contains all the parameters of the experiment.

The `.mpt` files generally contain a few more data columns than the corresponding binary `.mpr` files from what I have seen.

The `.mps` files simply relate different techniques together and store no data, while the other files contain the measurements.

### Structure of parsed `.mpt` files

```python
{
    'header': {
        'technique', #*
        'settings', #*
        'params': [{}], #*
        'loops': { #*
            'n',
            'indexes': [],
        },
    },
    'datapoints': [{}],
}
```

### Structure of parsed `.mpr` files

```python
[
    {
        'header': {
            'short_name',
            'long_name',
            'length',
            'version',
            'date',
        },
        'data': {
            'technique',
            'comments',
            'active_material_mass',
            'at_x',
            'molecular_weight',
            'atomic_weight',
            'acquisition_start',
            'e_transferred',
            'electrode_material',
            'electrolyte',
            'electrode_area',
            'reference_electrode',
            'characteristic_mass',
            'battery_capacity',
            'battery_capacity_unit',
            'params': {},
        },
    },
    {
        'header': {
            'short_name',
            'long_name',
            'length',
            'version',
            'date',
        },
        'data': {
            'n_datapoints'
            'n_columns'
            'datapoints': [{}]
        },
    },
    { #*
        'header': {
            'short_name',
            'long_name',
            'length',
            'version',
            'date',
        },
        'data': {
            'ewe_ctrl_min',
            'ewe_ctrl_max',
            'ole_timestamp',
            'filename',
            'host',
            'address',
            'ec_lab_version',
            'server_version',
            'interpreter_version',
            'device_sn',
            'averaging_points',
        },
    },
    { #*
        'header': {
            'short_name',
            'long_name',
            'length',
            'version',
            'date',
        },
        'data': {
            'n_indexes',
            'indexes': [],
        },
    },
]
```

### Structure of parsed `.mps` files

```python
{
    'header': { #*
        'filename',
        'general_settings': [],
    },
    'techniques': [
        {
            'technique',
            'params',
            
        },
    ],
    'data': { #*
        'mpr': [],
        'mpt': [],
    },
}
```

All the substructures marked with `#*` are not certain to be present in a given file. Also, no guarantees that the rest is *always* present.

This is especially relevant for `.mpt` files, which sometimes contain only data and no header info at all.

## Techniques

The techniques implemented are:

- `CA`
- `CP`
- `CV`
- `GCPL`
- `GEIS`
- `LOOP`
- `LSV`
- `MB`
- `OCV`
- `PEIS`
- `WAIT`
- `ZIR` (`TODO` for .mpr)

### Notes on implementing further techniques

In the best case you should have an `.mps`, `.mpr` and `.mpt` files ready that contain the technique you would like to implement.

For the parsing of EC-Lab ASCII files (`.mpt`/`.mps`) you simply add a `list` of parameter names in `technique_params.py` as they appear in these text files. If the technique has a changing number of parameters in these ASCII files, e.g. it contains a modifiable number of 'Limits' or 'Records', define the technique as a dictionary containing `head` and `tail`, like with `PEIS`. Then also write a function that completes the technique parameters (compare `construct_peis_params`). 

Make sure to also add the list of technique parameters into the `technique_params` dictionary or to add a case for the technique in `_parse_technique_params` / `_parse_techniques` in the `mpt.py` / `mps.py` modules.

If you want to implement the technique in the `.mpr` file parser, you will need to define a corresponding Numpy `dtype` in the `technique_params.py` module. I would recommend getting a solid hex editor (e.g. Hexinator, Hex Editor Neo) to find the actual binary data type of each parameter.

From the `.mpr` files I have seen, you will usually find the parameters at an offset of `0x1845` from the start of the data section in the `VMP settings` module or somewhere around there. Compare the parameter values in the binary data to the values in the corresponding ASCII files. 

As a rule of thumb, floats are usually 32bit little-endian (`<f4`), integers are often 8bit (`|u1`) or 16bit (`<u2`) wide and units are stored in 8bit integers. I have not gotten around to linking the integer value with the corresponding unit yet.

Good luck!
