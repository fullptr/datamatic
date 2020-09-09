from abc import ABC, abstractmethod
import pathlib
import sys
import importlib.util as iu

class CppType(ABC):
    @abstractmethod
    def __repr__(self): ...

    @staticmethod
    @abstractmethod
    def typename(self): ...


class Integer(CppType):
    def __init__(self, val):
        assert isinstance(val, int)
        self.val = val

    def __repr__(self):
        return str(self.val)

    @staticmethod
    def typename():
        return "int"


class Float(CppType):
    def __init__(self, val):
        assert isinstance(val, (int, float))
        self.val = val

    def __repr__(self):
        if "." not in str(self.val):
            return f"{self.val}.0f"
        return f"{self.val}f"

    @staticmethod
    def typename():
        return "float"


class Boolean(CppType):
    def __init__(self, val):
        assert isinstance(val, bool)
        self.val = val

    def __repr__(self):
        return "true" if self.val else "false"

    @staticmethod
    def typename():
        return "bool"


class String(CppType):
    def __init__(self, val):
        assert isinstance(val, str)
        self.val = val

    def __repr__(self):
        return f'"{self.val}"'

    @staticmethod
    def typename():
        return "std::string"


def get(typename):
    for cls in CppType.__subclasses__():
        if cls.typename() == typename:
            return cls
    print(f"Could not find {typename}")
    return None