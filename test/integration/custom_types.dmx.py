"""
Adds a custom type for the integration test to use.
"""

def main(ctx):

    @ctx.type("custom_type")
    def _(typename, obj):
        assert isinstance(obj, int)
        return f"{typename}{{{obj}}}"