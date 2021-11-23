import pytest

import greypatch as rp

@pytest.fixture
def si(): # a sample sub image
    fs = rp.FilterSettings()
    fs.read("tests/known_coords_sizes/within_cartoon_filter.yaml")
    return rp.get_sub_images(
        "tests/known_coords_sizes/blobs_within.jpg",
        file_settings=fs,
        dest_folder="",
        min_lesion_area=40
    )[0]

def test_healthy_obj_props(si):
    assert len(si.healthy_obj_props) == 6
    assert si.healthy_obj_props[0].area == 194531
    assert si.healthy_obj_props[0].size == "NA"

def test_outer_lesion_area_props(si):
    assert len(si.outer_lesion_area_props) == 2
    assert si.outer_lesion_area_props[0].area == 33792
    assert si.outer_lesion_area_props[0].area == 33792

def test_inner_lesion_area_props(si):
    assert len(si.outer_lesion_area_props) == 1
    assert si.outer_lesion_area_props[0].area == 33792

def test_inner_outer_match(si):
    assert si.matched_innerouter == [[0,1]]

