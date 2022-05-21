from __future__ import annotations  # https://www.python.org/dev/peps/pep-0563/

import importlib
import importlib.util
import warnings
import pkgutil
from collections import deque
from dataclasses import dataclass, field
from operator import attrgetter
from typing import Iterable, Optional, Union, List, Callable, Dict, Any, TypeVar, Type

from url_matcher import Patterns

from web_poet.utils import as_list

Strings = Union[str, Iterable[str]]

PageObjectRegistryTV = TypeVar("PageObjectRegistryTV", bound="PageObjectRegistry")


@dataclass(frozen=True)
class OverrideRule:
    """A single override rule that specifies when a Page Object should be used
    in lieu of another.

    This is instantiated when using the :func:`web_poet.handle_urls` decorator.
    It's also being returned as a ``List[OverrideRule]`` when calling the
    ``web_poet.default_registry``'s :meth:`~.PageObjectRegistry.get_overrides`
    method.

    You can access any of its attributes:

        * ``for_patterns`` - contains the list of URL patterns associated with
          this rule. You can read the API documentation of the `url-matcher
          <https://url-matcher.readthedocs.io/>`_ package for more information
          about the patterns.
        * ``use`` - The Page Object that will be **used**.
        * ``instead_of`` - The Page Object that will be **replaced**.
        * ``meta`` - Any other information you may want to store. This doesn't
          do anything for now but may be useful for future API updates.

    .. tip::

        The :class:`~.OverrideRule` is also hashable. This makes it easy to store
        unique rules and identify any duplicates.
    """

    for_patterns: Patterns
    use: Callable
    instead_of: Callable
    meta: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.for_patterns, self.use, self.instead_of))


