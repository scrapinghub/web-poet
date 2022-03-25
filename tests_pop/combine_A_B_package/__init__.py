"""This POP simply wants to repackage POP "A" and "B" into one unifying package."""

from web_poet import PageObjectRegistry

from . import base_A_package
from . import base_B_package

combined = {**base_A_package.REGISTRY, **base_B_package.REGISTRY}
REGISTRY = PageObjectRegistry(combined)
