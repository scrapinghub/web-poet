import json
import os
from pathlib import Path
from typing import Any, Iterable, Optional, Union

from itemadapter import ItemAdapter

from web_poet.serialization import SerializedDataFileStorage, serialize

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
