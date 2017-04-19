#!/usr/bin/env python
from setuptools import setup, find_packages
import os

__doc__ = """
A bug tracker.
"""


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='buggy',
    version='0.0.1',
    author='Fusionbox, Inc.',
    author_email='programmers@fusionbox.com',
    description=__doc__,
    long_description=read('README.md'),
    url='http://github.com/fusionbox/buggy',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'babel>=2.4',
        'Django>=1.11',
        'django-enumfields>=0.9',
        'django-compressor>=2.1',
        'django-pyscss>=2.0',
        'markdown>=2.6',
        'pillow>=4.1',
        'psycopg2>=2.7',
        'sorl-thumbnail>=12.4a1',
        'django-argonauts>=1.2',
        'django-ogmios>=0.10.0',
        'django-absoluteuri>=1.2.0',
        'bleach>=2.0.0',
    ],
    extras_require={
        'buggy_accounts': [
            'django-authtools>=1.5'
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: JavaScript',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    dependency_links=[
        # sorl 12.3 is packaged missing a migration. We need to install the
        # alpha version until 12.4 is on PyPI.
        'https://github.com/mariocesar/sorl-thumbnail/archive/v12.4a1.tar.gz#egg=sorl-thumbnail-12.4',
    ]
)
