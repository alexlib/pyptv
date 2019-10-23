from setuptools import setup

requirements = [
    'numpy==1.16.4',
    'certifi==2019.6.16',
    'chaco==4.7.2',
    'cloudpickle==1.2.1',
    'dask==1.2.2',
    'decorator==4.4.0',
    'enable==4.7.2',
    'fonttools==3.43.1',
    'future==0.17.1',
    'imageio==2.5.0',
    'libtiff==0.4.2',
    'networkx==2.3',
    'optv==0.2.6',
    'Pillow==6.2.0',
    'pyface==6.1.1',
    'Pygments==2.4.2',
    'PyQt5==5.12.2',
    'PyWavelets==1.0.3',
    'pyxdg==0.26',
    'PyYAML==5.1.1',
    'scikit-image==0.15.0',
    'scipy==1.3.0',
    'six==1.12.0',
    'toolz==0.9.0',
    'traits==5.1.1',
    'traitsui==6.1.1',
    'wincertstore==0.2',
]

setup(
    name='pyptv',
    version='0.1.3a',
    description='Python GUI for the OpenPTV library `liboptv`',
    author="Alex Liberzon",
    author_email='alex.liberzon@gmail.com',
    url='https://github.com/alexlib/pyptv',
    packages=['pyptv'],
    entry_points={
        'console_scripts': [
    		'pyptv=pyptv.pyptv_gui:main'
        ]
    },
    install_requires=requirements,
    keywords='pyptv',
    classifiers=[
        'Programming Language :: Python :: 3'
    ]
)
