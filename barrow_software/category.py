from unicodedata import category
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gio, Gtk

import sys

@Gtk.Template.from_file("category.ui")
class Category(Gtk.Button):
    __gtype_name__ = "Category"

    category_name: Gtk.Label = Gtk.Template.Child()
    category_description: Gtk.Label = Gtk.Template.Child()
    category_icon: Gtk.Image = Gtk.Template.Child()

    def __init__(self, name, icon, components, **kwargs):
        super(Gtk.Button, self).__init__(**kwargs)
        self.name = name
        self.description = "{} items".format(len(components))
        self.components = components
        self.category_name.set_label(name)
        self.category_description.set_label(self.description)
        self.icon_name = icon
        if(icon != None):
            print(icon)
            self.category_icon.set_from_icon_name(icon, 32)
