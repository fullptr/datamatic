def main(register):
    
    @register.compmethod
    def test_function(ctx):
        return "foobar"