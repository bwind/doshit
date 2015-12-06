from distutils.core import setup
from distutils.command.install import install

class custom_install(install):
    def run(self):
        install.run(self)


print setup(name='doshit',
      version='0.1.0',
      description='doshit',
      author='MetOcean Solutions',
      author_email='g.chalmers@metocean.co.nz',

      packages=['doshit'],

      cmdclass={'install': custom_install},

      requires=["redis", "psutil"],
      )
