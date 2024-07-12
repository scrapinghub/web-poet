from setuptools import find_packages, setup

with open("README.rst") as f:
    long_description = f.read()


setup(
    name="web-poet",
    version="0.17.0",
    description="Zyte's Page Object pattern for web scraping",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author="Zyte Group Ltd",
    author_email="opensource@zyte.com",
    url="https://github.com/scrapinghub/web-poet",
    packages=find_packages(include=["web_poet*"]),
    package_data={
        "web_poet": ["py.typed"],
    },
    entry_points={"pytest11": ["web-poet = web_poet.testing.pytest"]},
    install_requires=[
        "attrs >= 21.3.0",
        "form2request >= 0.1.1",
        "parsel >= 1.8.1",
        "url-matcher >= 0.2.0",
        "multidict >= 0.5.0",
        "w3lib >= 1.22.0",
        "async-lru >= 1.0.3",
        "itemadapter >= 0.8.0",
        "andi >= 0.5.0",
        "python-dateutil >= 2.7.0",
        "time-machine >= 2.7.1",
        "packaging >= 20.0",
        "backports.zoneinfo >= 0.2.1; python_version < '3.9' and platform_system != 'Windows'",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
