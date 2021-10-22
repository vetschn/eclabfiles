#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools

setuptools.setup(
    name="eclabfiles",
    version="0.2.dev",
    author="Nicolas Vetsch",
    author_email="nicolas.vetsch@gmx.ch",
    description="Parsing and converting of files from BioLogic's EC-Lab.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/vetschn/eclabfiles",
    classifiers=["Programming Language :: Python :: 3", ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(include=["eclabfiles"]),
    install_requires=["numpy", "pandas", "openpyxl"],
    python_requires=">=3.8",
    entry_points={"console_scripts": ['eclabfiles=eclabfiles.main']},
)
