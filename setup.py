from setuptools import setup, find_packages

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='python-form',
    version='0.1.0',
    description='A package for communicating with FORM',
    long_description=readme(),
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
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Physics',
    ],
    keywords='form, computer algebra',
    packages=find_packages(),
    package_data={
        'form': ['init.frm'],
    },
    test_suite='nose.collector',
    tests_require=['nose'],
)
