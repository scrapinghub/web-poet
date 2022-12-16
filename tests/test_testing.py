import datetime
import json
from pathlib import Path
from typing import Optional

from web_poet import WebPage
from web_poet.testing import (
    INPUT_DIR_NAME,
    META_FILE_NAME,
    OUTPUT_FILE_NAME,
    save_fixture,
)
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

    save_fixture(base_dir, [book_list_html_response], item)
    _assert_fixture_files(base_dir / "test-1")
    save_fixture(base_dir, [book_list_html_response], item, fixture_name="custom")
    _assert_fixture_files(base_dir / "custom")
    save_fixture(base_dir, [book_list_html_response], item, meta=meta)
    _assert_fixture_files(base_dir / "test-2", expected_meta=meta)


class MyItemPage(WebPage):
    async def to_item(self) -> dict:  # noqa: D102
        return {"foo": "bar"}


def test_pytest_plugin_pass(pytester, book_list_html_response) -> None:
    item = {"foo": "bar"}
    base_dir = pytester.path / "fixtures" / get_fq_class_name(MyItemPage)
    save_fixture(base_dir, [book_list_html_response], item)
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_pytest_plugin_fail(pytester, book_list_html_response) -> None:
    item = {"foo": "wrong"}
    base_dir = pytester.path / "fixtures" / get_fq_class_name(MyItemPage)
    save_fixture(base_dir, [book_list_html_response], item)
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)


class DateItemPage(WebPage):
    async def to_item(self) -> dict:  # noqa: D102
        return {
            "foo": "bar",
            "scraped_on": datetime.datetime.now().isoformat(),
        }


def test_pytest_frozen_time(pytester, book_list_html_response) -> None:
    frozen_time = datetime.datetime(2022, 3, 4, 20, 21, 22)
    item = {"foo": "bar", "scraped_on": frozen_time.isoformat()}
    meta = {"frozen_time": frozen_time.strftime("%Y-%m-%d %H:%M:%S")}
    base_dir = pytester.path / "fixtures" / get_fq_class_name(DateItemPage)
    save_fixture(base_dir, [book_list_html_response], item, meta)
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
