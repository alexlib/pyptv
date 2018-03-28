from setuptools import setup

requirements = [
    # package requirements go here
]

setup(
    name='pyptv',
    version='0.1.0',
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
