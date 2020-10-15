import pytest

import redpatch as rp

@pytest.fixture
def si(): # a sample sub image
    fs = rp.FilterSettings()
    fs.read("tests/known_coords_sizes/cartoon_filter.yaml")
    return rp.get_sub_images(
        "tests/known_coords_sizes/centered_leaf.jpg",
        file_settings=fs,
        dest_folder="",
        min_lesion_area=40,
        max_lc_ratio=2,
        min_lc_size=2,
        lc_prop_across_parent=0.1
    )[0]

def test_healthy_obj_props(si):
    assert len(si.healthy_obj_props) == 6
    assert si.healthy_obj_props[0].area == 194531
    assert si.healthy_obj_props[0].size == "NA"

def test_lesion_area_props(si):
    assert len(si.lesion_area_props) == 1
    assert si.lesion_area_props[0].area == 33792

def test_lesion_centre_props(si):
    big_centres = [i for i in si.lesion_centre_props if i.area > 300]
    assert len(big_centres) == 2
    assert big_centres[0].area == 363
    assert big_centres[1].area == 1262
    assert big_centres[0].size == "NA"
    assert big_centres[1].size == "NA"
