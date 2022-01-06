import importlib
import importlib.util
import warnings
import pkgutil
from dataclasses import dataclass, field
from typing import Iterable, Union, List, Callable, Dict, Any

from url_matcher import Patterns


@dataclass(frozen=True)
class OverrideRule:
    """A single override rule that specifies when a page object should be used
    instead of another."""

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


class PageObjectRegistry:
    """This contains the mapping rules that associates the Page Objects available
    for a given URL matching rule.

    Different Registry classes can be used to create different groups of
    annotations. Here's an example usage:

    .. code-block:: python

        from web_poet import PageObjectRegistry

        main_registry = PageObjectRegistry()
        secondary_registry = PageObjectRegistry()

        @main_registry.handle_urls("example.com", overrides=ProductPageObject)
        @secondary_registry.handle_urls("example.com", overrides=ProductPageObject)
        class ExampleComProductPage(ItemPage):
            ...

    The annotation indicates that the ``ExampleComProductPage``
    Page Object should be used instead of the ``ProductPageObject`` Page
    Object for all the URLs whose top level domain is ``example.com``.

    Moreover, this rule is available for the two (2) registries we've declared.
    This could be useful in cases wherein you want to categorize the rules by
    ``PageObjectRegistry``. They could each be accessed via:

    .. code-block:: python

        rules_main = main_registry.get_overrides()
        rules_secondary = main_registry.get_overrides()

    On the other hand, ``web-poet`` already provides a default Registry named
    ``default_registry`` for convenience. It can be directly accessed via:

    .. code-block:: python

        from web_poet import handle_urls, default_registry

        @handle_urls("example.com", overrides=ProductPageObject)
        class ExampleComProductPage(ItemPage):
            ...

        override_rules = default_registry.get_overrides()

    Notice that the ``handle_urls`` that we've imported is a part of
    ``default_registry``. This provides a shorter and quicker way to interact
    with the built-in default Registry.

    In addition, if you need to organize your Page Objects in your project, a
    single (1) default instance of the ``PageObjectRegistry`` would work, as
    long as you organize your files into modules.

    The rules could then be accessed using this method:

    * ``default_registry.get_overrides_from("my_scrapy_project.page_objects.site_A")``
    * ``default_registry.get_overrides_from("my_scrapy_project.page_objects.site_B")``
    """

    def __init__(self):
        self.data: Dict[Callable, OverrideRule] = {}

    def handle_urls(
        self,
        include: Union[str, Iterable[str]],
        overrides: Callable,
        *,
        exclude: Union[str, Iterable[str], None] = None,
        priority: int = 500,
        **kwargs,
    ):
        """
        Class decorator that indicates that the decorated Page Object should be
        used instead of the overridden one for a particular set the URLs.

        Which Page Object is overridden is determined by the ``overrides``
        parameter.

        Over which URLs the override happens is determined by the ``include``,
        ``exclude`` and ``priority`` parameters. See the documentation of the
        `url-matcher <https://url-matcher.readthedocs.io/>`_ package for more
        information about them.

        Any extra parameters are stored as meta information that can be later used.

        :param include: Defines the URLs that should be handled by the overridden Page Object.
        :param overrides: The Page Object that should be replaced by the annotated one.
        :param exclude: Defines URLs over which the override should not happen.
        :param priority: The resolution priority in case of conflicting annotations.
        """

        def wrapper(cls):
            rule = OverrideRule(
                for_patterns=Patterns(
                    include=_as_list(include),
                    exclude=_as_list(exclude),
                    priority=priority,
                ),
                use=cls,
                instead_of=overrides,
                meta=kwargs,
            )
            # If it was already defined, we don't want to override it
            if cls not in self.data:
                self.data[cls] = rule
            else:
                warnings.warn(
                    f"Multiple @handle_urls annotations with the same 'overrides' "
                    f"are ignored in the same Registry. Ignoring duplicate "
                    f"annotation on '{include}' for {cls}."
                )

            return cls

        return wrapper

    def get_overrides(self) -> List[OverrideRule]:
        """Returns all override rules that were declared using ``@handle_urls``."""
        return list(self.data.values())

    def get_overrides_from(self, module: str) -> List[OverrideRule]:
        """Returns the override rules that were declared using ``@handle_urls``
        in a specific module.

        This is useful if you've organized your Page Objects into multiple
        submodules in your project as you can filter them easily.
        """
        rules: Dict[Callable, OverrideRule] = {}

        for mod in walk_modules(module):
            # Dict ensures that no duplicates are collected and returned.
            rules.update(self._filter_from_module(mod.__name__))

        return list(rules.values())

    def _filter_from_module(self, module: str) -> Dict[Callable, OverrideRule]:
        return {
            cls: rule
            for cls, rule in self.data.items()
            if cls.__module__.startswith(module)
        }


# For ease of use, we'll create a default registry so that users can simply
# use its `handles_url()` method directly by `from web_poet import handles_url`
default_registry = PageObjectRegistry()
handle_urls = default_registry.handle_urls


def walk_modules(module: str) -> Iterable:
    """Return all modules from a module recursively.

    Note that this will import all the modules and submodules. It returns the
    provided module as well.
    """

    def onerror(err):
        raise err  # pragma: no cover

    spec = importlib.util.find_spec(module)
    if not spec:
        raise ImportError(f"Module {module} not found")
    mod = importlib.import_module(spec.name)
    yield mod
    if spec.submodule_search_locations:
        for info in pkgutil.walk_packages(
            spec.submodule_search_locations, f"{spec.name}.", onerror
        ):
            mod = importlib.import_module(info.name)
            yield mod
