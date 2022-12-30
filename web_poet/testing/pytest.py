import operator
from pathlib import Path
from typing import Any, Iterable, List, Optional, Set, Union

import pytest

from web_poet.testing.utils import OUTPUT_FILE_NAME, Fixture


class WebPoetFile(pytest.File):
    """Represents a directory containing test subdirectories for one Page Object."""

    @staticmethod
    def sorted(items: List["WebPoetItem"]) -> List["WebPoetItem"]:
        """Sort the test list by the test name."""
        return sorted(items, key=operator.attrgetter("name"))

    def collect(self) -> Iterable[Union[pytest.Item, pytest.Collector]]:  # noqa: D102
        result: List[WebPoetItem] = []
        for entry in self.path.iterdir():
            if entry.is_dir():
                item: WebPoetItem = WebPoetItem.from_parent(
                    self,
                    name=entry.name,
                    path=entry,
                )
                if item.fixture.is_valid():
                    result.append(item)
        return self.sorted(result)


class WebPoetItem(pytest.Item):
    """Represents a directory containing one test."""

    def __init__(
        self,
        name,
        parent=None,
        config: Optional[pytest.Config] = None,
        session: Optional[pytest.Session] = None,
        nodeid: Optional[str] = None,
        **kw
    ) -> None:
        super().__init__(name, parent, config, session, nodeid, **kw)
        self.fixture = Fixture(self.path)

    def runtest(self) -> None:  # noqa: D102
        self.fixture.assert_output()


_found_type_dirs: Set[Path] = set()


def pytest_collect_file(
    file_path: Path, path: Any, parent: pytest.Collector
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
        file: WebPoetFile = WebPoetFile.from_parent(
            parent,
            path=type_dir,
            name=type_dir.name,
        )
        return file
    return None
