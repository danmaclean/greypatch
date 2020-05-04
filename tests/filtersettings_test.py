import pytest
import redpatch as rp



def test_add_filter_settings():
    fs = rp.FilterSettings()
    h = (0.1, 0.2)
    s = (0.3, 0.4)
    v = (0.5, 0.6)
    fs.add_setting("my_setting", h=h, s=s, v=v)
    assert fs.settings["my_setting"]["h"] == h
    assert fs.settings["my_setting"]["s"] == s
    assert fs.settings["my_setting"]["v"] == v


