import json
import os.path as op
from pathlib import Path

from Datamatic import Validator
from Datamatic import Generator
from Datamatic.Plugins import Lua, Inspector

sprocket = op.abspath(op.dirname(__file__))
sprocket_base = op.dirname(sprocket)

with open("ComponentSpec.json") as specfile:
    spec = json.loads(specfile.read())

Validator.run(spec)

for file in Path(sprocket_base).glob("**/*.dm.*"):
    Generator.run(spec, str(file))

print("Done!")