from web_poet.mixins import SelectableMixin


class BrowserHtml(SelectableMixin, str):
    """HTML returned by a web browser,
    i.e. snapshot of the DOM tree in HTML format.
    """

    def _selector_input(self) -> str:
        return self
