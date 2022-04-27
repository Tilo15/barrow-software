from gi.repository import GLib, Adw, Gtk

import sys

class SoftwareFeatures:

    def __init__(self):
        self.is_libre = False
        self.is_nonfree = False
        self.is_trusted = False
        self.has_trackers = False
        self.uses_nonfree_services = False
        self.has_explicit_content = False
        self.is_featured = False
        self.is_peer_to_peer = False

    def has_antifeature(self):
        return self.is_nonfree or (not self.is_libre) or (not self.is_trusted) or self.has_trackers or self.uses_nonfree_services or self.has_explicit_content

    def set_free_from_licence_string(self, string):
        free_keywords = ["GPL", "MPL", "BSD", "MIT", "LGPL", "ASL", "AGPL", "OFL", "Unlicense", "CC-BY", "zlib", "PublicDomain", "Public Domain", "public domain"]
        self.is_libre = False
        self.is_nonfree = False
        if(string == "" or string == None):
            return
        
        for kw in free_keywords:
            if kw in string:
                print(kw, string)
                self.is_libre = True
                self.is_nonfree = False
                return

        if(string.lower() == "proprietary"):
            self.is_libre = False
            self.is_nonfree = True

@Gtk.Template.from_file("ui/software-item.ui")
class SoftwareItem(Gtk.Box):
    __gtype_name__ = "SoftwareItem"

    app_name: Gtk.Label = Gtk.Template.Child()
    app_short_desc: Gtk.Label = Gtk.Template.Child()
    app_icon: Gtk.Image = Gtk.Template.Child()
    antifeature_badge: Gtk.Revealer = Gtk.Template.Child()

    def __init__(self, name, short_description, long_description, package_name, size, licence, version, url, features: SoftwareFeatures, **kwargs):
        super(Gtk.Box, self).__init__(**kwargs)
        self.name = name
        self.short_desc = short_description
        self.long_description = long_description
        self.package_name = package_name
        self.features = features
        self.size = size
        self.licence = licence
        self.version = version
        self.url = url

        self.app_name.set_label(name)
        self.app_short_desc.set_label(short_description)
        self.antifeature_badge.set_reveal_child(self.features.has_antifeature())

    def set_icon_from_path(self, path):
        self.app_icon.set_from_file(path)
