import pytest
import redpatch as rp
import numpy as np

'''mock region properties object'''

class RP:
    def __init__(self, length=1, width=1, label=1, bbox=(0,0, 50,50), centroid = (25,25), image = None):

        self.major_axis_length = length
        self.minor_axis_length = width
        self.area = width * length
        self.label = label
        self.bbox = bbox
        self.centroid = centroid
        self.image = image
        self.coords = np.asarray([(i,j) for i in range(bbox[0], bbox[2]) for j in range(bbox[1],bbox[3])])



@pytest.fixture
def sample_parent_image():
    return np.array(
        [
            [False, False, False, False, False, False, False, False, False, False],
            [False, False, True, True, True, True, True, True, False, False],
            [False, False, True, True, True, True, True, True, False, False],
            [False, False, True, True, True, True, True, True, False, False],
            [False, False, True, True, True, True, True, True, False, False],
            [False, False, True, True, True, True, True, True, False, False],
            [False, False, True, True, True, True, True, True, False, False],
            [False, False, False, False, False, False, False, False, False, False]
        ],
        np.bool
    )

@pytest.fixture
def sample_lesion_region():
    return RP(length = 6 , width = 6, label="lesion", bbox=(0,3, 6,9), centroid = (3,6))

@pytest.fixture
def sample_parent_region(sample_parent_image):
    return RP(length=8, width=10, label="parent",bbox=(100,100, 110,108), centroid=(105,109), image=sample_parent_image)

@pytest.fixture
def lc(sample_lesion_region, sample_parent_region):
    return rp.LesionCentre(rprop = sample_lesion_region, parent_rprop=sample_parent_region, scale=1, pixel_length=1, max_ratio=1.5, minimum_size=4,prop_across_parent=40)

def test_lesion_centre(lc):
    assert lc.major_axis_length == 6
    assert lc.minor_axis_length == 6

def test_calc_offset_to_parent(lc):
    assert lc.offset_to_parent[0] == 100
    assert lc.offset_to_parent[1] == 100

def test_corrected_centroids(lc):
    assert lc.corrected_centroid[0] == 103
    assert lc.corrected_centroid[1] == 106

def test_correct_bbox(lc):
    assert lc.corrected_bbox[0] == 100
    assert lc.corrected_bbox[1] == 103
    assert lc.corrected_bbox[2] == 116
    assert lc.corrected_bbox[3] == 117

def test_prop_across_parent(lc):
    assert lc.prop_across_parent == 0.2

def test_passes(lc):
    assert lc.passed == False
