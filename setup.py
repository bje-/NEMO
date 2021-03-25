"""Setup script."""

import time
from setuptools import setup

setup(name='nemopt',
      # Use a datestamp as the version.
      version=time.strftime('%Y%m%d'),
      packages=['dijkstra', 'nemo'],
      description='National Electricity Market Optimiser',
      author='Ben Elliston',
      author_email='bje@air.net.au',
      license='GPLv3',
      url='https://nemo.ozlabs.org',
      keywords=['electricity', 'model', 'scenarios'],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Programming Language :: Python :: 3 :: Only',
          'Topic :: Scientific/Engineering'
      ],
      data_files=[('etc', ['nemo.cfg'])],
      scripts=['evolve', 'replay'],
      install_requires=[
          'deap',
          'Gooey>=1.0.4',
          'matplotlib',
          'numpy',
          'pandas',
          'pint'])
