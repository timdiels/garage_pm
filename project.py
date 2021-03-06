
project = dict(
    # Changing these attributes is not supported (you'll have to manually move and edit files)
    name='garage-pm',  # PyPI (or other index) name.
    package_name='garage_pm',  # name of the root package of this project, e.g. 'myproject' or 'myproject.subproject' 
    human_friendly_name='Garage Project Management',
    
    #
    description='A basic cross-platform project management tool with a focus on one-man projects.',
    author='Tim Diels',  # will appear in copyright mentioned in documentation: 'year, your name'
    author_email='timdiels.m@gmail.com',
    python_version=(3,5),
    readme_file='README.md',
    url='https://github.com/timdiels/garage_pm', # project homepage
    download_url='https://github.com/timdiels/garage_pm/releases/v{version}.tar.gz', # Template for url to download source archive from. You can refer to the current version with {version}. You can get one from github or gitlab for example.
    license='LGPL3',
 
    # What does your project relate to?
    keywords='office project-management',
    
    # Package indices to release to using `ct-release`
    # These names refer to those defined in ~/.pypirc.
    # For pypi, see http://peterdowns.com/posts/first-time-with-pypi.html
    # For devpi, see http://doc.devpi.net/latest/userman/devpi_misc.html#using-plain-setup-py-for-uploading
    index_test = 'pypitest',  # Index to use for testing a release, before releasing to `index_production`. `index_test` can be omitted if you have no test index
    index_production = 'pypi',
    
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
 
    # Auto generate entry points (optional)
    entry_points={
        'console_scripts': [
            'garage-pm = garage_pm.main:main',
        ],
    },
)
