import greypatch as rp
import numpy as np
from skimage import measure, io, color
import skimage
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from shapely.geometry.polygon import Polygon
import warnings
warnings.filterwarnings("ignore")


def _get_object_properties(label_array: np.ndarray, intensity_image: np.ndarray = None):
    """given a label array returns a list of computed RegionProperties objects."""
    return measure.regionprops(label_array, intensity_image=intensity_image)

def _ed(p1,p2):
    """
    calc euclidean distance between p1 and p2
    :param p1: tuple/list two dimensional point
    :param p2: tuple/list two dimensional point
    :return: int distance in pixels
    """
    return np.linalg.norm(np.array(p1) - np.array(p2))


def _make_match_dataframe(df):
    df['matched_with'] = df.matched_with.astype(str)
    o = df.query('area_type == "outer_lesion_area" &  matched_with != "None" ')
    o['matched_with'] = o.matched_with.astype(int)
    i = df.query('area_type == "inner_lesion_area" &  matched_with != "None" ')
    m = o.merge(i, left_on='matched_with', right_on='label', how='left')
    m['outer_inner_ratio_pixels'] = m['pixels_in_area_y'] / m['pixels_in_area_x']
    return m

def get_sub_images(imfile,
    file_settings = None, 
    dest_folder = None,
    min_lesion_area = None,
    scale = None,
    pixel_length = None
):
    """
    extracts different leaves from a single image file, returning them as individual SubImage objects.

    :param: imfile str -- path to the image
    :param: file_settings str -- FilterSettings object with image segmentation options
    :param: dest_folder str -- folder in which to place results files
    :param: min_lesion_area float -- minimum area for a lesion to pass filter. In either pixels or actual size if 'scale' passed
    :param: scale float -- pixels per real unit length, if known or computed earlier.
    :param: max_lc_ratio float -- maximum length/width ratio of lesion centre to pass filter
    :param: min_lc_size float -- minimum lesion centre size. Computed in real units if 'scale' passed. Computed as area of circle with same pixel volume as the centre.
    :param: lc_prop_across_parent float -- minimum proportion lesion centre must be across the width of the parent lesion (in the row the centre centroid occurs) to pass filter
    """
    im = rp.load_as_hsv(imfile)
    leaf_area_mask = rp.griffin_leaf_regions(im,
                                             h=file_settings['leaf_area']['h'],
                                             s=file_settings['leaf_area']['s'],
                                             v=file_settings['leaf_area']['v'])
    labelled_leaf_area, _ = rp.label_image(leaf_area_mask)
    leaf_area_properties = rp.get_object_properties(labelled_leaf_area)
    leaf_areas_to_keep = rp.filter_region_property_list(leaf_area_properties, rp.is_not_small)
    cleaned_leaf_area = rp.clean_labelled_mask(labelled_leaf_area, leaf_areas_to_keep)
    final_labelled_leaf_area, _ = rp.label_image(cleaned_leaf_area)
    three_d_final_labelled_leaf_area = np.dstack((final_labelled_leaf_area, final_labelled_leaf_area,
                                                  final_labelled_leaf_area))  # stupid hack because get object properties needs 3d label array to match image
    props = rp.subimage._get_object_properties(three_d_final_labelled_leaf_area, intensity_image=im)
    sub_labels = [p.image.astype(int)[:, :, -1] for p in props]
    sub_images = [p.intensity_image for p in props]
    cleared_leaf_sub_images = [rp.clear_background(sub_images[i], sub_labels[i]) for i in range(len(sub_labels))]
    sub_image_objs = []
    for sub_i_idx, sub_i in enumerate(cleared_leaf_sub_images, 1):
        sub_image_objs.append( rp.SubImage(sub_i, sub_i_idx, imfile, file_settings = file_settings, dest_folder = dest_folder, min_lesion_area = min_lesion_area, scale = scale, pixel_length = pixel_length  ) )
    return sub_image_objs


