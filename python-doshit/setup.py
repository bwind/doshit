from distutils.core import setup
from distutils.command.install import install
from shutil import copy2
import os
import errno

class custom_install(install):
    def run(self):
        if (os.path.exists('/usr/local/bin/')):
            dest = '/usr/local/bin/doshit'
        else:
            dest = '/usr/bin/doshit'
        try:
            copy2('doshit.py', dest)
            install.run(self)
        except IOError, e:
            if e.errno == errno.EACCES:
                print ''
                print 'Permission denied:'
                print 'could not copy to {0}'.format(dest)
                print ''
                print 'try using:'
                print '$ sudo python setup.py install'
                print 'or'
                print '$ su'
                print '$ python setup.py install'
                print ''
            else:
                raise e

print setup(name='doshit',
      version='0.1.0',
      description='doshit',
      author='MetOcean Solutions',
      author_email='g.chalmers@metocean.co.nz',

      packages=['doshit'],

      cmdclass={'install': custom_install},

      install_requires=["redis", "psutil"])
