import yaml


class FilterSettings:

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
            return (self)

    def __getitem__(self, item):
        return self.settings[item]

    # s = FilterSettings()
    # s.add_setting('health', h=(120, 120), s=(110, 110), v=(100, 100))
    # s.add_setting('whole_leaf', h=(120, 120), s=(110, 110), v=(100, 100))
    # s.write('test.yml')
    # d = s.read('test.yml')
    # print(d.settings)



