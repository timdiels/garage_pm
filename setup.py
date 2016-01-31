from chicken_turtle.setuptools import setup
from pathlib import Path

here = Path(__file__).parent

# setup
setup(
    # custom attrs
    here = here,
    readme_file='readme.md',
    
    # Overridden
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    # Note: you must add ancestors of any applicable classifier too
    classifiers='''
        Development Status :: 2 - Pre-Alpha
        Environment :: X11 Applications
        Environment :: X11 Applications :: Qt
        Intended Audience :: End Users/Desktop
        License :: OSI Approved
        License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)
        Natural Language :: English
        Operating System :: POSIX
        Operating System :: POSIX :: AIX
        Operating System :: POSIX :: BSD
        Operating System :: POSIX :: BSD :: BSD/OS
        Operating System :: POSIX :: BSD :: FreeBSD
        Operating System :: POSIX :: BSD :: NetBSD
        Operating System :: POSIX :: BSD :: OpenBSD
        Operating System :: POSIX :: GNU Hurd
        Operating System :: POSIX :: HP-UX
        Operating System :: POSIX :: IRIX
        Operating System :: POSIX :: Linux
        Operating System :: POSIX :: Other
        Operating System :: POSIX :: SCO
        Operating System :: POSIX :: SunOS/Solaris
        Operating System :: Unix
        Programming Language :: Python
        Programming Language :: Python :: 3 :: Only
        Programming Language :: Python :: 3
        Programming Language :: Python :: 3.2
        Programming Language :: Python :: 3.3
        Programming Language :: Python :: 3.4
        Programming Language :: Python :: 3.5
        Programming Language :: Python :: Implementation
        Programming Language :: Python :: Implementation :: CPython
        Programming Language :: Python :: Implementation :: Stackless
        Topic :: Office/Business
        Topic :: Office/Business :: Scheduling
    ''',
    
    # standard
    name='garage_pm',
    description='A basic cross-platform project management tool with a focus on one-man projects.',
    author='Tim Diels',
    author_email='timdiels.m@gmail.com',

    url='https://github.com/timdiels/garage_pm', # project homepage
 
    license='LGPL3',
 
    # What does your project relate to?
    keywords='office project-management',
 
    # Required dependencies
    setup_requires='chicken_turtle'.split(), # required to run setup.py. I'm not aware of any setup tool that uses this though
    install_requires=(
        'pyqt click '
    ).split(),
 
    # Optional dependencies
    extras_require={
        'dev': ''.split(),
        'test': 'pytest pytest-benchmark pytest-timeout pytest-xdist freezegun'.split(),
    },
    
    # Auto generate entry points
    entry_points={
        'console_scripts': [
            'garage-pm = garage_pm.main:main', # just an example, any module will do, this template doesn't care where you put it
        ],
    },
)