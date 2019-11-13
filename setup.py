from setuptools import setup

requirements = [
'chaco==4.8.0',
'enable==4.8.1',
'numpy==1.17.3',
'optv==0.2.6',
'PyQt5==5.12.2',
'scikit-image==0.16.2',
'Pygments==2.4.2',
]

setup(
    name='pyptv',
    version='0.1.4',
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
