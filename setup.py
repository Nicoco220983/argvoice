import os
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(HERE, "README.md")) as f:
    LONG_DESCRIPTION = f.read()

VERSION = '0.0.1' 
DESCRIPTION = 'Python package to build a menu from voice recognition'

setup(
    name="argvoice", 
    version=VERSION,
    author="Nicolas Carrez",
    author_email="<nicolas.carrez@gmail.com>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        "pyaudio",
        "vosk",
        "pyttsx3",
    ],
)