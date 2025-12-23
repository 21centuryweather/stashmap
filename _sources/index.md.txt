# stashmap

## Overview

:::{toctree}
:maxdepth: 2
:hidden:
:caption: Contents:
Home <self>
Examples <examples>
:::

The `stashmap` package provides functions to read and modify the stash and associated variables for the UM model. It main focus is to convert the relevant sections in the UM namelist (usually in `rose-app.conf`) into a `.csv` file for easy manipulation and then convert it back to the namelist format. 

It also includes helpers to get variable names from stash codes and to get the human version for the time and domain profiles. 

## Get started

For now, you can install this package into your preferred Python environment using:

```bash
$ pip install git+https://github.com/21centuryweather/stashmap.git
```

## Example

```python
import stashmap
```

Read from namelist:

```python
sections = stashmap.read_namelist("examples/rose-app.conf", print_summary=True)
```

Add human-readable variable names:

```python
stashmap.describe_variable(sections)

variables = [s for s in sections if isinstance(s, stashmap.Variable)]

for v in variables[0:15]:
    print("isec=", v.record.get('isec'), "item=", v.record.get('item'), "->", v.record.get('description'))
```

And write to csv:

```python
stashmap.export_sections_to_csv(sections, "examples/stash", section_type="variables")
```

For a longer, runnable example see the Usage page: :doc:`usage`.


## Licence

- Free software distributed under the MIT License.
