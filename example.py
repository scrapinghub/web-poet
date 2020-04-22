import http
import urllib.request

from core_po.builder import build
from core_po.objects import WebPageObject
from core_po.providers import PageObjectProvider, provides
from core_po.responses import HTMLResponse


@provides(HTMLResponse)
class HTMLResponseProvider(PageObjectProvider):

    def __init__(self, response: http.client.HTTPResponse):
        self.response = response

    def __call__(self):
        return HTMLResponse(
            url=self.response.url,
            content=self.response.read().decode('utf-8')
        )


class BookLinksPageObject(WebPageObject):

    @property
    def urls(self):
        return self.css('.image_container a::attr(href)').getall()

    def serialize(self) -> dict:
        return {
            'urls': self.urls,
        }


response = urllib.request.urlopen('http://books.toscrape.com')
page_object = build(BookLinksPageObject, response)
print(page_object.serialize())
