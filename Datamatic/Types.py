"""
A module that holds CppType, a base class for classes that represent
C++ types. Users can subclass this to add their own types to
Datamatic.
"""
from abc import ABC, abstractmethod


class Type(ABC):
    """
    Base type for all types used in Datamatic. Subclass this to add
    extra types.
    """

    @abstractmethod
    def __init__(self):
        """
        This should contain asserts to verify that the construction of
        this object was successful. This will be used in the validator
        to make sure the schema provided to Datamatic is valid.
        """

    @abstractmethod
    def __repr__(self):
        """
        This should return a string representation of how this object
        will look in C++.
        """

    @staticmethod
    @abstractmethod
    def typename():
        """
        This should return a string representation of how this type
        will look in C++.
        """


class Integer(Type):
    def __init__(self, val):
        assert isinstance(val, int)
        self.val = val

    def __repr__(self):
        return str(self.val)

    @staticmethod
    def typename():
        return "int"


class Float(Type):
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


class Boolean(Type):
    def __init__(self, val):
        assert isinstance(val, bool)
        self.val = val

    def __repr__(self):
        return "true" if self.val else "false"

    @staticmethod
    def typename():
        return "bool"


class String(Type):
    def __init__(self, val):
        assert isinstance(val, str)
        self.val = val

    def __repr__(self):
        return f'"{self.val}"'

    @staticmethod
    def typename():
        return "std::string"


def get(typename):
    for cls in Type.__subclasses__():
        if cls.typename() == typename:
            return cls
    print(f"Could not find {typename}")
    return None