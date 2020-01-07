import redpatch as rp
import numpy as np
from skimage import measure, io, color
import skimage
import os
import sys
import pandas as pd

import argparse
parser = argparse.ArgumentParser()

parser.add_argument("-s","--source_folder", help='folder containing images to analyse', type = str)
parser.add_argument("-d","--destination_folder", help='folder to write output. Created if does not exist. ')
parser.add_argument("-m", "--do_not_summarize", help="produce full output. If not used a summary result is produced.", action='store_true')
parser.add_argument("-f", "--filter_settings", help="file of filter settings to use.", default="default_filter.yml",type=str )
parser.add_argument("-c", "--create_default_filter", help="creates a default filter file of name provided in CREATE_DEFAULT_FILTER and exits", default=False, type=str)

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
    return cleared_leaf_sub_images, sub_labels


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


def _get_lesion_centres():
    pass

def _make_pandas(region_prop, area_type=None, image_file=None, sub_image_index = None, props=['area','label']):
    d = {p: [rp[p] for rp in region_prop]for p in props}
    d['area_type'] = [area_type for i in region_prop]
    d['image_file'] = [image_file for i in region_prop]
    d['sub_image_index'] = [sub_image_index for i in region_prop]
    return pd.DataFrame(d)

def _write_out(file, df, index=False):
    with open(file, "w") as out:
        out.write(df.to_csv(index=index))

def batch_process(folder=".", settings="settings.yml"):
    fs = rp.FilterSettings()
    fs.read(settings)
    image_files = [os.path.join(folder, f) for f in os.listdir(folder)]
    all_dfs = []
    for imfile in image_files:
        print("...doing image {}".format(imfile), file=sys.stderr)
        sub_ims, labels = _get_sub_images(imfile, fs)
        for sub_i_idx, sub_i in enumerate(sub_ims, 1):
            imtag = os.path.join(args.destination_folder, "{}_sub_image_{}{}".format(os.path.basename(imfile), sub_i_idx, ".jpg") )
            io.imsave(imtag, skimage.img_as_ubyte(color.hsv2rgb(sub_i)) )
            healthy_obj_props = _get_healthy_areas(sub_i, fs)
            lesion_area_props = _get_lesion_areas(sub_i, fs)  # 0 to many per image
            # lesion_centre_props = _get_lesion_centres(sub_i,fs)
            hdf = _make_pandas(healthy_obj_props, area_type="healthy_region", image_file=imfile, sub_image_index=sub_i_idx)
            ldf = _make_pandas(lesion_area_props, area_type="lesion_regions", image_file=imfile, sub_image_index=sub_i_idx)
            df = hdf.append(ldf,ignore_index=True)
            all_dfs.append(df)
    df = pd.concat(all_dfs)

    if not args.do_not_summarize:
        summary_df = ( df
                      .drop(['label'],axis=1)
                      .groupby(['image_file', 'sub_image_index', 'area_type'])
                      .sum()
                    )
        _write_out(os.path.join(args.destination_folder,"summary_results.csv",index = True), summary_df)
    else:
        _write_out(os.path.join(args.destination_folder, "tidy_results.csv"),df, index = False)



# TODO , annotated image, lesion centres.


if __name__ == '__main__':
    batch_process(folder=args.source_folder, settings=args.filter_settings)