import asyncio

from web_poet import consume_modules
from web_poet.simple_framework import get_item

from tutorial.items import Book
from tutorial.items import CategorizedBook

consume_modules("tutorial.pages")

item = asyncio.run(
    get_item("http://books.toscrape.com/catalogue/the-exiled_247/index.html", Book)
)
item = asyncio.run(
    get_item(
        "http://books.toscrape.com/catalogue/the-exiled_247/index.html",
        CategorizedBook,
        page_params={"category_rank": 24},
    )
)
print(item)
