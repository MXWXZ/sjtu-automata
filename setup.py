import setuptools
from sjtu_automata.__version__ import __title__, __description__, __url__, __version__, __author__, __author_email__, __license__

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name=__title__,
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    description=__description__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    license=__license__,
    url=__url__,
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'colorama',
        'requests',
        'Pillow',
        'click>=7.0',
        'pytesseract',
        'tenacity',
    ],
    python_requires='>=3',
    entry_points={
        'console_scripts': [
            'autoelect=sjtu_automata.autoelect:cli',
        ],
    },
)
