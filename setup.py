from setuptools import setup

setup(
    name='redpatch',
    version='0.0.1.dev26',
    packages=['redpatch', 'redpatch_notebooks'],
    url='https://github.com/TeamMacLean/redspot',
    license='LICENSE.txt',
    author='Dan MacLean',
    author_email='dan.maclean@tsl.ac.uk',
    description='Finding Disease Lesions in Plant Leaves',
    scripts=['scripts/redpatch-start', 'scripts/redpatch-batch-process.py'],
    include_package_data=True,
    package_data={"redpatch_notebooks": ['Redpatch Basic Use Example.ipynb',
                                         'leaf_and_square.jpg', 'single_input.jpg',
                                         'Using Threshold Sliders.ipynb',
                                         'Find Scale Card Filter Settings.ipynb'
                                         ]},
    python_requires='>=3.7',
    install_requires=[
        "ipywidgets == 7.5.1",
        "ipython == 7.8.0",
        "jupyter == 1.0.0",
        "numpy == 1.17.1",
        "matplotlib >= 3.1.0",
        "pytest == 5.1.2",
        "scikit-image >= 0.16.2",
        "scipy == 1.3.1",
        "pyyaml >=  5.2",
        "shapely >= 1.6.0",
        "pandas >= 0.25.0"
    ],
)
