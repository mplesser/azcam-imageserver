# from setuptools import find_packages, setup
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="azcam-imageserver",
    version="21.2.1",
    description="azcam extension for remote image server",
    long_description_content_type="text/markdown",
    long_description=long_description,
    author="Michael Lesser",
    author_email="mlesser@arizona.edu",
    keywords="python",
    packages=find_packages(),
    zip_safe=False,
    install_requires=["azcam"],
)
