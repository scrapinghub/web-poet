"""Returns all Override Rules from the default registry."""

import argparse
from typing import Callable, Optional, List

import tabulate

from web_poet import registry_pool, consume_modules, PageObjectRegistry
from web_poet.overrides import OverrideRule


def qualified_name(cls: Callable) -> str:
    return f"{cls.__module__}.{cls.__name__}"


def parse_args(raw_args: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tool that list the Page Object overrides from a package or module recursively"
    )
    parser.add_argument(
        "module",
        metavar="PKG_OR_MODULE",
        type=str,
        help="A package or module to list overrides from",
    )
    parser.add_argument(
        "--registry_name",
        default="default",
        type=str,
        help="Name of the registry to retrieve the rules from.",
    )
    return parser.parse_args(args=raw_args)


def load_registry(args: argparse.Namespace) -> Optional[PageObjectRegistry]:
    consume_modules(args.module)
    registry = registry_pool.get(args.registry_name)
    return registry


def display_table(registry_name: str, rules: List[OverrideRule]) -> None:
    headers = [
        "Registry",
        "Use this",
        "instead of",
        "for the URL patterns",
        "except for the patterns",
        "with priority",
        "meta",
    ]

    table = [
        (
            registry_name,
            qualified_name(rule.use),
            qualified_name(rule.instead_of),
            rule.for_patterns.include,
            rule.for_patterns.exclude,
            rule.for_patterns.priority,
            rule.meta,
        )
        for rule in rules
    ]
    print(tabulate.tabulate(table, headers=headers))


def main(raw_args: Optional[List[str]] = None) -> Optional[List[OverrideRule]]:
    args = parse_args(raw_args)  # pragma: no cover
    registry = load_registry(args)
    if not registry:
        print(f"No registry named {args.registry_name} found.")
        return None
    rules = registry.get_overrides(filters=args.module)
    display_table(registry.name, rules)
    return rules  # for ease of testing


if __name__ == "__main__":
    main()  # pragma: no cover
