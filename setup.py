""" A setuptools based setup module.

"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
#with open(path.join(here, 'README.md'), encoding='utf-8') as f:
#    long_description = f.read()

setup(name='SPECtate',
      version='0.9',
      description='A monitoring application for SPECjbb',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
      ],
      install_requires=['docopt', 'six', 'schema', 'uuid'],
      extras_require={
          'dev' : ['testfixtures'],
      }
)
