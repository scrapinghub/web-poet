import operator
from pathlib import Path
from typing import Any, Iterable, List, Optional, Set, Union

import pytest

from web_poet.testing.fixture import OUTPUT_FILE_NAME, Fixture

# https://github.com/pytest-dev/pytest/discussions/10261
_version_tuple = getattr(pytest, "version_tuple", None)
_new_pytest = _version_tuple and _version_tuple[0] >= 7


class WebPoetFile(pytest.File):
    """Represents a directory containing test subdirectories for one Page Object."""

    @staticmethod
    def sorted(items: List["WebPoetItem"]) -> List["WebPoetItem"]:
        """Sort the test list by the test name."""
        return sorted(items, key=operator.attrgetter("name"))

    def collect(self) -> Iterable[Union[pytest.Item, pytest.Collector]]:  # noqa: D102
        result: List[WebPoetItem] = []
        path = self.path if _new_pytest else Path(self.fspath)
        for entry in path.iterdir():
            if entry.is_dir():
                item: WebPoetItem = _get_item(
                    self,
                    name=entry.name,
                    path=entry,
                )
                if item.fixture.is_valid():
                    result.append(item)
        return self.sorted(result)


class WebPoetItem(pytest.Item):
    """Represents a directory containing one test."""

    if _new_pytest:

        def __init__(
            self,
            name,
            parent=None,
            config: Optional["pytest.Config"] = None,
            session: Optional[pytest.Session] = None,
            nodeid: Optional[str] = None,
            **kw,
        ) -> None:
            super().__init__(name, parent, config, session, nodeid, **kw)
            self.fixture = Fixture(self.path)

    else:

        def __init__(  # type: ignore[misc]
            self,
            name,
            parent=None,
            config: Optional[Any] = None,
            session: Optional[pytest.Session] = None,
            nodeid: Optional[str] = None,
        ) -> None:
            super().__init__(name, parent, config, session, nodeid)
            self.fixture = Fixture(Path(self.fspath, self.name))

    def runtest(self) -> None:  # noqa: D102
        self.fixture.assert_output()


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


if _new_pytest:

    def _get_item(parent: pytest.Collector, *, name: str, path: Path) -> WebPoetItem:
        return WebPoetItem.from_parent(
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

    def _get_file(parent: pytest.Collector, *, path: Path) -> WebPoetFile:
        return WebPoetFile.from_parent(
            parent,
            fspath=py.path.local(path),
        )

    def pytest_collect_file(  # type: ignore[misc]
        path: py.path.local, parent: pytest.Collector
    ) -> Optional[pytest.Collector]:
        return collect_file_hook(Path(path), parent)
