import os
import unittest


def load_tests(loader, standard_tests, pattern):
    # top level directory cached on loader instance
    this_dir = os.path.dirname(__file__)
    package_tests = loader.discover(start_dir=this_dir)
    standard_tests.addTests(package_tests)
    return standard_tests


#unittest.main()
