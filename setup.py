# -*- coding: utf-8 -*-
import setuptools
import os 


PROEJCT_DIR = os.path.dirname(os.path.abspath(__file__))


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


# file = os.path.join(PROEJCT_DIR, 'requirements.txt')
# with open('requires.txt', "r", encoding="utf-8") as f:
#     text = f.read().strip()
#     f.close()
#     packages = text.split('\n')
#     INSTALL_REQUIRES = [pack.strip() for pack in packages if len(pack.strip()) > 0]


PROJECT_PACKAGE_DIR = 'src'



setuptools.setup(
    name="kiwoomapi",
    version="0.5.4",
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
    package_dir={"": PROJECT_PACKAGE_DIR},
    packages=setuptools.find_packages(PROJECT_PACKAGE_DIR),
    python_requires=">=3.8",
    install_requires=[
        'PyQt5==5.15.1',
        'ipylib',
    ],
)

