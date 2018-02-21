from setuptools import setup, find_packages
from codecs import open
from os import path



here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='rental_checking',
    version='1.0.0',
    description='Checking encrypted equalities to provide privacy preserving rental checking',
    author='Fedor Beets',
    author_email='fedorbeets+rental@protonmail.ch',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Security :: Cryptography',
        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='rental checking functional encryption cryptography equality test',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=['web3',
                      'py_ecc',
                      'py-solc']

)
