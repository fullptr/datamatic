"""
A module that holds Plugin, a base class for plugins to Datamatic.
Users can implement plugins that hook up to tokens in dm files for
custom behaviour.
"""


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


class format(Plugin):
    @compmethod
    def comma(comp, spec):
        """
        Returns a comma for all components except for the last one. This is
        intended to be used for comma-separated lists with each element on a
        separate line.
        """
        if comp == spec["Components"][-1]:
            return ""
        return ","