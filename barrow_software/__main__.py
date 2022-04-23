import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gio, Gtk

import sys
from barrow_software.dnf_manager import DnfManager
from barrow_software.software_item import SoftwareItem


@Gtk.Template.from_file("main_window.ui")
class AppWindow(Gtk.ApplicationWindow):
    __gtype_name__ = "MainWindow"

    header_revealer: Gtk.Revealer = Gtk.Template.Child()
    results_revealer: Gtk.Revealer = Gtk.Template.Child()
    search_box: Gtk.Entry = Gtk.Template.Child()
    stack: Gtk.Stack = Gtk.Template.Child()
    results_list: Gtk.ListBox = Gtk.Template.Child()
    back_button: Gtk.ListBox = Gtk.Template.Child()

    progress_reveal: Gtk.Revealer = Gtk.Template.Child()
    progress_label: Gtk.Label = Gtk.Template.Child()
    progress_bar: Gtk.ProgressBar = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super(Gtk.ApplicationWindow, self).__init__(**kwargs)
        self.maximize()
        self.back_button.set_sensitive(False)
        self.stack.set_visible_child_name("loader")
        self.manager: DnfManager = None
        self.current_item: SoftwareItem = None
        DnfManager.create_threaded(self.manager_ready)
    
    def manager_ready(self, manager):
        self.manager = manager
        self.stack.set_visible_child_name("search")
        

    @Gtk.Template.Callback()
    def do_search(self, *args):
        self.clear_search_results()
        self.manager.search_threaded(self.search_box.get_text(), self.add_result_set)

    def add_result_set(self, results):
        for result in results:
            self.results_list.add(result)
        self.header_revealer.set_reveal_child(False)
        self.results_revealer.set_reveal_child(True)

    @Gtk.Template.Callback()
    def on_search_box_changed(self, widget):
        self.clear_search_results()
        if(self.search_box.get_text() == ""):
            self.header_revealer.set_reveal_child(True)
            self.results_revealer.set_reveal_child(False)

    def clear_search_results(self):
        for child in self.results_list.get_children():
            self.results_list.remove(child)

    @Gtk.Template.Callback()
    def on_results_list_row_activated(self, widget, selection: Gtk.ListBoxRow):
        item = selection.get_child()
        self.show_details(item)

    app_name: Gtk.Label = Gtk.Template.Child()
    app_short_desc: Gtk.Label = Gtk.Template.Child()
    app_desc: Gtk.Label = Gtk.Template.Child()
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
            self.stack.set_visible_child_name("search")
            self.back_button.set_sensitive(False)

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

class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="nz.barrow.software",
                         flags=Gio.ApplicationFlags.FLAGS_NONE, **kwargs)
        self.window = None

    def do_activate(self):
        self.window = self.window or AppWindow(application=self)
        self.window.present()


if __name__ == '__main__':
    Application().run(sys.argv)