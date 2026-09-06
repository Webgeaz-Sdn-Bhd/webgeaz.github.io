class Layout(object):
    ACCESS_POLICY = {"view": "authenticated", "page_layout": "authenticated"}

    def page_layout(self, ctx):
        return ("tracker", "layout", "layout")

    def view(self, ctx):
        # Shared layout data can be prepared here.
        pass
