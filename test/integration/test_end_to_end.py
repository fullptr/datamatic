"""
An integration test that uses a specfile and a template file.
"""
import tempfile
import shutil
import pathlib
import os.path as op
from unittest.mock import patch, call
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


def test_file_is_not_rewritten_if_no_change():
    """
    Similar to the above test, except in this one we also copy the expected file into the
    output directory. The file should not be written. We check this by patching
    print and making sure the expected message was printed. This is a bit brittle, so maybe
    there's a better way of doing this.
    """

    # GIVEN
    # The directory that this file is in. The template files are also located here.
    src_dir = op.dirname(op.abspath(__file__))

    # Create a new directory to run the test in.
    out_dir = tempfile.mkdtemp(prefix="datamatic_")
    
    # Copy the template file into the output and verify it's there. Also copy the expected.
    shutil.copy(op.join(src_dir, "actual.dm.cpp"), op.join(out_dir, "actual.dm.cpp"))
    assert op.exists(op.join(out_dir, "actual.dm.cpp"))

    shutil.copy(op.join(src_dir, "custom_types.dmx.py"), op.join(out_dir, "custom_types.dmx.py"))
    assert op.exists(op.join(out_dir, "custom_types.dmx.py"))

    shutil.copy(op.join(src_dir, "expected.cpp"), op.join(out_dir, "actual.cpp"))
    assert op.exists(op.join(out_dir, "actual.cpp"))

    # WHEN
    specfile = pathlib.Path(src_dir, "component_spec.json")
    with patch("builtins.print") as mock_print:
        main.main(specfile, pathlib.Path(out_dir))

    # THEN
    mock_print.assert_any_call(f"No change to {op.join(out_dir, 'actual.cpp')}")