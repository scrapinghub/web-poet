from __future__ import annotations

from collections import deque
from typing import Deque

from itemadapter import ItemAdapter
from itemadapter.adapter import (
    AdapterInterface,
    AttrsAdapter,
    DataclassAdapter,
    DictAdapter,
    PydanticAdapter,
    ScrapyItemAdapter,
)


class WebPoetTestItemAdapter(ItemAdapter):
    """A default adapter implementation"""

    # In case the user changes ItemAdapter.ADAPTER_CLASSES it's copied here.
    ADAPTER_CLASSES: Deque[type[AdapterInterface]] = deque(
        [
            ScrapyItemAdapter,
            DictAdapter,
            DataclassAdapter,
            AttrsAdapter,
            PydanticAdapter,
        ]
    )
