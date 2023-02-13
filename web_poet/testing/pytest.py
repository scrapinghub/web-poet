import operator
from pathlib import Path
from typing import Iterable, List, Optional, Set, Union

import pytest

from web_poet.testing.exceptions import (
    FieldsUnexpected,
    FieldValueError,
    ItemValueError,
)
from web_poet.testing.fixture import OUTPUT_FILE_NAME, Fixture
from web_poet.testing.utils import comparison_error_message

# https://github.com/pytest-dev/pytest/discussions/10261
_version_tuple = getattr(pytest, "version_tuple", None)
_new_pytest = _version_tuple and _version_tuple[0] >= 7


class _PathCompatMixin:
    @property
    def _path(self):
        return self.path if _new_pytest else Path(self.fspath)


class WebPoetFile(pytest.File, _PathCompatMixin):
    """Represents a directory containing test subdirectories for one Page Object."""

    @staticmethod
    def sorted(items: List["WebPoetCollector"]) -> List["WebPoetCollector"]:
        """Sort the test list by the test name."""
        return sorted(items, key=operator.attrgetter("name"))

    def collect(self) -> Iterable[Union[pytest.Item, pytest.Collector]]:  # noqa: D102
        result: List[WebPoetCollector] = []
        path = self._path
        for entry in path.iterdir():
            if entry.is_dir():
                item: WebPoetCollector = _get_collector(
                    self,
                    name=entry.name,
                    path=entry,
                )
                if item.fixture.is_valid():
                    result.append(item)
        return self.sorted(result)


class WebPoetCollector(pytest.Collector, _PathCompatMixin):
    """Represents a directory containing one test."""

    def __init__(self, name: str, parent=None, **kwargs) -> None:
        super(WebPoetCollector, self).__init__(name, parent, **kwargs)
        self.fixture = Fixture(self._path)

    def collect(self) -> Iterable[Union[pytest.Item, pytest.Collector]]:
        """Return a list of children (items and collectors) for this
        collection node."""
        if self.config.getoption("WEB_POET_TEST_PER_ITEM", default=False):
            return [
                WebPoetItem.from_parent(parent=self, name="item", fixture=self.fixture)
            ]
        else:
            field_tests = [
                WebPoetFieldItem.from_parent(
                    parent=self, name=field, fixture=self.fixture, field_name=field
                )
                for field in self.fixture.get_expected_output_fields()
            ]
            no_extra_fields_tests = [
                WebPoetNoExtraFieldsItem.from_parent(
                    parent=self, name="NO_EXTRA_FIELDS", fixture=self.fixture
                )
            ]
            return field_tests + no_extra_fields_tests


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
        if isinstance(excinfo.value, ItemValueError):
            got, expected = excinfo.value.args
            return comparison_error_message(
                config=self.config,
                op="==",
                expected=expected,
                got=got,
                prefix="The output doesn't match.",
            )
        else:
            return super().repr_failure(excinfo, style)


class WebPoetNoExtraFieldsItem(_WebPoetItem):
    def runtest(self) -> None:
        self.fixture.assert_no_extra_fields()

    def reportinfo(self):
        return self._path, 0, f"{self.fixture.short_name}: extra fields"

    def repr_failure(self, excinfo, style=None):
        if isinstance(excinfo.value, FieldsUnexpected):
            fields = excinfo.value.args[0]
            return f"The item contains unexpected fields: \n{self._format_extra_fields(fields)}"
        else:
            return super().repr_failure(excinfo, style)

    def _format_extra_fields(self, extra_fields):
        lines = []
        for field, value in extra_fields.items():
            lines.append(f" * {field} == {value!r}")
        return "\n".join(lines)


class WebPoetFieldItem(_WebPoetItem):
    def __init__(self, *, field_name: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.field_name = field_name

    def runtest(self) -> None:
        self.fixture.assert_field_correct(self.field_name)

    def reportinfo(self):
        return self._path, 0, f"{self.fixture.short_name} @ {self.field_name}"

    def repr_failure(self, excinfo, style=None):
        if isinstance(excinfo.value, FieldValueError):
            got, expected = excinfo.value.args
            return comparison_error_message(
                config=self.config,
                op="==",
                expected=expected,
                got=got,
                prefix=f"item.{self.field_name} is not correct.",
            )
        else:
            return super().repr_failure(excinfo, style)


_found_type_dirs: Set[Path] = set()


def collect_file_hook(
    file_path: Path, parent: pytest.Collector
) -> Optional[pytest.Collector]:
    if file_path.name == OUTPUT_FILE_NAME:
        testcase_dir = file_path.parent
        type_dir = testcase_dir.parent
        fixture = Fixture(testcase_dir)
        if not fixture.is_valid():
            return None
        if type_dir in _found_type_dirs:
            return None
        _found_type_dirs.add(type_dir)
        file: WebPoetFile = _get_file(
            parent,
            path=type_dir,
        )
        return file
    return None


def pytest_addoption(
    parser: "pytest.Parser", pluginmanager: "pytest.PytestPluginManager"
):
    parser.addoption(
        "--web-poet-test-per-item",
        dest="WEB_POET_TEST_PER_ITEM",
        action="store_true",
        help="web-poet: use a single test per item, not a test per field",
    )


if _new_pytest:

    def _get_item(parent: pytest.Collector, *, name: str, path: Path) -> WebPoetItem:
        return WebPoetItem.from_parent(
            parent,
            name=name,
            path=path,
        )

    def _get_collector(
        parent: pytest.Collector, *, name: str, path: Path
    ) -> WebPoetCollector:
        return WebPoetCollector.from_parent(
            parent,
            name=name,
            path=path,
        )

    def _get_file(parent: pytest.Collector, *, path: Path) -> WebPoetFile:
        return WebPoetFile.from_parent(
            parent,
            path=path,
        )

    def pytest_collect_file(
        file_path: Path, parent: pytest.Collector
    ) -> Optional[pytest.Collector]:
        return collect_file_hook(file_path, parent)

else:
    import py.path

    def _get_item(parent: pytest.Collector, *, name: str, path: Path) -> WebPoetItem:
        return WebPoetItem.from_parent(
            parent,
            name=name,
        )

    def _get_collector(
        parent: pytest.Collector, *, name: str, path: Path
    ) -> WebPoetCollector:
        return WebPoetCollector.from_parent(
            parent,
            name=name,
            fspath=py.path.local(path),
        )

    def _get_file(parent: pytest.Collector, *, path: Path) -> WebPoetFile:
        return WebPoetFile.from_parent(
            parent,
            fspath=py.path.local(path),
        )

    def pytest_collect_file(  # type: ignore[misc]
        path: py.path.local, parent: pytest.Collector
    ) -> Optional[pytest.Collector]:
        return collect_file_hook(Path(path), parent)
