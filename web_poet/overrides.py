import importlib
import importlib.util
import warnings
import pkgutil
from collections import deque
from dataclasses import dataclass, field
from types import ModuleType
from typing import Iterable, Optional, Union, List, Callable, Dict, Any

from url_matcher import Patterns

Strings = Union[str, Iterable[str]]


@dataclass
class OverrideRule:
    """A single override rule that specifies when a Page Object should be used
    instead of another.

    This is instantiated when using the :func:`web_poet.handle_urls` decorator.
    It's also being returned as a ``List[OverrideRule]`` when calling
    :meth:`~.PageObjectRegistry.get_overrides`.

    You can access any of its attributes:

        * ``for_patterns: Patterns`` - contains the URL patterns associated
          with this rule. You can read the API documentation of the
          `url-matcher <https://url-matcher.readthedocs.io/>`_ package for more
          information.
        * ``use: Callable`` - the Page Object that will be used.
        * ``instead_of: Callable`` - the Page Object that will be **replaced**.
        * ``meta: Dict[str, Any] = field(default_factory=dict)`` - Any other
          information you many want to store. This doesn't do anything for now
          but may be useful for future API updates.
    """

    for_patterns: Patterns
    use: Callable
    instead_of: Callable
    meta: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        # TODO: Remove this when the following has been implemented:
        #   - https://github.com/zytedata/url-matcher/issues/3
        pattern_hash = hash(
            (
                tuple(self.for_patterns.include),
                tuple(self.for_patterns.exclude),
                self.for_patterns.priority,
            )
        )
        return hash((pattern_hash, self.use, self.instead_of))


