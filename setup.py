#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools

setuptools.setup(
    name="eclabfiles",
    version="0.4.1",
    author="Nicolas Vetsch",
    author_email="vetschnicolas@gmail.com",
    description="Processing and converting of data files from BioLogic's EC-Lab.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/vetschn/eclabfiles",
    project_urls={"Bug Tracker": "https://github.com/vetschn/eclabfiles/issues"},
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
    ],
    keywords=["mpt", "mpr", "mps", "biologic", "ec-lab"],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    install_requires=["numpy", "pandas", "openpyxl"],
    python_requires=">=3.9",
)
