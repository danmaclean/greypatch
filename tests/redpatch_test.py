import pytest
import numpy as np
import math
import redpatch as rp

'''mock region properties object'''
class RP:

    def __init__(self, length=1, width=1, label=1):

        self.major_axis_length = length
        self.minor_axis_length = width
        self.area = width * length
        self.label = label


@pytest.fixture
def sample_hsv(): #white cross grey ground
  return np.array(
        [
            [[0.0, 0.0, 0.5], [0.0, 0.0, 1.0], [0.0, 0.0, 0.5] ],
            [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0] ],
            [[0.0, 0.0, 0.5], [0.0, 0.0, 1.0], [0.0, 0.0, 0.5] ]
        ],
        np.float64
    )

@pytest.fixture
def sample_hsv2(): #black cross white ground
    return np.array(
        [
            [[0.0, 0.0, 1.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0 ]],
            [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
            [[0.0, 0.0, 1.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
        ],
        np.float64
    )

@pytest.fixture
def sample_threshold_hsv(): #white cross. black ground
    return np.array(
        [
            [[0., 0., 0.], [0.0, 0.0, 1.0], [0., 0., 0.] ],
            [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0] ],
            [[0., 0., 0.], [0.0, 0.0, 1.0], [0., 0., 0.] ]
        ],
        np.float64
    )

@pytest.fixture
def sample_threshold_bool():
    return np.array(
        [
            [False, True, False],
            [True, True, True],
            [False, True, False]
        ]
    )
@pytest.fixture
def sample_rgb():
    return np.array( #white cross grey ground
        [
            [[ 127, 127, 127], [255,255,255], [ 127, 127, 127]],
            [[ 255, 255,255], [255,255,255], [255,255,255]],
            [[ 127, 127, 127], [ 255,255,255], [ 127, 127, 127]]
        ],
        np.int
    )

@pytest.fixture
def mask_to_label():
    return np.array(
        [
            [False, False, False, False, False, False, False, False],
            [False, True, True, False, False, True, True, False],
            [False, True, True, False, False, True, True, False],
            [False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False],
            [False, True, True, False, False, True, True, False],
            [False, True, True, False, False, True, True, False],
            [False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False]
        ]
    )

def test_builtin_values():
    assert rp.LEAF_AREA_HUE == tuple([i / 255 for i in (0, 255)])
    assert rp.LEAF_AREA_SAT == tuple([i / 255 for i in (50, 255)])
    assert rp.LEAF_AREA_VAL == tuple([i / 255 for i in (40, 255)])

    assert rp.HEALTHY_HUE == tuple([i / 255 for i in (40, 255)])
    assert rp.HEALTHY_SAT == tuple([i / 255 for i in (50, 255)])
    assert rp.HEALTHY_VAL == tuple([i / 255 for i in (0, 255)])

    assert rp.HEALTHY_RED == (4, 155)
    assert rp.HEALTHY_GREEN == (120, 175)
    assert rp.HEALTHY_BLUE == (0, 255)

    assert rp.LESION_HUE == tuple([i / 255 for i in (0, 41)])
    assert rp.LESION_SAT == tuple([i / 255 for i in (38, 255)])
    assert rp.LESION_VAL == tuple([i / 255 for i in (111, 255)])

#    assert rp.LESION_CENTRE_HUE == tuple([i / 255 for i in (0, 41)])
#    assert rp.LESION_CENTRE_SAT == tuple([i / 255 for i in (38, 255)])
#    assert rp.LESION_CENTRE_VAL == tuple([i / 255 for i in (111, 255)])

    assert rp.SCALE_CARD_HUE == (0.61, 1.0)
    assert rp.SCALE_CARD_SAT == (0.17, 1.0)
    assert rp.SCALE_CARD_VAL == (0.25, 0.75)

def test_threshold_hsv_img(sample_hsv, sample_threshold_bool):
    thr = rp.threshold_hsv_img(sample_hsv, h = (0., 0.5), s = (0., 0.5), v = (0.6, 1.0) )
    assert np.array_equal(thr, sample_threshold_bool)

    assert thr.dtype == 'bool', "should return dtype bool"
    assert thr.shape == (sample_hsv.shape[0], sample_hsv.shape[1]), "should return 2d array of same shape as first two dimensions of input array"

def test_hsv_to_rgb255(sample_hsv, sample_rgb):
    rgb = rp.hsv_to_rgb255(sample_hsv)
    assert np.array_equal(rgb, sample_rgb)


def test_load_as_hsv(sample_hsv, sample_hsv2):
    img = rp.load_as_hsv('tests/cross_plus_alpha.png')
    assert img.dtype == sample_hsv.dtype
    assert img.shape == sample_hsv.shape
    img = rp.load_as_hsv('tests/nine_pixel_white_ground_black_cross.png')
    assert np.array_equal(img, sample_hsv2)


def test_is_long_and_large():

    obj = RP(length = 3000, width = 300)
    assert rp.is_long_and_large(obj)
    obj = RP(length = 300, width = 300)
    assert not rp.is_long_and_large(obj)


def test_is_not_small():
    obj = RP(3000, 300)
    assert rp.is_not_small(obj)

def test_label_image( mask_to_label):
    label_array, num_labels = rp.label_image(mask_to_label)
    assert num_labels == 4
    assert label_array.max() == 4

def test_clean_labelled_mask(mask_to_label):
    label_array, num_labels = rp.label_image(mask_to_label)
    assert label_array.max() == 4
    objs = [RP(label = i) for i in range(1,4)] #3 rp objs with max label 3
    filtered = rp.clean_labelled_mask(label_array, objs)
    assert filtered.max() == 3

def test_clear_background(sample_hsv, sample_threshold_bool, sample_threshold_hsv):
    assert np.array_equal( rp.clear_background(sample_hsv, sample_threshold_bool), sample_threshold_hsv)

def test_pixel_volume_to_circular_area():
    assert math.isclose(rp.pixel_volume_to_circular_area(50, 10), 0.503, abs_tol=0.05)

