import asyncio
import json
from pathlib import Path
from typing import Any, Iterable, Optional, Set, Union

import pytest

from web_poet import ItemPage
from web_poet.serialization import SerializedDataFileStorage, deserialize, load_class
from web_poet.utils import ensure_awaitable


class WebPoetFile(pytest.File):
    """Represents a directory containing test case sibdirectories for one PO."""

    def collect(self) -> Iterable[Union[pytest.Item, pytest.Collector]]:  # noqa: D102
        for entry in self.path.iterdir():
            if entry.is_dir():
                item: WebPoetItem = WebPoetItem.from_parent(
                    self,
                    name=entry.name,
                    path=entry,
                )
                if item.input_path.is_dir() and item.output_path.is_file():
                    # item.add_marker(pytest.mark.asyncio)
                    yield item


class WebPoetItem(pytest.Item):
    """Represents a directory containing one test case."""

    @property
    def po_name(self) -> str:
        """The type name of the PO being tested."""
        if not self.parent:
            raise ValueError("WebPoetItem has no parent")
        return self.parent.name

    @property
    def input_path(self) -> Path:
        """The po subdirectory path."""
        return self.path / "po"

    @property
    def output_path(self) -> Path:
        """The output.json file path"""
        return self.path / "output.json"

    def get_po(self) -> ItemPage:
        """Return the PO object created from the saved input."""
        po_type = load_class(self.po_name)
        if not issubclass(po_type, ItemPage):
            raise TypeError(f"{self.po_name} is not a descendant of ItemPage")
        storage = SerializedDataFileStorage(self.input_path)
        return deserialize(po_type, storage.read())

    async def get_po_output(self) -> dict:
        """Return the output from the PO."""
        po = self.get_po()
        return await ensure_awaitable(po.to_item())

    def get_expected_output(self) -> dict:
        """Return the saved output."""
        return json.loads(self.output_path.read_bytes())

    def runtest(self) -> None:  # noqa: D102
        output = asyncio.run(self.get_po_output())
        expected_output = self.get_expected_output()
        assert output == expected_output


_found_po_dirs: Set[Path] = set()


def pytest_collect_file(
    file_path: Path, path: Any, parent: pytest.Collector
) -> Optional[pytest.Collector]:
    if file_path.name == "output.json":
        po_dir = file_path.parent.parent
        if po_dir in _found_po_dirs:
            return None
        _found_po_dirs.add(po_dir)
        file: WebPoetFile = WebPoetFile.from_parent(
            parent,
            path=po_dir,
            name=po_dir.name,
        )
        return file
    return None
