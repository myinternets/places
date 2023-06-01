import sys
import re
from setuptools import setup, find_packages


setup(
    name="places",
    version="0.0.1",
    url="https://github.com/tarekziade/places",
    packages=find_packages(),
    description=("Search Your History"),
    author="Tarek Ziadé",
    author_email="tarek@ziade.org",
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'places = places.cli:main',
        ],
    },
)
