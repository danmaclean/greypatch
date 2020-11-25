from setuptools import setup

setup(
    name='redpatch',
    version='0.2.2',
    packages=['redpatch', 'redpatch_notebooks'],
    url='https://github.com/TeamMacLean/redpatch',
    license='LICENSE.txt',
    author='Dan MacLean',
    author_email='dan.maclean@tsl.ac.uk',
    description='Finding Disease Lesions in Plant Leaves',
    scripts=['scripts/redpatch-start', 'scripts/redpatch-batch-process'],
    include_package_data=True,
    package_data={"redpatch_notebooks": ['Redpatch Basic Use Example.ipynb',
                                         'leaf_and_square.jpg', 'single_input.jpg',
                                         'Using Threshold Sliders.ipynb',
                                         'Find Scale Card Filter Settings.ipynb'
                                         ]},
    python_requires='>=3.6',
    install_requires=[
        "ipywidgets == 7.4.1",
        "ipython == 6.5.0",
        "jupyter >= 1.0.0",
        "numpy >= 1.15.1",
        "numba >= 0.48.0",
        "matplotlib >= 2.1.2",
        "pytest >= 5.1.2",
        "scikit-image >= 0.13.1",
        "scipy >= 1.3.1",
        "pyyaml >=  3.13",
        "shapely >= 1.6.0",
        "pandas >= 0.23.4",
        "yattag >= 1.12.2"
    ],
)
