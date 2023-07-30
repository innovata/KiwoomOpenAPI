# -*- coding: utf-8 -*-
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="KiwoomAPI",
    version="0.3.3",
    author="innovata sambong",
    author_email="iinnovata@gmail.com",
    description='Windows COM 기반으로 파이썬 32비트로만 동작하는 키움증권 오픈API 패키지',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=f"https://github.com/innovata/KiwoomOpenAPI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"":"src"},
    packages=setuptools.find_packages(),
    python_requires=">=3.8",
    install_requires=[
        'PyQt5', 'ipylib', 
    ],
)
