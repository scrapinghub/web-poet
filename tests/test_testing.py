from __future__ import annotations

import json
from collections import deque
from typing import TYPE_CHECKING, Any

import pytest
from itemadapter import ItemAdapter
from itemadapter.adapter import DictAdapter

from web_poet import HttpResponse, WebPage
from web_poet.testing import Fixture
from web_poet.testing.__main__ import main as cli_main
from web_poet.testing.fixture import INPUT_DIR_NAME, META_FILE_NAME, OUTPUT_FILE_NAME
from web_poet.utils import get_fq_class_name

if TYPE_CHECKING:
    from pathlib import Path


def test_save_fixture(book_list_html_response, tmp_path) -> None:
    base_dir = tmp_path / "fixtures" / "some.po"
    item = {"foo": "bar"}
    meta = {"foo": "bar", "frozen_time": "2022-01-01"}

    def _assert_fixture_files(
        directory: Path, expected_meta: dict | None = None
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


def test_save_fixture_unicode_item(book_list_html_response, tmp_path) -> None:
    base_dir = tmp_path / "fixtures" / "some.po"
    item = {"foo": "✓bar£"}

    Fixture.save(base_dir, inputs=[book_list_html_response], item=item)
    fixture = Fixture(base_dir / "test-1")
    assert json.loads(fixture.output_path.read_bytes()) == item
    assert fixture.get_expected_output() == item


def test_save_fixture_unicode_exception(book_list_html_response, tmp_path) -> None:
    base_dir = tmp_path / "fixtures" / "some.po"
    exc = ValueError("✓bar£")

    Fixture.save(base_dir, inputs=[book_list_html_response], exception=exc)
    fixture = Fixture(base_dir / "test-1")
    exc_data = json.loads(fixture.exception_path.read_bytes())
    assert exc_data == {"import_path": "builtins.ValueError", "msg": "✓bar£"}
    expected_exc = fixture.get_expected_exception()
    assert type(expected_exc) is ValueError
    assert expected_exc.args == ("✓bar£",)


def test_save_fixture_unicode_meta(book_list_html_response, tmp_path) -> None:
    base_dir = tmp_path / "fixtures" / "some.po"
    item = {"foo": "bar"}
    meta = {"foo": "✓bar£", "frozen_time": "2022-01-01"}

    Fixture.save(base_dir, inputs=[book_list_html_response], item=item, meta=meta)
    fixture = Fixture(base_dir / "test-1")
    meta_data = json.loads(fixture.meta_path.read_bytes())
    assert meta_data == meta
    assert fixture.get_meta() == meta


class MyItemPage(WebPage):
    async def to_item(self) -> dict:
        return {"foo": "bar"}


class CapitalizingDictAdapter(DictAdapter):
    def __getitem__(self, field_name: str) -> Any:
        item = super().__getitem__(field_name)
        if isinstance(item, str):
            return item.capitalize()
        return item


class CustomItemAdapter(ItemAdapter):
    ADAPTER_CLASSES = deque([CapitalizingDictAdapter])


def test_fixture_adapter(book_list_html_response, tmp_path) -> None:
    item = {"foo": "bar"}
    meta = {"adapter": CustomItemAdapter}
    base_dir = tmp_path / "fixtures" / get_fq_class_name(MyItemPage)

    fixture = Fixture.save(
        base_dir, inputs=[book_list_html_response], item=item, meta=meta
    )
    saved_output = json.loads(fixture.output_path.read_bytes())
    assert saved_output["foo"] == "Bar"

    loaded_fixture = Fixture(base_dir / "test-1")
    loaded_output = loaded_fixture.get_output()
    assert loaded_output["foo"] == "Bar"
    actual_output = loaded_fixture.get_expected_output()
    assert actual_output["foo"] == "Bar"


def test_fixture_asserts(book_list_html_response, tmp_path) -> None:
    item = {"foo": "bar"}
    base_dir = tmp_path / "fixtures" / get_fq_class_name(MyItemPage)
    Fixture.save(base_dir, inputs=[book_list_html_response], item=item)
    loaded_fixture = Fixture(base_dir / "test-1")
    loaded_fixture.assert_full_item_correct()
    loaded_fixture.assert_field_correct("foo")
    loaded_fixture.assert_no_extra_fields()
    loaded_fixture.assert_no_toitem_exceptions()
    with pytest.raises(KeyError):
        loaded_fixture.assert_field_correct("bar")


def test_fixture_asserts_standalone(book_list_html_response, tmp_path) -> None:
    item = {"foo": "bar"}
    type_name = get_fq_class_name(MyItemPage)
    base_dir = tmp_path / "fixtures" / "unrelated"
    Fixture.save(base_dir, inputs=[book_list_html_response], item=item)
    loaded_fixture = Fixture(base_dir / "test-1")
    loaded_fixture.assert_full_item_correct(type_name=type_name)
    loaded_fixture.assert_field_correct("foo", type_name=type_name)
    loaded_fixture.assert_no_extra_fields(type_name=type_name)
    loaded_fixture.assert_no_toitem_exceptions(type_name=type_name)
    with pytest.raises(KeyError):
        loaded_fixture.assert_field_correct("bar", type_name=type_name)


class MyItemPage3(WebPage):
    async def to_item(self) -> dict:
        return {"foo": "bar", "egg": "spam", "hello": "world"}


def test_cli_rerun(
    tmp_path: Path,
    book_list_html_response: HttpResponse,
    capsys: pytest.CaptureFixture[str],
) -> None:
    base_dir = tmp_path / "fixtures" / get_fq_class_name(MyItemPage3)
    fixture = Fixture.save(
        base_dir,
        inputs=[book_list_html_response],
        item={"foo": "bar2", "egg": "spam", "hello": "world"},
    )

    cli_main(["rerun", str(fixture.path)])
    captured = capsys.readouterr()
    assert not captured.err
    assert json.loads(captured.out) == {"foo": "bar", "egg": "spam", "hello": "world"}


def test_cli_rerun_fields(
    tmp_path: Path,
    book_list_html_response: HttpResponse,
    capsys: pytest.CaptureFixture[str],
) -> None:
    base_dir = tmp_path / "fixtures" / get_fq_class_name(MyItemPage3)
    fixture = Fixture.save(
        base_dir,
        inputs=[book_list_html_response],
        item={"foo": "bar2", "egg": "spam", "hello": "world"},
    )

    cli_main(["rerun", str(fixture.path), "--fields=foo,egg"])
    captured = capsys.readouterr()
    assert not captured.err
    assert json.loads(captured.out) == {"foo": "bar", "egg": "spam"}


def test_cli_rerun_fields_unknown_names(
    tmp_path: Path,
    book_list_html_response: HttpResponse,
    capsys: pytest.CaptureFixture[str],
) -> None:
    base_dir = tmp_path / "fixtures" / get_fq_class_name(MyItemPage3)
    fixture = Fixture.save(
        base_dir,
        inputs=[book_list_html_response],
        item={"foo": "bar2", "egg": "spam", "hello": "world"},
    )

    cli_main(["rerun", str(fixture.path), "--fields=foo,egg2"])
    captured = capsys.readouterr()
    assert (
        "Unknown field names: ['egg2']. Allowed names are: ['egg', 'foo', 'hello']"
        in captured.err
    )
    assert json.loads(captured.out) == {"foo": "bar"}


def test_cli_rerun_standalone_fixture(
    tmp_path: Path,
    book_list_html_response: HttpResponse,
    capsys: pytest.CaptureFixture[str],
) -> None:
    base_dir = tmp_path / "fixtures" / "unrelated"
    fixture = Fixture.save(
        base_dir,
        inputs=[book_list_html_response],
        item={"foo": "bar2", "egg": "spam", "hello": "world"},
    )

    cli_main(["rerun", str(fixture.path), "-p", get_fq_class_name(MyItemPage3)])
    captured = capsys.readouterr()
    assert not captured.err
    assert json.loads(captured.out) == {"foo": "bar", "egg": "spam", "hello": "world"}
