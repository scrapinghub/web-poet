import json
import os
from pathlib import Path
from typing import Any, Iterable, Union

from itemadapter import ItemAdapter

from web_poet.serialization import SerializedDataFileStorage, serialize

INPUT_DIR_NAME = "inputs"
OUTPUT_FILE_NAME = "output.json"


def save_fixture(
    base_directory: Union[str, os.PathLike], inputs: Iterable[Any], item: Any
) -> None:
    inputs_dir = Path(base_directory, INPUT_DIR_NAME)
    inputs_dir.mkdir(parents=True)
    serialized_inputs = serialize(inputs)
    storage = SerializedDataFileStorage(inputs_dir)
    storage.write(serialized_inputs)
    with Path(base_directory, OUTPUT_FILE_NAME).open("w") as f:
        json.dump(ItemAdapter(item).asdict(), f)
