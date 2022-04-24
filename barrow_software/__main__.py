import threading
from time import time
import gi

from barrow_software.category import Category
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gio, Gtk, Gdk

import sys
import time
from barrow_software.dnf_manager import DnfManager
from barrow_software.appstream_manager import AppStreamManager
from barrow_software.software_item import SoftwareItem
from barrow_software.human_bytes import HumanBytes


@Gtk.Template.from_file("main_window.ui")
class AppWindow(Gtk.ApplicationWindow):
    __gtype_name__ = "MainWindow"

    header_revealer: Gtk.Revealer = Gtk.Template.Child()
    search_icon_revealer: Gtk.Revealer = Gtk.Template.Child()
    search_stack: Gtk.Stack = Gtk.Template.Child()
    search_box: Gtk.Entry = Gtk.Template.Child()
    stack: Gtk.Stack = Gtk.Template.Child()
    results_list: Gtk.ListBox = Gtk.Template.Child()
    back_button: Gtk.ListBox = Gtk.Template.Child()
    loading_label: Gtk.Label = Gtk.Template.Child()

    category_flow: Gtk.FlowBox = Gtk.Template.Child()

    app_radio: Gtk.RadioButton = Gtk.Template.Child()
    package_radio: Gtk.RadioButton = Gtk.Template.Child()
    search_revealer: Gtk.Revealer = Gtk.Template.Child()

    progress_reveal: Gtk.Revealer = Gtk.Template.Child()
    progress_label: Gtk.Label = Gtk.Template.Child()
    progress_bar: Gtk.ProgressBar = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super(Gtk.ApplicationWindow, self).__init__(**kwargs)
        self.maximize()
        self.back_button.set_sensitive(False)
        self.stack.set_visible_child_name("loader")
        self.manager: DnfManager = None
        self.appstream: AppStreamManager = None
        self.current_item: SoftwareItem = None
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
            self.category_flow.add(category)
            category.connect("clicked", self.show_category)

        self.stack.set_visible_child_name("search")

    @Gtk.Template.Callback()
    def do_search(self, *args):
        self.clear_search_results()
        if(self.app_radio.get_active()):
            self.appstream.search_threaded(self.search_box.get_text(), self.add_result_set)

        if(self.package_radio.get_active()):
            self.manager.search_threaded(self.search_box.get_text(), self.add_result_set)

    def add_result_set(self, results):
        for result in results:
            self.results_list.add(result)
        self.header_revealer.set_reveal_child(False)
        self.search_icon_revealer.set_reveal_child(True)
        self.search_stack.set_visible_child_name("results")
        self.back_to = "search"
        self.back_button.set_sensitive(True)

    @Gtk.Template.Callback()
    def on_search_box_changed(self, widget):
        self.clear_search_results()
        if(self.search_box.get_text() == ""):
            self.header_revealer.set_reveal_child(True)
            self.search_icon_revealer.set_reveal_child(False)
            self.search_stack.set_visible_child_name("front")
            self.back_button.set_sensitive(False)

    def clear_search_results(self):
        for child in self.results_list.get_children():
            self.results_list.remove(child)

    @Gtk.Template.Callback()
    def on_results_list_row_activated(self, widget, selection: Gtk.ListBoxRow):
        item = selection.get_child()
        self.show_details(item)

    @Gtk.Template.Callback()
    def on_results_scroll(self, widget, event: Gdk.EventScroll):
        direction = event.get_scroll_deltas()
        if(direction.delta_y < 0):
            self.search_revealer.set_reveal_child(True)
        if(direction.delta_y > 0):
            self.search_revealer.set_reveal_child(False)

    @Gtk.Template.Callback()
    def on_categories_scroll(self, widget, event: Gdk.EventScroll):
        direction = event.get_scroll_deltas()
        if(direction.delta_y < 0):
            self.search_revealer.set_reveal_child(True)
            self.header_revealer.set_reveal_child(True)
        if(direction.delta_y > 0):
            self.search_revealer.set_reveal_child(False)
            self.header_revealer.set_reveal_child(False)

    app_name: Gtk.Label = Gtk.Template.Child()
    app_short_desc: Gtk.Label = Gtk.Template.Child()
    app_desc: Gtk.Label = Gtk.Template.Child()
    app_licence: Gtk.Label = Gtk.Template.Child()
    app_version: Gtk.Label = Gtk.Template.Child()
    app_website: Gtk.Label = Gtk.Template.Child()
    app_size: Gtk.Label = Gtk.Template.Child()
    app_icon: Gtk.Image = Gtk.Template.Child()
    install_revealer: Gtk.Revealer = Gtk.Template.Child()
    remove_revealer: Gtk.Revealer = Gtk.Template.Child()

    nonfree_badge: Gtk.Revealer = Gtk.Template.Child()
    trackers_badge: Gtk.Revealer = Gtk.Template.Child()
    p2p_badge: Gtk.Revealer = Gtk.Template.Child()
    thirdparty_badge: Gtk.Revealer = Gtk.Template.Child()
    nonfree_network_badge: Gtk.Revealer = Gtk.Template.Child()
    trusted_badge: Gtk.Revealer = Gtk.Template.Child()
    nsfw_badge: Gtk.Revealer = Gtk.Template.Child()
    foss_badge: Gtk.Revealer = Gtk.Template.Child()
    unknown_licence_badge: Gtk.Revealer = Gtk.Template.Child()
    featured_badge: Gtk.Revealer = Gtk.Template.Child()

    def show_details(self, item: SoftwareItem):
        self.back_button.set_sensitive(True)
        self.current_item = item
        self.app_name.set_label(item.name)
        self.app_short_desc.set_label(item.short_desc)
        self.app_desc.set_label(item.long_description)
        self.app_licence.set_label(item.licence)
        self.app_website.set_label("<a href=\"{}\">{}</a>".format(item.url, item.url))
        self.app_version.set_label(item.version)
        self.app_size.set_label(HumanBytes.format(item.size))
        self.app_icon.set_from_pixbuf(item.app_icon.get_pixbuf())
        installed = self.manager.query_installed(item.package_name)
        self.remove_revealer.set_reveal_child(installed)
        self.install_revealer.set_reveal_child(not installed)
        
        self.nonfree_badge.set_reveal_child(item.features.is_nonfree)
        self.trackers_badge.set_reveal_child(item.features.has_trackers)
        self.p2p_badge.set_reveal_child(item.features.is_peer_to_peer)
        self.thirdparty_badge.set_reveal_child(not item.features.is_trusted)
        self.nonfree_network_badge.set_reveal_child(item.features.uses_nonfree_services)
        self.trusted_badge.set_reveal_child(item.features.is_trusted)
        self.nsfw_badge.set_reveal_child(item.features.has_explicit_content)
        self.foss_badge.set_reveal_child(item.features.is_libre)
        self.unknown_licence_badge.set_reveal_child((not item.features.is_nonfree) and (not item.features.is_libre))
        self.featured_badge.set_reveal_child(item.features.is_featured)

        self.stack.set_visible_child_name("details")

    @Gtk.Template.Callback()
    def go_back(self, widget):
        if self.stack.get_visible_child_name() == "details":
            self.stack.set_visible_child_name(self.back_to)
            return

        if self.search_stack.get_visible_child_name() == "results":
            self.search_box.set_text("")
            self.back_button.set_sensitive(False)
            return

        if self.stack.get_visible_child_name() == "category":
            self.stack.set_visible_child_name("search")
            return


    @Gtk.Template.Callback()
    def do_install(self, widget):
        self.back_button.set_sensitive(False)
        self.manager.install_package_threaded(self.current_item.package_name, self.update_progress, self.operation_complete, None)

    @Gtk.Template.Callback()
    def do_remove(self, widget):
        self.back_button.set_sensitive(False)
        self.manager.remove_package_threaded(self.current_item.package_name, self.update_progress, self.operation_complete, None)

    def update_progress(self, frac, message):
        self.remove_revealer.set_reveal_child(False)
        self.install_revealer.set_reveal_child(False)
        self.progress_reveal.set_reveal_child(True)
        self.progress_label.set_label(message)
        self.progress_bar.set_fraction(frac)

    def operation_complete(self):
        self.back_button.set_sensitive(True)
        self.progress_reveal.set_reveal_child(False)
        installed = self.manager.query_installed(self.current_item.package_name)
        self.remove_revealer.set_reveal_child(installed)
        self.install_revealer.set_reveal_child(not installed)

    category_app_list: Gtk.ListBox = Gtk.Template.Child()
    category_name: Gtk.Label = Gtk.Template.Child()
    category_count: Gtk.Label = Gtk.Template.Child()
    category_icon: Gtk.Image = Gtk.Template.Child()
    category_header_revealer: Gtk.Revealer = Gtk.Template.Child()

    def show_category(self, category: Category):
        self.category_name.set_label(category.name)
        self.category_count.set_label("{} items in this category".format(len(category.components)))
        self.category_icon.set_from_icon_name(category.icon_name, 64)
        self.category_header_revealer.set_reveal_child(True)

        for child in self.category_app_list.get_children():
            self.category_app_list.remove(child)

        def batch(components):
            b = []
            for c in components:
                b.append(self.appstream.component_to_item(c))
                if(len(b) == 20):
                    GLib.idle_add(self.add_category_item_batch, b)
                    b = []
            GLib.idle_add(self.add_category_item_batch, b)
                
        self.stack.set_visible_child_name("category")
        self.back_button.set_sensitive(True)
        self.back_to = "category"

        threading.Thread(target=batch, args=(category.components,)).start()

    def add_category_item_batch(self, batch):
        for app in batch:
            if(app == None):
                continue
            self.category_app_list.add(app)

    @Gtk.Template.Callback()
    def on_category_list_scroll(self, widget, event: Gdk.EventScroll):
        direction = event.get_scroll_deltas()
        if(direction.delta_y < 0):
            self.category_header_revealer.set_reveal_child(True)
        if(direction.delta_y > 0):
            self.category_header_revealer.set_reveal_child(False)


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="nz.barrow.software",
                         flags=Gio.ApplicationFlags.FLAGS_NONE, **kwargs)
        self.window = None

    def do_activate(self):
        style_provider = Gtk.CssProvider()
        style_provider.load_from_path("style.css")

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.window = self.window or AppWindow(application=self)
        self.window.present()


if __name__ == '__main__':
    Application().run(sys.argv)