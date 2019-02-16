import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="monki",
    version="0.1.0",
    description="Easily patch functions at runtime.",
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
    include_package_data=True
)
