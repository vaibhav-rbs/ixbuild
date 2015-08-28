import unittest
import sys

loader = unittest.TestLoader()
r = loader.discover('./')
results = unittest.TestResult()
r.run(results)


