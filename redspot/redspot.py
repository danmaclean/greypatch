import numpy as np
from skimage import io
from skimage import color
import matplotlib.pyplot as plt
from scipy import ndimage as ndi
from skimage.color import label2rgb
from skimage import measure
from skimage import feature
from typing import Callable, List, Tuple, Union

HEALTHY_HUE = (0.156, 1.0)
HEALTHY_SAT = (0.196, 1.0)
HEALTHY_VAL = (0.0, 1.0)

HEALTHY_RED = (4, 155)
HEALTHY_GREEN = (120, 175)
HEALTHY_BLUE = (0, 255)

LESION_HUE = (0, 35)
LESION_SAT = (0, 255)
LESION_VAL = (5, 185)


def threshold_hsv_img(im: np.ndarray,
                      h: Tuple[float, float] = HEALTHY_HUE,
                      s: Tuple[float, float] = HEALTHY_SAT,
                      v: Tuple[float, float] = HEALTHY_VAL) -> np.ndarray:
    """returns a logical binary mask array (dtype bool_ of dimension im ( an HSV image) in which pixels in im pass the lower
    and upper thresholds specified in h, s and v (hue lower,upper; sat lower,upper and val lower, upper;
    respectively) """
    assert im.dtype.type is np.float64, "im must be np.ndarray of type float64. Looks like you're not using an HSV image."
    return _threshold_three_channels(im, c1_limits=h, c2_limits=s, c3_limits=v)


def hsv_to_rgb255(img) -> np.ndarray:
    """given an hsv image in (0.0,1.0) scale, converts to RGB image in (0,255)"""
    return (color.hsv2rgb(img) * 255).astype('int')


def threshold_rgb_img(im: np.ndarray,
                      r: Tuple[int, int] = HEALTHY_RED,
                      g: Tuple[int, int] = HEALTHY_GREEN,
                      b: Tuple[int, int] = HEALTHY_BLUE) -> np.ndarray:
    """returns a logical binary mask array (dtype bool_ of dimension im ( an RGB image) in which pixels in im pass the lower
    and upper thresholds specified in r, g and b (red lower,upper; green lower,upper and blue lower, upper;
    respectively) """
    assert im.dtype.type is np.int64, "im must be np.ndarray of type int in scale (0,255). Looks like you're not using a RGB image in range (0,255)."
    return _threshold_three_channels(im, c1_limits=r, c2_limits=g, c3_limits=b)


def _threshold_three_channels(im: np.ndarray,
                              c1_limits: Tuple[Union[int, float], Union[int, float]] = (0, 1),
                              c2_limits: Tuple[Union[int, float], Union[int, float]] = (0, 1),
                              c3_limits: Tuple[Union[int, float], Union[int, float]] = (0, 1)
                              ) -> np.ndarray:
    """returns a logical binary mask array (dtype bool_ of dimension im  in which pixels in im pass the lower
    and upper thresholds specified in c1_limits, c2_limits and c3_limits respectively) """

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
    hsv_img: np.ndarray
    """takes a file path and opens the image then converts to HSV colour space. 
    returns numpy array dtype float 64"""
    img = io.imread(fname)
    hsv_img = color.rgb2hsv(img)
    return hsv_img


def preview_mask(m: np.ndarray, width: int = 10, height: int = 5) -> None:
    """given a binary bool mask array returns a plot in two colours black = 1/True, white = 0/False"""
    plt.figure(figsize=(width, height))
    plt.imshow(m, cmap="binary")
    plt.show()


def preview_object_labels(label_array: np.ndarray, binary_image: np.ndarray) -> None:
    """given a labelled array from ndi.label and a background binary image, returns a plot with
    the objects described in the labelled array coloured in. For preview purposes not further analysis """
    overlay = label2rgb(label_array, image=binary_image)
    plt.imshow(overlay)
    plt.show()


def is_long_and_large(obj: measure._regionprops._RegionProperties, major_to_minor: int = 2,
                      min_area: int = 300 * 300) -> Union[bool, None]:
    """"given a region props object works ; returns True if the object represented has a
     major to minor axis ratio of > major_to_minor and takes up pixels of min_area,
     False otherwise and None if not calculable"""
    try:
        ratio = obj.major_axis_length / obj.minor_axis_length
        if ratio >= major_to_minor and obj.area >= min_area:
            return True
        else:
            return False
    except ZeroDivisionError:
        return None


def label_image(m: np.ndarray, structure=None, output=None) -> Tuple[np.ndarray, int]:
    """given a binary mask array, returns a version with the distinct islands labelled by integers,
    and a count of objects found. Thin wrapper around ndi.label """
    label_array: np.ndarray
    number_of_labels: int

    label_array, number_of_labels = ndi.label(m, structure, output)
    return label_array, number_of_labels


def get_object_properties(label_array: np.ndarray) -> List[measure._regionprops._RegionProperties]:
    """given a label array returns a list of computed RegionProperties objects."""
    return measure.regionprops(label_array, coordinates='xy')


def filter_region_property_list(region_props: List[measure._regionprops._RegionProperties],
                                func: Callable[[measure._regionprops._RegionProperties], bool]) \
        -> List[measure._regionprops._RegionProperties]:
    """given a list of region props, and a function that returns True/False for each region prop
     Returns a list of region props that have passed"""
    return [r for r in region_props if func(r)]


def clean_labelled_mask(label_array: np.ndarray,
                        region_props: List[measure._regionprops._RegionProperties]) -> np.ndarray:
    """given a label array, sets the labels not represented in region_props to Zero - effectively removing them from the image. Intended to be used on label images"""
    labels_to_keep: list = [r.label for r in region_props]
    keep_mask = np.isin(label_array, labels_to_keep)
    return label_array * keep_mask


def extract_image_segment(hsv_img: np.ndarray, region_prop: measure._regionprops._RegionProperties) -> np.ndarray:
    """given 3D hsv_img returns a slice covered by the bounding box of region_prop"""
    min_row, min_col, max_row, max_col = region_prop.bbox
    return hsv_img[min_row:max_row, min_col:max_col]


def griffiths_healthy_regions(hsv_img: np.ndarray,
                              h: Tuple[float, float] = HEALTHY_HUE,
                              s: Tuple[float, float] = HEALTHY_SAT,
                              v: Tuple[float, float] = HEALTHY_VAL) -> Tuple[np.ndarray, int]:
    """given an image in hsv applies Ciaran Griffiths detection for healthy regions.
    returns the mask of pixels and the pixel volume. Note does not convert to RGB - not clear
    at this time whether whether that code actually does anything in Ciaran's script."""
    # TODO: check with Ciaran whether the RGB change here is actually effective?!
    mask = threshold_hsv_img(hsv_img, h=h, s=s, v=v).astype(int)  # ,r,g,b)
    filled_mask = ndi.binary_fill_holes(mask)
    return (filled_mask, np.sum(mask))


def griffiths_lesion_regions(hsv_img, h: Tuple[float, float] = LESION_HUE, s: Tuple[float, float] = LESION_SAT,
                             v: Tuple[float, float] = LESION_VAL, sigma: float = 2.0) -> Tuple[np.ndarray, int]:
    """given an image in hsv applies Ciaran Griffiths detection for lesion regions.
    applies a hsv_space colour threshold, then finds edges with Canny and fills that mask for holes.
    returns a labelled mask of objects and the object count."""
    mask = threshold_hsv_img(hsv_img, h=h, s=s, v=v).astype(int)
    edges = feature.canny(mask, sigma=sigma)
    lesion_mask = ndi.binary_fill_holes(mask).astype(int)
    return ndi.label(lesion_mask)