class PageObjectRegistry(dict):
    """This contains the mapping rules that associates the Page Objects available
    for a given URL matching rule.

    Note that it's simply a ``dict`` subclass with added functionalities on
    storing, retrieving, and searching for the :class:`~.OverrideRule` instances.
    The **value** represents the :class:`~.OverrideRule` instance from which the
    Page Object in the **key** is allowed to be used. Since it's essentially a
    ``dict``, you can use any ``dict`` operations with it.

    ``web-poet`` already provides a default Registry named ``default_registry``
    for convenience. It can be directly accessed via:

    .. code-block:: python

        from web_poet import handle_urls, default_registry, ItemWebPage

        @handle_urls("example.com", overrides=ProductPageObject)
        class ExampleComProductPage(ItemWebPage):
            ...

        override_rules = default_registry.get_overrides()

    Notice that the ``@handle_urls`` that we're using is a part of the
    ``default_registry``. This provides a shorter and quicker way to interact
    with the built-in default :class:`~.PageObjectRegistry` instead of writing
    the longer ``@default_registry.handle_urls``.

    .. note::

        It is encouraged to simply use and import the already existing registry
        via ``from web_poet import default_registry`` instead of creating your
        own :class:`~.PageObjectRegistry` instance. Using multiple registries
        would be unwieldy in most cases.

        However, it might be applicable in certain scenarios like storing custom
        rules to separate it from the ``default_registry``. This :ref:`example
        <overrides-custom-registry>` from the tutorial section may provide some
        context.
    """

    @classmethod
    def from_override_rules(
        cls: Type[PageObjectRegistryTV], rules: List[OverrideRule]
    ) -> PageObjectRegistryTV:
        """An alternative constructor for creating a :class:`~.PageObjectRegistry`
        instance by accepting a list of :class:`~.OverrideRule`.

        This is useful in cases wherein you need to store some selected rules
        from multiple external packages.
        """
        return cls({rule.use: rule for rule in rules})

    def handle_urls(
        self,
        include: Strings,
        *,
        overrides: Callable,
        exclude: Optional[Strings] = None,
        priority: int = 500,
        **kwargs,
    ):
        """
        Class decorator that indicates that the decorated Page Object should be
        used instead of the overridden one for a particular set the URLs.

        The Page Object that is **overridden** is declared using the ``overrides``
        parameter.

        The **override** mechanism only works on certain URLs that match the
        ``include`` and ``exclude`` parameters. See the documentation of the
        `url-matcher <https://url-matcher.readthedocs.io/>`_ package for more
        information about them.

        Any extra parameters are stored as meta information that can be later used.

        :param include: The URLs that should be handled by the decorated Page Object.
        :param overrides: The Page Object that should be `replaced`.
        :param exclude: The URLs over which the override should **not** happen.
        :param priority: The resolution priority in case of `conflicting` rules.
            A conflict happens when the ``include``, ``override``, and ``exclude``
            parameters are the same. If so, the `highest priority` will be
            chosen.
        """

        def wrapper(cls):
            rule = OverrideRule(
                for_patterns=Patterns(
                    include=as_list(include),
                    exclude=as_list(exclude),
                    priority=priority,
                ),
                use=cls,
                instead_of=overrides,
                meta=kwargs,
            )
            # If it was already defined, we don't want to override it
            if cls not in self:
                self[cls] = rule
            else:
                warnings.warn(
                    f"Multiple @handle_urls annotations with the same 'overrides' "
                    f"are ignored in the same Registry. The following rule is "
                    f"ignored:\n{rule}",
                    stacklevel=2,
                )

            return cls

        return wrapper

    def get_overrides(self) -> List[OverrideRule]:
        """Returns all of the :class:`~.OverrideRule` that were declared using
        the ``@handle_urls`` annotation.

        .. warning::

            Remember to consider calling :func:`~.web_poet.overrides.consume_modules`
            beforehand to recursively import all submodules which contains the
            ``@handle_urls`` annotations from external Page Objects.
        """
        return list(self.values())

    def search_overrides(self, **kwargs) -> List[OverrideRule]:
        """Returns any :class:`OverrideRule` that has any of its attributes
        match the rules inside the registry.

        Sample usage:

        .. code-block:: python

            rules = registry.search_overrides(use=ProductPO, instead_of=GenericPO)
            print(len(rules))  # 1

        """

        # Short-circuit operation if "use" is the only search param used, since
        # we know that it's being used as the dict key.
        if {"use"} == kwargs.keys():
            rule = self.get(kwargs["use"])
            if rule:
                return [rule]
            return []

        getter = attrgetter(*kwargs.keys())

        def matcher(rule: OverrideRule):
            attribs = getter(rule)
            if not isinstance(attribs, tuple):
                attribs = tuple([attribs])
            if list(attribs) == list(kwargs.values()):
                return True
            return False

        results = []
        for rule in self.get_overrides():
            if matcher(rule):
                results.append(rule)
        return results


def _walk_module(module: str) -> Iterable:
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
    """This recursively imports all packages/modules so that the ``@handle_urls``
    annotation are properly discovered and imported.

    Let's take a look at an example:

    .. code-block:: python

        # FILE: my_page_obj_project/load_rules.py

        from web_poet import default_registry, consume_modules

        consume_modules("other_external_pkg.po", "another_pkg.lib")
        rules = default_registry.get_overrides()

    For this case, the :class:`~.OverrideRule` are coming from:

        - ``my_page_obj_project`` `(since it's the same module as the file above)`
        - ``other_external_pkg.po``
        - ``another_pkg.lib``
        - any other modules that was imported in the same process inside the
          packages/modules above.

    If the ``default_registry`` had other ``@handle_urls`` annotations outside
    of the packages/modules listed above, then the corresponding
    :class:`~.OverrideRule` won't be returned. Unless, they were recursively
    imported in some way similar to :func:`~.web_poet.overrides.consume_modules`.
    """

    for module in modules:
        gen = _walk_module(module)

        # Inspired by itertools recipe: https://docs.python.org/3/library/itertools.html
        # Using a deque() results in a tiny bit performance improvement that list().
        deque(gen, maxlen=0)
