from setuptools import setup, find_packages

setup(
    name='Jschon',
    version='0.1.0',
    description='A pythonic, extensible JSON Schema implementation',
    url='https://github.com/marksparkza/jschon',
    author='Mark Jacobson',
    python_requires='~=3.8',
    packages=find_packages(),
    install_requires=[
        'rfc3986',
    ],
    extras_require={
        'formats': [
            'python-dateutil',
            'email-validator',
            'idna',
            'rfc3987',
            'validators',
            'uri-template',
        ],
        'test': [
            'pytest',
            'coverage',
            'hypothesis',
        ],
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
    ],
)
