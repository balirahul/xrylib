from setuptools import setup, find_packages

setup(
    name="xrylib",
    version="1.0.0",
    description="Python library for parsing and extracting forensic data from XRY files",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="xrylib contributors",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Intended Audience :: Science/Research",
    ],
    keywords="forensics mobile xry msab digital-forensics",
)
