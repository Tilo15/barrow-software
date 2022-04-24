from re import L
import threading
from barrow_software.software_item import *
from barrow_software.category import *
from barrow_software.dnf_manager import DnfManager

class AppStreamManager:

    @staticmethod
    def create_threaded(dnf_manager, callback):
        def create():
            manager = AppStreamManager(dnf_manager)
            GLib.idle_add(lambda: callback(manager))
        threading.Thread(target=create).start()

    def __init__(self, dnf_manager: DnfManager):
        from gi.repository import AppStream
        self.pool = AppStream.Pool()
        self.pool.load()
        self.manager = dnf_manager
        self.categories = AppStream.get_default_categories(True)
        self.components = self.pool.get_components()
        AppStream.utils_sort_components_into_categories(self.components, self.categories, True)

    def search(self, query):
        results = self.pool.search(query)
        results = (x for x in results if x.get_pkgname() != None)
        results = (self.component_to_item(x) for x in results)
        results = (x for x in results if x != None)

        # Return in batches of 10
        batch = []
        for result in results:
            batch.append(result)
            if(len(batch) == 10):
                yield batch
                batch = []
        yield batch
        
    def component_to_item(self, component):
        features = SoftwareFeatures()
        features.is_trusted = True
        if(component.get_pkgname() == None):
            return None

        pkg = self.manager.get_package(component.get_pkgname())
        if(pkg == None):
            return None
        
        features.set_free_from_licence_string(component.get_project_license())
        desc = component.get_description() or ""
        desc = desc.replace("<p>", "").replace("</p>", "\n")
        desc = desc.replace("<ul>", "").replace("<li>", "‣ ").replace("</li>", "\n").replace("</ul>", "")
        item = SoftwareItem(component.get_name(), component.get_summary(), desc, component.get_pkgname(), pkg.downloadsize, component.get_project_license(), pkg.version, pkg.url, features)

        icon = component.get_icon_by_size(64, 64)
        if(icon != None):
            item.set_icon_from_path(icon.get_filename())

        return item
            
    def search_threaded(self, query, callback):
        def _search():
            for result in self.search(query):
                GLib.idle_add(lambda: callback(result))
        threading.Thread(target=_search).start()

    def get_categories(self):
        return [Category(x.get_name(), x.get_icon(), x.get_components()) for x in self.categories]

