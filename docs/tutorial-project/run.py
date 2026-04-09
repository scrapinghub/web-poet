import asyncio

from web_poet import consume_modules
from web_poet.framework import Poet

from tutorial.items import Book

consume_modules("tutorial.pages")

poet = Poet()
item = asyncio.run(
    poet.get_item("http://books.toscrape.com/catalogue/the-exiled_247/index.html", Book)
)
print(item)
