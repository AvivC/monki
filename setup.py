import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="monki",
    version="0.1.0",
    author="Aviv Cohn",
    author_email="avivcohn1@gmail.com",
    description="Easily patch functions at runtime.",
    long_description=long_description,
    url="https://github.com/AvivC/monki",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
