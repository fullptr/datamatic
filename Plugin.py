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