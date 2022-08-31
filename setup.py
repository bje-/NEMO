"""Setup script."""

import time

from setuptools import setup

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(name='nemopt',
      # Use a datestamp as the version.
      version=time.strftime('%Y%m%d'),
      packages=['awklite', 'nemo'],
      description='National Electricity Market Optimiser',
      author='Ben Elliston',
      author_email='bje@air.net.au',
      license='GPLv3',
      url='https://nemo.ozlabs.org',
      long_description=long_description,
      long_description_content_type='text/markdown',
      keywords=['electricity', 'model', 'scenarios'],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Environment :: X11 Applications',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Programming Language :: Python :: 3 :: Only',
          'Topic :: Scientific/Engineering',
      ],
      data_files=[('etc', ['nemo.cfg'])],
      scripts=['evolve', 'replay', 'summary'],
      install_requires=[
          'deap',
          'Gooey>=1.0.4',
          'matplotlib',
          'numpy',
          'pandas',
          'pint',
          'requests'])
