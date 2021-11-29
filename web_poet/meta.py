import importlib
import importlib.util
import pkgutil
import sys
from dataclasses import dataclass
from typing import Iterable, Union, List, Callable, Dict

from url_matcher import Patterns


HANDLE_URLS_NAMESPACES_KEY = "_handle_urls_namespaces_"


@dataclass(frozen=True)
class HandleUrlsSpec:
    patterns: Patterns
    overrides: Callable


def _as_list(value: Union[str, Iterable[str], None]) -> List[str]:
    """
    >>> _as_list(None)
    []
    >>> _as_list("foo")
    ['foo']
    >>> _as_list(["foo", "bar"])
    ['foo', 'bar']
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def handle_urls(include: Union[str, Iterable[str]],
                overrides: Callable,
                *,
                exclude: Union[str, Iterable[str], None] = None,
                priority: int = 500,
                namespace: str = "",
                ):
    """
    Class decorator that indicates that the decorated Page Object should be used instead of the overridden one
    for a particular set the URLs.

    Which Page Object is overridden is determined by the `overrides` parameter.

    Over which URLs the overridden happens is determined by the `include`, `exclude` and `priority` parameters.
    See the documentation of the `url-matcher` package for more information about them.

    Different namespaces can be used to create different groups of annotations. The default namespace is the empty
    string.

    For the example, the following Page Object is decorated with the `handle_urls` decorator:

    .. code-block:: python

        @handle_urls("example.com", overrides=ProductPageObject)
        class ExampleComProductPage(ItemPage):
            ...

    The annotation indicates that the `ExampleComProductPage` Page Object should be used
    instead of the `ProductPageObject` Page Object for all the URLs whose domain is `example.com`.

    :param include: Defines the URLs that should be handled by the overridden Page Object.
    :param overrides: The Page Object that should be replaced by the annotated one.
    :param exclude: Defines URLs over which the override should not happen.
    :param priority: The priority in case of conflicting annotations.
    """

    def wrapper(cls):
        module = sys.modules[cls.__module__]
        if not hasattr(module, HANDLE_URLS_NAMESPACES_KEY):
            setattr(module, HANDLE_URLS_NAMESPACES_KEY, {})

        handle_urls_dict = getattr(module, HANDLE_URLS_NAMESPACES_KEY)
        spec = HandleUrlsSpec(
            patterns=Patterns(
                include=_as_list(include),
                exclude=_as_list(exclude),
                priority=priority),
            overrides=overrides
        )
        namespace_dict = handle_urls_dict.setdefault(namespace, {})
        if cls not in namespace_dict:
            # If it was already defined, we don't want to override it
            namespace_dict[cls] = spec
        return cls

    return wrapper


def walk_modules(module: str) -> Iterable[type]:
    """
    Return all modules from a module recursively. Note that this will import all the modules and submodules.
    It returns the provided module as well.
    """
    def onerror(mod):
        raise

    spec = importlib.util.find_spec(module)
    if not spec:
        raise ImportError(f"Module {module} not found")
    mod = importlib.import_module(spec.name)
    yield mod
    if spec.submodule_search_locations:
        for info in pkgutil.walk_packages(spec.submodule_search_locations, f"{spec.name}.", onerror):
            mod = importlib.import_module(info.name)
            yield mod


def find_page_object_overrides(module: str, namespace: str = "") -> Dict[Callable, HandleUrlsSpec]:
    """
    Find all the Page Objects overrides in the given module/package and it submodules.

    Only the page objects that have been decorated with the `handle_urls` decorator will be returned.

    Note that this will import the module and its submodules.

    :param module: The module or package to search in
    :param namespace: Only return page objects in this namespace
    :return: Return a dictionary with all the page objects where the key is the page object type and the value is its
             associated :py:class:`web_poet.decorators.HandleUrlsSpec` metadata.
    """
    page_objects = {}
    for module in walk_modules(module):
        handle_urls_dict = getattr(module, HANDLE_URLS_NAMESPACES_KEY, {})
        page_objects.update(handle_urls_dict.get(namespace) or {})
    return page_objects
