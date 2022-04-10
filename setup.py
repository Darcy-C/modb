import setuptools

with open('./README.md', mode='r') as f:
    long_description = f.read()


setuptools.setup(
    name="modb-py",
    version="0.2",
    author="Darcy-C",
    # author_email="",
    description="modb, on-disk-database, the replacement for open. no third party dependency, using btree internally.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Darcy-C/modb",
    # project_urls={
    #     "Bug Tracker": "https://github.com/pypa/sampleproject/issues",
    # },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    # install_requires=[''],
    python_requires=">=3.6",
)
