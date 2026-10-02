from __future__ import annotations

import json
from typing import Any

import attrs

from web_poet import WebPage, cached_method, css, field, xpath


def _clean(value: str | None) -> str | None:
    """Collapse whitespace, mapping a blank value to ``None``."""
    return " ".join(value.split()) or None if value else None


def _clean_all(values: list[str]) -> list[str]:
    return [clean for value in values if (clean := _clean(value))]


@attrs.define(kw_only=True)
class Product:
    url: str
    name: str | None
    brand: str | None
    price: str | None
    regular_price: str | None
    rating: str | None
    review_count: str | None
    availability: str | None
    sku: str | None
    main_image: str | None
    images: list[str]
    features: list[str]
    breadcrumbs: list[str]


class ProductPage(WebPage[Product]):
    @field
    def url(self) -> str:
        return str(self.response.url)

    @field(out=[_clean])
    def name(self) -> str | None:
        return self.css("#productTitle::text").get()

    @field(out=[_clean])
    def brand(self) -> str | None:
        return self.css("#bylineInfo::text").get()

    @field(out=[_clean])
    def price(self) -> str | None:
        return self.css("span.a-price span.a-offscreen::text").get()

    @field(out=[_clean])
    def regular_price(self) -> str | None:
        return self.css("span.a-price.a-text-price span.a-offscreen::text").get()

    @field(out=[_clean])
    def rating(self) -> str | None:
        return self.css("#acrPopover::attr(title)").get()

    @field(out=[_clean])
    def review_count(self) -> str | None:
        return self.css("#acrCustomerReviewText::text").get()

    @field(out=[_clean])
    def availability(self) -> str | None:
        return self.xpath('//div[@id="availability"]//span/text()').get()

    @field(out=[_clean])
    def sku(self) -> str | None:
        return self.xpath('//input[@id="SKUX"]/@value').get()

    @field(out=[_clean])
    def main_image(self) -> str | None:
        return self.xpath('//img[@id="landingImage"]/@src').get()

    @field(out=[_clean_all])
    def images(self) -> list[str]:
        return self.css("#altImages img::attr(src)").getall()

    @field(out=[_clean_all])
    def features(self) -> list[str]:
        return self.css("#feature-bullets li span.a-list-item::text").getall()

    @field(out=[_clean_all])
    def breadcrumbs(self) -> list[str]:
        return self.css("#wayfinding-breadcrumbs_feature_div a::text").getall()


class DeclarativeProductPage(ProductPage, declarative_backend="frostwork"):
    """ProductPage with every selector declared instead of queried in a
    method."""

    name = field(css("#productTitle::text").get(), out=[_clean])
    brand = field(css("#bylineInfo::text").get(), out=[_clean])
    price = field(css("span.a-price span.a-offscreen::text").get(), out=[_clean])
    regular_price = field(
        css("span.a-price.a-text-price span.a-offscreen::text").get(), out=[_clean]
    )
    rating = field(css("#acrPopover::attr(title)").get(), out=[_clean])
    review_count = field(css("#acrCustomerReviewText::text").get(), out=[_clean])
    availability = field(
        xpath('//div[@id="availability"]//span/text()').get(), out=[_clean]
    )
    sku = field(xpath('//input[@id="SKUX"]/@value').get(), out=[_clean])
    main_image = field(xpath('//img[@id="landingImage"]/@src').get(), out=[_clean])
    images = field(css("#altImages img::attr(src)").getall(), out=[_clean_all])
    features = field(
        css("#feature-bullets li span.a-list-item::text").getall(), out=[_clean_all]
    )
    breadcrumbs = field(
        css("#wayfinding-breadcrumbs_feature_div a::text").getall(), out=[_clean_all]
    )


@attrs.define(kw_only=True)
class Review:
    author: str | None
    rating: str | None
    date: str | None
    text: str | None


@attrs.define(kw_only=True)
class ProductDetails:
    specifications: dict[str, str]
    reviews: list[Review]


