from distutils.core import setup
from distutils.command.install import install

class custom_install(install):
    def run(self):
        install.run(self)
        

print setup(name='dothis',
      version='0.0.1',
      description='DoThis',
      author='MetOcean Solutions',
      author_email='g.chalmers@metocean.co.nz',

      packages=['dothis'],

      cmdclass={'install': custom_install},

      requires=["redis", "psutil"],
      )
