import setuptools
import pathlib


setuptools.setup(
    name="epidatpy",
    version="1.0.0",
    author="Alex Reinhart",
    author_email="areinhar@stat.cmu.edu",
    description="A programmatic interface to Delphi's Epidata API.",
    long_description=pathlib.Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/cmu-delphi/epidatpy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    python_requires=">=3.6",
    install_requires=[f.strip() for f in pathlib.Path("requirements.txt").read_text().split("\n") if f],
    # package_data={'epidatpy': []}
)
