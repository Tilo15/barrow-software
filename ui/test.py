
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import GLib, Gio, Gtk, Gdk, Adw

import sys


@Gtk.Template.from_file("window.ui")
class AppWindow(Adw.ApplicationWindow):
    __gtype_name__ = "MainWindow"


    def __init__(self, **kwargs):
        super(Gtk.ApplicationWindow, self).__init__(**kwargs)
    
 

class Application(Adw.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="nz.barrow.software",
                         flags=Gio.ApplicationFlags.FLAGS_NONE, **kwargs)
        self.window = None

    def do_activate(self):
        self.window = self.window or AppWindow(application=self)
        self.window.present()


if __name__ == '__main__':
    Application().run(sys.argv)