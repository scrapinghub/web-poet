"""Returns all Override Rules from the default registry."""

import argparse
from typing import Callable

import tabulate

from web_poet import default_registry


def qualified_name(cls: Callable) -> str:
    return f"{cls.__module__}.{cls.__name__}"


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Tool that list the Page Object overrides from a package or module recursively"
    )
    parser.add_argument(
        "module",
        metavar="PKG_OR_MODULE",
        type=str,
        help="A package or module to list overrides from",
    )
    args = parser.parse_args(args)
    table = [
        (
            "Use this",
            "instead of",
            "for the URL patterns",
            "except for the patterns",
            "with priority",
            "meta",
        )
    ]
    table += [
        (
            qualified_name(rule.use),
            qualified_name(rule.instead_of),
            rule.for_patterns.include,
            rule.for_patterns.exclude,
            rule.for_patterns.priority,
            rule.meta,
        )
        for rule in default_registry.get_overrides(filters=args.module)
    ]
    print(tabulate.tabulate(table, headers="firstrow"))


if __name__ == "__main__":
    main()  # pragma: no cover
