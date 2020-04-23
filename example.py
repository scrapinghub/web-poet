import urllib.request

from core_po.objects import WebPageObject
from core_po.responses import HTMLResponse


class BookLinksPageObject(WebPageObject):

    @property
    def links(self):
        return self.css('.image_container a::attr(href)').getall()

    def serialize(self) -> dict:
        return {
            'links': self.links,
        }

response = urllib.request.urlopen('http://books.toscrape.com')
html_response = HTMLResponse(response.url, response.read().decode('utf-8'))
page_object = BookLinksPageObject(html_response)

print(page_object.serialize())
