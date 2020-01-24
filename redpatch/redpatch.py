"""
redpatch

A module for segmenting diseased leaf images to find healthy regions, lesion associated regions and lesion centres.


Workflow Overview
-----------------

1. Set scale sliders to find HSV values that segment whole leaves from background
2. Segment image into leaf sub-images
3. Set scale sliders to find HSV values that segment healthy regions within leaf sub-images
4. Segment the healthy region
5. Set scale sliders to find HSV values that segment lesion regions within leaf sub-images
6. Segment the lesion regions
7. Set scale sliders that segment lesion centres within lesion regions
8. Segment lesion centres
9. Quantify found objects

Basic Usage
-----------

1. Import module

    .. highlight:: python
    .. code-block:: python

    import redpatch as rp

2. Create an IPython file browser to select images

    .. highlight:: python
    .. code-block:: python

    f = rp.FileBrowser()
    f.widget()

3. Load an image into HSV colour space

    .. highlight:: python
    .. code-block:: python

    hsv_image = rp.load_as_hsv( f.path )

4. Create an image slider

    .. highlight:: python
    .. code-block:: python

    rp.run_threshold_preview(hsv_image, width = 2)


5. Find objects using HSV values

    .. highlight:: python
    .. code-block:: python

    # find raw objects
    lesion_region_mask, lesion_region_volume = rp.griffin_lesion_regions(cleared_image, h =(0.0, 0.82),
                                                                                        s = (0.2, 1.0),
                                                                                        v = (0.4, 1.0))
    # label regions
    labelled_lesion_regions, lesion_region_count = rp.label_image(lesion_region_mask)

    # visual preview of regions
    rp.preview_object_labels(labelled_lesion_regions, color.hsv2rgb(cleared_image))

    #filter regions
    lesion_regions_properties_list = rp.get_object_properties(labelled_lesion_regions)
    lesion_regions_to_keep = rp.filter_region_property_list(lesion_regions_properties_list, rp.is_not_small

6. Examine objects as scikit-image measure RegionProps objects

    .. highlight:: python
    .. code-block:: python

    first_lesion_region = lesion_regions_to_keep[0]
    first_lesion_region.area
"""

from skimage import io
from skimage import color
from skimage import measure
from skimage import feature
from scipy import ndimage as ndi
import matplotlib.pyplot as plt
import numpy as np
from typing import Callable, List, Tuple, Union
from ipywidgets import FloatRangeSlider, FloatProgress
from IPython.display import display
import ipywidgets as widgets
import math

#: Default values for h,s,v values in different griffin named functions
LEAF_AREA_HUE = tuple([i / 255 for i in (0, 255)])
LEAF_AREA_SAT = tuple([i / 255 for i in (50, 255)])
LEAF_AREA_VAL = tuple([i / 255 for i in (40, 255)])

HEALTHY_HUE = tuple([i / 255 for i in (40, 255)])
HEALTHY_SAT = tuple([i / 255 for i in (50, 255)])
HEALTHY_VAL = tuple([i / 255 for i in (0, 255)])

HEALTHY_RED = (4, 155)
HEALTHY_GREEN = (120, 175)
HEALTHY_BLUE = (0, 255)

LESION_HUE = tuple([i / 255 for i in (0, 41)])
LESION_SAT = tuple([i / 255 for i in (38, 255)])
LESION_VAL = tuple([i / 255 for i in (111, 255)])

LESION_CENTRE_HUE = tuple([i / 255 for i in (0, 41)])
LESION_CENTRE_SAT = tuple([i / 255 for i in (38, 255)])
LESION_CENTRE_VAL = tuple([i / 255 for i in (111, 255)])

SCALE_CARD_HUE = (0.61, 1.0)
SCALE_CARD_SAT = (0.17, 1.0)
SCALE_CARD_VAL = (0.25, 0.75)


