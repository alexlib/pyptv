from setuptools import setup
import versioneer

requirements = [
    'openptv'
]

setup(
    name='pyptv',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Python GUI for the OpenPTV",
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
