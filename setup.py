import pathlib
import re

from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent.resolve()
README = (HERE / 'README.rst').read_text(encoding='utf-8')
VERSION = eval(re.search(
    '^__version__ = (.*)$',
    (HERE / 'jschon' / '__init__.py').read_text(encoding='utf-8'),
    re.MULTILINE,
)[1])

setup(
    name='jschon',
    version=VERSION,
    description='A pythonic, extensible JSON Schema implementation.',
    long_description=README,
    long_description_content_type='text/x-rst',
    url='https://github.com/marksparkza/jschon',
    author='Mark Jacobson',
    author_email='mark@saeon.ac.za',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    python_requires='~=3.8',
    install_requires=[
        'rfc3986',
    ],
    extras_require={
        'requests': [
            'requests',
        ],
        'test': [
            'tox',
        ],
        'dev': [
            'pytest',
            'coverage',
            'hypothesis<6.0.4',
            'pytest-benchmark',
            'pytest-httpserver',
            'requests',
        ],
        'doc': [
            'sphinx',
            'sphinx-rtd-theme',
        ],
    },
)
