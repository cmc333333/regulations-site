import codecs
import os
import shutil
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.staticfiles.finders import get_finders
from django.contrib.staticfiles.storage import StaticFilesStorage

import regulations


"""
This command compiles the frontend for regulations-site after using the Django
``collectstatic`` command to override specific files, and places the output in
a directory named ``compiled`` at the root level of the project.

For example, the atf-eregs project uses ``regulations-site`` as a library and
overrides the contents of the
``regulations/static/regulations/css/less/mixins.less`` file. The
``atf_eregs/regulations/static/regulations/css/less/mixins.less`` file will be
copied over the base file from ``regulations-site`` and put into a build
directory by ``collectstatic``, and then the frontend build commands are run,
and the results are copied into ``compiled``, which can then be used as the
static directory for the CSS, font, JavaScript, and image assets.

"""


class Command(BaseCommand):
    help = 'Build the frontend, including local overrides.'
    BUILD_DIR = "./frontend_build"
    TARGET_DIR = "./compiled/regulations"

    def find_regulations_directory(self):
        child = regulations.__file__
        child_dir = os.path.split(child)[0]
        return os.path.split(child_dir)[0] or "."   # if regulations is local

    def remove_dirs(self):
        """Remove existing output dirs"""
        if os.path.exists(self.TARGET_DIR):
            shutil.rmtree(self.TARGET_DIR)
        # Delete everything in BUILD_DIR except node_modules, which we use for
        # caching the downloaded node libraries
        if os.path.exists(self.BUILD_DIR):
            for file_name in os.listdir(self.BUILD_DIR):
                with_path = os.path.join(self.BUILD_DIR, file_name)
                if os.path.isfile(with_path):
                    os.remove(with_path)
                elif file_name != 'node_modules':
                    shutil.rmtree(with_path)
        else:
            os.mkdir(self.BUILD_DIR)

    def copy_configs(self):
        """Copy over configs from regulations"""
        regulations_directory = self.find_regulations_directory()
        frontend_files = (
            "package.json",
            "bower.json",
            "Gruntfile.js",
            ".eslintrc"
        )
        for f_file in frontend_files:
            source = "%s/%s" % (regulations_directory, f_file)
            shutil.copy(source, "%s/" % self.BUILD_DIR)
        with codecs.open("%s/config.json" % self.BUILD_DIR, "w",
                         encoding="utf-8") as f:
            f.write('{"frontEndPath": "static/regulations"}')

    def _input_files(self):
        """Fetch all of the static files from the installed apps. Yield them
        as pairs of (path, file)"""
        files_seen = set()
        pairs = (pr for finder in get_finders() for pr in finder.list([".*"]))
        for path, storage in pairs:
            # Prefix the relative path if the source storage contains it
            if getattr(storage, 'prefix', None):
                prefixed_path = os.path.join(storage.prefix, path)
            else:
                prefixed_path = path

            if prefixed_path in files_seen:
                self.stdout.write(
                    "Using override for {}\n".format(prefixed_path))
            else:
                files_seen.add(prefixed_path)
                with storage.open(path) as source_file:
                    yield (prefixed_path, source_file)

    def collect_files(self):
        """Find and write static files. Along the way ignore the "compiled"
        directory, if present"""
        write_storage = StaticFilesStorage(self.BUILD_DIR + "/static/")
        original_dirs = settings.STATICFILES_DIRS
        settings.STATICFILES_DIRS = [s for s in original_dirs
                                     if s != 'compiled']
        for prefixed_path, source_file in self._input_files():
            write_storage.save(prefixed_path, source_file)
        settings.STATICFILES_DIRS = original_dirs

    def build_frontend(self):
        """Shell out to npm for building the frontend files"""
        os.chdir(self.BUILD_DIR)
        subprocess.call(["npm", "install"])
        os.chdir("..")

    def cleanup(self):
        shutil.copytree("%s/static/regulations" % self.BUILD_DIR,
                        self.TARGET_DIR)

    def handle(self, *args, **options):
        self.remove_dirs()
        self.copy_configs()
        self.collect_files()
        self.build_frontend()
        self.cleanup()
