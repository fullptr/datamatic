

def get_type(name):
    return {
        "Maths::vec3": Vec3
    }[name]


class Vec3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def type(self):
        return "Maths::vec3"

    def repr(self):
        return f"{self.type()}{{{self.x}, {self.y}, {self.z}}}"