import argparse

import tabulate

from web_poet.meta import find_page_object_overrides


def qualified_name(cls: callable) -> str:
    return f"{cls.__module__}.{cls.__name__}"


def main():
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
    args = parser.parse_args()
    table = [("Use this", "instead of that", "for URL patterns", "else these URL patterns", "with priority")]
    table += [(qualified_name(po), qualified_name(meta.overrides), meta.patterns.include, meta.patterns.exclude, meta.patterns.priority)
              for po, meta in find_page_object_overrides(args.module, args.namespace).items()]
    print(tabulate.tabulate(table, headers="firstrow"))


if __name__ == "__main__":
    main()