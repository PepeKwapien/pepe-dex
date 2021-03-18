from distutils.core import setup
import py2exe

setup(console=['gui.py'], requires=['requests', 'pyglet', 'PIL', 'python-Levenshtein', 'py2exe'])
