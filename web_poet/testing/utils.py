import asyncio
import json
import os
from pathlib import Path
from typing import Any, Iterable, Optional, Union

from freezegun import freeze_time
from itemadapter import ItemAdapter

from web_poet import ItemPage
from web_poet.serialization import (
    SerializedDataFileStorage,
    deserialize,
    load_class,
    serialize,
)
from web_poet.utils import ensure_awaitable

INPUT_DIR_NAME = "inputs"
OUTPUT_FILE_NAME = "output.json"
META_FILE_NAME = "meta.json"


def _get_available_filename(template: str, directory: Union[str, os.PathLike]) -> str:
    i = 1
    while True:
        result = Path(directory, template.format(i))
        if not result.exists():
            return result.name
        i += 1


class Fixture:
    """Represents a directory containing one test."""

    def __init__(self, type_name: str, path: Path) -> None:
        self.type_name = type_name
        self.path = path

    @property
    def input_path(self) -> Path:
        """The inputs subdirectory path."""
        return self.path / INPUT_DIR_NAME

    @property
    def output_path(self) -> Path:
        """The output file path."""
        return self.path / OUTPUT_FILE_NAME

    @property
    def meta_path(self) -> Path:
        """The metadata file path."""
        return self.path / META_FILE_NAME

    def is_valid(self) -> bool:
        """Return True if the fixture file structure is correct, False otherwise."""
        return self.input_path.is_dir() and self.output_path.is_file()

    def get_page(self) -> ItemPage:
        """Return the page object created from the saved input."""
        cls = load_class(self.type_name)
        if not issubclass(cls, ItemPage):
            raise TypeError(f"{self.type_name} is not a descendant of ItemPage")
        storage = SerializedDataFileStorage(self.input_path)
        return deserialize(cls, storage.read())

    def get_meta(self) -> dict:
        """Return the test metadata."""
        if not self.meta_path.exists():
            return {}
        return json.loads(self.meta_path.read_bytes())

    def get_output(self) -> dict:
        """Return the output from the recreated Page Object."""
        po = self.get_page()
        item = asyncio.run(ensure_awaitable(po.to_item()))
        return ItemAdapter(item).asdict()

    def get_expected_output(self) -> dict:
        """Return the saved output."""
        return json.loads(self.output_path.read_bytes())

    def assert_output(self):
        """Get the output and assert that it matches the expected output."""
        meta = self.get_meta()
        frozen_time: Optional[str] = meta.get("frozen_time")
        if frozen_time:
            with freeze_time(frozen_time):
                output = self.get_output()
        else:
            output = self.get_output()
        expected_output = self.get_expected_output()
        assert output == expected_output


def save_fixture(
    base_directory: Union[str, os.PathLike],
    inputs: Iterable[Any],
    item: Any,
    meta: Optional[dict] = None,
    fixture_name=None,
) -> Path:
    if not fixture_name:
        fixture_name = _get_available_filename("test-{}", base_directory)  # noqa: P103
    fixture_dir = Path(base_directory, fixture_name)
    inputs_dir = Path(fixture_dir, INPUT_DIR_NAME)
    inputs_dir.mkdir(parents=True)
    serialized_inputs = serialize(inputs)
    storage = SerializedDataFileStorage(inputs_dir)
    storage.write(serialized_inputs)
    with Path(fixture_dir, OUTPUT_FILE_NAME).open("w") as f:
        json.dump(ItemAdapter(item).asdict(), f, ensure_ascii=True, indent=4)
    if meta:
        with Path(fixture_dir, META_FILE_NAME).open("w") as f:
            json.dump(meta, f, ensure_ascii=True, indent=4)
    return fixture_dir
