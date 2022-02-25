class ReloadResponseData(Exception):
    """Indicates that there's something wrong with :class:`~.ResponseData` and
    it needs to be downloaded again.

    You should use this in instance where the HTTP Response is malformed, missing
    some required information, etc.

    This should be raised inside the subclasses of :class:`~.WebPage` or anything
    which requires :class:`~.ResponseData` as a dependency. The framework which
    handles the Page Objects should then attempt to create a new instance with a
    fresh :class:`~.ResponseData` dependency.
    """
    pass
