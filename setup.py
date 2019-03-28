from setuptools import setup

requirements = [
    # package requirements go here
    'optv',
    'numpy',
    'pyyaml',
    'scikit-image',
    'traits',
    'traitsui',
    'pygments',
    'future',
    'chaco',
    'enable'
]

setup(
    name='pyptv',
    version='0.1.1',
    description='Python GUI for the OpenPTV library `liboptv`',
    author="Alex Liberzon",
    author_email='alex.liberzon@gmail.com',
    url='https://github.com/alexlib/pyptv',
    packages=['pyptv'],
    entry_points={
        'console_scripts': [
            'pyptv=pyptv.cli:cli'
			'ptvgui=pyptv.pyptv_gui:main'
        ]
    },
    install_requires=requirements,
    keywords='pyptv',
    classifiers=[
        'Programming Language :: Python :: 2.7'
    ]
)
