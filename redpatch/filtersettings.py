"""
filtersettings

A module for creating filter settings for redpatch experiments


Workflow Overview
-----------------

1. Create empty object
2. Add threshold settings for selecting different parts of the image
3. Write settings to file for re-use

Basic Usage
-----------

1. Import module, create empty object

    .. highlight:: python
    .. code-block:: python

        import redpatch as rp
        fs = rp.FilterSettings()

2. Add some settings

    .. highlight:: python
    .. code-block:: python

        fs.add_setting("leaf_area", h=(0.1, 1.0), s=(0.3, 0.6), v=(0.4, 0.6) )

3. Access a setting by name

    .. highlight:: python
    .. code-block:: python

        fs.settings["leaf_area"]["h"]

3. Write settings to a file

    .. highlight:: python
    .. code-block:: python

        fs.write("my_settings.yaml")

4. Read in settings from a file

    .. highlight:: python
    .. code-block:: python

        fs = rp.FilterSettings()
        settings = fs.read("/some/file/settings.yaml")

5. Create a default filter settings file

    .. highlight:: python
    .. code-block:: python

        fs = rp.FilterSettings()
        fs.create_default_filter_file("/some/folder/settings.yaml")



"""

import yaml
from typing import Tuple
import redpatch as rp

class FilterSettings(object):
    """
    class representing groups of filter settings for different aspects of the image
    """

    def __init__(self):
        self.settings = {}

    def add_setting(self, tag: str, h: Tuple[float, float] = (), s: Tuple[float, float] = (),
                    v: Tuple[float, float] = () ) -> None:
        """
        add a setting to the object
    
        :param: tag str -- the name of the setting
        :param: h Tuple -- a 2-tuple of Hue thresholds (lower, upper)
        :param: s Tuple -- a 2-tuple of Saturation thresholds (lower, upper)
        :param: v Tuple -- a 2-tuple of Value thresholds (lower, upper)
        :return: None
        """

        self.settings[tag] = {'h': h, 's': s, 'v': v}

    def write(self, outfile: str) -> None:
        """
        write the settings to a yaml file

        :param: file str -- name of the file to write
        :return: None
        """

        with open(outfile, "w") as file:
            yaml.dump(self.settings, file)

    def read(self, infile: str) -> None:
        """

        :param: infile str -- name of the file to read
        :return: None
        """
        with open(infile) as file:
            self.settings = yaml.load(file, Loader=yaml.FullLoader)
            return self

    def create_default_filter_file(self, file: str = "default_filter.yml") -> None:
        """
        write a file containing the default filter settings
        :param file str -- name of the file to write:
        :return: None
        """
        self.add_setting("leaf_area", h=rp.LEAF_AREA_HUE, s=rp.LEAF_AREA_SAT, v=rp.LEAF_AREA_VAL)
        self.add_setting("healthy_area", h=rp.HEALTHY_HUE, s=rp.HEALTHY_SAT, v=rp.HEALTHY_VAL)
        self.add_setting("lesion_area", h=rp.LESION_HUE, s=rp.LESION_SAT, v=rp.LESION_VAL)
#        self.add_setting("lesion_centre", h=rp.LESION_CENTRE_HUE, s=rp.LESION_CENTRE_SAT, v=rp.LESION_CENTRE_VAL)
        self.add_setting("scale_card", h=rp.SCALE_CARD_HUE, s=rp.SCALE_CARD_SAT, v=rp.SCALE_CARD_VAL )
        self.write(file)

    def __getitem__(self, item):
        return self.settings[item]




