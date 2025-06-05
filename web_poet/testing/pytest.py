from __future__ import annotations

import operator
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

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

# https://github.com/pytest-dev/pytest/discussions/10261
_version_tuple = getattr(pytest, "version_tuple", None)
_new_pytest = _version_tuple and _version_tuple[0] >= 7


class _PathCompatMixin:
    @property
    def _path(self):
        return self.path if _new_pytest else Path(self.fspath)


class FixturesTestFile(pytest.File, _PathCompatMixin):
    """Represents the ``test.py`` file at the root of a fixtures dir."""

    @staticmethod
    def sorted(items: list[PageDir]) -> list[PageDir]:
        """Sort the test list by the test name."""
        return sorted(items, key=operator.attrgetter("name"))

    def collect(self) -> Iterable[pytest.Item | pytest.Collector]:
        result: list[PageDir] = []
        for page_path in self._path.parent.iterdir():
            if not page_path.is_dir():
                continue
            item: PageDir = _get_section(
                PageDir,
                self,
                name=page_path.name,
                path=page_path,
            )
            result.append(item)
        return self.sorted(result)


class PageDir(pytest.Collector, _PathCompatMixin):
    """Represents a directory containing test subdirectories for one Page Object."""

    def __init__(self, name: str, parent=None, **kwargs) -> None:
        super().__init__(name, parent, **kwargs)
        self.fixture = Fixture(self._path)

    @staticmethod
    def sorted(items: list[TestCase]) -> list[TestCase]:
        """Sort the test list by the test name."""
        return sorted(items, key=operator.attrgetter("name"))

    def collect(self) -> Iterable[pytest.Item | pytest.Collector]:
        result: list[TestCase] = []
        for testcase_path in self._path.iterdir():
            if not testcase_path.is_dir():
                continue
            item: TestCase = _get_section(
                TestCase,
                self,
                name=testcase_path.name,
                path=testcase_path,
            )
            if item.fixture.is_valid():
                result.append(item)
        return self.sorted(result)


class TestCase(pytest.Collector, _PathCompatMixin):
    """Represents a directory containing one testcase."""

    def __init__(self, name: str, parent=None, **kwargs) -> None:
        super().__init__(name, parent, **kwargs)
        self.fixture = Fixture(self._path)

    def collect(self) -> Iterable[pytest.Item | pytest.Collector]:
        """Return a list of children (items and collectors) for this
        collection node."""
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


class _WebPoetItem(pytest.Item, _PathCompatMixin):
    def __init__(self, *, fixture: Fixture, **kwargs) -> None:
        super().__init__(**kwargs)
        self.fixture = fixture


class WebPoetItem(_WebPoetItem):
    def runtest(self) -> None:
        self.fixture.assert_full_item_correct()

    def reportinfo(self):
        return self._path, 0, f"{self.fixture.short_name}"

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
        return self._path, 0, f"{self.fixture.short_name}: extra fields"

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
            self._path,
            0,
            f"{self.fixture.short_name}: to_item doesn't raise an error",
        )


class WebPoetExpectedException(_WebPoetItem):
    def runtest(self) -> None:
        self.fixture.assert_toitem_exception()

    def reportinfo(self):
        return (
            self._path,
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
            if _new_pytest:
                from pytest import ExceptionInfo  # noqa: PT013
            else:
                from _pytest._code import ExceptionInfo
            inner_excinfo = ExceptionInfo.from_exc_info(
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
        return self._path, 0, f"{self.fixture.short_name} @ {self.field_name}"

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


_found_fixtures_test_files: set[Path] = set()


def collect_file_hook(
    file_path: Path, parent: pytest.Collector
) -> pytest.Collector | None:
    if file_path.name in {OUTPUT_FILE_NAME, EXCEPTION_FILE_NAME}:
        testcase_dir = file_path.parent
        page_dir = testcase_dir.parent
        fixture = Fixture(testcase_dir)
        if not fixture.is_valid():
            return None
        fixtures_test_file = page_dir.parent / "test.py"
        if (
            fixtures_test_file in _found_fixtures_test_files
            or not fixtures_test_file.exists()
        ):
            return None
        _found_fixtures_test_files.add(fixtures_test_file)
        return _get_file(parent, path=fixtures_test_file)
    if file_path.name == "test.py" and file_path not in _found_fixtures_test_files:
        for page_dir in file_path.parent.iterdir():
            if not page_dir.is_dir():
                continue
            for testcase_dir in page_dir.iterdir():
                if not testcase_dir.is_dir():
                    continue
                for testcase_file in testcase_dir.iterdir():
                    if testcase_file.name not in {
                        OUTPUT_FILE_NAME,
                        EXCEPTION_FILE_NAME,
                    }:
                        continue
                    _found_fixtures_test_files.add(file_path)
                    return _get_file(parent, path=file_path)
    return None


def pytest_addoption(parser: pytest.Parser, pluginmanager: pytest.PytestPluginManager):
    parser.addoption(
        "--web-poet-test-per-item",
        dest="WEB_POET_TEST_PER_ITEM",
        action="store_true",
        help="web-poet: use a single test per item, not a test per field",
    )


T = TypeVar("T", bound=pytest.Collector)

if _new_pytest:

    def _get_section(
        cls: type[T], parent: pytest.Collector, *, name: str, path: Path
    ) -> T:
        return cls.from_parent(
            parent,
            name=name,
            path=path,
        )

    def _get_file(parent: pytest.Collector, *, path: Path) -> FixturesTestFile:
        return FixturesTestFile.from_parent(
            parent,
            path=path,
        )

    def pytest_collect_file(
        file_path: Path, parent: pytest.Collector
    ) -> pytest.Collector | None:
        return collect_file_hook(file_path, parent)

else:
    import py.path

    def _get_section(
        cls: type[T], parent: pytest.Collector, *, name: str, path: Path
    ) -> T:
        kwargs = {}
        if cls is not WebPoetItem:
            kwargs["fspath"] = py.path.local(path)  # noqa: PTH124
        return cls.from_parent(
            parent,
            name=name,
            **kwargs,
        )

    def _get_file(parent: pytest.Collector, *, path: Path) -> FixturesTestFile:
        return FixturesTestFile.from_parent(
            parent,
            fspath=py.path.local(path),  # noqa: PTH124
        )

    def pytest_collect_file(  # type: ignore[misc]
        path: py.path.local, parent: pytest.Collector
    ) -> pytest.Collector | None:
        return collect_file_hook(Path(path), parent)
