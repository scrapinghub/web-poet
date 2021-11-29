import sys
from pathlib import Path

import pytest
from url_matcher import Patterns

from po_lib import POTopLevel1, POTopLevel2, POTopLevelOverriden1, POTopLevelOverriden2
from po_lib.a_module import POModule
from po_lib.nested_package import PONestedPkg
from po_lib.nested_package.a_nested_module import PONestedModule, PONestedModuleOverridenSecondary
from web_poet.meta import find_page_object_overrides


POS = {POTopLevel1, POTopLevel2, POModule, PONestedPkg, PONestedModule}


@pytest.fixture(autouse=True)
def run_before_and_after_tests(tmpdir):
    """Fixture to execute asserts before and after a test is run in this module"""

    # Ensuring po_lib is in the packages path
    tests_path = str(Path(__file__).absolute().parent)
    sys.path.append(tests_path)

    yield  # this is where the testing happens

    # Cleaning up path
    del sys.path[-1]


def test_list_page_objects_from_pkg():
    """Tests that metadata is extracted properly from the po_lib package"""
    pos = find_page_object_overrides("po_lib")
    assert pos.keys() == POS

    for po, spec in pos.items():
        assert spec.overrides == po.expected_overrides, po
        assert spec.patterns == po.expected_patterns, po


def test_list_page_objects_from_module():
    pos = find_page_object_overrides("po_lib.a_module")
    assert len(pos) == 1
    spec = pos[POModule]
    assert spec.patterns == POModule.expected_patterns
    assert spec.overrides == POModule.expected_overrides


def test_list_page_objects_from_empty_module():
    pos = find_page_object_overrides("po_lib.an_empty_module")
    assert len(pos) == 0


def test_list_page_objects_from_empty_pkg():
    pos = find_page_object_overrides("po_lib.an_empty_package")
    assert len(pos) == 0


def test_list_page_objects_from_unknown_module():
    with pytest.raises(ImportError):
        find_page_object_overrides("po_lib.unknown_module")


def test_list_page_objects_from_namespace():
    pos = find_page_object_overrides("po_lib", namespace="secondary")
    assert len(pos) == 2

    potop2 = pos[POTopLevel2]
    assert potop2.patterns == Patterns(["example.org"])
    assert potop2.overrides == POTopLevelOverriden2

    pones = pos[PONestedModule]
    assert pones.patterns == Patterns(["example.com"])
    assert pones.overrides == PONestedModuleOverridenSecondary


def test_list_page_objects_from_empty_namespace():
    assert find_page_object_overrides("po_lib", namespace="foo") == {}
