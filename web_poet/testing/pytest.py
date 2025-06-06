from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from web_poet.testing.exceptions import (
    ExceptionNotRaised,
    FieldMissing,
    FieldsUnexpected,
    FieldValueIncorrect,
    ItemValueIncorrect,
    WrongExceptionRaised,
)
from web_poet.testing.fixture import EXCEPTION_FILE_NAME, OUTPUT_FILE_NAME, Fixture
from web_poet.testing.utils import comparison_error_message
from web_poet.utils import get_fq_class_name

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


class TestCase(pytest.File):
    """Represents the ``output.json`` or ``exception.json`` file in a testcase
    directory."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fixture = Fixture(self.path.parent)

    def collect(self) -> Iterable[pytest.Item | pytest.Collector]:
        if self.fixture.exception_path.exists():
            return [
                WebPoetExpectedException.from_parent(
                    parent=self, name="TO_ITEM_RAISES", fixture=self.fixture
                )
            ]
        if self.config.getoption("WEB_POET_TEST_PER_ITEM", default=False):
            return [
                WebPoetItem.from_parent(parent=self, name="item", fixture=self.fixture)
            ]
        overall_tests: list[pytest.Item] = [
            WebPoetNoToItemException.from_parent(
                parent=self, name="TO_ITEM_DOESNT_RAISE", fixture=self.fixture
            ),
            WebPoetNoExtraFieldsItem.from_parent(
                parent=self, name="NO_EXTRA_FIELDS", fixture=self.fixture
            ),
        ]
        field_tests: list[pytest.Item] = [
            WebPoetFieldItem.from_parent(
                parent=self, name=field, fixture=self.fixture, field_name=field
            )
            for field in self.fixture.get_expected_output_fields()
        ]
        return overall_tests + field_tests


class _WebPoetItem(pytest.Item):
    def __init__(self, *, fixture: Fixture, **kwargs) -> None:
        super().__init__(**kwargs)
        self.fixture = fixture


class WebPoetItem(_WebPoetItem):
    def runtest(self) -> None:
        self.fixture.assert_full_item_correct()

    def reportinfo(self):
        return self.path, 0, f"{self.fixture.short_name}"

    def repr_failure(self, excinfo, style=None):
        if isinstance(excinfo.value, ItemValueIncorrect):
            got, expected = excinfo.value.args
            return comparison_error_message(
                config=self.config,
                op="==",
                expected=expected,
                got=got,
                prefix="The output doesn't match.",
            )
        return super().repr_failure(excinfo, style)


class WebPoetNoExtraFieldsItem(_WebPoetItem):
    def runtest(self) -> None:
        if self.fixture.to_item_raised():
            raise pytest.skip(
                "Skipping a test for unexpected item fields "
                "because to_item raised an exception."
            )
        self.fixture.assert_no_extra_fields()

    def reportinfo(self):
        return self.path, 0, f"{self.fixture.short_name}: extra fields"

    def repr_failure(self, excinfo, style=None):
        if isinstance(excinfo.value, FieldsUnexpected):
            fields = excinfo.value.args[0]
            return f"The item contains unexpected fields: \n{self._format_extra_fields(fields)}"
        return super().repr_failure(excinfo, style)

    def _format_extra_fields(self, extra_fields):
        lines = []
        for field, value in extra_fields.items():
            lines.append(f" * {field} = {value!r}")
        return "\n".join(lines)


class WebPoetNoToItemException(_WebPoetItem):
    def runtest(self) -> None:
        self.fixture.assert_no_toitem_exceptions()

    def reportinfo(self):
        return (
            self.path,
            0,
            f"{self.fixture.short_name}: to_item doesn't raise an error",
        )


class WebPoetExpectedException(_WebPoetItem):
    def runtest(self) -> None:
        self.fixture.assert_toitem_exception()

    def reportinfo(self):
        return (
            self.path,
            0,
            f"{self.fixture.short_name}: to_item raises {self.fixture.get_expected_exception().__class__.__name__}",
        )

    def repr_failure(self, excinfo, style=None):
        expected = self.fixture.get_expected_exception()
        if isinstance(excinfo.value, ExceptionNotRaised):
            return (
                f"to_item() didn't raise an exception."
                f" {get_fq_class_name(type(expected))} was expected."
            )
        if isinstance(excinfo.value, WrongExceptionRaised):
            got = excinfo.value.__cause__
            inner_excinfo = pytest.ExceptionInfo.from_exc_info(
                (type(got), got, got.__traceback__)
            )
            return (
                f"to_item() raised a wrong exception. Expected"
                f" {get_fq_class_name(type(expected))}, got"
                f" {get_fq_class_name(type(got))}.\n\n"
                + str(super().repr_failure(inner_excinfo, style))
            )
        return super().repr_failure(excinfo, style)


class WebPoetFieldItem(_WebPoetItem):
    def __init__(self, *, field_name: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.field_name = field_name

    def runtest(self) -> None:
        if self.fixture.to_item_raised():
            raise pytest.skip(
                f"Skipping a test for item.{self.field_name} "
                f"because to_item raised an exception"
            )
        self.fixture.assert_field_correct(self.field_name)

    def reportinfo(self):
        return self.path, 0, f"{self.fixture.short_name} @ {self.field_name}"

    def repr_failure(self, excinfo, style=None):
        if isinstance(excinfo.value, FieldValueIncorrect):
            got, expected = excinfo.value.args
            return comparison_error_message(
                config=self.config,
                op="==",
                expected=expected,
                got=got,
                prefix=f"item.{self.field_name} is not correct.",
            )
        if isinstance(excinfo.value, FieldMissing):
            field_name = excinfo.value.args[0]
            return f"item.{field_name} is missing."
        return super().repr_failure(excinfo, style)


def pytest_addoption(parser: pytest.Parser, pluginmanager: pytest.PytestPluginManager):
    parser.addoption(
        "--web-poet-test-per-item",
        dest="WEB_POET_TEST_PER_ITEM",
        action="store_true",
        help="web-poet: use a single test per item, not a test per field",
    )


def pytest_collect_file(
    file_path: Path, parent: pytest.Collector
) -> pytest.Collector | None:
    if file_path.name in {OUTPUT_FILE_NAME, EXCEPTION_FILE_NAME}:
        fixture = Fixture(file_path.parent)
        if fixture.is_valid():
            return TestCase.from_parent(parent, path=file_path)
    return None
