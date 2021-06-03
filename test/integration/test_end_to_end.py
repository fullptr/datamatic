"""
An integration test that uses a specfile and a template file.
"""
import tempfile
import shutil
import pathlib
import os.path as op
from datamatic import main


# The directory that this file is in. The template files are also located here.
src_dir = op.dirname(op.abspath(__file__))


def test_end_to_end():
    """
    Creates a temporary directory and copies the template file. Run datamatic on the directory
    and verify that a new file as been created with the same contents as the expected file.

    This end_to_end test should cover all datamatic features, such as flags, custom types and
    custom functions.
    """

    # GIVEN
    # The directory that this file is in. The template files are also located here.
    src_dir = op.dirname(op.abspath(__file__))

    # Create a new directory to run the test in.
    out_dir = tempfile.mkdtemp(prefix="datamatic_")
    
    # Copy the template file into the output and verify it's there
    shutil.copy(op.join(src_dir, "actual.dm.cpp"), op.join(out_dir, "actual.dm.cpp"))
    assert op.exists(op.join(out_dir, "actual.dm.cpp"))

    shutil.copy(op.join(src_dir, "custom_types.dmx.py"), op.join(out_dir, "custom_types.dmx.py"))
    assert op.exists(op.join(out_dir, "custom_types.dmx.py"))

    # WHEN
    specfile = pathlib.Path(src_dir, "component_spec.json")
    main.main(specfile, pathlib.Path(out_dir))

    # THEN
    # New file should be created
    assert op.exists(op.join(out_dir, "actual.cpp"))

    expected_file = op.join(src_dir, "expected.cpp")
    actual_file = op.join(out_dir, "actual.cpp")
    with open(expected_file) as expected, open(actual_file) as actual:
        assert expected.read() == actual.read()
