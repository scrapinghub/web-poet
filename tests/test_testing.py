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

from web_poet import HttpClient, HttpRequest, HttpResponse, WebPage, field
from web_poet.exceptions import HttpResponseError
from web_poet.page_inputs.client import _SavedResponseData
from web_poet.testing import Fixture
from web_poet.testing.__main__ import main as cli_main
from web_poet.testing.fixture import INPUT_DIR_NAME, META_FILE_NAME, OUTPUT_FILE_NAME
from web_poet.utils import get_fq_class_name

N_TESTS = len(attrs.fields(Product)) + 2


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
        assert (input_dir / "HttpResponse-info.json").exists()
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
    async def to_item(self) -> dict:
        return {"foo": "bar"}


class MyItemPage2(WebPage):
    async def to_item(self) -> dict:
        return {"foo": None}


def _save_fixture(pytester, page_cls, page_inputs, expected):
    base_dir = pytester.path / "fixtures" / get_fq_class_name(page_cls)
    return Fixture.save(base_dir, inputs=page_inputs, item=expected)


def test_pytest_plugin_pass(pytester, book_list_html_response) -> None:
    _save_fixture(
        pytester,
        page_cls=MyItemPage,
        page_inputs=[book_list_html_response],
        expected={"foo": "bar"},
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=3)


def test_pytest_plugin_bad_field_value(pytester, book_list_html_response) -> None:
    _save_fixture(
        pytester,
        page_cls=MyItemPage,
        page_inputs=[book_list_html_response],
        expected={"foo": "not bar"},
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1, passed=2)
    result.stdout.fnmatch_lines("item.foo is not correct*")


def test_pytest_plugin_bad_field_value_None(pytester, book_list_html_response) -> None:
    _save_fixture(
        pytester,
        page_cls=MyItemPage2,
        page_inputs=[book_list_html_response],
        expected={"foo": "bar"},
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1, passed=2)
    result.stdout.fnmatch_lines("item.foo is not correct*")
    result.stdout.fnmatch_lines("Expected: 'bar', got: None*")


def test_pytest_plugin_missing_field(pytester, book_list_html_response) -> None:
    _save_fixture(
        pytester,
        page_cls=MyItemPage,
        page_inputs=[book_list_html_response],
        expected={"foo": "bar", "foo2": "bar2"},
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1, passed=3)
    result.stdout.fnmatch_lines("item.foo2 is missing*")


def test_pytest_plugin_extra_field(pytester, book_list_html_response) -> None:
    _save_fixture(
        pytester,
        page_cls=MyItemPage,
        page_inputs=[book_list_html_response],
        expected={"foo2": "bar2"},
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=2, passed=1)
    result.stdout.fnmatch_lines("item.foo2 is missing*")
    result.stdout.fnmatch_lines("*unexpected fields*")
    result.stdout.fnmatch_lines("*foo = 'bar'*")


class FieldExceptionPage(WebPage):
    @field
    def foo(self):
        return "foo"

    @field
    def bar(self):
        raise Exception


def test_pytest_plugin_field_exception(pytester, book_list_html_response) -> None:
    _save_fixture(
        pytester,
        page_cls=FieldExceptionPage,
        page_inputs=[book_list_html_response],
        expected={"foo": "foo", "bar": "bar"},
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1, skipped=3)
    result.stdout.fnmatch_lines("*FAILED*TO_ITEM_DOESNT_RAISE*")


def test_pytest_plugin_compare_item(pytester, book_list_html_response) -> None:
    _save_fixture(
        pytester,
        page_cls=MyItemPage,
        page_inputs=[book_list_html_response],
        expected={"foo": "bar"},
    )
    result = pytester.runpytest("--web-poet-test-per-item")
    result.assert_outcomes(passed=1)


def test_pytest_plugin_compare_item_fail(pytester, book_list_html_response) -> None:
    _save_fixture(
        pytester,
        page_cls=MyItemPage,
        page_inputs=[book_list_html_response],
        expected={"foo": "not bar"},
    )
    result = pytester.runpytest("--web-poet-test-per-item")
    result.assert_outcomes(passed=0, failed=1)

    result.stdout.fnmatch_lines("*{'foo': 'bar'} != {'foo': 'not bar'}*")
    result.stdout.fnmatch_lines("*The output doesn't match*")


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
    async def to_item(self) -> Item:
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
        outcomes = {"passed": N_TESTS}
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
        2022, 3, 4, 20, 21, 22, tzinfo=dateutil.tz.tzoffset(None, -7.5 * 3600)
    )
    _assert_frozen_item(
        frozen_time,
        pytester,
        book_list_html_response,
        outcomes={"failed": 1, "passed": N_TESTS - 1},
    )


@pytest.mark.skipif(time_machine.HAVE_TZSET, reason="Tests Windows-specific code")
def test_pytest_frozen_time_tz_windows_pass(pytester, book_list_html_response) -> None:
    frozen_time = datetime.datetime(
        2022, 3, 4, 20, 21, 22, tzinfo=dateutil.tz.tzlocal()
    )
    _assert_frozen_item(frozen_time, pytester, book_list_html_response)


