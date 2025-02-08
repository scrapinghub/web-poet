from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from zoneinfo import ZoneInfo

import dateutil.parser
import dateutil.tz
import time_machine

from web_poet import ItemPage
from web_poet.serialization import (
    SerializedDataFileStorage,
    deserialize,
    load_class,
    serialize,
)
from web_poet.utils import ensure_awaitable, get_fq_class_name, memoizemethod_noargs

from ..serialization.utils import _exception_from_dict, _exception_to_dict, _format_json
from .exceptions import (
    ExceptionNotRaised,
    FieldMissing,
    FieldsUnexpected,
    FieldValueIncorrect,
    ItemValueIncorrect,
    WrongExceptionRaised,
)
from .itemadapter import WebPoetTestItemAdapter

if TYPE_CHECKING:
    import datetime
    import os
    from collections.abc import Iterable

    from itemadapter import ItemAdapter

    # typing.Self requires Python 3.11
    from typing_extensions import Self

logger = logging.getLogger(__name__)


INPUT_DIR_NAME = "inputs"
OUTPUT_FILE_NAME = "output.json"
EXCEPTION_FILE_NAME = "exception.json"
META_FILE_NAME = "meta.json"


def _get_available_filename(template: str, directory: str | os.PathLike[str]) -> str:
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
        self._output_error: Exception | None = None

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
    def exception_path(self) -> Path:
        """The exception file path."""
        return self.path / EXCEPTION_FILE_NAME

    @property
    def meta_path(self) -> Path:
        """The metadata file path."""
        return self.path / META_FILE_NAME

    def is_valid(self) -> bool:
        """Return True if the fixture file structure is correct, False otherwise."""
        return self.input_path.is_dir() and (
            self.output_path.is_file() or self.exception_path.is_file()
        )

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
        meta_dict = json.loads(self.meta_path.read_bytes())
        if meta_dict.get("adapter"):
            meta_dict["adapter"] = load_class(meta_dict["adapter"])
        return meta_dict

    def _get_adapter_cls(self) -> type[ItemAdapter]:
        cls = self.get_meta().get("adapter")
        if not cls:
            return WebPoetTestItemAdapter
        return cast("type[ItemAdapter]", cls)

    def _get_output(self) -> dict:
        page = self.get_page()
        item = asyncio.run(ensure_awaitable(page.to_item()))
        return self._get_adapter_cls()(item).asdict()

    @memoizemethod_noargs
    def get_output(self) -> dict:
        """
        Return the output from the recreated Page Object,
        taking frozen time in account.
        """
        try:
            meta = self.get_meta()
            frozen_time: str | None = meta.get("frozen_time")
            if frozen_time:
                frozen_time_parsed = self._parse_frozen_time(frozen_time)
                with time_machine.travel(frozen_time_parsed):
                    return self._get_output()
            else:
                return self._get_output()
        except Exception as e:
            self._output_error = e
            raise

    def item_to_json(self, item: Any) -> str:
        """Convert an item to a JSON string."""
        return _format_json(self._get_adapter_cls()(item).asdict())

    @memoizemethod_noargs
    def get_expected_output(self) -> dict:
        """Return the saved output."""
        return json.loads(self.output_path.read_bytes())

    @memoizemethod_noargs
    def get_expected_exception(self) -> Exception:
        """Return the saved exception."""
        data = json.loads(self.exception_path.read_bytes())
        return _exception_from_dict(data)

    @staticmethod
    def _parse_frozen_time(meta_value: str) -> datetime.datetime:
        """Parse and possibly fix the frozen_time metadata string."""
        parsed_value = dateutil.parser.parse(meta_value)

        if parsed_value.tzinfo is None:
            # if it's left as None, time_machine will set it to timezone.utc,
            # but we want to interpret the value as local time
            return parsed_value.astimezone()

        if not time_machine.HAVE_TZSET:
            logger.warning(
                f"frozen_time {meta_value} includes timezone data which"
                f" is not supported on Windows, converting to local"
            )
            return parsed_value.astimezone()

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

    def assert_full_item_correct(self) -> None:
        """Get the output and assert that it matches the expected output."""
        output = _format_json(self.get_output())
        expected_output = _format_json(self.get_expected_output())
        if output != expected_output:
            raise ItemValueIncorrect(output, expected_output)

    def assert_field_correct(self, name: str) -> None:
        """Assert that a certain field in the output matches the expected value"""
        actual_item = self.get_output()
        if name not in actual_item:
            raise FieldMissing(name)
        expected_field = json.loads(_format_json(self.get_expected_output()[name]))
        actual_field = json.loads(_format_json(actual_item[name]))
        if actual_field != expected_field:
            raise FieldValueIncorrect(actual_field, expected_field)

    def assert_no_extra_fields(self) -> None:
        """Assert that there are no extra fields in the output"""
        output = self.get_output()
        expected_output = self.get_expected_output()
        extra_field_keys = output.keys() - expected_output.keys()
        extra_fields = {key: output[key] for key in extra_field_keys}
        if extra_fields:
            raise FieldsUnexpected(extra_fields)

    def to_item_raised(self) -> bool:
        """Return True if to_item raised an error.
        Note that if to_item hasn't been called yet, this method returns False.
        """
        return self._output_error is not None

    def assert_no_toitem_exceptions(self) -> None:
        """Assert that to_item() can be run (doesn't raise an error)"""
        self.get_output()

    def assert_toitem_exception(self) -> None:
        """Assert that to_item() raises an exception of the expected type"""
        try:
            self.get_output()
        except Exception as ex:
            received_type = type(ex)
            expected_type = type(self.get_expected_exception())
            if received_type != expected_type:
                raise WrongExceptionRaised from ex
        else:
            raise ExceptionNotRaised

    @classmethod
    def save(
        cls,
        base_directory: str | os.PathLike[str],
        *,
        inputs: Iterable[Any],
        item: Any = None,
        exception: Exception | None = None,
        meta: dict | None = None,
        fixture_name=None,
    ) -> Self:
        """Save and return a fixture."""
        if not fixture_name:
            fixture_name = _get_available_filename("test-{}", base_directory)
        fixture_dir = Path(base_directory, fixture_name)
        fixture = cls(fixture_dir)
        fixture.input_path.mkdir(parents=True)

        serialized_inputs = serialize(inputs)
        storage = SerializedDataFileStorage(fixture.input_path)
        storage.write(serialized_inputs)

        if meta:
            if meta.get("adapter"):
                meta["adapter"] = get_fq_class_name(meta["adapter"])
            fixture.meta_path.write_text(_format_json(meta))

        if item is not None:
            with fixture.output_path.open("w") as f:
                f.write(fixture.item_to_json(item))

        if exception:
            exc_data = _exception_to_dict(exception)
            fixture.exception_path.write_text(_format_json(exc_data))

        return fixture
