from setuptools import setup
from Cython.Build import cythonize

setup(
    name='FastBitboard Engine',
    ext_modules=cythonize("FastBitboard.pyx", compiler_directives={'language_level': "3"}),
)