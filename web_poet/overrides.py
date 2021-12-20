import importlib
import importlib.util
import warnings
import pkgutil
import sys
from dataclasses import dataclass, field
from typing import Iterable, Union, List, Callable, Dict, Any

from url_matcher import Patterns

# Used by ``PageObjectRegistry`` to declare itself in a module so that it's
# easily discovered by ``find_page_object_overrides()`` later on.
REGISTRY_MODULE_ANCHOR = "_registry_module_anchor_"


@dataclass(frozen=True)
class HandleUrlsSpec:
    """Meta information used by the :py:func:`web_poet.handle_urls` decorator"""

    patterns: Patterns
    overrides: Callable
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OverrideRule:
    """A single override rule. Specify when a page object should be used instead of another"""

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

        main_registry = PageObjectRegistry(name="main")
        secondary_registry = PageObjectRegistry(name="secondary")

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

        from web_poet import find_page_object_overrides

        po_path = "my_scrapy_project.page_objects"

        rules_main = find_page_object_overrides(po_path, registry="main")
        rules_secondary = find_page_object_overrides(po_path, registry="secondary")

    However, ``web-poet`` already contains a default Registry named ``"default"``.
    It can be directly accessed via:

    .. code-block:: python

        from web_poet import handle_urls, find_page_object_overrides

        @handle_urls("example.com", overrides=ProductPageObject)
        class ExampleComProductPage(ItemPage):
            ...

        # The `registry` is already set to 'default'
        find_page_object_overrides("my_scrapy_project.page_objects")

    Notice that there was no need to directly use the ``PageObjectRegistry`` as
    the convenience functions would suffice. In addition, if you need to organize
    your Page Objects in your Scrapy project, a single (1) instance of the
    ``PageObjectRegistry`` would work, as long as you organize your files
    into modules. The rules could then be accessed like:

    * ``find_page_object_overrides("my_scrapy_project.page_objects.site_A")``
    * ``find_page_object_overrides("my_scrapy_project.page_objects.site_B")``
    """

    def __init__(self, name: str = ""):
        self.name = name
        self.data: Dict[Callable, HandleUrlsSpec] = {}

    def _declare_registry_in_module(self, cls):
        """This allows the Registry to be easily discovered later on by
        ``find_page_object_overrides()`` by explicitly declaring its presence
        on the given module.
        """

        module = sys.modules[cls.__module__]
        if not hasattr(module, REGISTRY_MODULE_ANCHOR):
            registries = {self.name: self}
        else:
            registries = getattr(module, REGISTRY_MODULE_ANCHOR)
            registries[self.name] = self

        setattr(module, REGISTRY_MODULE_ANCHOR, registries)

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
            self._declare_registry_in_module(cls)

            spec = HandleUrlsSpec(
                patterns=Patterns(
                    include=_as_list(include),
                    exclude=_as_list(exclude),
                    priority=priority,
                ),
                overrides=overrides,
                meta=kwargs,
            )
            # If it was already defined, we don't want to override it
            if cls not in self.data:
                self.data[cls] = spec
            else:
                warnings.warn(
                    f"Multiple @handle_urls annotations with the same 'overrides' "
                    f"are ignored in the same Registry. Ignoring duplicate "
                    f"annotation on '{include}' for {cls}."
                )

            return cls

        return wrapper

    def get_data_from_module(self, module: str) -> Dict[Callable, HandleUrlsSpec]:
        """Returns the override mappings that were declared using ``handle_urls``
        in a specific module.

        This is useful if you've organized your Page Objects into multiple
        submodules in your project.
        """
        return {
            cls: spec
            for cls, spec in self.data.items()
            if cls.__module__.startswith(module.__name__)
        }

    def __repr__(self) -> str:
        return f"PageObjectRegistry(name='{self.name}')"


# For ease of use, we'll create a default registry so that users can simply
# use its `handles_url()` method directly by `from web_poet import handles_url`
default_registry = PageObjectRegistry(name="default")
handle_urls = default_registry.handle_urls


def walk_modules(module: str) -> Iterable:
    """
    Return all modules from a module recursively. Note that this will import all the modules and submodules.
    It returns the provided module as well.
    """

    def onerror(_):
        raise

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


def find_page_object_overrides(
    module: str, registry: str = "default"
) -> List[OverrideRule]:
    """
    Find all the Page Objects overrides in the given module/package and its
    submodules.

    The Page Objects that have been decorated with the ``handle_urls`` decorator
    from the specified Registry ``name`` will be returned.

    Note that this will explore the `module` and traverse its `submodules`.

    :param module: The module or package to search in
    :param registry: Only return page objects overrides in this registry
    :return: Return a list of :py:class:`web_poet.overrides.OverrideRule` metadata.
    """

    page_objects: Dict[Callable, HandleUrlsSpec] = {}
    for module in walk_modules(module):
        handle_urls_dict = getattr(module, REGISTRY_MODULE_ANCHOR, {})

        # A module could have multiple non-default PageObjectRegistry instances
        registry = handle_urls_dict.get(registry)
        if not registry:
            continue

        page_objects.update(registry.get_data_from_module(module))

    return [
        OverrideRule(
            for_patterns=spec.patterns,
            use=po,
            instead_of=spec.overrides,
            meta=spec.meta,
        )
        for po, spec in page_objects.items()
    ]