class ProductDetailsPage(WebPage[ProductDetails]):
    """Extraction that walks nodes instead of reading a value out of a
    document-wide query, and so cannot be expressed as a single selector."""

    @field
    def specifications(self) -> dict[str, str]:
        specifications = {}
        for row in self.css("#prodDetails tr"):
            label = _clean(row.css("th::text").get())
            value = _clean(" ".join(row.css("td::text").getall()))
            if label and value:
                specifications[label] = value
        return specifications

    @field
    def reviews(self) -> list[Review]:
        return [
            Review(
                author=_clean(review.css("span.a-profile-name::text").get()),
                rating=_clean(
                    review.css('[data-hook="review-star-rating"] span::text').get()
                ),
                date=_clean(review.css('[data-hook="review-date"]::text').get()),
                text=_clean(
                    " ".join(review.css('[data-hook="reviewText"] ::text').getall())
                ),
            )
            for review in self.css('div[data-hook="review"]')
        ]


@attrs.define(kw_only=True)
class Article:
    url: str
    headline: str | None
    description: str | None
    image: str | None
    date_published: str | None
    sections: list[str]
    paragraphs: list[str]
    figures: list[str]


class ArticlePage(WebPage[Article]):
    @field
    def url(self) -> str:
        return str(self.response.url)

    @field(out=[_clean])
    def headline(self) -> str | None:
        return self.css("h1::text").get()

    @field(out=[_clean])
    def description(self) -> str | None:
        return self.css('meta[property="og:description"]::attr(content)').get()

    @field(out=[_clean])
    def image(self) -> str | None:
        return self.css('meta[property="og:image"]::attr(content)').get()

    @field(out=[_clean])
    def date_published(self) -> str | None:
        return self.xpath("//time/@datetime").get()

    @field(out=[_clean_all])
    def sections(self) -> list[str]:
        return self.css("article h2::text").getall()

    @field(out=[_clean_all])
    def paragraphs(self) -> list[str]:
        return self.css('article [data-component="text-block"] p::text').getall()

    @field(out=[_clean_all])
    def figures(self) -> list[str]:
        return self.css("article figure img::attr(src)").getall()


class DeclarativeArticlePage(ArticlePage, declarative_backend="frostwork"):
    """ArticlePage with every selector declared instead of queried in a
    method."""

    headline = field(css("h1::text").get(), out=[_clean])
    description = field(
        css('meta[property="og:description"]::attr(content)').get(), out=[_clean]
    )
    image = field(css('meta[property="og:image"]::attr(content)').get(), out=[_clean])
    date_published = field(xpath("//time/@datetime").get(), out=[_clean])
    sections = field(css("article h2::text").getall(), out=[_clean_all])
    paragraphs = field(
        css('article [data-component="text-block"] p::text').getall(), out=[_clean_all]
    )
    figures = field(css("article figure img::attr(src)").getall(), out=[_clean_all])


@attrs.define(kw_only=True)
class ArticleMetadata:
    headline: str | None
    description: str | None
    date_published: str | None
    date_modified: str | None
    author: str | None
    publisher: str | None
    image: str | None


class JsonLdArticlePage(WebPage[ArticleMetadata]):
    """Metadata read out of the JSON-LD of the page, parsing it once."""

    @cached_method
    def _metadata(self) -> dict[str, Any]:
        return json.loads(self.css('script[type="application/ld+json"]::text').get(""))

    @field
    def headline(self) -> str | None:
        return self._metadata().get("headline")

    @field
    def description(self) -> str | None:
        return self._metadata().get("description")

    @field
    def date_published(self) -> str | None:
        return self._metadata().get("datePublished")

    @field
    def date_modified(self) -> str | None:
        return self._metadata().get("dateModified")

    @field
    def author(self) -> str | None:
        return self._metadata()["author"][0]["name"]

    @field
    def publisher(self) -> str | None:
        return self._metadata()["publisher"]["name"]

    @field
    def image(self) -> str | None:
        return self._metadata()["image"]["url"]


