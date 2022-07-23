#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pipenv install twine --dev

import os
import sys

from setuptools import Command, setup, find_packages
from Cython.Distutils import build_ext, Extension

# Package meta-data.
NAME = 'aiouring'
DESCRIPTION = 'An io_uring adapter for asyncio, depends on liburing.so'
URL = 'https://github.com/GhostSignal/aiouring'
EMAIL = '2685780449@qq.com'
AUTHOR = 'GhostSignal'
REQUIRES_PYTHON = '>=3.6.0'
VERSION = "0.1.0"

# What packages are required for this module to be executed?
REQUIRED = [
    # 'requests', 'maya', 'records',
]

# What packages are optional?
EXTRAS = {
    # 'fancy feature': ['django'],
}

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        LONG_DESCRIPTION = '\n' + f.read()
except FileNotFoundError:
    LONG_DESCRIPTION = DESCRIPTION

# Impott C/C++ source code files
C_CPP_FILES = []
for root, _, files in os.walk(os.path.join(here, NAME)):
    for i in files:
        if i.split(".")[-1].lower() in ("h", "c", "hpp", "cpp"):
            C_CPP_FILES.append(os.path.join(root, i)[len(here)+1:])


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from shutil import rmtree
        self.status('Removing previous builds…')
        for i in ('dist', 'build', NAME.lower()+'.egg-info'):
            try:
                rmtree(os.path.join(here, i))
            except OSError:
                pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system(f'{sys.executable} setup.py sdist bdist_wheel --universal')

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        self.status('Pushing git tags…')
        os.system(f'git tag v{VERSION}')
        os.system('git push --tags')

        sys.exit()


# Where the magic happens:
setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    platforms=[sys.platform],
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=["tests", "tests.*"]),
    # If your package is a single module, use this instead of 'packages':
    # py_modules=['mypackage'],

    # entry_points={
    #     'console_scripts': ['mycli=mymodule:cli'],
    # },
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='MIT',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Topic :: System :: Networking',
        'Programming Language :: Cython',
        'Programming Language :: Python :: 3',
    ],
    # $ setup.py publish support.
    cmdclass={
        'build_ext': build_ext,
        'upload': UploadCommand,
    },
    ext_modules=[
        Extension(
            "aiouring._core",
            ["aiouring/_core/UringProactor.pyx"],
            include_dirs=["aiouring/_core"],
            libraries=['uring'],
            cython_cplus=True,
            cython_c_in_temp=True
        )
    ],
    headers=C_CPP_FILES
)
