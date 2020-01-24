"""
redpatch-batch-process

A utility for running redpatch functions on a folder of images.


See the help:

    redpatch --help

Usage Examples:

    Basic use:
        redpatch-batch-process.py --source_folder ~/Desktop/single_image --destination_folder ~/Desktop/test_out --filter_settings ~/Desktop/default_filter.yml

    Tidy full output:
        redpatch-batch-process.py --create_tidy_output --source_folder ~/Desktop/single_image --destination_folder ~/Desktop/test_out --filter_settings ~/Desktop/default_filter.yml

    Use a scale card:
        redpatch-batch-process.py --scale_card_side_length 5 --source_folder ~/Desktop/single_image --destination_folder ~/Desktop/test_out --filter_settings ~/Desktop/default_filter.yml

    Create a default filter settings YAML file:
        redpatch-batch-process.py --create_default_filter ~/Desktop/default_filter.yml
"""


import redpatch as rp
import numpy as np
from skimage import measure, io, color
import skimage
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from shapely.geometry.polygon import Polygon

import argparse
parser = argparse.ArgumentParser(add_help=True, formatter_class=argparse.RawDescriptionHelpFormatter, description = """
redpatch-batch-process

A utility for running redpatch functions on a folder of images.


See the help:

    redpatch --help

Usage Examples:

    Basic use:
        redpatch-batch-process --source_folder ~/Desktop/single_image --destination_folder ~/Desktop/test_out --filter_settings ~/Desktop/default_filter.yml

    Tidy full output:
        redpatch-batch-process --create_tidy_output --source_folder ~/Desktop/single_image --destination_folder ~/Desktop/test_out --filter_settings ~/Desktop/default_filter.yml

    Use a scale card:
        redpatch-batch-process --scale_card_side_length 5 --source_folder ~/Desktop/single_image --destination_folder ~/Desktop/test_out --filter_settings ~/Desktop/default_filter.yml

    Create a default filter settings YAML file:
        redpatch-batch-process --create_default_filter ~/Desktop/default_filter.yml
""")

parser.add_argument("-s","--source_folder", help='folder containing images to analyse', type = str)
parser.add_argument("-d","--destination_folder", help='folder to write output. Created if does not exist. ')
parser.add_argument("-t", "--create_tidy_output", help="produce an additional full tidy output.", action='store_true')
parser.add_argument("-f", "--filter_settings", help="file of filter settings to use.", default="default_filter.yml",type=str )
parser.add_argument("-c", "--create_default_filter", help="creates a default filter file of name provided in CREATE_DEFAULT_FILTER and exits", default=False, type=str)
parser.add_argument("-l", "--scale_card_side_length", help="find a scale card in each image and calculate pixels per centimetre", default=False)

args = parser.parse_args()

if args.create_default_filter:
    fs = rp.FilterSettings()
    fs.create_default_filter_file(args.create_default_filter)
    sys.exit("Written default filter file to {}".format(args.create_default_filter))
elif not args.source_folder or not args.destination_folder:
    parser.print_help(sys.stderr)
    sys.exit('source and destination folder must be provided')

if not os.path.exists(args.source_folder):
    parser.print_help(sys.stderr)
    sys.exit("source folder {} does not exist".format(args.source_folder))

if not os.path.exists(args.destination_folder):
    os.mkdir(args.destination_folder)

if not os.path.exists(args.filter_settings):
    parser.print_help(sys.stderr)
    sys.exit("filter settings file {} does not exist".format(args.filter_settings))

class RegionPropPlus(object ):

    def __init__(self, rprop, parent_rprop):
        for attr_name in dir(rprop):
            if not attr_name.startswith("_"):
                val = getattr(rprop, attr_name)
                setattr(self, attr_name, val)
        self.parent_label = parent_rprop.label
        self.corrected_bbox = self.correct_bbox(parent_rprop)
        self.corrected_coords = self.correct_coords(parent_rprop)

    def correct_bbox(self, parent_rprop):
        return [x + y for x, y in zip(parent_rprop.bbox, self.bbox)]

    def correct_coords(self, parent_rprop):
        p = np.asarray(self.coords) #todo ##correct coords
        min_row, min_col, max_row, max_col = parent_rprop.bbox
        return np.add(p, [min_row, min_col])

    def __getitem__(self, item):
        return getattr(self, item)


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
    cleared_leaf_sub_images = [rp.clear_background(sub_images[i], sub_labels[i]) for i in range(len(sub_labels))]
    return cleared_leaf_sub_images


