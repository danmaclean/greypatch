import os
import ipywidgets as widgets
from pathlib import Path


class FileBrowser(object):
    """ Implements an ipywidgets file chooser.
    >>> f = FileBrowser()
    >>> f.widget() # activate the widget
    >>> ...
    >>> f.path # get the selected file...
    """

    def __init__(self):
        self.path = str(Path.home())
        self._update_files()

    def _update_files(self):
        self.files = list()
        self.dirs = list()
        if os.path.isdir(self.path):
            for f in os.listdir(self.path):
                ff = self.path + "/" + f
                if os.path.isdir(ff) and f[0] != '.':
                    self.dirs.append(f)
                else:
                    if not f.startswith((".", "$", "~")):
                        self.files.append(f)

    def widget(self):
        box = widgets.VBox()
        self._update(box)
        return box

    def _update(self, box):

        def on_click(b):
            if b.description == 'up one level':
                self.path = os.path.split(self.path)[0]
            else:
                self.path = self.path + "/" + b.description
            self._update_files()
            self._update(box)

        buttons = []
        # if self.files:
        button = widgets.Button(description='up one level', background_color='#aaaaaa')
        button.on_click(on_click)
        buttons.append(button)
        for f in sorted(self.dirs):
            button = widgets.Button(description=f)
            button.style.button_color = 'lightgreen'
            button.on_click(on_click)
            buttons.append(button)
        for f in sorted(self.files):
            button = widgets.Button(description=f, background_color='#ff0000')
            button.style.button_color = 'lightblue'
            button.on_click(on_click)
            buttons.append(button)
        box.children = tuple([widgets.HTML("You have selected: %s" % (self.path,))] + buttons)

