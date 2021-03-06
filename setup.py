import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="monki",
    version="0.1.1",
    description="Patch functions at runtime, the easy way.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/avivc/monki",
    author="Aviv Cohn",
    author_email="avivcohn1@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent"
    ],
    packages=["monki"],
    keywords="monkey patching utility programming development",
    include_package_data=True
)
