from setuptools import setup

setup(
    name='greypatch',
    version='0.1.0',
    packages=['greypatch'],
    url='https://github.com/TeamMacLean/greypatch',
    license='LICENSE.txt',
    author='Dan MacLean',
    author_email='dan.maclean@tsl.ac.uk',
    description='Finding Different Disease Lesions in Plant Leaves',
    scripts=['scripts/greypatch-batch-process'],
    python_requires='>=3.6',
    install_requires=[
        "ipywidgets == 7.5.1",
        "ipython == 7.8.0",
        "jupyter >= 1.0.0",
        "numpy >= 1.17.1",
        "numba >= 0.48.0",
        "matplotlib >= 3.1.0",
        "pytest >= 5.1.2",
        "scikit-image >= 0.16.2",
        "scipy >= 1.3.1",
        "pyyaml >=  5.2",
        "shapely >= 1.6.0",
        "pandas >= 0.25.0",
        "yattag >= 1.12.2"
    ],
)
