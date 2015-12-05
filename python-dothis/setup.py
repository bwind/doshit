from distutils.core import setup
from distutils.command.install import install
from distutils import archive_util
from glob import iglob
from shutil import copy
from os.path import join
from os.path import basename

def copy_files(src_glob, dst_folder):
    for fname in iglob(src_glob):
        copy(fname, join(dst_folder, basename(fname)))

class custom_install(install):
    def run(self):
        install.run(self)
        #archive_util.mkpath("/etc/cloudburst", mode=774)
        #copy_files('cloudburst/config/*.yml', '/etc/cloudburst')

setup(name='dothis',
      version='0.1',
      description='DoThis',
      author='MetOcean Solutions',
      author_email='g.chalmers@metocean.co.nz',

      packages=['dothis'],

      cmdclass={'install': custom_install},

      install_requires=["redis",
                        "psutil"],
      )
