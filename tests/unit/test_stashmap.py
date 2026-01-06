from stashmap import read_namelist, write_namelist, describe_variable, describe_profiles, export_sections_to_csv
from stashmap import Variable, TimeProfile, DomainProfile
import os

def test_parse_namelist(capsys):
    """
    Test that read_namelist works or maybe not.
    """
    read_namelist("examples/rose-app.conf", print_summary=True)
    
    out = capsys.readouterr().out.strip()
    expected_out = "Parsed 215 sections — DomainProfile: 8/26, OutputStream: 7/12, TimeProfile: 10/26, UseProfile: 8/14, Variable: 133/137"
    
    # Check printed summary
    assert out == expected_out, f"Expected {expected_out} but got {out}"

    out = read_namelist("examples/rose-app.conf", print_summary=False)
    
    # Check number of sections parsed
    assert len(out) == 215

    # Check the class type
    assert type(out[1]).__name__ == "OutputStream"

    string = """
    [namelist:umstash_streq(04201_07f065b3)] 
    dom_name='DIAG'
    isec=4
    item=201
    package='2D Standard Diagnostics'
    tim_name='T3HACUM'
    use_name='UPA'
    """

    out2 = read_namelist(string)

    # Check number of sections parsed from string
    assert len(out2) == 1
    # Check the class type
    assert type(out2[0]).__name__ == "Variable"

def test_write_namelist(tmp_path):
    """
    Test that write_namelist works.
    """

    sections = read_namelist("examples/rose-app.conf", print_summary=False)

    output_file = tmp_path / "output_namelist.conf"
    write_namelist(sections, output_file)

    # Read back the generated file
    with open(output_file, 'r') as f:
        content = f.read()

    # Check that the content is not empty
    assert len(content) > 0

    string = """[namelist:umstash_streq(04201_07f065b3)]
dom_name='DIAG'
isec=4
item=201
package='2D Standard Diagnostics'
tim_name='T3HACUM'
use_name='UPA'
"""

    section = read_namelist(string)

    output_file = tmp_path / "output_namelist.conf"
    write_namelist(section, output_file)

    # Read back the generated file
    with open(output_file, 'r') as f:
        content = f.read()

    # Check that the content is not empty
    assert len(content) > 0

    #Check content matches expected
    assert string.strip() + "\n\n" == content

    # Saves correctly even when adding the variable name
    describe_variable(section)
    write_namelist(section, output_file)
    assert string.strip() + "\n\n" == content

    # Read from csv and write namelist

    write_namelist("examples/new_stash_vars.csv", output_file)

    with open(output_file, "r") as f:
        content = f.read()

    assert len(content) > 0


def test_export_sections_to_csv(tmp_path):
    """
    Test that export_sections_to_csv works.
    """

    sections = read_namelist("examples/rose-app.conf", print_summary=False)

    output_csv = str(tmp_path) + "/stash"
    export_sections_to_csv(sections, output_csv)

    # Check that the file was created
    assert os.path.exists(output_csv + "_variables.csv")

    # Read back the CSV and check content
    with open(output_csv + "_variables.csv", 'r') as f:
        content = f.read()

    assert len(content) > 0


def test_describe():
    """
    Test that describe_variable and describe_profile work.
    """

    # Test describe_variable with a stash code
    out = describe_variable("m01s01i004")
    expected = 'TEMPERATURE AFTER SW RAD INCREMENTS'
    assert out == expected, f"Expected {expected} but got {out}"

    # Test describe_variable with namelist  sections
    sections = read_namelist("examples/rose-app.conf", print_summary=True)

    describe_variable(sections)

    variables = [s for s in sections if isinstance(s, Variable)]

    out  = variables[0].record.get('description')
    expected = 'U COMPNT OF WIND AFTER TIMESTEP'
    assert out == expected, f"Expected {expected} but got {out}"

    # Test time_profile description

    describe_profiles(sections)

    time = [s for s in sections if isinstance(s, TimeProfile)]

    out  = time[0].record.get('description').strip()
    expected = 'Instantaneous every 24 hours,'
    assert out == expected, f"Expected {expected} but got {out}"
    
    # Test domain_profile description

    domain = [s for s in sections if isinstance(s, DomainProfile)]

    out  = domain[0].record.get('description').strip()
    expected = 'Global, Model rho levels: levels 1,'
    assert out == expected, f"Expected {expected} but got {out}"