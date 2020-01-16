import yaml
import redpatch as rp

class FilterSettings(object):


    def __init__(self):
        self.settings = {}

    def add_setting(self, tag, h=(), s=(), v=()):
        self.settings[tag] = {'h': h, 's': s, 'v': v}

    def write(self, outfile):
        with open(outfile, "w") as file:
            yaml.dump(self.settings, file)

    def read(self, infile):
        with open(infile) as file:
            self.settings = yaml.load(file, Loader=yaml.FullLoader)
            return self

    def create_default_filter_file(self, file="default_filter.yml"):
        self.add_setting("leaf_area", h=rp.LEAF_AREA_HUE, s=rp.LEAF_AREA_SAT, v=rp.LEAF_AREA_VAL)
        self.add_setting("healthy_area", h=rp.HEALTHY_HUE, s=rp.HEALTHY_SAT, v=rp.HEALTHY_VAL)
        self.add_setting("lesion_area", h=rp.LESION_HUE, s=rp.LESION_SAT, v=rp.LESION_VAL)
        self.add_setting("lesion_centre", h=rp.LESION_CENTRE_HUE, s=rp.LESION_CENTRE_SAT, v=rp.LESION_CENTRE_VAL)
        self.add_setting("scale_card", h=rp.SCALE_CARD_HUE, s=rp.SCALE_CARD_SAT, v=rp.SCALE_CARD_VAL )
        self.write(file)

    def __getitem__(self, item):
        return self.settings[item]

    # s = FilterSettings()
    # s.add_setting('health', h=(120, 120), s=(110, 110), v=(100, 100))
    # s.add_setting('whole_leaf', h=(120, 120), s=(110, 110), v=(100, 100))
    # s.write('test.yml')
    # d = s.read('test.yml')
    # print(d.settings)


