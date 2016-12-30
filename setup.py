from setuptools import setup, find_packages


setup(name="opcua-widgets",
      version="0.4.0",
      description="OPC-UA Widgets",
      author="Olivier R-D et al.",
      url='https://github.com/FreeOpcUa/opcua-widgets',
      packages=["uawidgets"],
      license="GNU General Public License",
      install_requires=["freeopcua"],
      )
