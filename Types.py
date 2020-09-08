from abc import ABC, abstractmethod

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

class Vec2(CppType):
    def __init__(self, val):
        assert isinstance(val, list)
        assert all([isinstance(x, float) for x in val])
        self.x, self.y = [Float(t) for t in val]

    def __repr__(self):
        return f'{self.typename()}{{{self.x}, {self.y}}}'

    @staticmethod
    def typename():
        return "Maths::vec2"

class Vec3(CppType):
    def __init__(self, val):
        assert isinstance(val, list)
        assert all([isinstance(x, float) for x in val])
        self.x, self.y, self.z = [Float(t) for t in val]

    def __repr__(self):
        return f'{self.typename()}{{{self.x}, {self.y}, {self.z}}}'

    @staticmethod
    def typename():
        return "Maths::vec3"

class Vec4(CppType):
    def __init__(self, val):
        assert isinstance(val, list)
        assert all([isinstance(x, float) for x in val])
        self.x, self.y, self.z, self.w = [Float(t) for t in val]

    def __repr__(self):
        return f'{self.typename()}{{{self.x}, {self.y}, {self.z}, {self.w}}}'

    @staticmethod
    def typename():
        return "Maths::vec4"

class Quat(CppType):
    def __init__(self, val):
        assert isinstance(val, list)
        assert all([isinstance(x, float) for x in val])
        self.x, self.y, self.z, self.w = [Float(t) for t in val]

    def __repr__(self):
        return f'{self.typename()}{{{self.x}, {self.y}, {self.z}, {self.w}}}'

    @staticmethod
    def typename():
        return "Maths::quat"

class Mat4(CppType): # TODO: Implement
    def __init__(self, val):
        pass

    def __repr__(self):
        return f"{self.typename()}{{1.0}}"

    @staticmethod
    def typename():
        return "Maths::mat4"

class QueueVec3(CppType): # TODO: Implement
    def __init__(self, val):
        pass

    def __repr__(self):
        return f"{self.typename()}{{}}"

    @staticmethod
    def typename():
        return "std::queue<Maths::vec3>"

def get(typename):
    for cls in CppType.__subclasses__():
        if cls.typename() == typename:
            return cls
    print(f"Could not find {typename}")
    return None