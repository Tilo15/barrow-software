import threading
from time import time
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import GLib, Gio, Gtk, Gdk, Adw

import sys
import time
from barrow_software.dnf_manager import DnfManager
from barrow_software.appstream_manager import AppStreamManager
from barrow_software.category import Category


@Gtk.Template.from_file("ui/window.ui")
class AppWindow(Adw.ApplicationWindow):
    __gtype_name__ = "MainWindow"

    stack: Gtk.Stack = Gtk.Template.Child()
    app_loader: Gtk.Box = Gtk.Template.Child()
    loading_label: Gtk.Label = Gtk.Template.Child()
    category_list: Gtk.ListBox = Gtk.Template.Child()

    leaflet: Adw.Leaflet = Gtk.Template.Child()
    search_page: Gtk.Box = Gtk.Template.Child()
    results_page: Gtk.Box = Gtk.Template.Child()

    result_title: Gtk.Label = Gtk.Template.Child()
    result_subtitle: Gtk.Label = Gtk.Template.Child()
    result_icon: Gtk.Image = Gtk.Template.Child()
    results: Gtk.FlowBox = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super(Gtk.ApplicationWindow, self).__init__(**kwargs)
        # self.back_button.set_sensitive(False)
        self.stack.set_visible_child(self.app_loader)
        self.manager: DnfManager = None
        self.appstream: AppStreamManager = None
        # self.current_item: SoftwareItem = None
        self.loading_label.set_text("Loading package manager data…")
        self.back_to = "search"
        DnfManager.create_threaded(self.dnf_manager_ready)
    
    def dnf_manager_ready(self, manager):
        self.manager = manager
        self.loading_label.set_text("Loading AppStream data…")
        AppStreamManager.create_threaded(self.manager, self.appstream_manager_ready)

    def appstream_manager_ready(self, appstream):
        self.appstream: AppStreamManager = appstream
        categories = self.appstream.get_categories()
        for category in categories:
            self.category_list.insert(category, -1)

        self.stack.set_visible_child(self.leaflet)

    @Gtk.Template.Callback()
    def go_back(self, widget):
        self.leaflet.navigate(Adw.NavigationDirection.BACK)

    @Gtk.Template.Callback()
    def category_selected(self, widget, child):
        self.show_category(child.get_child())
    
    def show_category(self, category: Category):
        self.result_title.set_label(category.name)
        self.result_subtitle.set_label("{} items in this category".format(len(category.components)))
        self.result_icon.set_from_icon_name(category.icon_name)

        while True:
            child = self.results.get_first_child()
            if(child == None):
                break
            self.results.remove(child)

        def batch(components):
            b = []
            for c in components:
                b.append(self.appstream.component_to_item(c))
                if(len(b) == 20):
                    GLib.idle_add(self.add_category_item_batch, b)
                    b = []
            GLib.idle_add(self.add_category_item_batch, b)
                
        self.leaflet.set_visible_child(self.results_page)
        self.back_to = "category"

        threading.Thread(target=batch, args=(category.components,)).start()

    def add_category_item_batch(self, batch):
        for app in batch:
            if(app == None):
                continue
            self.results.insert(app, -1)


class Application(Adw.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="nz.barrow.software",
                         flags=Gio.ApplicationFlags.FLAGS_NONE, **kwargs)
        self.window = None

    def do_activate(self):
        style_provider = Gtk.CssProvider()
        style_provider.load_from_path("style.css")

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.window = self.window or AppWindow(application=self)
        self.window.present()


if __name__ == '__main__':
    Application().run(sys.argv)