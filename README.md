

# Welcome to stashmap

|  |  |
|----|----|
| Package | [![Latest PyPI Version](https://img.shields.io/pypi/v/stashmap.svg)](https://pypi.org/project/stashmap/) [![Supported Python Versions](https://img.shields.io/pypi/pyversions/stashmap.svg)](https://pypi.org/project/stashmap/) |
| Coverage | [![Codecov test coverage](https://codecov.io/gh/21centuryweather/stashmap/graph/badge.svg)](https://app.codecov.io/gh/21centuryweather/stashmap) |

The `stashmap` package provides functions to read and modify the stash
and associated variables for the UM model. It main focus is to convert
the relevant sections in the UM namelist (usually in `rose-app.conf`)
into a `.csv` file for easy manipulation and then convert it back to the
namelist format.

It also includes helpers to get variable names from stash codes and to
get the human version for the time and domain profiles.

## Get started

For now, you can install this package into your preferred Python
environment using:

``` bash
$ pip install git+https://github.com/21centuryweather/stashmap.git
```

## Example

``` python
import stashmap
```

Read from namelist:

``` python
sections = stashmap.read_namelist("examples/rose-app.conf", print_summary=True)
```

    Parsed 215 sections — DomainProfile: 8/26, OutputStream: 7/12, TimeProfile: 10/26, UseProfile: 8/14, Variable: 133/137

Add human-readable variable names:

``` python
stashmap.describe_variable(sections)

variables = [s for s in sections if isinstance(s, stashmap.Variable)]

for v in variables[0:15]:
    print("isec=", v.record.get('isec'), "item=", v.record.get('item'), "->", v.record.get('description'))
```

    isec= 0 item= 2 -> U COMPNT OF WIND AFTER TIMESTEP
    isec= 0 item= 2 -> U COMPNT OF WIND AFTER TIMESTEP
    isec= 0 item= 3 -> V COMPNT OF WIND AFTER TIMESTEP
    isec= 0 item= 3 -> V COMPNT OF WIND AFTER TIMESTEP
    isec= 0 item= 4 -> THETA AFTER TIMESTEP
    isec= 0 item= 4 -> THETA AFTER TIMESTEP
    isec= 0 item= 10 -> SPECIFIC HUMIDITY AFTER TIMESTEP
    isec= 0 item= 10 -> SPECIFIC HUMIDITY AFTER TIMESTEP
    isec= 0 item= 12 -> QCF AFTER TIMESTEP
    isec= 0 item= 12 -> QCF AFTER TIMESTEP
    isec= 0 item= 24 -> SURFACE TEMPERATURE AFTER TIMESTEP
    isec= 0 item= 24 -> SURFACE TEMPERATURE AFTER TIMESTEP
    isec= 0 item= 25 -> BOUNDARY LAYER DEPTH AFTER TIMESTEP
    isec= 0 item= 150 -> W COMPNT OF WIND AFTER TIMESTEP
    isec= 0 item= 150 -> W COMPNT OF WIND AFTER TIMESTEP

And write to csv:

``` python
stashmap.export_sections_to_csv(sections, "examples/stash", section_type="variables")
```

## Copyright

- Copyright © 2025 Pao Corrales.
- Free software distributed under the [MIT License](./LICENSE).
