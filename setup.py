from setuptools import setup

requirements = ['numpy','scipy','matplotlib','chaco','enable',\
                'kiwisolver','openptv']

setup(
    name='pyptv',
    version='0.1.3',
    description='Python GUI for the OpenPTV library `liboptv`',
    author="Alex Liberzon",
    author_email='alex.liberzon@gmail.com',
    url='https://github.com/alexlib/pyptv',
    packages=['pyptv'],
    entry_points={
        'console_scripts': [
            'pyptv=pyptv.cli:cli'
        ]
    },
    install_requires=requirements,
    keywords='pyptv',
    classifiers=[
        'Programming Language :: Python :: 2.7'
    ]
)
