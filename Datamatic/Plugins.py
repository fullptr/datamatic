import pathlib
import sys
import importlib.util as iu


class Plugin:
    @classmethod
    def get(cls, name):
        for c in cls.__subclasses__():
            if c.__name__ == name:
                return c
        raise RuntimeError(f"Could not find plugin {name}")


def compmethod(method):
    method.__type = "Comp"
    return staticmethod(method)


def attrmethod(method):
    method.__type = "Attr"
    return staticmethod(method)


def load_all(directory):
    for file in pathlib.Path(directory).glob("**/*.dm_plugin.py"):
        name = file.parts[-1].split(".")[0]
        spec = iu.spec_from_file_location(name, str(file))
        module = iu.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)