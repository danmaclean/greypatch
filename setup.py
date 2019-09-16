from setuptools import setup

setup(
    name='redspot',
    version='0.0.1dev0',
    packages=['redspot', 'redspot_notebooks'],
    url='https://github.com/TeamMacLean/redspot',
    license='LICENSE.txt',
    author='Dan MacLean',
    author_email='dan.maclean@tsl.ac.uk',
    description='Finding Disease Lesions in Plant Leaves',
    scripts=['scripts/redspot-start'],
    include_package_data=True,
    package_data={"redspot_notebooks": ['Redspot Basic Use Example.ipynb']},
    python_requires='>=3.7',
    install_requires=[
        "jupyter >= 1.0.0",
        "scikit-image >= 0.15.0",
        "scipy >= 1.3.1",
        "numpy >= 1.17.1",
        "matplotlib >= 3.1.1",
        "pytest >= 5.1.2"
    ],
)
