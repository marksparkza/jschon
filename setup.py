import pathlib

from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent.resolve()
README = (HERE / 'README.md').read_text(encoding='utf-8')

setup(
    name='jschon',
    version='0.2.0',
    description='A pythonic, extensible JSON Schema implementation.',
    long_description=README,
    long_description_content_type='text/markdown',
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
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    python_requires='~=3.8',
    install_requires=['rfc3986'],
    extras_require={
        'test': ['tox'],
        'dev': [
            'pytest',
            'coverage',
            'hypothesis',
            'pytest-benchmark',
        ]
    },
)
