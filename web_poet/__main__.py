import argparse
from typing import Callable

import tabulate

from web_poet.overrides import find_page_object_overrides


def qualified_name(cls: Callable) -> str:
    return f"{cls.__module__}.{cls.__name__}"


def main(args=None):
    parser = argparse.ArgumentParser(description=
                                     "Tool that list the Page Object overrides from a package or module recursively")
    parser.add_argument(
        "module",
        metavar="PKG_OR_MODULE",
        type=str,
        help="A package or module to list overrides from",
    )
    parser.add_argument(
        "--namespace", "-n", metavar="NAMESPACE", type=str, help="Namespace to list overrides from",
        default=""
    )
    args = parser.parse_args(args)
    table = [("Use this", "instead of", "for the URL patterns", "except for the patterns", "with priority", "meta")]
    table += [(qualified_name(rule.use), qualified_name(rule.instead_of), rule.for_patterns.include, rule.for_patterns.exclude, rule.for_patterns.priority, rule.meta)
              for rule in find_page_object_overrides(args.module, args.namespace)]
    print(tabulate.tabulate(table, headers="firstrow"))


if __name__ == "__main__":
    main()