class SubImage(object):

    """
    class representing sub-image (leaf containing area) of a larger image.

    :ivar sub_i: the subimage
    :ivar sub_i_idx: the index of the subimage from the subimage list
    :ivar scale: the scale of the image if computed
    :ivar pixel_length: the length of a pixel side in real units
    :ivar imtag: the name of the file this subimage is referred to in the output
    :ivar annot_imtag: the name of the annotated image file this subimage is referred to in the output
    :ivar parent_image_file: the name of the file this subimage is derived from
    :ivar healthy_obj_props: list of HealthyAreas found in the subimage
    :ivar leaf_area_props: list of LeafAreas found in the subimage
    :ivar lesion_area_props: list of LesionAreas found in the subimage
    :ivar lesion_centre_props: list of LesionCentres found in the subimage
    """

    def __init__(self, 
    sub_i, 
    sub_i_idx, 
    parent_image_file,
    file_settings = None, 
    dest_folder = None,
    min_lesion_area = None,
    scale = None,
    pixel_length = None
    ):

        self.sub_i = sub_i
        self.index = sub_i_idx
        if scale:
            self.scale = scale
            self.pixel_length = pixel_length
        else:
            self.scale = "NA"
            self.pixel_length = "NA"
        self.imtag = os.path.join(dest_folder, "{}_sub_image_{}{}".format(os.path.basename(parent_image_file), sub_i_idx, ".jpg") )
        self.annot_imtag = os.path.join(dest_folder, "{}_sub_image_{}{}".format(os.path.basename(parent_image_file), sub_i_idx, "_annotated.jpg"))
        self.parent_image_file = parent_image_file
        self.healthy_obj_props = self._get_healthy_areas(sub_i, file_settings, scale, pixel_length)
        self.outer_lesion_area_props = self._get_lesion_areas(sub_i, file_settings, scale, pixel_length, key="outer_lesion_area", min_lesion_area = min_lesion_area)  # 0 to many per image
        self.inner_lesion_area_props = self._get_lesion_areas(sub_i, file_settings, scale, pixel_length, key="inner_lesion_area", min_lesion_area = min_lesion_area)
        self.matched_innerouter = self._match_innerouter()



    def _get_healthy_areas(self, im, fs,scale, pixel_length):
        """
        Finds healthy areas according to filtersettings in fs

        :param im: the image to search
        :param fs: a FilterSettings object
        :return: list of HealthyArea objects
        """
        healthy_mask, _ = rp.griffin_healthy_regions(im,
                                                        h=fs['healthy_area']['h'],
                                                        s=fs['healthy_area']['s'],
                                                        v=fs['healthy_area']['v'])
        labelled_healthy_area, _ = rp.label_image(healthy_mask)
        labelled_healthy_area_properties = rp.get_object_properties(labelled_healthy_area)
        return [rp.HealthyArea(o,scale, pixel_length) for o in labelled_healthy_area_properties]

    def _get_leaf_areas(self, im, fs,scale,pixel_length):
        """
        Finds whole leaf areas according to filtersettings in fs

        :param im: the image to search
        :param fs: a FilterSettings object
        :return: list of LeafArea objects
        """
        leaf_area_mask = rp.griffin_leaf_regions(im,
                                                h=fs['leaf_area']['h'],
                                                s=fs['leaf_area']['s'],
                                                v=fs['leaf_area']['v'])
        labelled_leaf_area, _ = rp.label_image(leaf_area_mask)
        leaf_area_properties = rp.get_object_properties(labelled_leaf_area)
        return [rp.LeafArea(o,scale,pixel_length) for o in leaf_area_properties]


    def _get_lesion_areas(self, im, fs, scale, pixel_length, key='outer_lesion_area', min_lesion_area = None):
        """
        Finds brown lesion areas according to filtersettings in fs

        :param im: the image to search
        :param fs: a FilterSettings object
        :param key: a FilterSettings object key string specifying which params to use (IE which lesion type to search for)
        :param min_lesion_area: the minimum area to set a LesionArea objects passed attribute to TRUE
        :return: list of LesionArea objects
        """
        lesion_area_mask, _ = rp.griffin_lesion_regions(im,
                                                        h=fs[key]['h'],
                                                        s=fs[key]['s'],
                                                        v=fs[key]['v'])
        labelled_lesion_area, _ = rp.label_image(lesion_area_mask)
        labelled_lesion_area_properties = rp.get_object_properties(labelled_lesion_area)
        return [rp.LesionArea(o, scale, pixel_length, min_lesion_area=min_lesion_area) for o in
                labelled_lesion_area_properties]

    def _calc_size(self, img):
        """
        get size in inches of an annotated output image of img.shape at 72 DPI
        :param img: img to use
        :return: (width_inches, height_inches)
        """
        img = img
        h,w,_ = img.shape
        dpi = 72
        inches_w = w / dpi
        inches_h = h / dpi
        return tuple([inches_w, inches_h])



    def _match_innerouter(self):
        """
        for each inner lesion finds the closest outer lesion and matches it up.

        :return: list of lists, [inner_lesion, outer_lesion]
        """
        inners = {}
        outers = {}
        matches = []


        for i, inner in enumerate(self.inner_lesion_area_props):
            if inner.passed:
                min = np.inf
                for o, outer in enumerate(self.outer_lesion_area_props):
                    if outer.passed:
                        #print("inner {} - outer {} : {}" .format(inner.centroid, outer.centroid, _ed(np.array(inner.centroid), np.array(outer.centroid) ) ) )
                        if _ed(np.array(inner.centroid), np.array(outer.centroid)) < min:
                            inners[i] = o

        for o, outer in enumerate(self.outer_lesion_area_props):
            if outer.passed:
                min = np.inf
                for i, inner in enumerate(self.inner_lesion_area_props):
                    if inner.passed:
                        if _ed(np.array(outer.centroid), np.array(inner.centroid)) < min:
                            outers[o] = i

        for current_inner in inners.keys():
            best_outer = inners[current_inner]
            if best_outer in outers and outers[best_outer] == current_inner: #reciprocal nearest
                matches.append([current_inner, best_outer])
                self.inner_lesion_area_props[current_inner].matches_with = str(self.outer_lesion_area_props[best_outer].label)
                self.outer_lesion_area_props[best_outer].matches_with = str(self.inner_lesion_area_props[current_inner].label)




    def _make_polygons_for_image(self, list_of_rprops ):
        """
        make overlay colour patches for the annotated output image
        :param list_of_rprops: ImageArea or subclass for which to make patches for
        :return: list of polygons
        """
        polys = []
        for rprop in list_of_rprops:
            coords = rprop.coords
            if len(coords) > 2: #need 3 points for a polygon
                p = np.asarray(coords)
                p.T[[0,1]] = p.T[[1,0]]
                p = Polygon(p)
                x, y = p.exterior.xy
                polys.append([x,y])
        return polys

    def write_annotated_sub_image(self):
        """
        create output annotated subimage jpeg with results overlay
        :return: None
        """
        size = self._calc_size(self.sub_i)
        fig = plt.figure(figsize=size)
        img = skimage.img_as_ubyte(color.hsv2rgb(self.sub_i))
        plt.imshow(img)
        brown = (165/255, 42/255, 42/255, 0.5)
        grey = (125/255, 125/255, 125/255, 0.5)
        green = (45/255, 90/255, 39/255, 0.5)
        healthy_polys = self._make_polygons_for_image(self.healthy_obj_props)
        outer_lesion_polys = self._make_polygons_for_image(self.outer_lesion_area_props)

        inner_lesion_polys = self._make_polygons_for_image(self.inner_lesion_area_props)

        for p in healthy_polys:
            plt.plot(p[0], p[1], color=green )

        for p in outer_lesion_polys:
            plt.plot(p[0], p[1], color=brown )

        for p in inner_lesion_polys:
            plt.plot(p[0], p[1], color=grey)

        ax = plt.gca()
        for p in self.outer_lesion_area_props:
            if p.passed:
                l = "outer: "  + str(p.label)
                ax.annotate(l, xy=tuple(reversed(p.centroid)), xycoords='data', color="white")
        for p in self.inner_lesion_area_props:
            if p.passed:
                l = "inner: " + str(p.label)
                ax.annotate(l, xy=tuple(reversed(p.centroid)), xycoords='data', color="white")

        h_patch = mpatches.Patch(color=green, label='Healthy')
        l_patch = mpatches.Patch(color=brown, label="Outer Lesion")
        c_patch = mpatches.Patch(color=grey, label="Inner Lesion")
        plt.legend(bbox_to_anchor=(1, 1), bbox_transform=plt.gcf().transFigure,handles=[h_patch,l_patch,c_patch],loc="upper right")
        plt.savefig(self.annot_imtag, dpi = 72, )
        plt.close(fig)

    def write_sub_image(self):
        """
        write out subimage (nonannotated)
        :return: None
        """
        io.imsave(self.imtag, skimage.img_as_ubyte(color.hsv2rgb(self.sub_i)))

    def _make_pandas(self, regions, area_type=None, image_file=None, sub_image_index = None):
        """
        makes a pandas dataframe of the results

        :param regions: ImageArea or subclass list
        :param area_type: type of the image_area
        :param image_file: the image the regions are derived from
        :param sub_image_index: the index of the subimage the regions are derived from
        :return: pandas.dataframe
        """
        nrow = len(regions)
        d = {}
        #d = {p: [rp[p] for rp in regions] for p in props}
        d['label'] = [r.label for r in regions]
        d['area_type'] = [area_type] * nrow
        d['matched_with'] = [r.matches_with for r in regions]
        d['passed'] = [r.passed for r in regions]
        d['pixels_in_area'] = [r.area for r in regions]
        d['scale'] =  [r.scale for r in regions]
        d['size'] = [r.size for r in regions]
        d['image_file'] = [image_file] * nrow
        d['sub_image_index'] = [sub_image_index] * nrow


        return pd.DataFrame(d)


    def get_results_dataframes(self, passed_only=False):
        """
        generates a pandas dataframe of results from the SubImage object
        :return: pandas.dataframe
        """


        outer_df = self._make_pandas(self.outer_lesion_area_props, area_type = "outer_lesion_area",
                                     image_file=self.parent_image_file, sub_image_index=self.index)
        inner_df = self._make_pandas(self.inner_lesion_area_props, area_type = "inner_lesion_area",
                                     image_file=self.parent_image_file, sub_image_index=self.index)

        if passed_only:
            inner_df = inner_df[inner_df["passed"]]
            outer_df = outer_df[outer_df["passed"]]

        return inner_df, outer_df





