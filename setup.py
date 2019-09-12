from setuptools import setup

setup(
    name='redspot',
    version='0.0.1dev',
    packages=['redspot', 'redspot_notebooks'],
    url='https://github.com/TeamMacLean/redspot',
    license='LICENSE.txt',
    author='Dan MacLean',
    author_email='dan.maclean@tsl.ac.uk',
    description='Finding Disease Lesions in Plant Leaves',
    scripts=['scripts/redspot-start'],
    include_package_data=True,
    package_data={"redspot_notebooks": ['Untitled.ipynb']},
    install_requires=[
        "jupyter >= 1.0.0"
    ],
)