def threshold_hsv_img(im: np.ndarray,
                      h: Tuple[float, float] = HEALTHY_HUE,
                      s: Tuple[float, float] = HEALTHY_SAT,
                      v: Tuple[float, float] = HEALTHY_VAL) -> np.ndarray:
    """
    Selects pixels passing an HSV image threshold in all three channels.

    Returns a logical binary mask array (dtype bool_ of dimension im ( an HSV image) in which pixels in im pass the lower
    and upper thresholds specified in h, s and v (hue lower,upper; sat lower,upper and val lower, upper;
    respectively)

    :param: im np.ndarray -- a numpy ndarray
    :param: h Tuple -- a 2-tuple of Hue thresholds (lower, upper)
    :param: s Tuple -- a 2-tuple of Saturation thresholds (lower, upper)
    :param: v Tuple -- a 2-tuple of Value thresholds (lower, upper)
    :return: np.ndarray -- a logical array (dtype bool_) with shape == im


    """
    assert im.dtype.type is np.float64, "im must be np.ndarray of type float64. Looks like you're not using an HSV image."
    return _threshold_three_channels(im, c1_limits=h, c2_limits=s, c3_limits=v)


def hsv_to_rgb255(img: np.ndarray) -> np.ndarray:
    """
    Convert HSV image to RGB image.

    Given an HSV image in (0.0,1.0) range, converts to RGB image in (0,255). Usually needed prior to viewing as most viewers interpret images as RGB.

    :param: img np.ndarray -- a numpy ndarray
    :return: np.ndarray -- a numpy ndarray with shape == img

    """
    return (color.hsv2rgb(img) * 255).astype('int')


def threshold_rgb_img(im: np.ndarray,
                      r: Tuple[int, int] = HEALTHY_RED,
                      g: Tuple[int, int] = HEALTHY_GREEN,
                      b: Tuple[int, int] = HEALTHY_BLUE) -> np.ndarray:
    """
    Selects pixels passing an RGB image threshold in all three channels.

    Returns a logical binary mask array (dtype bool_ of dimension im ( an RGB image) in which pixels in im pass the lower
    and upper thresholds specified in r, g and b (red lower,upper; green lower,upper and blue lower, upper;
    respectively)

    :param: im np.ndarray -- a numpy ndarray
    :param: r Tuple -- a 2-tuple of Red thresholds (lower, upper)
    :param: g Tuple -- a 2-tuple of Green thresholds (lower, upper)
    :param: b Tuple -- a 2-tuple of Blue thresholds (lower, upper)
    :return: np.ndarray -- a logical array (dtype bool_) with shape == im

    """
    assert im.dtype.type is np.int64, "im must be np.ndarray of type int in scale (0,255). Looks like you're not using a RGB image in range (0,255)."
    return _threshold_three_channels(im, c1_limits=r, c2_limits=g, c3_limits=b)


def _threshold_three_channels(im: np.ndarray,
                              c1_limits: Tuple[Union[int, float], Union[int, float]] = (0, 1),
                              c2_limits: Tuple[Union[int, float], Union[int, float]] = (0, 1),
                              c3_limits: Tuple[Union[int, float], Union[int, float]] = (0, 1)
                              ) -> np.ndarray:
    """
    Thresholds an image.

    Internal method.

    Returns a logical binary mask array (dtype bool_ of dimension im  in which pixels in im pass the lower
    and upper thresholds specified in c1_limits, c2_limits and c3_limits respectively)

    :param: im np.ndarray -- a numpy ndarray
    :param: c1_limits Tuple -- a 2-tuple of channel 1 thresholds (lower, upper)
    :param: c2_limits Tuple -- a 2-tuple of channel 2 thresholds (lower, upper)
    :param: c3_limits Tuple -- a 2-tuple of channel 3 thresholds (lower, upper)
    :return: np.ndarray -- a logical array (dtype bool_) with shape == im
    """
    c1 = im[:, :, 0]
    c2 = im[:, :, 1]
    c3 = im[:, :, 2]

    c1_min, c1_max = c1_limits
    c2_min, c2_max = c2_limits
    c3_min, c3_max = c3_limits

    c1_mask = np.logical_and(
        c1 >= c1_min, c1 <= c1_max
    )
    c2_mask = np.logical_and(
        c2 >= c2_min, c2 <= c2_max
    )
    c3_mask = np.logical_and(
        c3 >= c3_min, c3 <= c3_max
    )
    return np.logical_and(c1_mask, c2_mask, c3_mask)


