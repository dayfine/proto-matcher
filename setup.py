import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="proto_matcher",
    version="0.0.2",
    author="dayfine",
    author_email="",
    description="Test matcher for protobuffer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dayfine/proto-matcher",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
