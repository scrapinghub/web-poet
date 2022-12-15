import json
from pathlib import Path

from web_poet import WebPage
from web_poet.testing import INPUT_DIR_NAME, OUTPUT_FILE_NAME, save_fixture
from web_poet.utils import get_fq_class_name


def test_save_fixture(book_list_html_response, tmp_path) -> None:
    base_dir = tmp_path / "fixtures" / "some.po"
    item = {"foo": "bar"}

    def _assert_fixture_files(directory: Path) -> None:
        input_dir = directory / INPUT_DIR_NAME
        assert (input_dir / "HttpResponse-body.html").exists()
        assert (input_dir / "HttpResponse-body.html").read_bytes() == bytes(
            book_list_html_response.body
        )
        assert (input_dir / "HttpResponse-other.json").exists()
        assert (directory / OUTPUT_FILE_NAME).exists()
        assert json.loads((directory / OUTPUT_FILE_NAME).read_bytes()) == item

    save_fixture(base_dir, [book_list_html_response], item)
    _assert_fixture_files(base_dir / "test-1")
    save_fixture(base_dir, [book_list_html_response], item, fixture_name="custom")
    _assert_fixture_files(base_dir / "custom")
    save_fixture(base_dir, [book_list_html_response], item)
    _assert_fixture_files(base_dir / "test-2")


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
