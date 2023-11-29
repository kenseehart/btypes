from setuptools import setup

setup(
    name='btypes',
    version='0.1.1',
    author='Ken Seehart',
    author_email='ken@seehart.com',
    packages=['btypes'],
    url='https://github.com/kenseehart/btypes',
    license='LICENSE',
    description='A framework for structured bitfield processing',
    long_description=open('README.md').read(),
    install_requires=[
        "libcst",
    ],
)
