from setuptools import find_packages, setup

with open("README.rst") as f:
    long_description = f.read()


setup(
    name="web-poet",
    version="0.6.0",
    description="Zyte's Page Object pattern for web scraping",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author="Zyte Group Ltd",
    author_email="opensource@zyte.com",
    url="https://github.com/scrapinghub/web-poet",
    packages=find_packages(exclude=("tests",)),
    package_data={
        "web_poet": ["py.typed"],
    },
    install_requires=[
        "attrs >= 21.3.0",
        "parsel",
        "url-matcher",
        "multidict",
        "w3lib >= 1.22.0",
        "async-lru >= 1.0.3",
        "itemadapter >= 0.7.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
