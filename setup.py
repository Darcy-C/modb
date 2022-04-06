import setuptools

setuptools.setup(
    name="modb",
    version="0.0.1",
    author="darcy",
    # author_email="",
    description="My Own DataBase Implementation",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    # url="https://github.com/pypa/sampleproject",
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