def load_as_hsv(fname: str) -> np.ndarray:
    """
    Load a file into HSV colour space.

    Takes a file path and opens the image then converts to HSV colour space.
    returns numpy array dtype float 64

    :param: fname str -- path to the image
    :return: np.ndarray -- numpy array containing image

    """
    img = io.imread(fname)
    assert len(img.shape) == 3, "Image at: {} does not appear to be a colour image.".format(fname)
    hsv_img = color.rgb2hsv(img)
    return hsv_img


def preview_mask(m: np.ndarray, width: int = 5, height: int = 5) -> None:
    """
    Draw a mask to screen.

    Given a binary bool mask array draws a plot in two colours black = 1/True, white = 0/False.
    Intended for use in IPython and interactive sessions as the plot renders immediately

    :param: m np.ndarray -- the mask to draw.
    :param: width int -- width in inches of the plot
    :param: height int -- height in inches of the plot
    :return: None
    """
    plt.figure(figsize=(width, height))
    plt.imshow(m, cmap="binary_r")
    plt.show()


def preview_hsv(img: np.ndarray, width: int = 5, height: int = 5) -> None:
    """
    Draw an HSV image to screen.

    Given an HSV image, generates a preview image and draws to screen.
    Intended for use in IPython and interactive sessions as the plot renders immediately.

    :param: img np.ndarray -- the image to draw
    :param: width int -- width in inches of the plot
    :param: height int -- height in inches of the plot
    :return: None
    """
    plt.figure(figsize=(width, height))
    plt.imshow(color.hsv2rgb(img))
    plt.show()


def preview_object_labels(label_array: np.ndarray, binary_image: np.ndarray, width: int = 5, height: int = 5) -> None:
    """
    Draw a preview image of objects in a mask, colouring by labels.

    Given a labelled object array from rp.label_image and a background binary image, returns a plot with
    the objects described in the labelled array coloured in.
    Intended for use in IPython and interactive sessions as the plot renders immediately.

    :param: label_array np.ndarray -- labelled object array/image
    :return: None
    """
    overlay = color.label2rgb(label_array, image=binary_image, bg_label=0)
    plt.figure(figsize=(width, height))
    plt.imshow(overlay)
    plt.show()


def is_long_and_large(obj: measure._regionprops._RegionProperties, major_to_minor: int = 2,
                      min_area: int = 300 * 300) -> Union[bool, None]:
    """"
    Work out whether an object is long and large.

    Given a region props object works ; returns True if the object represented has a
    major to minor axis ratio of > major_to_minor and takes up pixels of min_area,
    False otherwise and None if not calculable

    :param: obj skimage.measure._regionprops._RegionProperties -- a region properties object
    :param: major_to_minor int -- the ratio of the long to short side that defines whether the object is long
    :param: min_area int -- the total area that defines whether the object is large.
    :return: None or bool
    """
    try:
        ratio = obj.major_axis_length / obj.minor_axis_length
        if ratio >= major_to_minor and obj.area >= min_area:
            return True
        else:
            return False
    except ZeroDivisionError:
        return None


def is_not_small(obj: measure._regionprops._RegionProperties, min_area: int = 50 * 50) -> Union[bool, None]:
    """"
    Work out whether an object is not small.

    Given a region props object this function returns True if its area is greater than min_area.
    False if not and None if the value is not calculable

    :param: obj skimage.measure._regionprops._RegionProperties -- a region properties object
    :param: min_area int -- minimum area threshold
    :return: None or bool
    """
    try:
        if obj.area >= min_area:
            return True
        else:
            return False
    except:
        return None


def label_image(m: np.ndarray, structure=None, output=None) -> Tuple[np.ndarray, int]:
    """
    Creates labels for the objects in an image.

    Given a binary mask array, returns a version with the distinct islands labelled by integers,
    and a count of objects found. Thin wrapper around ndi.label

    :param: m np.ndarray -- binary mask image/array
    :param: structure np.ndarray -- custom structuring object if needed (default None)
    :return: a labelled image mask
    """

    label_array, number_of_labels = ndi.label(m, structure, output)
    return label_array, number_of_labels


