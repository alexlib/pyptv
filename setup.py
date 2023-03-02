from setuptools import setup

requirements = [
    'chaco',
    'enable',
    'optv',
    'PyQt5',
    'scikit-image',
    'Pygments',
    'six',
    'imagecodecs',
    'flowtracks',
    'pandas',
    'tables',
    'pyparsing',
    'tqdm'
]

setup(
    name='pyptv',
    version='0.2.1',
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
