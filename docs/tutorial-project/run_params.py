import asyncio

from web_poet import consume_modules
from web_poet.simple_framework import Poet

from tutorial.items import CategorizedBook

consume_modules("tutorial.pages")

poet = Poet()
item = asyncio.run(
    poet.get_item(
        "http://books.toscrape.com/catalogue/the-exiled_247/index.html",
        CategorizedBook,
        page_params={"category_rank": 24},
    )
)
print(item)
