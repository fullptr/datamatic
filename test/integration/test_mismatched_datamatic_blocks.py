from datamatic.validator import InvalidSpecError
import tempfile
import shutil
import pathlib
import os.path as op
from datamatic import main
import pytest


def test_mismatched_datamatic_blocks():
    """
    Verify that trying to nest datamatic blocks is an error.
    """

    # GIVEN
    # The directory that this file is in. The template files are also located here.
    src_dir = op.dirname(op.abspath(__file__))

    # Create a new directory to run the test in.
    out_dir = tempfile.mkdtemp(prefix="datamatic_")
    
    # Copy the template file into the output and verify it's there
    shutil.copy(op.join(src_dir, "invalid.dm.cpp"), op.join(out_dir, "invalid.dm.cpp"))
    assert op.exists(op.join(out_dir, "invalid.dm.cpp"))

    shutil.copy(op.join(src_dir, "custom_types.dmx.py"), op.join(out_dir, "custom_types.dmx.py"))
    assert op.exists(op.join(out_dir, "custom_types.dmx.py"))

    # WHEN
    specfile = pathlib.Path(src_dir, "component_spec.json")

    # THEN
    with pytest.raises(RuntimeError):
        main.main(specfile, pathlib.Path(out_dir))