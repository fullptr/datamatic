"""
An integration test that uses a specfile and a template file.
"""
import shutil
from pathlib import Path
import os.path as op
from unittest.mock import patch
from datamatic import main
import pytest


# The directory that this file is in. The template files are also located here.
@pytest.fixture
def src_path():
    return Path(op.dirname(op.abspath(__file__)))


def copy_to_test(src_dir: Path, out_dir: Path, filename, new_filename=None):
    if new_filename is None:
        new_filename = filename

    old_file = src_dir / filename
    new_file = out_dir / new_filename

    shutil.copy(str(old_file), str(new_file))
    assert new_file.exists()


def test_end_to_end_simple(src_path, tmp_path):
    """
    Creates a temporary directory and copies the template file. Run datamatic on the directory
    and verify that a new file as been created with the same contents as the expected file.

    This end_to_end test should cover all datamatic features, such as flags, custom types and
    custom functions.
    """    
    # Copy the template file into the output and verify it's there
    copy_to_test(src_path, tmp_path, "actual.dm.cpp")
    copy_to_test(src_path, tmp_path, "custom_functions.dmx.py")

    # WHEN
    specfile = src_path / "component_spec.json"
    main.main(specfile, tmp_path)

    expected_file = src_path / "expected.cpp"
    actual_file = tmp_path / "actual.cpp"
    
    assert actual_file.exists()
    with open(expected_file) as expected, open(actual_file) as actual:
        assert expected.read() == actual.read()


def test_file_is_not_rewritten_if_no_change(src_path, tmp_path):
    """
    Similar to the above test, except in this one we also copy the expected file into the
    output directory. The file should not be written. We check this by patching
    print and making sure the expected message was printed. This is a bit brittle, so maybe
    there's a better way of doing this.
    """
    # Copy the template file into the output and verify it's there. Also copy the expected.
    copy_to_test(src_path, tmp_path, "actual.dm.cpp")
    copy_to_test(src_path, tmp_path, "custom_functions.dmx.py")
    copy_to_test(src_path, tmp_path, "expected.cpp", "actual.cpp")

    # WHEN
    specfile = src_path / "component_spec.json"
    with patch("builtins.print") as mock_print:
        main.main(specfile, tmp_path)

    # THEN
    mock_print.assert_any_call(f"No change to {tmp_path / 'actual.cpp'}")