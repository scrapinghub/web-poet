import asyncio

from web_poet import consume_modules
from web_poet.framework import Framework

from tutorial.items import CategorizedBook

consume_modules("tutorial.pages")

framework = Framework()
item = asyncio.run(
    framework.get_item(
        "http://books.toscrape.com/catalogue/the-exiled_247/index.html",
        CategorizedBook,
        page_params={"category_rank": 24},
    )
)
print(item)
