from attrs import define


@define
class Book:
    title: str


from typing import Optional


@define
class CategorizedBook(Book):
    category: str
    category_rank: Optional[int] = None
