import redpatch as rp

fs = FilterSettings()
fs.add_setting("leaf_area", h=rp.LEAF_AREA_HUE, s=rp.LEAF_AREA_SAT, v=rp.LEAF_AREA_VAL)
fs.write("test.yml")

import numpy as np
from skimage import measure


def get_object_properties(label_array: np.ndarray, intensity_image: np.ndarray = None):
    """given a label array returns a list of computed RegionProperties objects."""
    return measure.regionprops(label_array, intensity_image=intensity_image)


def _get_sub_images(imfile, fs):
    im = rp.load_as_hsv(imfile)
    leaf_area_mask = rp.griffin_leaf_regions(im,
                                             h=fs['leaf_area']['h'],
                                             s=fs['leaf_area']['s'],
                                             v=fs['leaf_area']['v'])
    labelled_leaf_area, leaf_areas_found = rp.label_image(leaf_area_mask)
    leaf_area_properties = rp.get_object_properties(labelled_leaf_area)
    leaf_areas_to_keep = rp.filter_region_property_list(leaf_area_properties, rp.is_not_small)
    cleaned_leaf_area = rp.clean_labelled_mask(labelled_leaf_area, leaf_areas_to_keep)
    final_labelled_leaf_area, final_leaf_areas_found = rp.label_image(cleaned_leaf_area)
    three_d_final_labelled_leaf_area = np.dstack((final_labelled_leaf_area, final_labelled_leaf_area,
                                                  final_labelled_leaf_area))  # stupid hack because get object properties needs 3d label array to match image
    props = get_object_properties(three_d_final_labelled_leaf_area, intensity_image=im)
    sub_labels = [p.image.astype(int)[:, :, -1] for p in props]
    sub_images = [p.intensity_image for p in props]
    cleared_leaf_sub_image = [rp.clear_background(sub_images[i], sub_labels[i]) for i in range(len(sub_labels))]
    return (cleared_leaf_sub_images, sub_labels)


def _get_healthy_portion(im, fs):
    healthy_mask, healthy_volume = rp.griffin_healthy_regions(im,
                                                              h=fs['healthy_area']['h'],
                                                              s=fs['healthy_area']['s'],
                                                              v=fs['healthy_area']['v'])
    ##here add all code to get a list of lesion regions object - ie labelled, filtered and properties found
    ##
    return healthy_mask


def _get_lesion_masks(im, fs):
    lesion_region_mask, lesion_region_volume = rp.griffin_lesion_regions(im,
                                                                         h=fs['lesion_area']['h'],
                                                                         s=fs['lesion_area']['s'],
                                                                         v=fs['lesion_area']['v'])
    ##here add all code to get a list of lesion regions object - ie labelled, filtered and properties found
    ##
    return lesion_region_mask


def _get_lesion_centres(???)


import os
import importlib

importlib.reload(rp)


def batch_process(folder=".", settings="test.yml"):
    fs = FilterSettings()
    fs.read(settings)
    image_files = os.listdir(folder)
    for imfile in image_files:
        ims, labels = _get_sub_images(imfile, fs)
        for sub_im in ims:
            healthy_masks = [_get_healthy_masks(s, fs) for i in ims]  # 0 or 1 per image
            filtered_healthy_masks =
            lesion_objs = [_get_lesion_masks(i, fs) for i in ims]  # 0 to many per image
            for lr in lesion_masks:
                lesion_centres = _get_lesion_centres(lr)
        return ims, labels


ims, labels = batch_process("/Users/macleand/Desktop/single_image/")