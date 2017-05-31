"""Setup script."""

from setuptools import find_packages, setup

_metadata = dict(
    name='python-form',
    version='0.2.1',
    description='A package for communicating with FORM',
    author='Takahiro Ueda',
    author_email='tueda@nikhef.nl',
    url='https://github.com/tueda/python-form',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Physics',
    ],
    keywords='binding, form, computer algebra',
    package_data={'form': ['init.frm']},
    setup_requires=['nose'],
)


def readme():
    """Read the README file."""
    with open('README.rst') as f:
        return f.read()


def setup_package():
    """Entry point."""
    md = dict(_metadata)
    md['long_description'] = readme()
    md['packages'] = find_packages()
    setup(**md)


if __name__ == '__main__':
    setup_package()
