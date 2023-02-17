import argparse
from pathlib import Path

from web_poet.testing import Fixture


def rerun(args):
    fixture = Fixture(Path(args.fixture_path))
    item = fixture.get_output()
    print(fixture.item_to_json(item))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m web_poet.testing",
        description="web-poet testing utilities",
    )
    subparsers = parser.add_subparsers()
    parser_rerun = subparsers.add_parser(
        "rerun",
        description="Run the page object used in a fixture, print its output "
        "as JSON. This is most useful when the page object is changed, "
        "and you want to update the test case."
        "",
    )
    parser_rerun.add_argument("fixture_path", type=str, help="Path to a fixture")
    parser_rerun.set_defaults(func=rerun)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
