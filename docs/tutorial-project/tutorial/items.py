from attrs import define


@define(kw_only=True)
class Book:
    title: str


from typing import Optional


@define(kw_only=True)
class CategorizedBook(Book):
    category: str
    category_rank: Optional[int] = None
