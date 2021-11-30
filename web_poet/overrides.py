import importlib
import importlib.util
import pkgutil
import sys
from dataclasses import dataclass, field
from typing import Iterable, Union, List, Callable, Dict, Any

from url_matcher import Patterns


OVERRIDES_NAMESPACES_KEY = "_overrides_namespaces_"


@dataclass(frozen=True)
class HandleUrlsSpec:
    patterns: Patterns
    overrides: Callable
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OverrideRule:
    for_patterns: Patterns
    use: Callable
    instead_of: Callable
    meta: Dict[str, Any] = field(default_factory=dict)


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
                **kwargs
                ):
    """
    Class decorator that indicates that the decorated Page Object should be used instead of the overridden one
    for a particular set the URLs.

    Which Page Object is overridden is determined by the `overrides` parameter.

    Over which URLs the override happens is determined by the `include`, `exclude` and `priority` parameters.
    See the documentation of the `url-matcher` package for more information about them.

    Different namespaces can be used to create different groups of annotations. The default namespace is the empty
    string.

    For the example, the following Page Object is decorated with the `handle_urls` decorator:

    .. code-block:: python

        @handle_urls("example.com", overrides=ProductPageObject)
        class ExampleComProductPage(ItemPage):
            ...

    The annotation indicates that the `ExampleComProductPage` Page Object should be used
    instead of the `ProductPageObject` Page Object for all the URLs whose top level domain is `example.com`.

    Any extra parameters are stored as meta information that can be later used.

    :param include: Defines the URLs that should be handled by the overridden Page Object.
    :param overrides: The Page Object that should be replaced by the annotated one.
    :param exclude: Defines URLs over which the override should not happen.
    :param priority: The resolution priority in case of conflicting annotations.
    """

    def wrapper(cls):
        module = sys.modules[cls.__module__]
        if not hasattr(module, OVERRIDES_NAMESPACES_KEY):
            setattr(module, OVERRIDES_NAMESPACES_KEY, {})

        handle_urls_dict = getattr(module, OVERRIDES_NAMESPACES_KEY)
        spec = HandleUrlsSpec(
            patterns=Patterns(
                include=_as_list(include),
                exclude=_as_list(exclude),
                priority=priority),
            overrides=overrides,
            meta=kwargs,
        )
        namespace_dict = handle_urls_dict.setdefault(namespace, {})
        if cls not in namespace_dict:
            # If it was already defined, we don't want to override it
            namespace_dict[cls] = spec
        return cls

    return wrapper


def walk_modules(module: str) -> Iterable:
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


def find_page_object_overrides(module: str, namespace: str = "") -> List[OverrideRule]:
    """
    Find all the Page Objects overrides in the given module/package and it submodules.

    The page objects that have been decorated with the `handle_urls` decorator will be returned.

    Note that this will import the module and its submodules.

    :param module: The module or package to search in
    :param namespace: Only return page objects overrides in this namespace
    :return: Return a list of :py:class:`web_poet.overrides.OverrideRule` metadata.
    """
    page_objects: Dict[Callable, HandleUrlsSpec] = {}
    for module in walk_modules(module):
        handle_urls_dict = getattr(module, OVERRIDES_NAMESPACES_KEY, {})
        page_objects.update(handle_urls_dict.get(namespace) or {})
    return [OverrideRule(for_patterns=spec.patterns, use=po, instead_of=spec.overrides, meta=spec.meta)
            for po, spec in page_objects.items()]