def _get_healthy_areas(im, fs):
    healthy_mask, healthy_volume = rp.griffin_healthy_regions(im,
                                                              h=fs['healthy_area']['h'],
                                                              s=fs['healthy_area']['s'],
                                                              v=fs['healthy_area']['v'])
    labelled_healthy_area, healthy_areas_found = rp.label_image(healthy_mask)
    labelled_healthy_area_properties = rp.get_object_properties(labelled_healthy_area)
    return labelled_healthy_area_properties


def _get_lesion_areas(im, fs):
    lesion_area_mask, lesion_region_volume = rp.griffin_lesion_regions(im,
                                                                       h=fs['lesion_area']['h'],
                                                                       s=fs['lesion_area']['s'],
                                                                       v=fs['lesion_area']['v'])
    labelled_lesion_area, lesion_areas_found = rp.label_image(lesion_area_mask)
    labelled_lesion_area_properties = rp.get_object_properties(labelled_lesion_area)
    return labelled_lesion_area_properties


def _get_lesion_centres(im, fs,  lesion_area_region_prop_list ):
    #needs to be fixed  to properly adjust the coordinates of the region properties
    #im = whole leaf sub image

    mod_lesion_centres = []
    for lesion_area in lesion_area_region_prop_list:
        if lesion_area.area > 10:
            lesion_centres = rp.griffin_lesion_centres(im, lesion_area, h=fs['lesion_centre']['h'],
                                      s=fs['lesion_centre']['s'],
                                   v=fs['lesion_centre']['v'])
            for lc in lesion_centres:
                mod_lc = RegionPropPlus(lc, lesion_area)
                mod_lesion_centres.append(mod_lc)
    return mod_lesion_centres

def _get_scale_card(imfile, fs, side_length):
    im = rp.load_as_hsv(imfile)
    return rp.griffin_scale_card(im, h=fs['scale_card']['h'],
                                             s=fs['scale_card']['s'],
                                             v=fs['scale_card']['v'],
                                       side_length=side_length
                                       )


def _make_pandas(region_prop, area_type=None, image_file=None, sub_image_index = None, props=['area','label']):
    d = {p: [rp[p] for rp in region_prop] for p in props}
    d['area_type'] = [area_type for i in region_prop]
    d['image_file'] = [image_file for i in region_prop]
    d['sub_image_index'] = [sub_image_index for i in region_prop]
    if area_type == 'lesion_centre':
        d['parent_lesion_region'] = [lc.parent_label for lc in region_prop]
    else:
        d['parent_lesion_region'] = ["NA" for i in region_prop]

    return pd.DataFrame(d)

def _write_out(file, df, index=False):
    with open(file, "w") as out:
        out.write(df.to_csv(index=index))

def _make_polygons_for_image( list_of_rprops ):

    polys = []
    for i, rprop in enumerate(list_of_rprops, 1):
        coords = []
        if isinstance(rprop, RegionPropPlus):
            coords = rprop.corrected_coords
        else:
            coords = rprop.coords
        if len(coords) > 2: #need 3 points for a polygon
            p = np.asarray(coords) # TODO change if lesion centre - for offset acc to new  bounding box
            p.T[[0,1]] = p.T[[1,0]]
            p = Polygon(p)
            x, y = p.exterior.xy
            polys.append([x,y])
    return polys

def _calc_size(img):
    h,w, d = img.shape
    dpi = 72
    inches_w = w / dpi
    inches_h = h / dpi
    return tuple([inches_w, inches_h])

