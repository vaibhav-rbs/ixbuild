import os
import sys


__doc__ = """

Common variables, paths to files, etc
"""


rootDir = os.getcwd() 
shellDir = os.path.join(os.getcwd(), os.path.pardir, 'freenas/scripts')
build_script_path = ''



## git locations
git_paths = {'freenas-93' : 'https://github.com/freenas/freenas.git', 'freenas10' : 'https://github.com/freenas/freenas-build.git'} 
