import abc


# FIXME: refactor _providers / provides / register,  make a nicer API
providers = {}


class PageObjectProvider(abc.ABC):
    """Abstract class that represents a Page Object provider."""

    @abc.abstractmethod
    def __call__(self):
        """Providers should implement the ``__call__`` method."""
        pass


def register(provider, cls):
    """Registers a Provider that provides an object of type ``cls``."""
    providers[cls] = provider


def provides(cls):
    """Decorates Provider classes registering them as providers."""
    def decorator(provider):
        register(provider, cls)
        return provider

    return decorator
