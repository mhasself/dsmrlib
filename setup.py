from distutils.core import setup

VERSION = '0.1'

import glob

## Everything in bin is a script
scripts = [x for x in glob.glob('bin/*') if x[-1] != '~']

setup (name = 'dsmrlib',
       version = VERSION,
       description = 'Down-sampling and multi-res data sources.',
       #package_dir = {'dsmrlib': 'python'},
       scripts = scripts,
       packages = ['dsmrlib',
                   ])