class JmesPathArticlePage(WebPage[ArticleMetadata]):
    """The same metadata, read with one JMESPath query per field."""

    _JSON_LD = 'script[type="application/ld+json"]::text'

    def _jmespath(self, expression: str) -> Any:
        return self.css(self._JSON_LD).jmespath(expression).get()

    @field
    def headline(self) -> str | None:
        return self._jmespath("headline")

    @field
    def description(self) -> str | None:
        return self._jmespath("description")

    @field
    def date_published(self) -> str | None:
        return self._jmespath("datePublished")

    @field
    def date_modified(self) -> str | None:
        return self._jmespath("dateModified")

    @field
    def author(self) -> str | None:
        return self._jmespath("author[0].name")

    @field
    def publisher(self) -> str | None:
        return self._jmespath("publisher.name")

    @field
    def image(self) -> str | None:
        return self._jmespath("image.url")


@attrs.define(kw_only=True)
class JobPosting:
    url: str
    title: str | None
    company: str | None
    location: str | None
    posted: str | None
    applicants: str | None
    description: str | None
    criteria_labels: list[str]
    criteria_values: list[str]


class JobPostingPage(WebPage[JobPosting]):
    @field
    def url(self) -> str:
        return str(self.response.url)

    @field(out=[_clean])
    def title(self) -> str | None:
        return self.css("h1::text").get()

    @field(out=[_clean])
    def company(self) -> str | None:
        return self.css(".topcard__org-name-link::text").get()

    @field(out=[_clean])
    def location(self) -> str | None:
        return self.css(".topcard__flavor--bullet::text").get()

    @field(out=[_clean])
    def posted(self) -> str | None:
        return self.css(".posted-time-ago__text::text").get()

    @field(out=[_clean])
    def applicants(self) -> str | None:
        return self.css(".num-applicants__caption::text").get()

    @field(out=[_clean])
    def description(self) -> str | None:
        return " ".join(self.css(".show-more-less-html__markup ::text").getall())

    @field(out=[_clean_all])
    def criteria_labels(self) -> list[str]:
        return self.css(".description__job-criteria-subheader::text").getall()

    @field(out=[_clean_all])
    def criteria_values(self) -> list[str]:
        return self.xpath(
            '//span[contains(@class, "description__job-criteria-text")]/text()'
        ).getall()


@attrs.define(kw_only=True)
class Minimal:
    title: str | None
    heading: str | None
    link: str | None


class MinimalPage(WebPage[Minimal]):
    """A page object small enough for its numbers to be the cost of web-poet
    itself, rather than the cost of the document."""

    @field(out=[_clean])
    def title(self) -> str | None:
        return self.css("title::text").get()

    @field(out=[_clean])
    def heading(self) -> str | None:
        return self.css("h1::text").get()

    @field(out=[_clean])
    def link(self) -> str | None:
        return self.xpath("//a/@href").get()


class DeclarativeJobPostingPage(JobPostingPage, declarative_backend="frostwork"):
    """JobPostingPage with every selector declared instead of queried in a
    method."""

    title = field(css("h1::text").get(), out=[_clean])
    company = field(css(".topcard__org-name-link::text").get(), out=[_clean])
    location = field(css(".topcard__flavor--bullet::text").get(), out=[_clean])
    posted = field(css(".posted-time-ago__text::text").get(), out=[_clean])
    applicants = field(css(".num-applicants__caption::text").get(), out=[_clean])
    description = field(
        css(".show-more-less-html__markup ::text").getall(), out=[" ".join, _clean]
    )
    criteria_labels = field(
        css(".description__job-criteria-subheader::text").getall(), out=[_clean_all]
    )
    criteria_values = field(
        xpath(
            '//span[contains(@class, "description__job-criteria-text")]/text()'
        ).getall(),
        out=[_clean_all],
    )


class DeclarativeMinimalPage(MinimalPage, declarative_backend="frostwork"):
    """MinimalPage with every selector declared instead of queried in a
    method."""

    title = field(css("title::text").get(), out=[_clean])
    heading = field(css("h1::text").get(), out=[_clean])
    link = field(xpath("//a/@href").get(), out=[_clean])
