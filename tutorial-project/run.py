from web_poet.example import get_item

item = get_item(
    "http://books.toscrape.com/catalogue/the-exiled_247/index.html",
    page_modules=["tutorial.pages"],
    page_params={"category_rank": 24},
)
print(item)
