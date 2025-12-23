Examples
========

Reading (and parsing) the STASH sections in a namelist
------------------------------------------------------

You can read and parse the STASH sections in a namelist file using the
`parse_namelist()` function. This function takes the path to a namelist file and 
returns a list of class `BaseSection`. 

The function will parse **variable** sections (that start with "namelist:umstash_streq"),
**domain** and **time** profiles ("namelist:umstash_domain" and
"namelist:umstash_time" respectively), **use** sections ("namelist:umstash_use") and the **model output streams** sections
("namelist:nlstcall_pp"). 

By identifying the different sections, the function with asign a class to each one:

``` python
'umstash_use': UseProfile,
'umstash_time': TimeProfile,
'umstash_domain': DomainProfile,
'umstash_streq': Variable,
'nlstcall_pp': OutputStream,
```
Here is an example of how to use the `parse_namelist()` function:

.. jupyter-execute::

    import stashmap
    sections = stashmap.read_namelist("examples/rose-app.conf", print_summary=True)


Human-readable version of variables and profiles
------------------------------------------------    

stash codes (like "m01s01i004") are not very informative. You can get a human-readable
version of the variables with the function `describe_variable()`. This function takes a
list (of class BaseSection) or a string (a single stash code) and returns the variable name. 

Here is an example of how to use the `describe_variable()` function:

Using the stash code:

.. jupyter-execute::

    stashmap.describe_variable("m01s01i004")


Using a list of sections obtained from a namelist:

.. jupyter-execute::

    sections = stashmap.read_namelist("examples/rose-app.conf", print_summary=True)
    
    stashmap.describe_variable(sections)

    variables = [s for s in sections if isinstance(s, stashmap.Variable)]

    for v in variables[0:15]:
        print("isec=", v.record.get('isec'), "item=", v.record.get('item'), "->", v.record.get('description'))


In the same way, you can get a human-readable version of the time and domain profiles with `describe_profiles()`:

For time profiles it will decode each element and construct a description based on the values of the different fields.

.. jupyter-execute::

    sections = stashmap.read_namelist("examples/rose-app.conf", print_summary=True)

    stashmap.describe_profiles(sections)
    
    time = [s for s in sections if isinstance(s, stashmap.TimeProfile)]

    for t in time:
        print(t.record.get('tim_name'), "->", t.record.get('description'))


And the same for domain profiles:

.. jupyter-execute::

    sections = stashmap.read_namelist("examples/rose-app.conf", print_summary=True)

    stashmap.describe_profiles(sections)
    
    domain = [s for s in sections if isinstance(s, stashmap.DomainProfile)]

    for d in domain:
        print(d.record.get('dom_name'), "->", d.record.get('description'))


It is recomended to use these functions after reading a namelist file with `parse_namelist()` to get 
a human-readable version of the variables and profiles defined in the namelist.

Exporting to csv fields
-----------------------

On of the main reasons for this package to exist is to be able to read the namelist and save it into a 
csv file and work on the stash list, hopefully after you added the human-readable description for each one.
The function `export_sections_to_csv()` takes the list of sections obtained from `parse_namelist()` and
a path (without extension) to save the csv files. By default, it will create different 3 csv files for 
variables, time profiles and domain profiles. Optionally you can export only variables by setting 
`section_type='variables'`.

.. jupyter-execute::

    stashmap.export_sections_to_csv(sections, "examples/stash")


For this example, it will create on file called `stash_variables.csv`.

Exporting to namelist
----------------------

Finally, it is possible to export back to namelist format.



The function `write_namelist()` takes a list of sections (of class BaseSection) or a path to a csv file with
the necessary columns and creates a text file in namelist format. Then, you can copy the content of that file 
to the `rose-app.conf`.

.. jupyter-execute::

    stashmap.write_namelist(sections, "examples/new_stash.txt")

    N = 10
    with open("examples/new_stash.txt", "r") as file:
        for i in range(N):
            line = next(file).strip()
            print(line)

.. note::
    Currently, if the input is a csv file, it will only export variable sections (umstash_streq).

.. jupyter-execute::

    stashmap.write_namelist("examples/stash_variables.csv", "examples/new_stash.txt")

    N = 10
    with open("examples/new_stash.txt", "r") as file:
        for i in range(N):
            line = next(file).strip()
            print(line)