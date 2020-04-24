from setuptools import setup, find_packages


with open('README.rst') as f:
    long_description = f.read()


setup(
    name='core-po',
    version='0.0.1',
    description="Scrapinghub's Page Object pattern for web scraping",
    long_description=long_description,
    author='Scrapinghub',
    author_email='info@scrapinghub.com',
    # FIXME: change url when repository is moved to Scrapinghub's organization
    url='https://github.com/victor-torres/core-po',
    packages=find_packages(
        exclude=(
            'tests',
        )
    ),
    install_requires=(
        'andi>=0.3',
        'attrs',
        'parsel',
    ),
    classifiers=(
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ),
)