def get_object_properties(label_array: np.ndarray, intensity_image: np.ndarray = None, ) -> List[
    measure._regionprops._RegionProperties]:
    """
    Compute object properties. EG. area.

    Given a label array returns a list of computed RegionProperties objects.

    :param: label_array np.ndarray -- the label array to compute properties from
    :param: intensity_image np.ndarray -- the image on which properties are computed
    :return: list of skimage.measure.regionprops objects
    """
    return measure.regionprops(label_array, intensity_image=intensity_image)


def filter_region_property_list(region_props: List[measure._regionprops._RegionProperties],
                                func: Callable[[measure._regionprops._RegionProperties], bool]) \
        -> List[measure._regionprops._RegionProperties]:
    """
    Filters region props objects from a list if they do not satisfy a condition.

    Given a list of region props, and a function that returns True/False for each region prop
    Returns a list of region props that have passed

    :param: region_props List -- list of skimage.measure.RegionProps objects
    :param: func Callable -- a function that returns True/False to be evaluated against the RegionProps objects
    :return: List of RegionProps

    """
    return [r for r in region_props if func(r)]


def clean_labelled_mask(label_array: np.ndarray,
                        region_props: List[measure._regionprops._RegionProperties]) -> np.ndarray:
    """
    Removes unwanted object pixels from a mask.

    Given a label array, sets the labels not represented in region_props to Zero
    removing them from the image. Intended to be used on label images

    :param: label_array np.ndarray -- the label array from which non-represented objects will be removed
    :param: region_props List -- list of skimage.measure.RegionProps, the objects to keep in the label array
    :return: np.ndarray -- cleaned label array

    """
    labels_to_keep: list = [r.label for r in region_props]
    keep_mask = np.isin(label_array, labels_to_keep)
    return label_array * keep_mask


def extract_image_segment(hsv_img: np.ndarray, region_prop: measure._regionprops._RegionProperties) -> np.ndarray:
    """

    Return a rectangular segment of an image covering a region object.

    Given 3D hsv_img returns a slice covered by the bounding box of region_prop

    :param: hsv_img np.ndarray -- an hsv scaled image
    :param: region_prop -- a RegionProps object describing the extent of the subimage
    :return: np.ndarray

    """
    min_row, min_col, max_row, max_col = region_prop.bbox
    return hsv_img[min_row:max_row, min_col:max_col]


def griffin_healthy_regions(hsv_img: np.ndarray,
                            h: Tuple[float, float] = HEALTHY_HUE,
                            s: Tuple[float, float] = HEALTHY_SAT,
                            v: Tuple[float, float] = HEALTHY_VAL) -> Tuple[np.ndarray, int]:
    """
    Perform Ciaran Griffin's Healthy Region extraction.

    Given an image in hsv applies Ciaran Griffin's detection for healthy regions.
    returns the mask of pixels and the pixel volume.

    :param: hsv_img np.ndarray -- an HSV scaled image
    :param: h Tuple -- minimum and maximum Hue threshold values
    :param: s Tuple -- minimum and maximum Saturation threshold values
    :param: v Tuple -- minimum and maximum Value threshold values
    :return: np.ndarray, int


    """
    # rgb_img = hsv_to_rgb255(hsv_img)
    mask = threshold_hsv_img(hsv_img, h=h, s=s, v=v).astype(int)  # ,r,g,b)
    filled_mask = ndi.binary_fill_holes(mask)

    return (filled_mask, np.sum(mask))


def griffin_lesion_regions(hsv_img, h: Tuple[float, float] = LESION_HUE, s: Tuple[float, float] = LESION_SAT,
                           v: Tuple[float, float] = LESION_VAL) -> Tuple[np.ndarray, int]:
    """given an image in hsv applies Ciaran Griffin's detection for lesion regions.
    applies a hsv_space colour threshold,
    returns a labelled mask of objects and the object count."""
    mask = threshold_hsv_img(hsv_img, h=h, s=s, v=v).astype(int)
    lesion_mask = ndi.binary_fill_holes(mask)
    return lesion_mask, np.sum(mask)


def griffin_leaf_regions(hsv_img, h: Tuple[float, float] = LEAF_AREA_HUE, s: Tuple[float, float] = LEAF_AREA_SAT,
                         v: Tuple[float, float] = LEAF_AREA_VAL) -> Tuple[np.ndarray, int]:
    """given an image in hsv applies Ciaran Griffin's detection for leaf area regions.
    applies a hsv_space colour threshold and fills that mask for holes.
    returns a binary mask and object count."""
    mask = threshold_hsv_img(hsv_img, h=h, s=s, v=v).astype(int)
    return ndi.binary_fill_holes(mask)