@attrs.define
class ClientPage(WebPage):
    client: HttpClient

    async def to_item(self) -> dict:
        resp1 = await self.client.get("http://books.toscrape.com/1.html")
        resp2 = await self.client.post("http://books.toscrape.com/2.html", body=b"post")
        return {"foo": "bar", "additional": [resp1.body.decode(), resp2.body.decode()]}


def test_httpclient(pytester, book_list_html_response) -> None:
    url1 = "http://books.toscrape.com/1.html"
    request1 = HttpRequest(url1)
    response1 = HttpResponse(url=url1, body=b"body1", encoding="utf-8")
    url2 = "http://books.toscrape.com/2.html"
    request2 = HttpRequest(url2, method="POST", body=b"post")
    response2 = HttpResponse(url=url2, body=b"body2", encoding="utf-8")
    responses = [
        _SavedResponseData(request1, response1),
        _SavedResponseData(request2, response2),
    ]
    client = HttpClient(responses=responses)

    base_dir = pytester.path / "fixtures" / get_fq_class_name(ClientPage)
    item = {
        "foo": "bar",
        "additional": ["body1", "body2"],
    }
    Fixture.save(base_dir, inputs=[book_list_html_response, client], item=item)
    input_dir = base_dir / "test-1" / INPUT_DIR_NAME
    assert (input_dir / "HttpResponse-body.html").read_bytes() == bytes(
        book_list_html_response.body
    )
    assert (input_dir / "HttpClient-0-HttpRequest.info.json").exists()
    assert (input_dir / "HttpClient-0-HttpResponse.info.json").exists()
    assert (input_dir / "HttpClient-0-HttpResponse.body.html").read_bytes() == b"body1"
    assert (input_dir / "HttpClient-1-HttpResponse.body.html").read_bytes() == b"body2"
    result = pytester.runpytest()
    result.assert_outcomes(passed=4)


def test_httpclient_no_response(pytester, book_list_html_response) -> None:
    url = "http://books.toscrape.com/1.html"
    request = HttpRequest(url)
    response = HttpResponse(url=url, body=b"body1", encoding="utf-8")
    responses = [
        _SavedResponseData(request, response),
    ]
    client = HttpClient(responses=responses)

    item = {
        "foo": "bar",
        "additional": ["body1", "body2"],
    }
    _save_fixture(
        pytester,
        page_cls=ClientPage,
        page_inputs=[book_list_html_response, client],
        expected=item,
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1, skipped=3)


@attrs.define
class ClientExceptionPage(WebPage):
    client: HttpClient

    async def to_item(self) -> dict:
        msg = ""
        try:
            await self.client.get("http://books.toscrape.com/1.html")
        except HttpResponseError as ex:
            msg = ex.args[0]
        return {"foo": "bar", "exception": msg}


def test_httpclient_exception(pytester, book_list_html_response) -> None:
    url = "http://books.toscrape.com/1.html"
    request = HttpRequest(url)
    response = HttpResponse(url=url, body=b"body1", status=404, encoding="utf-8")
    responses = [
        _SavedResponseData(request, response),
    ]
    client = HttpClient(responses=responses)

    item = {
        "foo": "bar",
        "exception": "404 NOT_FOUND response for http://books.toscrape.com/1.html",
    }
    _save_fixture(
        pytester,
        page_cls=ClientExceptionPage,
        page_inputs=[book_list_html_response, client],
        expected=item,
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=4)


class MyItemPage3(WebPage):
    async def to_item(self) -> dict:  # noqa: D102
        return {"foo": "bar", "egg": "spam", "hello": "world"}


def test_cli_rerun(pytester, book_list_html_response, capsys) -> None:
    fixture = _save_fixture(
        pytester,
        page_cls=MyItemPage3,
        page_inputs=[book_list_html_response],
        expected={"foo": "bar2", "egg": "spam", "hello": "world"},
    )
    cli_main(["rerun", str(fixture.path)])
    captured = capsys.readouterr()
    assert not captured.err
    assert json.loads(captured.out) == {"foo": "bar", "egg": "spam", "hello": "world"}


def test_cli_rerun_fields(pytester, book_list_html_response, capsys) -> None:
    fixture = _save_fixture(
        pytester,
        page_cls=MyItemPage3,
        page_inputs=[book_list_html_response],
        expected={"foo": "bar2", "egg": "spam", "hello": "world"},
    )
    cli_main(["rerun", str(fixture.path), "--fields=foo,egg"])
    captured = capsys.readouterr()
    assert not captured.err
    assert json.loads(captured.out) == {"foo": "bar", "egg": "spam"}


def test_cli_rerun_fields_unknown_names(
    pytester, book_list_html_response, capsys
) -> None:
    fixture = _save_fixture(
        pytester,
        page_cls=MyItemPage3,
        page_inputs=[book_list_html_response],
        expected={"foo": "bar2", "egg": "spam", "hello": "world"},
    )
    cli_main(["rerun", str(fixture.path), "--fields=foo,egg2"])
    captured = capsys.readouterr()
    assert (
        "Unknown field names: ['egg2']. Allowed names are: ['egg', 'foo', 'hello']"
        in captured.err
    )
    assert json.loads(captured.out) == {"foo": "bar"}
