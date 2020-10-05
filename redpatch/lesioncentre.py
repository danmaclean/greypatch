from skimage import measure
import redpatch as rp
import numpy as np

class LesionCentre(object):
    """represents a LesionCentre object.
    uses RegionProp and parent RegionProp and leaf RegionProp 
    """
    def __init__(self, 
    rprop: measure._regionprops._RegionProperties = None, 
    parent_rprop: measure._regionprops._RegionProperties = None,
    scale: float = None,
    scale_in_cm: bool = False,
    max_ratio: float = None,
    minimum_size: float = None,
    prop_across_parent: float = None
    ):
        for attr_name in dir(rprop):
            if not attr_name.startswith("_"):
                val = getattr(rprop, attr_name)
                setattr(self, attr_name, val)
        self.parent_label = parent_rprop.label
        try:
            self.long_axis_to_short_axis_ratio = self.major_axis_length / self.minor_axis_length
        except ZeroDivisionError:
            self.long_axis_to_short_axis_ratio = float('inf')

        self.offset_to_parent = self.calc_offset_to_parent(parent_rprop)

        self.corrected_bbox = self.correct_bbox(parent_rprop)
        self.corrected_coords = self.correct_coords(parent_rprop)
        self.corrected_centroid = self.correct_centroids(parent_rprop)
        self.prop_across_parent = self.prop_across_parent(parent_rprop) 
        self.size = self.area

        if (scale_in_cm):
            #print("doing reals area")
            self.size = rp.circular_area_to_pixel_volume(self.area, scale)
            #print(self.area, scale, self.size)
            #self.distance_to_margin = self.distance_to_margin / scale 
        self.passed = self.passes(max_ratio = max_ratio, minimum_size = minimum_size, prop_across_parent = prop_across_parent)


    def correct_bbox(self, parent_rprop):
        return [int(x) + int(y) for x, y in zip(parent_rprop.bbox, self.bbox)]

    def calc_offset_to_parent(self, parent_rprop):
        offsets = parent_rprop.bbox[0:2]
        return offsets

    def correct_coords(self, parent_rprop):
        p = np.asarray(self.coords)
        min_row, min_col, _, _ = parent_rprop.bbox
        return np.add(p, [min_row, min_col])

    def correct_centroids(self, parent_rprop):
        #print("___correct centroids___")
        #print(self.centroid)
        #print(parent_rprop.centroid)
        res = (self.centroid[0] + self.offset_to_parent[0], self.centroid[1] + self.offset_to_parent[1])
        #print(res)
        return res

    def prop_across_parent(self, parent_rprop):
        #if not self.label == 100:
            #return 0
        #print("__dist to margin__")
        # returns distance to nearest margin in pixels
        #row that the lesion centre centroid is in
        #print(self.centroid)
        #print(self.corrected_centroid)
        #print(leaf_rprop.centroid)
        try:
            row_needed = int(self.centroid[0])
         #   print("row to get", row_needed)

            row = list(parent_rprop.image[row_needed, :])
          #  print("row_length =",len(row))
            col = list(parent_rprop.image[:, row_needed])
          #  print("col_length =", len(col))
        except IndexError: #if due to rounding of corrected value index is out of bounds
            #print("did exception")
            min_row, _, max_row, _ = parent_rprop.bbox
            row = [True] * (max_row - min_row)
        #print(row)
        #first and last column of pixels in the leaf in that row
        left_leaf_margin = row.index(1)
        #print("left_margin", left_leaf_margin)
        try:
            right_leaf_margin = row[left_leaf_margin:].index(0) + left_leaf_margin
        except ValueError:
            right_leaf_margin = len(row) - 1
        #print("right margin", right_leaf_margin)
        #col that the lesion centre centroid is in 
        col = self.centroid[1]
        #print(col)
        dist_to_left = abs(left_leaf_margin - col)
        #print("dist to left",  dist_to_left)
        dist_to_right = abs(right_leaf_margin - col)
        #print("dist_to_right",dist_to_right )
        res = min( [dist_to_left, dist_to_right] )
        prop_across_parent = res / len(row)
        #print(res)
        #print(prop_across_parent)
        return prop_across_parent

        

    def __getitem__(self, item):
        return getattr(self, item)

    def passes(self, max_ratio = None, minimum_size = None, prop_across_parent = None):
        length_pass = self.long_axis_to_short_axis_ratio <= max_ratio
        size_pass = self.size >= minimum_size
        distance_pass = self.prop_across_parent >= prop_across_parent
        if length_pass and size_pass and distance_pass:
            return True
        else:
            return False


