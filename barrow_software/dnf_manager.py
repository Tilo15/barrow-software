import threading
import html
import time
from barrow_software.software_item import *

class DnfManager:

    @staticmethod
    def create_threaded(callback):
        def create():
            manager = DnfManager()
            GLib.idle_add(lambda: callback(manager))
        threading.Thread(target=create).start()

    def __init__(self):
        import dnf
        self.base = dnf.Base()
        self.base.read_all_repos()
        self.base.fill_sack()

    def search(self, query):
        q = self.base.sack.query()
        q = q.available().latest()
        terms = query.split(" ")
        for t in query.split(" "):
            terms.append(t.lower())

        r1 = q.filter(name=terms)
        yield [self.__create_item_from_package(x) for x in r1]

        r2 = q.filter(file=terms).difference(r1)
        yield [self.__create_item_from_package(x) for x in r2]

        r3 = q.filter(name__substr=terms).difference(r1).difference(r2)
        yield [self.__create_item_from_package(x) for x in r3]
        
            
    def __create_item_from_package(self, pkg):
        features = SoftwareFeatures()
        features.is_trusted = True
        features.set_free_from_licence_string(pkg.license)
        desc = pkg.description
        return SoftwareItem("{} {}".format(pkg.name, pkg.version), pkg.summary, html.escape(desc), pkg.name, pkg.downloadsize, pkg.license, pkg.version, pkg.url, features)

    def __get_action_strings(self):
        import dnf.callback
        return {
            dnf.callback.PKG_INSTALL: "Installing",
            dnf.callback.PKG_CLEANUP: "Cleaning up",
            dnf.callback.PKG_DOWNGRADE: "Downgrading",
            dnf.callback.PKG_DOWNGRADED: "Downgraded",
            dnf.callback.PKG_ERASE: "Erasing",
            dnf.callback.PKG_OBSOLETE: "Obsoleting",
            dnf.callback.PKG_OBSOLETED: "Obsoleted",
            dnf.callback.PKG_REINSTALL: "Reinstalling",
            dnf.callback.PKG_REINSTALLED: "Reinstalled",
            dnf.callback.PKG_REMOVE: "Removing",
            dnf.callback.PKG_SCRIPTLET: "Running scriptlet for",
            dnf.callback.PKG_UPGRADE: "Upgrading",
            dnf.callback.PKG_UPGRADED: "Upgraded",
            dnf.callback.PKG_VERIFY: "Verifying"
        }

    def __get_progress_handler(self, callback, offset, segments):
        import dnf.callback
        action_strings = self.__get_action_strings()
        class InstallProgressHandler(dnf.callback.TransactionProgress):
            def __init__(self):
                self.last_cb = 0
                super().__init__()

            def progress(self, package, action, ti_done, ti_total, ts_done, ts_total):
                cb_time = time.time()
                if(cb_time < self.last_cb + 0.01):
                    return
                self.last_cb = cb_time
                print(package, action, ti_done, ti_total, ts_done, ts_total)
                frac = (float(ts_done-1) + (float(ti_done) / float(ti_total))) / float(ts_total)
                if action == dnf.callback.PKG_VERIFY:
                    frac = 1
                    
                callback(offset + frac/segments, "{} package '{}'…".format(action_strings[action], package))
        return InstallProgressHandler()


    def search_threaded(self, query, callback):
        def _search():
            for result in self.search(query):
                GLib.idle_add(lambda: callback(result))
        threading.Thread(target=_search).start()


    def install_package(self, package, progress_cb, complete_cb, failure_cb):
        import dnf.callback
        progress_cb(0.0, "Resolving transaction…")
        self.base.install(package)
        self.base.resolve()

        class DownloadProgressHandler(dnf.callback.DownloadProgress):
            def __init__(self):
                self.last_cb = 0
                super().__init__()

            def start(self, total_files, total_size, total_drpms=0):
                self.tsize = total_size
                self.tprogress = 0.0
                self.files = {}

            def progress(self, payload, done):
                cb_time = time.time()
                if(cb_time < self.last_cb + 0.1):
                    return
                self.last_cb = cb_time

                if(str(payload) not in self.files):
                    self.files[str(payload)] = 0
                
                self.files[str(payload)] = done
                total = sum(self.files.values())

                self.tprogress = total / self.tsize
                progress_cb(self.tprogress / 2.0, "Downloading package '{}'…".format(payload))

        self.base.download_packages(self.base.transaction.install_set, DownloadProgressHandler())
        progress_cb(0.5, "Preparing to install…")

        self.base.do_transaction(self.__get_progress_handler(progress_cb, 0.5, 2.0))

        self.__init__()
        complete_cb()

    def remove_package(self, package, progress_cb, complete_cb, failure_cb):
        progress_cb(0.0, "Resolving transaction…")
        self.base.remove(package)
        self.base.resolve()
        self.base.do_transaction(self.__get_progress_handler(progress_cb, 0.0, 1.0))
        self.__init__()
        complete_cb()


    def install_package_threaded(self, package, progress_cb, complete_cb, failure_cb):
        def _pcb(*args):
            GLib.idle_add(lambda: progress_cb(*args))
        def _ccb(*args):
                GLib.idle_add(lambda: complete_cb(*args))
        def _fcb(*args):
                GLib.idle_add(lambda: failure_cb(*args))

        threading.Thread(target=self.install_package, args=(package, _pcb, _ccb, _fcb)).start()

    def remove_package_threaded(self, package, progress_cb, complete_cb, failure_cb):
        def _pcb(*args):
            GLib.idle_add(lambda: progress_cb(*args))
        def _ccb(*args):
                GLib.idle_add(lambda: complete_cb(*args))
        def _fcb(*args):
                GLib.idle_add(lambda: failure_cb(*args))

        threading.Thread(target=self.remove_package, args=(package, _pcb, _ccb, _fcb)).start()

        

    def query_installed(self, package_name):
        q = self.base.sack.query()
        q = q.installed()
        r = q.filter(name=package_name)
        for a in r:
            return True
        return False
            

# base.install_specs(['gimp'])
# print("Resolving transaction...",)
# base.resolve()
# print("Downloading packages...")
# progress = dnf.cli.progress.MultiFileProgressMeter()
# base.download_packages(base.transaction.install_set, progress)
# print("Installing...")
# base.do_transaction()