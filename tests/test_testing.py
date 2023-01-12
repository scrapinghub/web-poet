import datetime
import json
import sys
from pathlib import Path
from typing import Optional

import attrs
import dateutil.tz
import pytest
import time_machine
from itemadapter import ItemAdapter
from zyte_common_items import Item, Metadata, Product

from web_poet import HttpResponse, WebPage
from web_poet.testing import Fixture
from web_poet.testing.fixture import INPUT_DIR_NAME, META_FILE_NAME, OUTPUT_FILE_NAME
from web_poet.utils import get_fq_class_name


def test_save_fixture(book_list_html_response, tmp_path) -> None:
    base_dir = tmp_path / "fixtures" / "some.po"
    item = {"foo": "bar"}
    meta = {"foo": "bar", "frozen_time": "2022-01-01"}

    def _assert_fixture_files(
        directory: Path, expected_meta: Optional[dict] = None
    ) -> None:
        input_dir = directory / INPUT_DIR_NAME
        assert (input_dir / "HttpResponse-body.html").exists()
        assert (input_dir / "HttpResponse-body.html").read_bytes() == bytes(
            book_list_html_response.body
        )
        assert (input_dir / "HttpResponse-other.json").exists()
        assert (directory / OUTPUT_FILE_NAME).exists()
        assert json.loads((directory / OUTPUT_FILE_NAME).read_bytes()) == item
        if expected_meta:
            assert (
                json.loads((directory / META_FILE_NAME).read_bytes()) == expected_meta
            )
        else:
            assert not (directory / META_FILE_NAME).exists()

    Fixture.save(base_dir, inputs=[book_list_html_response], item=item)
    _assert_fixture_files(base_dir / "test-1")
    Fixture.save(
        base_dir, inputs=[book_list_html_response], item=item, fixture_name="custom"
    )
    _assert_fixture_files(base_dir / "custom")
    Fixture.save(base_dir, inputs=[book_list_html_response], item=item, meta=meta)
    _assert_fixture_files(base_dir / "test-2", expected_meta=meta)


class MyItemPage(WebPage):
    async def to_item(self) -> dict:  # noqa: D102
        return {"foo": "bar"}


def test_pytest_plugin_pass(pytester, book_list_html_response) -> None:
    item = {"foo": "bar"}
    base_dir = pytester.path / "fixtures" / get_fq_class_name(MyItemPage)
    Fixture.save(base_dir, inputs=[book_list_html_response], item=item)
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_pytest_plugin_fail(pytester, book_list_html_response) -> None:
    item = {"foo": "wrong"}
    base_dir = pytester.path / "fixtures" / get_fq_class_name(MyItemPage)
    Fixture.save(base_dir, inputs=[book_list_html_response], item=item)
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)


@attrs.define(kw_only=True)
class MetadataLocalTime(Metadata):
    dateDownloadedLocal: Optional[str] = None


def _get_product_item(date: datetime.datetime) -> Product:
    if date.tzinfo is None:
        # convert to the aware object so that date_local_str always includes the offset
        date = date.astimezone()
    date_str = date.astimezone(dateutil.tz.UTC).strftime("%Y-%M-%dT%H:%M:%SZ")
    date_local_str = date.strftime("%Y-%M-%dT%H:%M:%S%z")
    return Product(
        url="http://example.com",
        name="foo",
        metadata=MetadataLocalTime(
            dateDownloaded=date_str, dateDownloadedLocal=date_local_str  # type: ignore[call-arg]
        ),
    )


class DateItemPage(WebPage):
    async def to_item(self) -> Item:  # noqa: D102
        date = datetime.datetime.now().astimezone()
        return _get_product_item(date)


def _assert_frozen_item(
    frozen_time: datetime.datetime,
    pytester: pytest.Pytester,
    response: HttpResponse,
    *,
    outcomes: dict = None,
) -> None:
    # this makes an item with datetime fields corresponding to frozen_time
    item = ItemAdapter(_get_product_item(frozen_time)).asdict()
    # this marks the fixture to be run under frozen_time
    meta = {"frozen_time": frozen_time.strftime("%Y-%m-%d %H:%M:%S %z")}
    base_dir = pytester.path / "fixtures" / get_fq_class_name(DateItemPage)
    Fixture.save(base_dir, inputs=[response], item=item, meta=meta)
    # this runs the test, faking the time and the timezone from frozen_time,
    # the result should contain frozen_time in the datetime fields
    result = pytester.runpytest()
    if outcomes is None:
        outcomes = {"passed": 1}
    result.assert_outcomes(**outcomes)


@pytest.mark.xfail(not time_machine.HAVE_TZSET, reason="Works on Windows only in UTC")
def test_pytest_frozen_time_utc(pytester, book_list_html_response) -> None:
    frozen_time = datetime.datetime(2022, 3, 4, 20, 21, 22, tzinfo=dateutil.tz.UTC)
    _assert_frozen_item(frozen_time, pytester, book_list_html_response)


def test_pytest_frozen_time_naive(pytester, book_list_html_response) -> None:
    frozen_time = datetime.datetime(2022, 3, 4, 20, 21, 22)
    _assert_frozen_item(frozen_time, pytester, book_list_html_response)


@pytest.mark.skipif(not time_machine.HAVE_TZSET, reason="Not supported on Windows")
@pytest.mark.parametrize("offset", [-5, 0, 8])
def test_pytest_frozen_time_tz(pytester, book_list_html_response, offset) -> None:
    if sys.version_info >= (3, 9):
        from zoneinfo import ZoneInfo
    else:
        from backports.zoneinfo import ZoneInfo

    tzinfo = ZoneInfo(f"Etc/GMT{-offset:+d}")
    frozen_time = datetime.datetime(2022, 3, 4, 20, 21, 22, tzinfo=tzinfo)
    _assert_frozen_item(frozen_time, pytester, book_list_html_response)


@pytest.mark.skipif(time_machine.HAVE_TZSET, reason="Tests Windows-specific code")
def test_pytest_frozen_time_tz_windows_fail(pytester, book_list_html_response) -> None:
    frozen_time = datetime.datetime(
        2022, 3, 4, 20, 21, 22, tzinfo=dateutil.tz.tzoffset(None, -7.5)
    )
    _assert_frozen_item(
        frozen_time, pytester, book_list_html_response, outcomes={"failed": 1}
    )


@pytest.mark.skipif(time_machine.HAVE_TZSET, reason="Tests Windows-specific code")
def test_pytest_frozen_time_tz_windows_pass(pytester, book_list_html_response) -> None:
    frozen_time = datetime.datetime(
        2022, 3, 4, 20, 21, 22, tzinfo=dateutil.tz.tzlocal()
    )
    _assert_frozen_item(frozen_time, pytester, book_list_html_response)