def _as_list(value: Optional[Strings]) -> List[str]:
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

        main_registry = PageObjectRegistry(name="main")
        secondary_registry = PageObjectRegistry(name="secondary")

        @main_registry.handle_urls("example.com", overrides=ProductPageObject)
        @secondary_registry.handle_urls("example.com/shop/?id=*", overrides=ProductPageObject)
        class ExampleComProductPage(ItemPage):
            ...

    .. warning::

        Each :class:`~.PageObjectRegistry` instance should have a unique **name**
        value. Otherwise, a ``ValueError`` is raised.

    The annotation indicates that the ``ExampleComProductPage``
    Page Object should be used instead of the ``ProductPageObject`` Page
    Object for all the URLs whose top level domain is ``example.com``.

    Moreover, this rule is available for the two (2) registries we've declared.
    This could be useful in cases wherein you want to categorize the rules by
    :class:`~.PageObjectRegistry`. They could each be accessed via:

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
    single (1) default instance of the :class:`~.PageObjectRegistry` would work,
    as long as you organize your files into modules.

    The rules could then be accessed using this method:

    * ``default_registry.get_overrides(filters="my_scrapy_project.page_objects.site_A")``
    * ``default_registry.get_overrides(filters="my_scrapy_project.page_objects.site_B")``

    Lastly, you can access all of the :class:`~.PageObjectRegistry` that were
    ever instantiated via ``web_poet.registry_pool`` which is simply a mapping
    structured as ``Dict[str, PageObjectRegistry]``:

    .. code-block:: python

        from web_poet import registry_pool

        print(registry_pool)
        # {
        #     'default': <web_poet.overrides.PageObjectRegistry object at 0x7f47d654d8b0>,
        #     'main': <web_poet.overrides.PageObjectRegistry object at 0x7f47d525c3d0>,
        #     'secondary': <web_poet.overrides.PageObjectRegistry object at 0x7f47d52024c0>
        # }

    .. warning::

        Please be aware that there might be some :class:`~.PageObjectRegistry`
        that are not available, most especially if you're using them from external
        packages.

        Thus, it's imperative to use :func:`~.web_poet.overrides.consume_modules`
        beforehand:

        .. code-block:: python

            from web_poet import registry_pool, consume_modules

            consume_modules("external_pkg")

            print(registry_pool)
            # {
            #     'default': <web_poet.overrides.PageObjectRegistry object at 0x7f47d654d8b0>,
            #     'main': <web_poet.overrides.PageObjectRegistry object at 0x7f47d525c3d0>,
            #     'secondary': <web_poet.overrides.PageObjectRegistry object at 0x7f47d52024c0>
            #     'ecommerce': <external_pkg.PageObjectRegistry object at 0x7f47d8328420>
            # }
    """

    def __init__(self, name: str):
        self._data: Dict[Callable, OverrideRule] = {}

        if not name:
            raise ValueError("A registry should have a name.")

        if name in registry_pool:
            raise ValueError(f"A registry named '{name}' already exists.")
        registry_pool[name] = self
        self.name = name

    def handle_urls(
        self,
        include: Strings,
        overrides: Callable,
        *,
        exclude: Optional[Strings] = None,
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
            if cls not in self._data:
                self._data[cls] = rule
            else:
                warnings.warn(
                    f"Multiple @handle_urls annotations with the same 'overrides' "
                    f"are ignored in the same Registry. Ignoring duplicate "
                    f"annotation on '{include}' for {cls}."
                )

            return cls

        return wrapper

    def get_overrides(
        self, consume: Optional[Strings] = None, filters: Optional[Strings] = None
    ) -> List[OverrideRule]:
        """Returns a ``List`` of :class:`~.OverrideRule` that were declared using
        ``@handle_urls``.

        :param consume: packages/modules that need to be imported so that it can
            properly load the :meth:`~.PageObjectRegistry.handle_urls` annotations.
        :param filters: packages/modules that are of interest can be declared
            here to easily extract the rules from them. Use this when you need
            to pinpoint specific rules.

        .. warning::

            Remember to consider using the ``consume`` parameter to properly load
            the :meth:`~.PageObjectRegistry.handle_urls` from external Page
            Objects

            The ``consume`` parameter provides a convenient shortcut for calling
            :func:`~.web_poet.overrides.consume_modules`.
        """
        if consume:
            consume_modules(*_as_list(consume))

        if not filters:
            return list(self._data.values())

        else:
            # Dict ensures that no duplicates are collected and returned.
            rules: Dict[Callable, OverrideRule] = {}

            for item in _as_list(filters):
                for mod in walk_module(item):
                    rules.update(self._filter_from_module(mod.__name__))

            return list(rules.values())

    def _filter_from_module(self, module: str) -> Dict[Callable, OverrideRule]:
        return {
            cls: rule
            for cls, rule in self._data.items()
            # A "." is added at the end to prevent incorrect matching on cases
            # where package names are substrings of one another. For example,
            # if module = "my_project.po_lib", then it filters like so:
            #   - "my_project.po_lib_sub.POLibSub"                (filtered out)
            #   - "my_project.po_lib.POTopLevel1"                 (accepted)
            #   - "my_project.po_lib.nested_package.PONestedPkg"  (accepted)
            if cls.__module__.startswith(module + ".") or cls.__module__ == module
        }

    @property
    def data(self) -> Dict[Callable, OverrideRule]:
        """Return the ``Dict[Calalble, OverrideRule]`` mapping that were
        registered via :meth:`web_poet.handle_urls` annotations.
        """
        return self._data  # pragma: no cover

    @data.setter
    def data(self, value: Dict[Callable, OverrideRule]) -> None:
        self._data = value  # pragma: no cover

    def data_from(self, *pkgs_or_modules: str) -> Dict[Callable, OverrideRule]:
        """Return ``data`` values that are filtered by package/module.

        This can be used in lieu of :meth:`PageObjectRegistry.data`.
        """

        results = {}
        for item in pkgs_or_modules:
            results.update(self._filter_from_module(item))
        return results


# When the `PageObjectRegistry` class is instantiated, it records itself to
# this pool so that all instances can easily be accessed later on.
registry_pool: Dict[str, PageObjectRegistry] = {}


def walk_module(module: str) -> Iterable:
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


def consume_modules(*modules: str) -> None:
    """A quick wrapper for :func:`~.walk_module` to efficiently consume the
    generator and recursively load all packages/modules.

    This function is essential to be run before attempting to retrieve all
    :meth:`~.PageObjectRegistry.handle_urls` annotations from :class:`~.PageObjectRegistry`
    to ensure that they are properly acknowledged by importing them in runtime.

    Let's take a look at an example:

    .. code-block:: python

        # my_page_obj_project/load_rules.py

        from web_poet import default_registry, consume_modules

        consume_modules("other_external_pkg.po", "another_pkg.lib")
        rules = default_registry.get_overrides()

    For this case, the ``List`` of :class:`~.OverrideRule` are coming from:

        - ``my_page_obj_project`` `(since it's the same module as the file above)`
        - ``other_external_pkg.po``
        - ``another_pkg.lib``

    So if the ``default_registry`` had other ``@handle_urls`` annotations outside
    of the packages/modules listed above, then the :class:`~.OverrideRule` won't
    be returned.

    .. note::

        :meth:`~.PageObjectRegistry.get_overrides` provides a shortcut for this
        using its ``consume`` parameter. Thus, the code example above could be
        shortened even further by:

        .. code-block:: python

            from web_poet import default_registry

            rules = default_registry.get_overrides(consume=["other_external_pkg.po", "another_pkg.lib"])
    """

    for module in modules:
        gen = walk_module(module)

        # Inspired by itertools recipe: https://docs.python.org/3/library/itertools.html
        # Using a deque() results in a tiny bit performance improvement that list().
        deque(gen, maxlen=0)
