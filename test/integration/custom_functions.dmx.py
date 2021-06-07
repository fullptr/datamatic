def main(register):
    
    @register.compmethod("test.foo")
    def _(ctx):
        return "foobar"