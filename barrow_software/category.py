from unicodedata import category
from gi.repository import GLib, Gio, Gtk

import sys

@Gtk.Template.from_file("ui/category-item.ui")
class Category(Gtk.Box):
    __gtype_name__ = "CategoryItem"

    title: Gtk.Label = Gtk.Template.Child()
    subtitle: Gtk.Label = Gtk.Template.Child()
    icon: Gtk.Image = Gtk.Template.Child()

    def __init__(self, name, icon, components, **kwargs):
        super(Gtk.Box, self).__init__(**kwargs)
        self.name = name
        self.description = "{} items".format(len(components))
        self.components = components
        self.title.set_label(name)
        self.subtitle.set_label(self.description)
        self.icon_name = icon
        if(icon != None):
            print(icon)
            self.icon.set_from_icon_name(icon)
