import os
from setuptools import setup, find_packages

VERSION = "1.0.0"


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="perl",
    version=VERSION,
    author="Richard Terry",
    author_email="code@radiac.net",
    description=("Perl as a Python package"),
    license="BSD",
    keywords="socket telnet",
    url="http://radiac.net/projects/python-perl/",
    long_description=read("README.rst"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Perl",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    install_requires=["six"],
    setup_requires=["pytest-runner"],
    tests_require=[
        "pytest",
        "pytest-black",
        "pytest-cov",
        "pytest-flake8",
        "pytest-isort",
        "pytest-mypy",
    ],
    zip_safe=True,
    packages=find_packages(exclude=("docs", "tests*")),
    include_package_data=True,
)
