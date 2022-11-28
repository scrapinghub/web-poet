from web_poet import field, handle_urls, WebPage

from ..items import Book


@handle_urls(
    "books.toscrape.com/catalogue/*/index.html",
    exclude="*/category/*",
)
class BookPage(WebPage[Book]):

    @field
    async def title(self):
        return self.css("h1::text").get()


from attrs import define

from web_poet import Returns
from web_poet import HttpClient, Returns
from web_poet import HttpClient, PageParams, Returns

from ..items import CategorizedBook


@handle_urls(
    "books.toscrape.com/catalogue/*/index.html",
    exclude="*/category/*",
    priority=1000,
)
@define
class CategorizedBookPage(BookPage, Returns[CategorizedBook]):
    http: HttpClient
    page_params: PageParams
    _books_per_page = 20

    @field
    async def category(self):
        return self.css(".breadcrumb a::text").getall()[-1]

    @field
    async def category_rank(self):
        category_rank = self.page_params.get("category_rank")
        if category_rank is not None:
            return category_rank
        response, book_url, page = self.response, self.url, 0
        category_page_url = self.css(".breadcrumb a::attr(href)").getall()[-1]
        while category_page_url:
            category_page_url = response.urljoin(category_page_url)
            response = await self.http.get(category_page_url)
            urls = response.css("h3 a::attr(href)").getall()
            for position, url in enumerate(urls, start=1):
                url = str(response.urljoin(url))
                if url == book_url:
                    return page * self._books_per_page + position
            category_page_url = response.css(".next a::attr(href)").get()
            if not category_page_url:
                return None
            page += 1
