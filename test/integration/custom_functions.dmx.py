def main(register):
    
    @register.compmethod("test.foo")
    def _(spec, comp):
        return "foobar"