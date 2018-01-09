#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from pip.req import parse_requirements
import pip
import os

this_path = os.path.abspath(os.path.join(__file__,'..'))
requirements_path = os.path.join(this_path, 'requirements.txt')
reqs=[]
if os.path.exists(requirements_path):
    reqs = [str(ir.req) for ir in parse_requirements(requirements_path,
        session=pip.download.PipSession())]

setup(
    name='pewpew',
    version='0.1.0',
    description="PEW stands for Process Event-Wise. As this library does multiprocessing, this is PEW PEW.",
    long_description="TODO: Fill in",
    author="Kevin Wierman",
    author_email='kwierman@gmail.com',
    url='https://github.com/kwierman/pewpew',
    packages=find_packages(),
    package_dir={'pewpew':
                 'pewpew'},
    entry_points={
        'console_scripts': [
            'pewpew=pewpew.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=reqs,
    license="MIT license",
    zip_safe=False,
    keywords='pewpew',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests'
)