def _annotate_sub_img(img, healthy, lesions, centres, file=None):
    size = _calc_size(img)
    plt.figure(figsize=size)
    img = skimage.img_as_ubyte(color.hsv2rgb(img))
    plt.imshow(img)
    hcol = (127/255, 191/255, 63/255, 0.5 )
    lcol = (243/255, 80/255, 21/255, 0.5 )
    ccol = (248/255, 252/255, 17/255, 0.66)
    healthy_polys = _make_polygons_for_image(healthy)
    lesion_polys = _make_polygons_for_image(lesions)
    centre_polys = _make_polygons_for_image(centres)

    for p in healthy_polys:
        plt.plot(p[0], p[1], color=hcol )

    for p in lesion_polys:
        plt.plot(p[0], p[1], color=lcol )

    for p in centre_polys:
        plt.plot(p[0], p[1], color=ccol)

    h_patch = mpatches.Patch(color=hcol, label='Healthy')
    l_patch = mpatches.Patch(color=lcol, label="Lesion")
    c_patch = mpatches.Patch(color=ccol, label="Centres")
    plt.legend(bbox_to_anchor=(1, 1), bbox_transform=plt.gcf().transFigure,handles=[h_patch,l_patch,c_patch],loc="upper right")
    plt.savefig(file, dpi = 72, )

def batch_process(folder=".", settings="settings.yml"):
    fs = rp.FilterSettings()
    fs.read(settings)
    image_files = [os.path.join(folder, f) for f in os.listdir(folder)]
    report = rp.RPReport(folder, image_files, fs)
    all_dfs = []
    for imfile in image_files:
        print("...doing image {}".format(imfile), file=sys.stderr)

        scale = False
        if args.scale_card_side_length:
            scale = _get_scale_card(imfile, fs, side_length=args.scale_card_side_length)

        sub_ims = _get_sub_images(imfile, fs)
        for sub_i_idx, sub_i in enumerate(sub_ims, 1):
            imtag = os.path.join(args.destination_folder, "{}_sub_image_{}{}".format(os.path.basename(imfile), sub_i_idx, ".jpg") )
            io.imsave(imtag, skimage.img_as_ubyte(color.hsv2rgb(sub_i)) )
            report.add_subimages(imfile, imtag)

            healthy_obj_props = _get_healthy_areas(sub_i, fs)
            lesion_area_props = _get_lesion_areas(sub_i, fs)  # 0 to many per image
            lesion_centre_props = _get_lesion_centres(sub_i, fs, lesion_area_props,)

            imtag = os.path.join(args.destination_folder, "{}_sub_image_{}{}".format(os.path.basename(imfile), sub_i_idx, "_annotated.jpg"))
            _annotate_sub_img(sub_i, healthy_obj_props, lesion_area_props, lesion_centre_props,  file=imtag)
            report.add_annotated_subimages(imfile, imtag)

            hdf = _make_pandas(healthy_obj_props, area_type="healthy_region", image_file=imfile, sub_image_index=sub_i_idx)
            ldf = _make_pandas(lesion_area_props, area_type="lesion_region", image_file=imfile, sub_image_index=sub_i_idx)
            lcdf = _make_pandas(lesion_centre_props, area_type="lesion_centre", image_file=imfile, sub_image_index=sub_i_idx)
            df = hdf.append([ldf,lcdf], ignore_index=True)

            if args.scale_card_side_length:
                df['pixels_per_cm'] = [scale] * len(df)
            all_dfs.append(df)

    df = pd.concat(all_dfs)
    summary_df = (df
                  .drop(['label'], axis=1)
                  .groupby(['image_file', 'sub_image_index', 'area_type', 'pixels_per_cm'])
                  .sum()
                  )
    report.summary = summary_df
    report.write(os.path.join(args.destination_folder))
    _write_out(os.path.join(args.destination_folder, "summary_results.csv"), summary_df, index=True)

    if args.create_tidy_output:
        _write_out(os.path.join(args.destination_folder, "tidy_results.csv"),df, index = False)





if __name__ == '__main__':
    batch_process(folder=args.source_folder, settings=args.filter_settings)