def griffin_lesion_centres(hsv_img, lesion_region: measure._regionprops._RegionProperties,
                           h: Tuple[float, float] = LEAF_AREA_HUE, s: Tuple[float, float] = LEAF_AREA_SAT,
                           v: Tuple[float, float] = LEAF_AREA_VAL, sigma: float = 2.0):
    """finds lesion centres in a given lesion region"""
    # convert to grey for canny
    img_grey = color.rgb2gray(color.hsv2rgb(hsv_img))
    sub_img = get_region_subimage(lesion_region, img_grey)
    edges = feature.canny(sub_img, sigma=sigma).astype(int)
    mask = ndi.binary_fill_holes(edges)
    labelled_image, count = label_image(mask)
    region_props = get_object_properties(labelled_image, edges)
    return region_props


def griffin_scale_card(hsv_img, h, s, v, side_length=5):
    '''returns pixels per cm of scale card object'''
    mask = threshold_hsv_img(hsv_img, h=h, s=s, v=v).astype(int)
    card_mask = ndi.binary_fill_holes(mask)
    labelled_image, count = label_image(card_mask)
    region_props = get_object_properties(labelled_image, card_mask)
    biggest_obj_area = sorted(region_props, key=lambda rp: rp.area, reverse=True)[
        0].area  # assume biggest object is scale card
    side = math.sqrt(biggest_obj_area)
    return side / float(side_length)


def clear_background(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """given an image and a binary mask, clears all pixels in the image (ie sets to zero)
    the zero/false pixels in the mask"""
    i = img.copy()
    a = i[:, :, 0] * mask
    b = i[:, :, 1] * mask
    c = i[:, :, 2] * mask
    return np.dstack([a, b, c])


def run_threshold_preview(image: np.ndarray, height: int = 15, width: int = 15, slider_width: int = 500) -> None:
    """ Given an HSV image, generates some sliders and an overlay image. Shows the image colouring the
    pixels that are included in the sliders thresholds in red. Note this does not return an image or
     mask of those pixels, its just a tool for finding the thresholds"""

    slider_width = str(slider_width) + 'px'

    @widgets.interact_manual(
        h=FloatRangeSlider(min=0., max=1., step=0.01, readout_format='.2f', layout={'width': slider_width}),
        s=FloatRangeSlider(min=0., max=1., step=0.01, readout_format='.2f', layout={'width': slider_width}),
        v=FloatRangeSlider(min=0., max=1., step=0.01, readout_format='.2f', layout={'width': slider_width})
    )
    def interact_plot(h=(0.2, 0.4), s=(0.2, 0.4), v=(0.2, 0.4)):
        f = FloatProgress(min=0, max=100, step=1, description="Progress:")
        display(f)

        x = threshold_hsv_img(image, h=h, s=s, v=v)
        f.value += 25

        i = image.copy()
        f.value += 25

        i[x] = (0, 1, 1)
        f.value += 25

        plt.figure(figsize=(width, height))
        plt.imshow(color.hsv2rgb(i))
        f.value += 25

        return_string = "Selected Values\nHue: {0}\nSaturation: {1}\nValue: {2}\n".format(h, s, v)
        print(return_string)


def get_region_subimage(region_obj: measure._regionprops._RegionProperties, source_image: np.ndarray) -> np.ndarray:
    min_row, min_col, max_row, max_col = region_obj.bbox
    """given a RegionProperties object and a source image, will return the portion of the image
    coverered by the RegionProperties object"""
    if len(source_image.shape) == 3:
        return source_image[min_row:max_row, min_col:max_col, :]
    else:
        return source_image[min_row:max_row, min_col:max_col]


def estimate_hsv_from_rgb(r, g, b):
    arr = skimage.color.rgb2hsv([[[r, g, b]]])
    h = float(arr[:, :, 0])
    s = float(arr[:, :, 1])
    v = float(arr[:, :, 2])
    return h, s, v
