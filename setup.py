"""Setup script."""

import time
from setuptools import setup

setup(name='nemopt',
      # Use a datestamp as the version.
      version=time.strftime('%Y%m%d'),
      packages=['nemo'],
      description='National Electricity Market Optimiser',
      author='Ben Elliston',
      author_email='bje@air.net.au',
      license='GPLv3',
      url='https://nemo.ozlabs.org',
      keywords=['electricity', 'model', 'scenarios'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Programming Language :: Python',
          'Topic :: Scientific/Engineering'
      ],
      data_files=[('etc', ['nemo.cfg'])],
      scripts=['evolve.py', 'replay.py'],
      install_requires=['numpy', 'pandas', 'matplotlib', 'deap'])
