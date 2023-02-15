import asyncio
import datetime
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Optional, Type, TypeVar, Union

import dateutil.parser
import dateutil.tz
import time_machine
from itemadapter import ItemAdapter

from web_poet import ItemPage
from web_poet.serialization import (
    SerializedDataFileStorage,
    deserialize,
    load_class,
    serialize,
)
from web_poet.utils import ensure_awaitable, memoizemethod_noargs

from .exceptions import (
    FieldMissing,
    FieldsUnexpected,
    FieldValueIncorrect,
    ItemValueIncorrect,
)

logger = logging.getLogger(__name__)


INPUT_DIR_NAME = "inputs"
OUTPUT_FILE_NAME = "output.json"
META_FILE_NAME = "meta.json"


FixtureT = TypeVar("FixtureT", bound="Fixture")


def _get_available_filename(template: str, directory: Union[str, os.PathLike]) -> str:
    i = 1
    while True:
        result = Path(directory, template.format(i))
        if not result.exists():
            return result.name
        i += 1


class Fixture:
    """Represents a directory containing one test."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @property
    def type_name(self) -> str:
        """The name of the type being tested."""
        return self.path.parent.name

    @property
    def test_name(self) -> str:
        """The name of the test."""
        return self.path.name

    @property
    def short_name(self) -> str:
        """The name of this fixture"""
        return f"{self.type_name}/{self.test_name}"

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

    def _get_output(self) -> dict:
        page = self.get_page()
        item = asyncio.run(ensure_awaitable(page.to_item()))
        return ItemAdapter(item).asdict()

    @memoizemethod_noargs
    def get_output(self) -> dict:
        """
        Return the output from the recreated Page Object,
        taking frozen time in account.
        """
        meta = self.get_meta()
        frozen_time: Optional[str] = meta.get("frozen_time")
        if frozen_time:
            frozen_time_parsed = self._parse_frozen_time(frozen_time)
            with time_machine.travel(frozen_time_parsed):
                return self._get_output()
        else:
            return self._get_output()

    @memoizemethod_noargs
    def get_expected_output(self) -> dict:
        """Return the saved output."""
        return json.loads(self.output_path.read_bytes())

    @staticmethod
    def _parse_frozen_time(meta_value: str) -> datetime.datetime:
        """Parse and possibly fix the frozen_time metadata string."""
        parsed_value = dateutil.parser.parse(meta_value)

        if parsed_value.tzinfo is None:
            # if it's left as None, time_machine will set it to timezone.utc,
            # but we want to interpret the value as local time
            parsed_value = parsed_value.astimezone()
            return parsed_value

        if not time_machine.HAVE_TZSET:
            logger.warning(
                f"frozen_time {meta_value} includes timezone data which"
                f" is not supported on Windows, converting to local"
            )
            return parsed_value.astimezone()

        if sys.version_info >= (3, 9):
            from zoneinfo import ZoneInfo
        else:
            from backports.zoneinfo import ZoneInfo

        if parsed_value.tzinfo == dateutil.tz.UTC:
            return parsed_value.replace(tzinfo=ZoneInfo("UTC"))

        offset = parsed_value.tzinfo.utcoffset(None)
        assert offset is not None  # typing
        offset_hours = int(offset.days * 24 + offset.seconds / 3600)
        tzinfo = ZoneInfo(f"Etc/GMT{-offset_hours:+d}")
        return parsed_value.replace(tzinfo=tzinfo)

    def get_expected_output_fields(self):
        """Return a list of the expected output field names."""
        output = self.get_expected_output()
        return list(output.keys())

    def assert_full_item_correct(self):
        """Get the output and assert that it matches the expected output."""
        output = self.get_output()
        expected_output = self.get_expected_output()
        if output != expected_output:
            raise ItemValueIncorrect(output, expected_output)

    def assert_field_correct(self, name: str):
        """Assert that a certain field in the output matches the expected value"""
        expected_output = self.get_expected_output()[name]
        if name not in self.get_output():
            raise FieldMissing(name)
        output = self.get_output()[name]
        if output != expected_output:
            raise FieldValueIncorrect(output, expected_output)

    def assert_no_extra_fields(self):
        """Assert that there are no extra fields in the output"""
        output = self.get_output()
        expected_output = self.get_expected_output()
        extra_field_keys = output.keys() - expected_output.keys()
        extra_fields = {key: output[key] for key in extra_field_keys}
        if extra_fields:
            raise FieldsUnexpected(extra_fields)

    @classmethod
    def save(
        cls: Type[FixtureT],
        base_directory: Union[str, os.PathLike],
        *,
        inputs: Iterable[Any],
        item: Any,
        meta: Optional[dict] = None,
        fixture_name=None,
    ) -> FixtureT:
        """Save and return a fixture."""
        if not fixture_name:
            fixture_name = _get_available_filename(
                "test-{}", base_directory  # noqa: P103
            )
        fixture_dir = Path(base_directory, fixture_name)
        fixture = cls(fixture_dir)
        fixture.input_path.mkdir(parents=True)
        serialized_inputs = serialize(inputs)
        storage = SerializedDataFileStorage(fixture.input_path)
        storage.write(serialized_inputs)
        with fixture.output_path.open("w") as f:
            json.dump(ItemAdapter(item).asdict(), f, ensure_ascii=True, indent=4)
        if meta:
            with fixture.meta_path.open("w") as f:
                json.dump(meta, f, ensure_ascii=True, indent=4)
        return fixture
